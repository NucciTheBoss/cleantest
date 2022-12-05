#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""LXD test environment provider functions and utilities."""

import os
from collections import namedtuple
from typing import Any, Callable, Dict, List, Union

from cleantest.control.configurator import Configure
from cleantest.provider.data import EnvDataStore, LXDDataStore

from ._handler import LXDProvider, Result

LXDClientConfig = namedtuple(
    "LXDClientConfig", ["endpoint", "version", "cert", "verify", "timeout", "project"]
)


class lxd:
    def __init__(
        self,
        name: str = "test",
        image: Union[str, List[str]] = ["jammy-amd64"],
        preserve: bool = True,
        env: EnvDataStore = EnvDataStore(),
        data: LXDDataStore = LXDDataStore(),
        image_config: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
        client_config: LXDClientConfig = None,
        parallel: bool = False,
        num_threads: int = None,
    ) -> None:
        self._name = name
        self._preserve = preserve
        self._env = env
        self._data = data
        self._parallel = parallel
        self._client_config = client_config
        self._clean_config = Configure()

        if type(image) == str:
            self._image = [image]
        else:
            self._image = image

        if type(image_config) == dict:
            self._data.add_config(image_config)
        elif type(image_config) == list:
            for c in image_config:
                self._data.add_config(c)

        if (type(num_threads) != int or num_threads < 1) and self._parallel is True:
            env_var = os.getenv("CLEANTEST_NUM_THREADS")
            self._num_threads = (
                env_var if env_var is not None and type(env_var) == int else os.cpu_count()
            )
        elif type(num_threads) == int and self._parallel is True:
            self._num_threads = num_threads

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Dict[str, Result]:
            handler = (
                LXDProvider.parallel(self, func)
                if self._parallel is True
                else LXDProvider.serial(self, func)
            )
            return handler.run()

        return wrapper
