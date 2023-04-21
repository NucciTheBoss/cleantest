# Copyright 2023 Jason C. Nucciarone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Archon for the LXD test environment provider."""

import csv
import json
import logging
import os
import pathlib
import shlex
import shutil
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from io import BytesIO, StringIO
from ipaddress import IPv4Address, IPv6Address
from typing import Deque, Dict, List, Optional, Tuple, Union

from pylxd import Client

from cleantest import Env
from cleantest.data import Dir, File
from cleantest.hooks import StartEnvHook, StopEnvHook
from cleantest.meta import Result, Singleton
from cleantest.meta.utils import sourcefetch, thread_count
from cleantest.utils import run

from .config import LXDConfigurer

logger = logging.getLogger(__name__)


class Error(Exception):
    """Raise when LXDArchon encounters an error."""


@dataclass(frozen=True)
class _WorkOrder:
    target: str


@dataclass(frozen=True)
class _DeployWorkOrder(_WorkOrder):
    image: str
    provision_script: Optional[os.PathLike] = None
    resources: Optional[List[File, Dir]] = None


@dataclass(frozen=True)
class _ExecuteWorkOrder(_WorkOrder):
    command: str


@dataclass(frozen=True)
class _PushWorkOrder(_WorkOrder):
    data: Union[File, Dir]
    uid: Optional[int] = None
    username: Optional[str] = None
    gid: Optional[int] = None
    groupname: Optional[str] = None
    mode: Optional[oct] = None
    overwrite: bool = False


def _handle_startenv_hooks(instance, hooks: Deque[StartEnvHook]) -> None:
    """Handle StartEnvHooks.

    Args:
        instance: Test environment instance to operate on.
        hooks: Start environment hooks to process.
    """
    dispatch = {"charmlib": lambda x: Env().add(json.loads(x))}
    logger.debug(f"Executing StartEnvHooks {hooks} inside {instance.name}")
    while hooks:
        hook = hooks.pop()
        if hook.packages:
            for package in hook.packages:
                tmp = package._dumps()
                instance.execute(["mkdir", "-p", "/root/init/pkg"])
                instance.files.put("/root/init/pkg/install", tmp["injectable"])
                result = instance.execute(["python3", "/root/init/pkg/install"])

                if package.__class__.__name__.lower() in dispatch:
                    dispatch[package.__class__.__name__.lower()](result.stdout)
        if hook.push:
            for item in hook.push:
                item.load()
                tmp = item._dumps(mode="push")
                instance.execute(["mkdir", "-p", "/root/init/data"])
                instance.files.put("/root/init/data/dump", tmp["injectable"])
                instance.execute(["python3", "/root/init/data/dump"])


def _handle_stopenv_hooks(instance, hooks: Deque[StopEnvHook]) -> None:
    """Handle StopEnvHooks.

    Args:
        instance: Test environment instance to operate on.
        hooks: Stop environment hooks to process.
    """
    logger.debug(f"Executing StopEnvHooks {hooks} inside {instance.name}")
    while hooks:
        hook = hooks.pop()
        if hook.pull:
            for item in hook.pull:
                tmp = item._dumps(mode="pull")
                instance.execute(["mkdir", "-p", "/root/.stopenv/pull"])
                instance.files.put(
                    "/root/.stopenv/pull/load",
                    tmp["injectable"],
                )
                result = json.loads(
                    instance.execute(["python3", "/root/.stopenv/pull/load"]).stdout
                )
                tmp = item._loads(result["checksum"], result["data"])
                tmp.dump()


