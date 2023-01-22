#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Handler for LXD test environments."""

import inspect
import json
import re
import tempfile
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable, Dict, List

from pylxd import Client

from cleantest.meta import (
    BaseEntrypoint,
    BaseHandler,
    BasePackage,
    CleantestInfo,
    Injectable,
    Result,
)


class InstanceMetadata:
    """Metaclass to track key information about LXD test environments.

    Args:
        name (str): Name of the test environment instance.
        image (str): Name of image being used for the test environment instance.
        exists (bool): Bool representing whether test environment exists.
            True - test environment instance exists.
            False - test environment instance does not exist (Default: False).
    """

    def __init__(self, name: str, image: str, exists: bool = False) -> None:
        self.name = name
        self.image = image
        self.exists = exists


class LXDHandler(BaseHandler):
    """Handler mixin for running tests that use LXD as the test environment provider."""

    @property
    def _client(self) -> Client:
        """Get the connection to the LXD API socket.

        Returns:
            (Client): Connection to LXD API socket.
        """
        if self._lxd_client_config is None:
            return Client(project="default")
        else:
            return Client(
                endpoint=self._lxd_client_config.endpoint,
                version=self._lxd_client_config.version,
                cert=self._lxd_client_config.cert,
                verify=self._lxd_client_config.verify,
                timeout=self._lxd_client_config.timeout,
                project=self._lxd_client_config.project,
            )

    @property
    def _instance_metadata(self) -> List[InstanceMetadata]:
        """Create metaclasses to track key information about LXD test environments.

        Returns:
            (List[InstanceMetadata]): List of metaclasses.
        """
        return [
            InstanceMetadata(name=f"{self._name}-{i}", image=i) for i in self._image
        ]

    def _build(self, instance: InstanceMetadata) -> None:
        """Build LXD test environment instance.

        Args:
            instance (InstanceMetadata): Instance to build.
        """
        if instance.exists is False:
            config = self._lxd_provider_config.get_instance_config(instance.image)
            config.name = instance.name
            self._client.instances.create(config.dict(), wait=True)
            instance = self._client.instances.get(instance.name)
            instance.start(wait=True)
            self._init(instance)
        else:
            if self._client.instances.get(instance.name).status.lower() == "stopped":
                self._client.instances.get(instance.name).start(wait=True)

    def _init(self, instance: Any) -> None:
        """Initialize LXD test environment instance after it has been built.

        Args:
            instance (Any): Instance to initialize.
        """
        meta = CleantestInfo()
        instance.execute(["mkdir", "-p", "/root/init/cleantest"])
        for name, data in meta.dump():
            instance.files.put(
                f"/root/init/cleantest/install_{name}",
                data["injectable"],
            )
            instance.execute(["python3", f"/root/init/cleantest/install_{name}"])

    def _execute(self, test: str, instance: InstanceMetadata) -> Any:
        """Execute a testlet inside an LXD test environment instance.

        Args:
            test (str): Testlet to execute inside test environment instance.
            instance (InstanceMetadata): Test environment instance to execute testlet inside.

        Returns:
            (Any): Result of the testlet.
        """
        instance = self._client.instances.get(instance.name)
        instance.files.put("/root/test", test)
        instance.execute(["chmod", "+x", "/root/test"])
        return instance.execute(["/root/test"], environment=self._env.dump())

    def _teardown(self, instance: InstanceMetadata) -> None:
        """Teardown an LXD test environment instance after the testing has completed.

        Args:
            instance (InstanceMetadata): Test environment instance to teardown.
        """
        instance = self._client.instances.get(instance.name)
        instance.stop(wait=True)
        instance.delete(wait=True)

    def _process(self, result: Any) -> Result:
        """Process returned result by testlet.

        Args:
            result (Any): Raw result to process.

        Returns:
            (Result): Processed result.
        """
        return Result(
            exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr
        )

    def _exists(self, instance: InstanceMetadata) -> InstanceMetadata:
        """Check whether an instance exists.

        Args:
            instance (InstanceMetadata): Instance to check the existence of.

        Returns:
            (InstanceMetadata): Update instance metadata.
        """
        if self._client.instances.exists(instance.name):
            instance.exists = True

        return instance

    def _handle_start_env_hooks(self, instance: InstanceMetadata) -> None:
        """Handle start env hooks.

        Args:
            instance (InstanceMetadata): Instance to run start env hooks in.
        """
        start_env_hooks = self._lxd_provider_config.startenv_hooks
        while start_env_hooks:
            hook = start_env_hooks.pop()
            instance = self._client.instances.get(instance.name)
            if hook.packages is not None:
                for pkg in hook.packages:
                    self._handle_package_install(instance, pkg)
            if hook.upload is not None:
                for artifact in hook.upload:
                    self._handle_artifact_upload(instance, artifact)

    def _handle_stop_env_hooks(self, instance: InstanceMetadata) -> None:
        """Handle stop env hooks.

        Args:
            instance (InstanceMetadata): Instance to run stop env hooks in.
        """
        stop_env_hooks = self._lxd_provider_config.stopenv_hooks
        while stop_env_hooks:
            hook = stop_env_hooks.pop()
            instance = self._client.instances.get(instance.name)
            if hook.download is not None:
                for artifact in hook.download:
                    self._handle_artifact_download(instance, artifact)

    def _handle_package_install(self, instance: Any, pkg: BasePackage) -> None:
        """Install a package inside an LXD test environment instance.

        Args:
            instance (Any): Instance to install package in.
            pkg (BasePackage): Package to install in instance.
        """
        dispatch = {"charmlib": lambda x: self._env.add(json.loads(x))}

        dump_data = pkg._dump()
        instance.execute(["mkdir", "-p", "/root/init/pkg"])
        instance.files.put("/root/init/pkg/install", dump_data["injectable"])
        result = instance.execute(["python3", "/root/init/pkg/install"])

        if pkg.__class__.__name__.lower() in dispatch:
            dispatch[pkg.__class__.__name__.lower()](result.stdout)

    def _handle_artifact_upload(self, instance: Any, artifact: Injectable) -> None:
        """Upload an artifact to an LXD test environment instance.

        Args:
            instance (Any): Instance to upload artifact to.
            artifact (Injectable): Artifact to upload.
        """
        artifact.load()
        dump_data = artifact._dump(mode="push")
        instance.execute(["mkdir", "-p", "/root/init/data"])
        instance.files.put("/root/init/data/dump", dump_data["injectable"])
        instance.execute(["python3", "/root/init/data/dump"])

    def _handle_artifact_download(self, instance: Any, artifact: Injectable) -> None:
        """Download an artifact from an LXD test environment instance.

        Args:
            instance (Any): Instance to download artifact from.
            artifact (Injectable): Artifact to download.
        """
        dump_data = artifact._dump(mode="pull")
        instance.execute(["mkdir", "-p", "/root/post/data"])
        instance.files.put(
            "/root/post/data/load",
            dump_data["injectable"],
        )
        result = json.loads(
            instance.execute(["python3", "/root/post/data/load"]).stdout
        )
        with tempfile.NamedTemporaryFile():
            holder = artifact.__class__._load(result["checksum"], result["data"])
            holder.dump()


