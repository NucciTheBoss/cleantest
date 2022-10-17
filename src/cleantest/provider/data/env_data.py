#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Environment variable management for test providers."""

import os
from typing import Any, Dict, Type
from types import Self


class EnvDataStore:
    def __new__(cls: Type[Self]) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(EnvDataStore, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.__env = {}

    def append(self, env_var: str, value: str) -> None:
        if env_var not in self.__env.keys():
            self.__env.update({env_var: []})

        self.__env[env_var].append(value)

    def get(self, env_var: str) -> Any | None:
        """Retrieve environment variable from store.

        Args:
            env_var (str): Environment variable to retrieve.

        Returns:
            Any | None: Environment variable value. Returns None if variable is not in store.
        """
        try:
            if type(self.__env[env_var]) == list:
                return os.pathsep.join(self.__env[env_var])
        except KeyError:
            return None

    @property
    def _raw_env(self) -> Dict[str, Any]:
        return self.__env