class LXDArchon(metaclass=Singleton):
    """Direct the LXD test environment provider via the LXD API socket."""

    _instances = set()

    @property
    def _client(self) -> Client:
        """Connect to LXD API Unix socket."""
        return Client(**self.config.client.dict())

    @property
    def config(self) -> LXDConfigurer:
        """Get the LXD test environment provider configurer."""
        return LXDConfigurer()

    @property
    def env(self) -> Env:
        """Get environment configuration information."""
        return Env()

    def exists(self, target: str) -> bool:
        """Check that specified test environment instance exists.

        Args:
            target: Instance to determine existence of.
        """
        return self._client.instances.exists(target)

    def deploy(
        self,
        target: Union[str, List[str]],
        image: str,
        provision_script: Optional[Union[str, os.PathLike]] = None,
        resources: Optional[List[Union[File, Dir]]] = None,
    ) -> None:
        """Deploy a new test environment instance to the LXD cluster.

        Args:
            target: Name of new test environment instance to add to the cluster.
            image: Image to use for new test environment instance.
            provision_script: Provisioning script to run after new instance starts.
            resources:
                Resources to upload into the test environment instance after
                new instance starts. You should only upload resources that are
                required for provisioning the test environment instance.
        """
        targets = [target] if type(target) == str else target
        resources = resources if resources is not None else []
        with ProcessPoolExecutor(max_workers=thread_count()) as executor:
            work_sheet = [
                _DeployWorkOrder(
                    target=target,
                    image=image,
                    provision_script=provision_script,
                    resources=resources,
                )
                for target in targets
            ]
            for result in executor.map(self._deploy, work_sheet):
                self._instances.add(result)

    def _deploy(self, work_order: _DeployWorkOrder) -> str:
        """Deploy a new test environment instance. INTERNAL USE ONLY.

        Returns:
            str: Name of deployed instance.
        """
        config = self.config.fetch_config(work_order.image)
        config.name = work_order.target
        logger.debug(f"Creating instance {config.name} with configuration:\n{config}")
        self._client.instances.create(config.dict(), wait=True)
        instance = self._client.instances.get(config.name)
        # TODO: Need to modify the start function so that it does not
        #   progress until a LXD VM has been assigned a public address.
        #   e.g. a `test_connectivity` method or something similar
        instance.start(wait=True)

        logger.debug(f"Injecting cleantest and dependencies into {config.name}")
        instance.execute(["mkdir", "-p", "/root/.init/cleantest"])
        for name, data in sourcefetch():
            instance.files.put(
                f"/root/.init/cleantest/install_{name}",
                data["injectable"],
            )
            instance.execute(["python3", f"/root/.init/cleantest/install_{name}"])

        for resource in work_order.resources:
            logger.debug(f"Uploading resource to {config.name}")
            self.push(
                config.name,
                src=resource.src,
                dest=resource.dest,
                username="root",
                groupname="root",
            )

        if work_order.provision_script is not None:
            logger.debug(f"Executing provision script on {config.name}")
            self.push(
                config.name,
                src=work_order.provision_script,
                dest="/root/.init/provision",
            )
            instance.execute(["python3", "/root/.init/provision"])

        _handle_startenv_hooks(instance, self.config.startenv_hooks)

        return config.name

    def execute(self, target: Union[str, List[str]], command: str) -> Dict[str, Result]:
        """Execute commands on test environment instances.

        Args:
            target: Test environment instance(s) to execute command inside of.
            command: Command to execute on test environment instances.
        """
        targets = [target] if type(target) == str else target
        for target in targets:
            if not self.exists(target):
                raise Error(f"Target instance {target} does not exist.")

        results = {}
        with ProcessPoolExecutor(max_workers=thread_count()) as executor:
            work_sheet = [_ExecuteWorkOrder(target, command) for target in targets]
            for name, result in executor.map(self._execute, work_sheet):
                results.update({name: result})

        return results

    def _execute(self, work_order: _ExecuteWorkOrder) -> Tuple[str, Result]:
        """Execute command on test environment instance. INTERNAL USE ONLY.

        Returns:
            Tuple[str, Result]: Name of target instance and result of execution.
        """
        logger.debug(f"Executing command {work_order.command} on {work_order.target}")
        instance = self._client.instances.get(work_order.target)
        result = instance.execute(
            shlex.split(work_order.command), environment=self.env.dumps()
        )
        return work_order.target, Result(result.exit_code, result.stdout, result.stderr)

    def restart(self, target: Union[str, List[str]]) -> None:
        """Restart test environment instances.

        Args:
            target: Test environment instance(s) to restart.
        """
        targets = [target] if type(target) == str else target
        for target in targets:
            if not self.exists(target):
                raise Error(f"Target instance {target} does not exist.")

        with ProcessPoolExecutor(max_workers=thread_count()) as executor:
            work_sheet = [_WorkOrder(target=target) for target in targets]
            for _ in executor.map(self._restart, work_sheet):
                pass

    def _restart(self, work_order: _WorkOrder) -> None:
        """Restart test environment instance. INTERNAL USE ONLY."""
        logger.debug(f"Restarting instance {work_order.target}")
        instance = self._client.instances.get(work_order.target)
        instance.restart(wait=True)

    def remove(self, target: Union[str, List[str]]) -> None:
        """Remove test environment instances from LXD provider.

        Args:
            target: Test environment instance(s) to remove.
        """
        targets = [target] if type(target) == str else target
        for target in targets:
            if not self.exists(target):
                raise Error(f"Target instance {target} does not exist.")

        with ProcessPoolExecutor(max_workers=thread_count()) as executor:
            work_sheet = [_WorkOrder(target=target) for target in targets]
            for _ in executor.map(self._remove, work_sheet):
                pass

    def _remove(self, work_order: _WorkOrder) -> None:
        """Remove test environment instance from LXD provider. INTERNAL USE ONLY."""
        logger.debug(f"Removing instance {work_order.target}")
        instance = self._client.instances.get(work_order.target)
        _handle_stopenv_hooks(instance, self.config.stopenv_hooks)
        instance.stop(wait=True)
        instance.delete(wait=True)

    def destroy(self) -> None:
        """Destroy all test environment instances in LXD provider."""
        logger.debug(f"Destroying instances {self._instances}")
        self.remove([*self._instances])

    def pull(
        self,
        target: str,
        src: Union[str, os.PathLike],
        dest: Union[str, os.PathLike],
        uid: Optional[int] = None,
        username: Optional[str] = None,
        gid: Optional[int] = None,
        groupname: Optional[str] = None,
        mode: Optional[oct] = None,
        overwrite: bool = False,
    ) -> None:
        """Pull object from test environment instance.

        Args:
            target: Instance to pull object from.
            src: Location of object to pull from test environment instance.
            dest: Destination to save object to on host.
            uid: uid to set as owner of object on host. Default: None.
            username: User to set as owner of object on host. Default: None.
            gid: gid to set as group of object on host. Default: None.
            groupname: Group name to set as group of object on host. Default: None.
            mode: Mode to set on object on host. Default: None.
            overwrite: Overwrite object if it already exists on host. Default: False.
        """
        if not self.exists(target):
            raise Error(f"Target instance {target} does not exist.")
        if uid and username:
            raise Error("Specify only uid or username, not both.")
        if gid and groupname:
            raise Error("Specify only gid or groupname, not both.")

        instance = self._client.instances.get(target)
        instance.execute(["mkdir", "-p", "/root/.pull"])
        if instance.execute(["test", "-f", f"{src}"]).exit_code == 0:
            data = File(src, dest, overwrite=overwrite)
        elif instance.execute(["test", "-d", f"{src}"]).exit_code == 0:
            data = Dir(src, dest, overwrite=overwrite)
        else:
            raise Error(f"{src} is neither file or directory in {target}.")

        instance.files.put("/root/.pull/load", data._dumps(mode="pull")["injectable"])
        tmp = json.loads(instance.execute(["python3", "/root/.pull/load"]).stdout)
        result = data.__class__._loads(tmp["checksum"], tmp["data"])
        result.dump()
        if result.dest.is_dir():
            for directory in result.dest.iterdir():
                if uid or username:
                    shutil.chown(directory, user=uid or username)
                if gid or groupname:
                    shutil.chown(directory, group=gid or groupname)
                if mode:
                    directory.chmod(mode)
        else:
            if uid is not None or username is not None:
                shutil.chown(data.dest, user=uid or username)
            if gid or groupname is not None:
                shutil.chown(data.dest, group=gid or groupname)
            if mode is not None:
                data.dest.chmod(mode)

    def push(
        self,
        target: Union[str, List[str]],
        src: Union[str, os.PathLike, StringIO, BytesIO],
        dest: Union[str, os.PathLike],
        uid: Optional[int] = None,
        username: Optional[str] = None,
        gid: Optional[int] = None,
        groupname: Optional[str] = None,
        mode: Optional[oct] = None,
        overwrite: bool = False,
    ) -> None:
        """Push an object into test environment instances.

        Args:
            target: Instance to push object to.
            src: Location of object to push to instance.
            dest: Destination to save object to on instance.
            uid: uid to set as owner of object on instance. Default: None.
            username: User to set as owner of object on instance. Default: None.
            gid: gid to set as group of object on instance. Default: None.
            groupname: Group name to set as group of object on instance. Default: None.
            mode: Mode to set on object on instance. Default: None.
            overwrite: Overwrite object on instance if it exists. Default: False.
        """
        targets = [target] if type(target) == str else target
        for target in targets:
            if not self.exists(target):
                raise Error(f"Target instance {target} does not exist.")
        if uid and username:
            raise Error("Specify only uid or username, not both.")
        if gid and groupname:
            raise Error("Specify only gid or groupname, not both.")

        if pathlib.Path(src).is_file() or type(src) == StringIO or type(src) == BytesIO:
            data = File(src, dest, overwrite=overwrite)
        elif pathlib.Path(src).is_dir():
            data = Dir(src, dest, overwrite=overwrite)
        else:
            raise FileNotFoundError(f"{src} not found on system.")

        with ProcessPoolExecutor(max_workers=thread_count()) as executor:
            work_sheet = [
                _PushWorkOrder(target, data, uid, username, gid, groupname, mode)
                for target in targets
            ]
            for _ in executor.map(self._push, work_sheet):
                pass

    def _push(self, work_order: _PushWorkOrder) -> None:
        """Push an object into test environment instances. INTERNAL USE ONLY."""
        instance = self._client.instances.get(work_order.target)
        instance.execute(["mkdir", "-p", "/root/.push"])
        work_order.data.load()
        instance.files.put(
            "root/.push/dump", work_order.data._dumps(mode="push")["injectable"]
        )
        instance.execute(["python3", "/root/.push/dump"])
        if work_order.uid or work_order.username:
            instance.execute(
                [
                    "chown",
                    "-R",
                    f"{work_order.uid or work_order.username}:",
                    f"{work_order.data.dest}",
                ]
            )
        if work_order.gid or work_order.groupname:
            instance.execute(
                [
                    "chown",
                    "-R",
                    f":{work_order.gid or work_order.groupname}",
                    f"{work_order.data.dest}",
                ]
            )
        if work_order.mode:
            instance.execute(
                ["chmod", "-R", f"{work_order.mode}", f"{work_order.data.dest}"]
            )

    def get_public_address(
        self, target: str, ipv6: bool = False
    ) -> Optional[Union[IPv4Address, IPv6Address]]:
        """Get the public address of a test environment instance.

        Args:
            target: Name of test environment instance.
            ipv6: Get the public IPv6 address rather than IPv4 address.
                Default: False.

        Returns:
            Union[IPv4Address, IPv6Address]:
                Public address of test environment instance.
                None if the instance does not have a public address.
        """
        # TODO: Eventually change this to use the LXD API provided by pylxd.
        tmp = csv.reader(StringIO(next(run("lxc list -c n46 -f csv")).stdout))
        for row in tmp:
            if row[0] == target and ipv6:
                return IPv6Address(row[2].split(" ")[0]) if row[2] != "" else None
            elif row[0] == target:
                return IPv4Address(row[1].split(" ")[0]) if row[1] != "" else None

        return None
