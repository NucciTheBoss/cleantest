#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""LXD test environment provider functions and utilities."""

from __future__ import annotations

from types import NoneType
from typing import Any, Callable, Dict, List, Tuple

from pydantic import BaseModel
from pylxd import Client

from cleantest.control.configurator import Configure
from cleantest.provider._handler import LXDHandler
from cleantest.provider.data import EnvDataStore, LXDDataStore


class LXDClientConfig(BaseModel):
    endpoint: Any | None = None
    version: str = "1.0"
    cert: Tuple[str, str] | None = None
    verify: bool | str = True
    timeout: float | Tuple[float, float] | None = None
    project: str = "default"


class lxd:
    def __init__(
        self,
        name: str = "test",
        image: str | List[str] = ["jammy-amd64"],
        preserve: bool = True,
        env: EnvDataStore = EnvDataStore(),
        data: LXDDataStore = LXDDataStore(),
        image_config: Dict[str, Any] | List[Dict[str, Any]] | None = None,
        client_config: LXDClientConfig | None = None,
    ) -> None:
        self._name = name
        self._preserve = preserve
        self._env = env
        self._data = data

        if type(image) == str:
            self._image = [image]
        else:
            self._image = image

        if type(image_config) == dict:
            self._data.add_config(image_config)
        elif type(image_config) == list:
            for c in image_config:
                self._data.add_config(c)

        if type(client_config) == NoneType:
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

        self._cleanconfig = Configure()

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> None:
            handler = LXDHandler.serial(self, func)
            return handler.run()

        return wrapper