class Serial(BaseEntrypoint, LXDHandler):
    """Entrypoint for running tests in serial using LXD.

    Args:
        attr (Dict[str, Any]): Attributes from lxd decorator to mount.
        func (Callable): Testlet to inject inside LXD test environment instances.
    """

    def __init__(self, attr: Dict[str, Any], func: Callable) -> None:
        [setattr(self, k, v) for k, v in attr.items()]
        self._func = inspect.getsource(func)
        self._func_name = func.__name__

    def run(self) -> Dict[str, Result]:
        """Run LXD tests in serial.

        Returns:
            (Dict[str, Result]): Aggregated results of all LXD test environment instances.
        """
        results = {}
        for i in self._instance_metadata:
            self._build(self._exists(i))
            self._handle_start_env_hooks(i)
            result = self._execute(
                self._make_testlet(
                    self._func, self._func_name, [re.compile(r"^@lxd\(([^)]+)\)")]
                ),
                i,
            )
            self._handle_stop_env_hooks(i)
            if self._preserve is False:
                self._teardown(i)
            results.update({i.name: self._process(result)})

        return results


class Parallel(BaseEntrypoint, LXDHandler):
    """Entrypoint for running tests in parallel using LXD.

    Args:
        attr (Dict[str, Any]): Attributes from lxd decorator to mount.
        func (Callable): Testlet to inject inside LXD test environment instances.
    """

    def __init__(self, attr: Dict[str, Any], func: Callable) -> None:
        [setattr(self, k, v) for k, v in attr.items()]
        self._func = inspect.getsource(func)
        self._func_name = func.__name__

    def run(self) -> Dict[str, Result]:
        """Run LXD tests in parallel.

        Returns:
            (Dict[str, Any]): Aggregated results of all LXD test environment instances.
        """
        results = {}
        with ProcessPoolExecutor(
            max_workers=self._num_threads,
        ) as pool:
            pool_results = pool.map(self._target, self._instance_metadata)
            for res in pool_results:
                [results.update({key: value}) for key, value in res.items()]

        return results

    def _target(self, i: InstanceMetadata) -> Dict[str, Result]:
        """Target function run inside the parallel process pool.

        Args:
            i (InstanceMetadata): Instance to operate on.

        Returns:
            (Dict[str, Result]): Result of test run inside LXD test environment instance.
        """
        self._build(self._exists(i))
        self._handle_start_env_hooks(i)
        result = self._execute(
            self._make_testlet(
                self._func, self._func_name, [re.compile(r"^@lxd\(([^)]+)\)")]
            ),
            i,
        )
        self._handle_stop_env_hooks(i)
        if self._preserve is False:
            self._teardown(i)

        return {i.name: self._process(result)}


class LXDProvider:
    """Return LXD test environment provider based on passed parameters from lxd decorator."""

    @staticmethod
    def serial(lxd, func: Callable) -> "Serial":
        """Return entrypoint for running tests in serial using LXD.

        Args:
            lxd (lxd): LXD decorator.
            func (Callable): Testlet.

        Returns:
            (Serial): Serial entrypoint.
        """
        return Serial(lxd.__dict__, func)

    @staticmethod
    def parallel(lxd, func: Callable) -> "Parallel":
        """Return entrypoint for running tests in parallel using LXD.

        Args:
            lxd (lxd): LXD decorator.
            func (Callable): Testlet.

        Returns:
            (Parallel): Parallel entrypoint.
        """
        return Parallel(lxd.__dict__, func)
