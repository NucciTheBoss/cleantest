#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Direct the LXD test environment provider and instances."""

import csv
import json
import logging
import os
import pathlib
import shlex
import shutil
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor
from io import StringIO
from ipaddress import IPv4Address, IPv6Address
from typing import Dict, List, Optional, Tuple, Union

from pylxd import Client

from cleantest.control.lxd._lxd_configurer import LXDConfigurer
from cleantest.data import Dir, File
from cleantest.meta import Result
from cleantest.meta._cleantest_info import CleantestInfo
from cleantest.meta.utils import thread_count
from cleantest.utils import run

logger = logging.getLogger(__name__)

# Metaclass to encapsulate work information sent to _add threads.
_AddWorkOrder = namedtuple(
    "_AddWorkOrder",
    ["name", "image", "provision_script", "resources"],
    defaults=[None, None, None, None],
)

# Metaclass to encapsulate work information sent to _execute threads.
_ExecuteWorkOrder = namedtuple(
    "_ExecuteWorkOrder",
    ["target", "command"],
    defaults=[None, None],
)


class LXDArchonError(Exception):
    """Raise when LXDArchon encounters an error."""


class LXDArchon:
    """Direct the LXD test environment provider via the LXD API socket."""

    __instances = set()

    def __new__(cls) -> "LXDArchon":
        """Create new LXDArchon instance.

        Returns:
            (LXDArchon): New LXDArchon instance.
        """
        if not hasattr(cls, f"_{cls.__name__}__instance"):
            cls.__instance = super(LXDArchon, cls).__new__(cls)
        return cls.__instance

    @property
    def __client(self) -> Client:
        """Establish connection to LXD API socket.

        Returns:
            (Client): Connection to LXD API socket.
        """
        return Client(**self.config.client_config.dict())

    @property
    def config(self) -> LXDConfigurer:
        """Get LXDConfigurer instance containing configuration information.

        Returns:
            (LXDConfigurer): LXDConfigurer instance.
        """
        return LXDConfigurer()

    def exists(self, target: str) -> bool:
        """Check that specified test environment instance exists.

        Args:
            target (str): Instance to determine existence of.

        Returns:
            (bool): True if instance exists; False if otherwise.
        """
        return self.__client.instances.exists(target)

    def add(
        self,
        name: Union[str, List[str]],
        image: str,
        provision_script: Optional[Union[str, os.PathLike]] = None,
        resources: Optional[List[Union[File, Dir]]] = None,
    ) -> None:
        """Add a new test environment instance to the LXD cluster.

        Args:
            name (Union[str, List[str]]):
                Name of new test environment instance to add to the cluster.
            image (str):
                Image to use for new test environment instance.
            provision_script (Optional[Union[bytes, os.PathLike, str]]):
                Provisioning script to run after new instance starts.
            resources (Optional[List[Union[File, Dir]]]):
                Resources to upload into the test environment instance after
                new instance starts. You should only upload resources that are
                required for provisioning the test environment instance.
        """
        names = [name] if type(name) == str else name
        resources = resources if resources is not None else []
        with ProcessPoolExecutor(max_workers=thread_count()) as pool:
            for result in pool.map(
                self._add,
                (
                    _AddWorkOrder(name, image, provision_script, resources)
                    for name in names
                ),
            ):
                self.__instances.add(result)

    def _add(self, work_order: _AddWorkOrder) -> str:
        """Sub-function for setting up new test environment instance.

        Args:
            work_order (_AddWorkOrder):
                Information needed to add a new test environment instance.
        """
        _ = self.config.get_instance_config(work_order.image)
        _.name = work_order.name
        self.__client.instances.create(_.dict(), wait=True)
        instance = self.__client.instances.get(work_order.name)
        # TODO: Need to modify the start function so that it does not
        #   progress until a LXD VM has been assigned a public address.
        instance.start(wait=True)

        logger.info("Before injection")
        instance.execute(shlex.split("mkdir -p /root/.init/cleantest"))
        for name, data in CleantestInfo().dumps():
            instance.files.put(
                f"/root/.init/cleantest/install_{name}",
                data["injectable"],
            )
            instance.execute(
                shlex.split(f"python3 /root/.init/cleantest/install_{name}")
            )
        logger.info("After injection")
        for resource in work_order.resources:
            self.push(
                work_order.name, data_obj=resource, username="root", groupname="root"
            )

        if work_order.provision_script is not None:
            logger.info(f"Executing provision script {work_order.provision_script}")
            self.push(
                work_order.name,
                data_obj=[File(work_order.provision_script, "/root/.init/provision")],
            )
            instance.execute(shlex.split("python3 /root/.init/provision"))

        return work_order.name

    def execute(self, target: Union[str, List[str]], command: str) -> Dict[str, Result]:
        """Execute commands on test environment instances.

        Args:
            target (Union[str, List[str]]):
                Test environment instances to execute commands inside of.
            command (str):
                Command to execute.
        """
        _ = {}
        targets = [target] if type(target) == str else target
        [self.exists(target) for target in targets]
        with ProcessPoolExecutor(max_workers=thread_count()) as pool:
            for name, result in pool.map(
                self._execute,
                (_ExecuteWorkOrder(target, command) for target in targets),
            ):
                assert result.exit_code == 0
                _.update({name: result})

        return _

    def _execute(self, work_order: _ExecuteWorkOrder) -> Tuple[str, Result]:
        """Sub-function for executing commands on test environment instances.

        Args:
            work_order (_ExecuteWorkOrder):
                Information needed to execute command on a test environment instance.

        Returns:
            (Tuple[str, Result]): Name of target instance and result of execution.
        """
        instance = self.__client.instances.get(work_order.target)
        _ = instance.execute(shlex.split(work_order.command))
        return work_order.target, Result(_.exit_code, _.stdout, _.stderr)

    def pull(  # noqa C901
        self,
        target: str,
        src: Optional[Union[str, os.PathLike]] = None,
        dest: Optional[Union[str, os.PathLike]] = None,
        data_obj: Optional[List[Union[Dir, File]]] = None,
        uid: Optional[int] = None,
        username: Optional[str] = None,
        gid: Optional[int] = None,
        groupname: Optional[str] = None,
        mode: Optional[oct] = None,
        overwrite: bool = False,
    ) -> None:
        """Pull object from test environment instance.

        Args:
            target (str):
                Instance to pull object from.
            src (Optional[Union[str, os.PathLike]]):
                File path of object to pull from test environment instance.
                (Default: None).
            dest (Optional[Union[str, os.PathLike]]):
                Destination to pull object to. (Default: None).
            data_obj (Optional[List[Union[Dir, File]]]):
                Cleantest data object(s) to pull. (Default: None).
            uid (Optional[int]):
                uid to set as owner of object on host. (Default: None).
            username (Optional[str]):
                User to set as owner of object on host. (Default: None).
            gid (Optional[int]):
                gid to set as group of object on host. (Default: None).
            groupname (Optional[str]):
                Group name to set as group of object on host. (Default: None).
            mode (Optional[oct]):
                Mode to set on object on host. (Default: None).
            overwrite (bool):
                Overwrite object if it already exists on host. (Default: False).

        Raises:
            LXDArchonError: Raised if error is encountered when pulling object.
        """
        _objects = (
            [data_obj]
            if isinstance(data_obj, File) or isinstance(data_obj, Dir)
            else data_obj
            if data_obj is not None
            else []
        )

        if not self.exists(target):
            raise LXDArchonError(
                f"Instance {target} does not exist. Cannot pull object."
            )
        if src is None and dest is None and data_obj is None:
            raise LXDArchonError(f"Nothing to pull from {target}.")
        if (src is not None and dest is None) or (src is None and dest is not None):
            raise LXDArchonError(
                f"src or dest not specified. (src: {src}, dest: {dest}),"
            )
        if uid is not None and username is not None:
            raise LXDArchonError("Please specify only uid or username, not both.")
        if gid is not None and groupname is not None:
            raise LXDArchonError("Please specify only gid or groupname, not both.")

        instance = self.__client.instances.get(target)
        instance.execute(shlex.split("mkdir -p /root/.pull"))

        if src is not None and dest is not None:
            if instance.execute(shlex.split(f"test -f  {src}")).exit_code == 0:
                _ = File(src, dest, overwrite=overwrite)
            elif instance.execute(shlex.split(f"test -d {src}")).exit_code == 0:
                _ = Dir(src, dest, overwrite=overwrite)
            else:
                raise LXDArchonError(f"{src} is not a file or directory.")

            _objects.append(_)

        for _ in _objects:
            instance.files.put("/root/.pull/load", _._dumps(mode="pull")["injectable"])
            result = json.loads(
                instance.execute(shlex.split("python3 /root/.pull/load")).stdout
            )
            placeholder = _.__class__._loads(result["checksum"], result["data"])
            placeholder.dump()
            if (
                uid is not None
                or username is not None
                or gid is not None
                or groupname is not None
            ):
                if placeholder.dest.is_dir():
                    for d in placeholder.dest.iterdir():
                        shutil.chown(d, user=uid or username, group=gid or groupname)
                else:
                    shutil.chown(
                        placeholder.dest, user=uid or username, group=gid or groupname
                    )
            if mode is not None:
                if placeholder.dest.is_dir():
                    for d in placeholder.dest.iterdir():
                        d.chmod(mode)
                else:
                    placeholder.chmod(mode)

    def push(  # noqa C901
        self,
        target: str,
        src: Optional[Union[str, os.PathLike]] = None,
        dest: Optional[Union[str, os.PathLike]] = None,
        data_obj: Optional[List[Union[Dir, File]]] = None,
        uid: Optional[int] = None,
        username: Optional[str] = None,
        gid: Optional[int] = None,
        groupname: Optional[str] = None,
        mode: Optional[oct] = None,
        overwrite: bool = False,
    ) -> None:
        """Push object into test environment instance.

        Args:
            target (str):
                Instance to push object to.
            src (Optional[Union[str, os.PathLike]]):
                File path of object to push. (Default: None).
            dest (Optional[Union[str, os.PathLike]]):
                Destination to push object to. (Default: None).
            data_obj (Optional[List[Union[Dir, File]]]):
                Cleantest data object(s) to push. (Default: None).
            uid (Optional[int]):
                uid to set as owner of object inside test environment instance.
                (Default: None).
            username (Optional[str]):
                User to set as owner of object inside test environment instance.
                (Default: None).
            gid (Optional[int]):
                gid to set as group of object inside test environment instance.
                (Default: None).
            groupname (Optional[str]):
                Group name to set as group of object inside test environment instance.
                (Default: None).
            mode (Optional[oct]):
                Mode to set on object inside test environment instance.
                (Default: None).
            overwrite (bool):
                Overwrite object if it already exists in the test environment instance.
                (Default: False).

        Raises:
            LXDArchonError: Raised if error is encountered when pushing object.
        """
        _objects = (
            [data_obj]
            if isinstance(data_obj, File) or isinstance(data_obj, Dir)
            else data_obj
            if data_obj is not None
            else []
        )

        if not self.exists(target):
            raise LXDArchonError(
                f"Instance {target} does not exist. Cannot push object."
            )
        if src is None and dest is None and data_obj is None:
            raise LXDArchonError(f"Nothing to push to {target}.")
        if (src is not None and dest is None) or (src is None and dest is not None):
            raise LXDArchonError(
                f"src or dest not specified. (src: {src}, dest: {dest}),"
            )
        if uid is not None and username is not None:
            raise LXDArchonError("Please specify only uid or username, not both.")
        if gid is not None and groupname is not None:
            raise LXDArchonError("Please specify only gid or groupname, not both.")

        instance = self.__client.instances.get(target)
        instance.execute(shlex.split("mkdir -p /root/.push"))
        if src is not None and dest is not None:
            if pathlib.Path(src).is_file():
                _ = File(src, dest, overwrite=overwrite)
            elif pathlib.Path(src).is_dir():
                _ = Dir(src, dest, overwrite=overwrite)
            else:
                raise FileNotFoundError(f"Cannot locate src {src} on file system.")

            _objects.append(_)

        for _ in _objects:
            _.load()
            instance.files.put("/root/.push/dump", _._dumps(mode="push")["injectable"])
            instance.execute(shlex.split("python3 /root/.push/dump"))
            if (
                uid is not None
                or username is not None
                or gid is not None
                or groupname is not None
            ):
                instance.execute(
                    shlex.split(
                        f"chown -R {uid or username}:{gid or groupname} {str(_.dest)}"
                    )
                )
            if mode is not None:
                instance.execute(shlex.split(f"chmod -R {mode} {str(_.dest)}"))

    def destroy(self) -> None:
        """Destroy all test environment instances in LXD cluster."""
        logger.info(f"Destroying instances {self.__instances}")
        for i in self.__instances:
            instance = self.__client.instances.get(i)
            instance.stop(wait=True)
            instance.delete(wait=True)

    def get_public_address(
        self, target: str, ipv6: bool = False
    ) -> Optional[Union[IPv4Address, IPv6Address]]:
        """Get the public address of a test environment instance.

        Args:
            target (str): Name of test environment instance.
            ipv6 (bool): Get the public IPv6 address rather than IPv4 address.
                (Default: False).

        Returns:
            (Union[IPv4Address, IPv6Address]):
                Public address of test environment instance.
                None if the instance does not have a public address.
        """
        _ = csv.reader(StringIO(next(run("lxc list -c n46 -f csv")).stdout))
        for row in _:
            if row[0] == target and ipv6:
                return IPv6Address(row[2].split(" ")[0]) if row[2] != "" else None
            elif row[0] == target:
                return IPv4Address(row[1].split(" ")[0]) if row[1] != "" else None
