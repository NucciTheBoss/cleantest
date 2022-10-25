#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Handler for LXD-based test environments."""

import json
import os
import re
from typing import Any, Callable, Dict, List

from pydantic import BaseModel

from cleantest.pkg.charmlib import Charmlib
from cleantest.pkg.pip import Pip
from cleantest.provider._handler.base_handler import Handler, Result


class Instance(BaseModel):
    name: str
    image: str
    exists: bool = False


class LXDHandler(Handler):
    def __init__(self, attr: Dict[str, Any], func: Callable, threaded: bool) -> None:
        [setattr(self, k, v) for k, v in attr.items()]
        self.func = func
        self.threaded = threaded

    @classmethod
    def serial(cls, lxd, func: Callable) -> object:
        return cls(lxd.__dict__, func, False)

    @classmethod
    def parallel(cls, lxd, func: Callable) -> object:
        return cls(lxd.__dict__, func, True)

    def run(self) -> Result:
        instances = []
        for i in self._image:
            instances.append(Instance(name=f"{self._name}-{i}", image=i))

        self._build(self._check_exists(instances))
        self._handle_start_env_hooks(instances)
        result = self._execute(
            self._construct_testlet(self.func, [re.compile("@lxd(.*)")]), instances
        )
        if self._preserve is False:
            self._teardown(instances)

        return self._process(result)

    def _check_exists(self, instances: List[Instance]) -> List[Instance]:
        exists_status = []
        for i in instances:
            if self._client.instances.exists(i.name):
                i.exists = True
                exists_status.append(i)
            else:
                exists_status.append(i)

        return exists_status

    def _build(self, instances: List[Instance]) -> None:
        for i in instances:
            if i.exists is False:
                config = self._data.get_config(i.image)
                config.name = i.name
                self._client.instances.create(config.dict(), wait=True)
                self._client.instances.get(i.name).start(wait=True)
            else:
                if (tmp := self._client.instances.get(i.name)).status.lower() == "stopped":
                    tmp.start(wait=True)

    def _execute(self, test: str, instances: List[Instance]) -> Any:
        for i in instances:
            instance = self._client.instances.get(i.name)
            instance.files.put("/root/test", test)
            instance.execute(["chmod", "+x", "/root/test"])
            return instance.execute(["/root/test"], environment=self._env.dump())

    def _process(self, result: Any) -> Result:
        return Result(exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr)

    def _teardown(self, instances: List[Instance]) -> None:
        for i in instances:
            instance = self._client.instances.get(i.name)
            instance.stop(wait=True)
            instance.delete(wait=True)

    def _handle_start_env_hooks(self, instances: List[Instance]) -> None:
        startenvhooks = self._cleanconfig.get_start_env_hooks()
        while len(startenvhooks) > 0:
            hook = startenvhooks.pop()
            for i in instances:
                instance = self._client.instances.get(i.name)
                if hook.packages is not None:
                    for pkg in hook.packages:
                        self.__handle_package_install(instance, pkg)

    def __handle_package_install(self, instance: Any, pkg: Charmlib | Pip) -> None:
        dump_data = pkg._dump()
        remote_file_path = f"/root/{os.path.basename(dump_data['path'])}"
        instance.files.put(remote_file_path, open(dump_data["path"], "rb").read())
        instance.files.put(
            "/root/install", self._construct_pkg_installer(pkg, remote_file_path, dump_data["hash"])
        )
        instance.execute(["chmod", "+x", "/root/install"])
        holder = instance.execute(["/root/install"])
        dump_data = json.loads(holder.stdout)
        pkg_result = instance.files.get(dump_data["path"])
        new_pkg = pkg.__class__._load(pkg_result, dump_data["hash"])
        self._env.add(new_pkg._result)
