#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Environment variable management for test providers."""

import os
from typing import Any, Dict


class EnvDataStore:
    def __init__(self) -> None:
        self.__env = {}

    def append(self, env_var: str, value: str) -> None:
        if env_var not in self.__env.keys():
            self.__env.update({env_var: []})

        self.__env[env_var].append(value)

    def get(self, env_var: str) -> Any:
        if isinstance(self.__env[env_var], list):
            return os.pathsep.join(self.__env[env_var])

    @property
    def _raw_env(self) -> Dict[str, Any]:
        return self.__env
