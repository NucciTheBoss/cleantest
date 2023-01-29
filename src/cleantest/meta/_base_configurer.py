#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Private metaclass that provides tooling needed by configurer classes."""

import copy
from collections import deque
from typing import Deque, Union

from cleantest.control.hooks import StartEnvHook, StopEnvHook
from cleantest.meta.mixins import Resettable


class BaseConfigurerError(Exception):
    """Base error for all configurer classes."""


class DuplicateHookNameError(Exception):
    """Raised when more than one hook of the same type have the same name."""


class _HookRegistry(Resettable):
    """Centrally store hooks for use by test environment providers."""

    metadata = set()
    startenv = deque()
    stopenv = deque()

    def __new__(cls) -> "_HookRegistry":
        if not hasattr(cls, "_instance"):
            cls._instance = super(_HookRegistry, cls).__new__(cls)
        return cls._instance

    def reset(self) -> None:
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
            raise DuplicateHookNameError(
                (
                    f"Hook type {hook.__class__.__name__} with name "
                    f"{hook.name} already exists."
                )
            )


class BaseConfigurer(Resettable):
    """Base configure mixin for configurers."""

    def reset(self) -> None:
        """Reset the hook registry."""
        _HookRegistry().reset()

    def register_hook(self, *hooks: Union[StartEnvHook, StopEnvHook]) -> None:
        """Register hooks in the hook registry.

        Args:
            *hooks (Union[StartEnvHook, StopEnvHook]): Hooks to register.
        """
        dispatch = {
            StartEnvHook.__name__: _HookRegistry().startenv,
            StopEnvHook.__name__: _HookRegistry().stopenv,
        }
        for hook in hooks:
            _HookRegistry().lint(hook)
            dispatch[hook.__class__.__name__].appendleft(hook)
            _HookRegistry().metadata.add((hook.name, hook.__class__.__name__))

    def unregister_hook(self, *hook_names: str) -> None:
        """Unregister hooks from the hook registry.

        Args:
            *hook_names (str): Names of hooks to unregister.
        """
        dispatch = {
            StartEnvHook.__name__: _HookRegistry().startenv,
            StopEnvHook.__name__: _HookRegistry().stopenv,
        }
        for name in hook_names:
            for hook in _HookRegistry().metadata:
                if name == hook[0]:
                    [
                        dispatch[hook[1]].remove(i)
                        for i in dispatch[hook[1]]
                        if i.name == name
                    ]
                    _HookRegistry().metadata.remove(hook)

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
