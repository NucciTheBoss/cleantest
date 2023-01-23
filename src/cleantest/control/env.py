#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Environment variable management for test providers."""

import os
from typing import Any, Dict, Optional

from cleantest._meta.mixins import Resettable


class Env(Resettable):
    """Manage environment data for test environments."""

    _env = {}

    def __new__(cls) -> "Env":
        """Create new Env object instance.

        Returns:
            (Env): New object instance.
        """
        if not hasattr(cls, "_instance"):
            cls._instance = super(Env, cls).__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset environment information."""
        cls._env = {}

    def add(self, env_mapping: Dict[str, Any]) -> None:
        """Add new values to environment.

        Args:
            env_mapping (Dict[str, Any]):
                Key, value mapping to add to the environment store.
        """
        self._env.update(env_mapping)

    def remove(self, env_var: str) -> None:
        """Remove an environment variable from store.

        Does nothing if environment variable does not exist in store.

        Args:
            env_var (str): Environment variable to Remove from the store.
        """
        if env_var in self._env.keys():
            del self._env[env_var]

    def get(self, env_var: str) -> Optional[Any]:
        """Retrieve environment variable from store.

        Args:
            env_var (str): Environment variable to retrieve.

        Returns:
            (Optional[Any]): Environment variable value.
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
