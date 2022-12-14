#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Base tooling needed by configurer classes."""

import copy
from collections import deque
from typing import Deque, Union

from cleantest.control.hooks import StartEnvHook, StopEnvHook


class DuplicateHookNameError(Exception):
    """Raised when more than one hook of the same type have the same name."""

    ...


class HookRegistry:
    """Centrally store hooks for use by test environment providers."""

    metadata = set()
    startenv = deque()
    stopenv = deque()

    def __new__(cls) -> "HookRegistry":
        if not hasattr(cls, "instance"):
            cls._instance = super(HookRegistry, cls).__new__(cls)
        return cls._instance

    def lint(self, hook: Union[StartEnvHook, StopEnvHook]) -> None:
        """Lint hooks to ensure they compliant with set restrictions."""
        lint = [h for h in self.metadata if hook.name == h[0] and hook.__class__.__name__ == h[1]]
        if len(lint) > 0:
            raise DuplicateHookNameError(
                f"Hook type {hook.__class__.__name__} with name {hook.name} already exists."
            )


class BaseConfigurer:
    """Base configure mixin for configurers."""

    def register_hook(self, *hooks: Union[StartEnvHook, StopEnvHook]) -> None:
        """Register hooks in the hook registry.

        Args:
            *hooks (Union[StartEnvHook, StopEnvHook]): Hooks to register.
        """
        dispatch = {
            StartEnvHook.__name__: HookRegistry().startenv,
            StopEnvHook.__name__: HookRegistry().stopenv,
        }
        for hook in hooks:
            HookRegistry().lint(hook)
            dispatch[hook.__class__.__name__].appendleft(hook)
            HookRegistry().metadata.add((hook.name, hook.__class__.__name__))

    def unregister_hook(self, *hook_names: str) -> None:
        """Unregister hooks from the hook registry.

        Args:
            *hook_names (str): Names of hooks to unregister.
        """
        dispatch = {
            StartEnvHook.__name__: HookRegistry().startenv,
            StopEnvHook.__name__: HookRegistry().stopenv,
        }
        for name in hook_names:
            for hook in HookRegistry().metadata:
                if name == hook[0]:
                    [dispatch[hook[1]].remove(i) for i in dispatch[hook[1]] if i.name == name]
                    HookRegistry().metadata.remove(hook)

    @property
    def startenv_hooks(self) -> Deque[StartEnvHook]:
        """Retrieve hooks that will run when the test environment starts.

        Returns:
            (Deque[StartEnvHook]): Deque containing start environment hooks.
        """
        return copy.deepcopy(HookRegistry().startenv)

    @property
    def stopenv_hooks(self) -> Deque[StopEnvHook]:
        """Retrieve hooks that will run when the test environment stops.

        Returns:
            (Deque[StopEnvHook]): Deque containing stop environment hooks.
        """
        return copy.deepcopy(HookRegistry().stopenv)
