#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Handler for LXD test environment provider and instances."""

import inspect
import json
import re
import tempfile
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable, Iterable, List, Literal, Optional, Tuple

from pylxd import Client

from cleantest.meta import BasePackage, Injectable, Result
from cleantest.meta._base_harness import (
    BaseEntrypoint,
    BaseEntrypointError,
    BaseHarness,
)
from cleantest.meta._cleantest_info import CleantestInfo


class LXDEntrypointError(BaseEntrypointError):
    """Raise if error is encountered when starting test run with LXD."""


class InstanceMetadata:
    """Metaclass to track key information about LXD test environments.

    Args:
        name (str): Name of the test environment instance.
        image (Optional[str]):
            Name of image being used for the test environment instance
            (Default: None).
        exists (bool): Bool representing whether test environment exists.
            True - test environment instance exists.
            False - test environment instance does not exist (Default: False).
    """

    def __init__(
        self, name: str, image: Optional[str] = None, exists: bool = False
    ) -> None:
        self.name = name
        self.image = image
        self.exists = exists

    def __repr__(self) -> str:
        """String representation of InstanceMetadata."""
        return (
            f"{self.__class__.__name__}(name={self.name}, "
            f"image={self.image}, exists={self.exists})"
        )


class LXDHarness(BaseHarness):
    """Mixin for controlling the LXD hypervisor via its unix socket."""

    @property
    def _client(self) -> Client:
        """Get the connection to the LXD API socket.

        Returns:
            (Client): Connection to LXD API socket.
        """
        return Client(**self._lxd_config.client_config.dict())

    @property
    def _instance_metadata(self) -> List[InstanceMetadata]:
        """Create metaclasses to track key information about LXD test environments.

        Returns:
            (List[InstanceMetadata]): List of metaclasses.
        """
        return [
            InstanceMetadata(name=f"{self._name}-{i}", image=i) for i in self._image
        ]

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

    def _init(self, instance: InstanceMetadata) -> None:
        """Initialize LXD test environment instance.

        Args:
            instance (InstanceMetadata): Instance to initialize.
        """
        if instance.exists is False:
            config = self._lxd_config.get_instance_config(instance.image)
            config.name = instance.name
            self._client.instances.create(config.dict(), wait=True)
            instance = self._client.instances.get(instance.name)
            instance.start(wait=True)
            meta = CleantestInfo()
            instance.execute(["mkdir", "-p", "/root/init/cleantest"])
            for name, data in meta.dumps():
                instance.files.put(
                    f"/root/init/cleantest/install_{name}",
                    data["injectable"],
                )
                instance.execute(["python3", f"/root/init/cleantest/install_{name}"])
        else:
            if self._client.instances.get(instance.name).status.lower() == "stopped":
                self._client.instances.get(instance.name).start(wait=True)

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
        result = instance.execute(["/root/test"], environment=self._env.dump())
        return Result(
            exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr
        )

    def _teardown(self, instance: InstanceMetadata) -> None:
        """Teardown an LXD test environment instance after the testing has completed.

        Args:
            instance (InstanceMetadata): Test environment instance to teardown.
        """
        instance = self._client.instances.get(instance.name)
        instance.stop(wait=True)
        instance.delete(wait=True)

    def _handle_start_env_hooks(self, instance: InstanceMetadata) -> None:
        """Handle start env hooks.

        Args:
            instance (InstanceMetadata): Instance to run start env hooks in.
        """
        start_env_hooks = self._lxd_config.startenv_hooks
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
        stop_env_hooks = self._lxd_config.stopenv_hooks
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

        dump_data = pkg._dumps()
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
        dump_data = artifact._dumps(mode="push")
        instance.execute(["mkdir", "-p", "/root/init/data"])
        instance.files.put("/root/init/data/dump", dump_data["injectable"])
        instance.execute(["python3", "/root/init/data/dump"])

    def _handle_artifact_download(self, instance: Any, artifact: Injectable) -> None:
        """Download an artifact from an LXD test environment instance.

        Args:
            instance (Any): Instance to download artifact from.
            artifact (Injectable): Artifact to download.
        """
        dump_data = artifact._dumps(mode="pull")
        instance.execute(["mkdir", "-p", "/root/post/data"])
        instance.files.put(
            "/root/post/data/load",
            dump_data["injectable"],
        )
        result = json.loads(
            instance.execute(["python3", "/root/post/data/load"]).stdout
        )
        with tempfile.NamedTemporaryFile():
            holder = artifact.__class__._loads(result["checksum"], result["data"])
            holder.dump()


