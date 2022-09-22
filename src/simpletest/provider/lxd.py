#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""LXD test environment provider functions and utilities."""

from __future__ import annotations

import re
from types import NoneType
from typing import Any, Callable, Dict, List, Tuple

from pydantic import BaseModel
from pylxd import Client

from simpletest.provider._base import Provider, Result
from simpletest.provider.data import LXDDataStore


class Instance(BaseModel):
    name: str
    image: str
    exists: bool = False


class LXDClientConfig(BaseModel):
    endpoint: Any | None = None
    version: str = "1.0"
    cert: Tuple[str, str] | None = None
    verify: bool | str = True
    timeout: float | Tuple[float, float] | None = None
    project: str = "default"


class lxd(Provider):
    def __init__(
        self,
        name: str = "test",
        image: str | List[str] = ["jammy-amd64"],
        preserve: bool = True,
        data: LXDDataStore = LXDDataStore(),
        image_config: Dict[str, Any] | List[Dict[str, Any]] | None = None,
        client_config: LXDClientConfig | None = None,
    ) -> None:
        self._name = name
        self._preserve = preserve
        self._data = data

        if isinstance(image, str):
            self._image = [image]
        else:
            self._image = image

        if isinstance(image_config, dict):
            self._data.add_config(image_config)
        elif isinstance(image_config, list):
            for c in image_config:
                self._data.add_config(c)

        if isinstance(client_config, NoneType):
            self._client = Client(project="default")
        else:
            self._client = Client(
                endpoint=client_config.endpoint,
                version=client_config.version,
                cert=client_config.cert,
                verify=client_config.verify,
                timeout=client_config.timeout,
                project=client_config.project,
            )

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> None:
            instances = []
            for i in self._image:
                instances.append(Instance(name=f"{self._name}-{i}", image=i))

            self._build(self._check_exists(instances))
            result = self._execute(self._construct(func, [re.compile("@lxd(.*)")]), instances)
            if self._preserve is False:
                self._teardown(instances)

            return self._process(result)

        return wrapper

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
            result = instance.execute(["/root/test"])
            return result

    def _process(self, result: Any) -> Result:
        return Result(exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr)

    def _teardown(self, instances: List[Instance]) -> None:
        for i in instances:
            instance = self._client.instances.get(i.name)
            instance.stop(wait=True)
            instance.delete(wait=True)
