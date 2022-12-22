#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Environment variable management for test providers."""

import os
from typing import Any, Dict, Union


class EnvDataStore:
    """Manage environment data for test environments."""

    _env = {}

    def __new__(cls) -> object:
        if not hasattr(cls, "instance"):
            cls.instance = super(EnvDataStore, cls).__new__(cls)
        return cls.instance

    def add(self, env_mapping: Dict[str, Any]) -> None:
        """Add new values to environment.

        Args:
            (Dict[str, Any]): Key, value mapping to add to the environment store.
        """
        self._env.update(env_mapping)

    def get(self, env_var: str) -> Union[Any, None]:
        """Retrieve environment variable from store.

        Args:
            env_var (str): Environment variable to retrieve.

        Returns:
            (Union[Any, None]): Environment variable value.
                Returns None if variable is not in store.
        """
        try:
            if type(self._env[env_var]) == list:
                return os.pathsep.join(self._env[env_var])
        except KeyError:
            return None

    def dump(self) -> Dict[str, Any]:
        """Dump environment store as a dictionary.

        Returns:
            (Dict[str, Any]): Environment store as a dictionary.
        """
        result = {}
        for k, v in self._env.items():
            if type(v) == list:
                result.update({k: os.pathsep.join(v)})
            else:
                result.update({k: v})

        return result