class LXDProviderEntrypoint(BaseEntrypoint, LXDHarness):
    """Entrypoint to running testlets with LXD test environment provider.

    Args:
        strategy (Literal["serial", "serial_target", "parallel", "parallel_target"]):
        func (Callable):
        **kwargs (Any):
    """

    def __init__(
        self,
        strategy: Literal["serial", "serial_target", "parallel", "parallel_target"],
        func: Callable,
        **kwargs: Any,
    ) -> None:
        strategy_options = {
            "serial": self._serial_entrypoint,
            "serial_target": self._serial_target_entrypoint,
            "parallel": self._parallel_entrypoint,
            "parallel_target": self._parallel_target_entrypoint,
        }
        if strategy not in strategy_options.keys():
            raise LXDEntrypointError(
                (
                    f"{strategy} is not a valid strategy. "
                    f"Your options are {strategy_options}."
                )
            )
        setattr(self, "run", strategy_options[strategy])
        [setattr(self, k, v) for k, v in kwargs.items()]
        self._func = inspect.getsource(func)
        self._func_name = func.__name__

    def run(self) -> Iterable[Tuple[str, Result]]:
        """Method behavior is defined by passed strategy."""

    def _serial_entrypoint(self) -> Iterable[Tuple[str, Result]]:
        """Run testlets in serial. LXD instances will be created as needed.

        Yields:
            (Iterable[Tuple[str, Result]]):
                Aggregated results of testlet runs from each instance.
        """
        for instance in self._instance_metadata:
            yield self._run(instance)

    def _serial_target_entrypoint(self) -> Iterable[Tuple[str, Result]]:
        """Run testlets in serial inside pre-existing test environment instance.

        Yields:
            (Iterable[Tuple[str, Result]]):
                Aggregated results of testlet runs from each instance.
        """
        for instance in [
            self._exists(InstanceMetadata(name=name)) for name in self._target_instances
        ]:
            self._exists(instance)
            if not instance.exists:
                raise LXDEntrypointError(f"Instance {instance.name} does not exist.")
            yield self._run_target(instance)

    def _parallel_entrypoint(self) -> Iterable[Tuple[str, Result]]:
        """Run testlets in parallel inside pre-existing test environment instance.

        Yields:
            (Iterable[Tuple[str, Result]]):
                Aggregated results of testlet runs from each instance.
        """
        with ProcessPoolExecutor(max_workers=self._num_threads) as pool:
            results = pool.map(self._run, self._instance_metadata)
            for result in results:
                yield result

    def _parallel_target_entrypoint(self) -> Iterable[Tuple[str, Result]]:
        """Run testlets in parallel. LXD instances already exist.

        Yields:
            (Iterable[Tuple[str, Result]]):
                Aggregated results of testlet runs from each instance.
        """
        instance_metadata = [
            self._exists(InstanceMetadata(name=name)) for name in self._target_instances
        ]
        for instance in instance_metadata:
            if not instance.exists:
                raise LXDEntrypointError(f"Instance {instance.name} does not exist.")
        with ProcessPoolExecutor(max_workers=self._num_threads) as pool:
            results = pool.map(self._run_target, instance_metadata)
            for result in results:
                yield result

    def _run(self, instance: InstanceMetadata) -> Tuple[str, Result]:
        """Run testlet inside of test environment instance.

        Args:
            instance (InstanceMetadata):
                Test environment instance to operate on.

        Returns:
            (Tuple[str, Result]):
                Result of test run inside LXD test environment instance.
        """
        self._init(self._exists(instance))
        self._handle_start_env_hooks(instance)
        result = self._execute(
            self._make_testlet(
                self._func, self._func_name, [re.compile(r"^@lxd\(([^)]+)\)")]
            ),
            instance,
        )
        self._handle_stop_env_hooks(instance)
        if self._preserve is False:
            self._teardown(instance)

        return instance.name, result

    def _run_target(self, instance: InstanceMetadata) -> Tuple[str, Result]:
        """Run testlet inside pre-existing test environment instance.

        Args:
            instance (InstanceMetadata):
                Test environment instance to operate on.

        Returns:
            (Tuple[str, Result]):
                Result of test run inside of pre-existing
                LXD test environment instance.
        """
        return instance.name, self._execute(
            self._make_testlet(
                self._func, self._func_name, [re.compile(r"^@lxd\(([^)]+)\)")]
            ),
            instance,
        )
