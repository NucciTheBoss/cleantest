# Copyright 2023 Jason C. Nucciarone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Environment variable management for test providers."""

import os
from typing import Any, Dict, Optional

from cleantest.meta import Singleton


class Env(metaclass=Singleton):
    """Manage environment data for test environments."""

    _env = {}

    def add(self, env_mapping: Dict[str, Any]) -> None:
        """Add new values to environment.

        Args:
            env_mapping: Key, value mapping to add to the environment store.
        """
        self._env.update(env_mapping)

    def remove(self, env_var: str) -> None:
        """Remove an environment variable from store.

        Args:
            env_var: Environment variable to Remove from the store.

        Notes:
            Does nothing if environment variable does not exist in store.
        """
        if env_var in self._env.keys():
            del self._env[env_var]

    def get(self, env_var: str, default: Optional[Any] = None) -> Any:
        """Retrieve environment variable from store.

        Args:
            env_var: Environment variable to retrieve.
            default: Value to return if environment variable is not present in store.

        Returns:
            Any: Environment variable value.
        """
        try:
            if type(self._env[env_var]) == list:
                return os.pathsep.join(self._env[env_var])
            else:
                return self._env[env_var]
        except KeyError:
            return default

    def clear(self) -> None:
        """Clear current environment information store."""
        self._env = {}

    def dumps(self) -> Dict[str, Any]:
        """Dump environment store as a dictionary.

        Returns:
            Dict[str, Any]: Environment variable store as a dictionary.
        """
        result = {}
        for k, v in self._env.items():
            if type(v) == list:
                result.update({k: os.pathsep.join(v)})
            else:
                result.update({k: v})

        return result
