#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Handler for LXD test environments."""

import inspect
import json
import pathlib
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
    def __init__(self, name: str, image: str, exists: bool = False) -> None:
        self.name = name
        self.image = image
        self.exists = exists


class LXDHandler(BaseHandler):
    @property
    def _client(self) -> Client:
        if self._client_config is None:
            return Client(project="default")
        else:
            return Client(
                endpoint=self._client_config.endpoint,
                version=self._client_config.version,
                cert=self._client_config.cert,
                verify=self._client_config.verify,
                timeout=self._client_config.timeout,
                project=self._client_config.project,
            )

    @property
    def _instance_metadata(self) -> List[InstanceMetadata]:
        return [InstanceMetadata(name=f"{self._name}-{i}", image=i) for i in self._image]

    def _build(self, instance: InstanceMetadata) -> None:
        if instance.exists is False:
            config = self._data.get_config(instance.image)
            config.name = instance.name
            self._client.instances.create(config.dict(), wait=True)
            instance = self._client.instances.get(instance.name)
            instance.start(wait=True)
            self._init(instance)
        else:
            if self._client.instances.get(instance.name).status.lower() == "stopped":
                self._client.instances.get(instance.name).start(wait=True)

    def _init(self, instance: Any) -> None:
        meta = CleantestInfo()
        instance.execute(["mkdir", "-p", "/root/init"])
        for module, src in {**meta.src, **meta.dependencies}.items():
            instance.files.put(f"/root/init/{module}.tar.gz", src)
            instance.files.put(
                f"/root/init/install_{module}",
                meta.make_pkg_injectable(f"/root/init/{module}.tar.gz"),
            )
            instance.execute(["python3", f"/root/init/install_{module}"])

    def _execute(self, test: str, instance: InstanceMetadata) -> Any:
        instance = self._client.instances.get(instance.name)
        instance.files.put("/root/test", test)
        instance.execute(["chmod", "+x", "/root/test"])
        return instance.execute(["/root/test"], environment=self._env.dump())

    def _teardown(self, instance: InstanceMetadata) -> None:
        instance = self._client.instances.get(instance.name)
        instance.stop(wait=True)
        instance.delete(wait=True)

    def _process(self, result: Any) -> Result:
        return Result(exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr)

    def _exists(self, instance: InstanceMetadata) -> InstanceMetadata:
        if self._client.instances.exists(instance.name):
            instance.exists = True

        return instance

    def _handle_start_env_hooks(self, instance: InstanceMetadata) -> None:
        start_env_hooks = self._clean_config.get_start_env_hooks()
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
        stop_env_hooks = self._clean_config.get_stop_env_hooks()
        while stop_env_hooks:
            hook = stop_env_hooks.pop()
            instance = self._client.instances.get(instance.name)
            if hook.download is not None:
                for artifact in hook.download:
                    self._handle_artifact_download(instance, artifact)

    def _handle_package_install(self, instance: Any, pkg: BasePackage) -> None:
        dispatch = {"charmlib": lambda x: self._env.add(json.loads(x))}

        dump_data = pkg._dump()
        data_path = pathlib.Path(dump_data.path)
        instance.execute(["mkdir", "-p", "/root/init/pkg"])
        instance.files.put(f"/root/init/pkg/{data_path.name}", data_path.read_bytes())
        instance.files.put(
            "/root/init/pkg/install",
            pkg.__injectable__(f"/root/init/pkg/{data_path.name}", dump_data.hash),
        )
        result = instance.execute(["python3", "/root/init/pkg/install"])

        if pkg.__class__.__name__.lower() in dispatch:
            dispatch[pkg.__class__.__name__.lower()](result.stdout)

    def _handle_artifact_upload(self, instance: Any, artifact: Injectable) -> None:
        artifact.load()
        dump_data = artifact._dump()
        data_path = pathlib.Path(dump_data.path)
        instance.execute(["mkdir", "-p", "/root/init/data"])
        instance.files.put(f"/root/init/data/{data_path.name}", data_path.read_bytes())
        instance.files.put(
            "/root/init/data/dump",
            artifact.__injectable__(
                f"/root/init/data/{data_path.name}", dump_data.hash, mode="upload"
            ),
        )
        instance.execute(["python3", "/root/init/data/dump"])

    def _handle_artifact_download(self, instance: Any, artifact: Injectable) -> None:
        dump_data = artifact._dump()
        data_path = pathlib.Path(dump_data.path)
        instance.execute(["mkdir", "-p", "/root/post/data"])
        instance.files.put(f"/root/post/data/{data_path.name}", data_path.read_bytes())
        instance.files.put(
            "/root/post/data/load",
            artifact.__injectable__(
                f"/root/post/data/{data_path.name}", dump_data.hash, mode="download"
            ),
        )
        result = json.loads(instance.execute(["python3", "/root/post/data/load"]).stdout)
        data = instance.files.get(result["path"])
        with tempfile.NamedTemporaryFile() as fout:
            handler = pathlib.Path(fout.name)
            handler.write_bytes(data)
            holder = artifact.__class__._load(str(handler), result["hash"])
            holder.dump()


class Serial(BaseEntrypoint, LXDHandler):
    def __init__(self, attr: Dict[str, Any], func: Callable) -> None:
        [setattr(self, k, v) for k, v in attr.items()]
        self._func = inspect.getsource(func)
        self._func_name = func.__name__

    def run(self) -> Dict[str, Result]:
        results = {}
        for i in self._instance_metadata:
            self._build(self._exists(i))
            self._handle_start_env_hooks(i)
            result = self._execute(
                self._make_testlet(self._func, self._func_name, [re.compile(r"^@lxd\(([^)]+)\)")]),
                i,
            )
            self._handle_stop_env_hooks(i)
            if self._preserve is False:
                self._teardown(i)
            results.update({i.name: self._process(result)})

        return results


class Parallel(BaseEntrypoint, LXDHandler):
    def __init__(self, attr: Dict[str, Any], func: Callable) -> None:
        [setattr(self, k, v) for k, v in attr.items()]
        self._func = inspect.getsource(func)
        self._func_name = func.__name__

    def run(self) -> Dict[str, Result]:
        results = {}
        with ProcessPoolExecutor(
            max_workers=self._num_threads,
        ) as pool:
            pool_results = pool.map(self._target, self._instance_metadata)
            for res in pool_results:
                [results.update({key: value}) for key, value in res.items()]

        return results

    def _target(self, i: InstanceMetadata) -> Dict[str, Result]:
        self._build(self._exists(i))
        self._handle_start_env_hooks(i)
        result = self._execute(
            self._make_testlet(self._func, self._func_name, [re.compile(r"^@lxd\(([^)]+)\)")]),
            i,
        )
        self._handle_stop_env_hooks(i)
        if self._preserve is False:
            self._teardown(i)

        return {i.name: self._process(result)}


class LXDProvider:
    @staticmethod
    def serial(lxd, func: Callable) -> "Serial":
        return Serial(lxd.__dict__, func)

    @staticmethod
    def parallel(lxd, func: Callable) -> "Parallel":
        return Parallel(lxd.__dict__, func)
