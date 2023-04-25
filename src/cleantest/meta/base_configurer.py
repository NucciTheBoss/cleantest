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

"""Private metaclass that provides tooling needed by configurer classes."""

import copy
from collections import deque
from typing import Deque, Union

from cleantest.hooks import StartEnvHook, StopEnvHook

from .mixins import Singleton


class Error(Exception):
    """Raise if HookRegistry or BaseConfigurer encounter an error."""


class _HookRegistry(metaclass=Singleton):
    """Centrally store hooks for use by test environment providers."""

    metadata = set()
    startenv = deque()
    stopenv = deque()

    def clear(self) -> None:
        """Reset metadata and hook queues."""
        self.metadata = set()
        self.startenv = deque()
        self.stopenv = deque()

    def lint(self, hook: Union[StartEnvHook, StopEnvHook]) -> None:
        """Lint hooks to ensure they compliant with set restrictions."""
        lint = [
            h
            for h in self.metadata
            if hook.name == h[0] and hook.__class__.__name__ == h[1]
        ]
        if len(lint) > 0:
            raise Error(
                (
                    f"Hook type {hook.__class__.__name__} with name "
                    f"{hook.name} already exists."
                )
            )


class BaseConfigurer:
    """Base configure mixin for configurers."""

    @property
    def startenv_hooks(self) -> Deque[StartEnvHook]:
        """Retrieve hooks that will run when the test environment starts.

        Returns:
            (Deque[StartEnvHook]): Deque containing start environment hooks.
        """
        return copy.deepcopy(_HookRegistry().startenv)

    @property
    def stopenv_hooks(self) -> Deque[StopEnvHook]:
        """Retrieve hooks that will run when the test environment stops.

        Returns:
            (Deque[StopEnvHook]): Deque containing stop environment hooks.
        """
        return copy.deepcopy(_HookRegistry().stopenv)

    def register_hook(self, *hook: Union[StartEnvHook, StopEnvHook]) -> None:
        """Register hooks in the hook registry.

        Args:
            *hook: Hook to register.
        """
        dispatch = {
            StartEnvHook.__name__: _HookRegistry().startenv,
            StopEnvHook.__name__: _HookRegistry().stopenv,
        }
        for new_hook in hook:
            _HookRegistry().lint(new_hook)
            dispatch[new_hook.__class__.__name__].appendleft(new_hook)
            _HookRegistry().metadata.add((new_hook.name, hook.__class__.__name__))

    def unregister_hook(self, *hook_name: str) -> None:
        """Unregister hooks from the hook registry.

        Args:
            *hook_name: Name of hook to unregister.
        """
        dispatch = {
            StartEnvHook.__name__: _HookRegistry().startenv,
            StopEnvHook.__name__: _HookRegistry().stopenv,
        }
        for name in hook_name:
            for hook in _HookRegistry().metadata:
                if name == hook[0]:
                    [
                        dispatch[hook[1]].remove(i)
                        for i in dispatch[hook[1]]
                        if i.name == name
                    ]
                    _HookRegistry().metadata.remove(hook)

    def clear(self) -> None:
        """Clear the hook registry."""
        _HookRegistry().clear()
