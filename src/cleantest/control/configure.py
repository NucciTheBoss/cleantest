#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manage the state and flow of cleantest."""

import copy
from collections import deque
from typing import Deque, Union

from cleantest.hooks import StartEnvHook, StartTestletHook, StopEnvHook, StopTestletHook


class DuplicateHookNameError(Exception):
    ...


class HookRegistry:
    start_env: Deque[StartEnvHook] = deque()
    stop_env: Deque[StopEnvHook] = deque()
    start_testlet: Deque[StartTestletHook] = deque()
    stop_testlet: Deque[StopTestletHook] = deque()


class Configure:

    _hook_registry = HookRegistry()
    _metadata = set()

    def __new__(cls) -> "Configure":
        if not hasattr(cls, "instance"):
            cls.instance = super(Configure, cls).__new__(cls)
        return cls.instance

    def register_hook(
        self, *hooks: Union[StartEnvHook, StopEnvHook, StartTestletHook, StopTestletHook]
    ) -> None:
        dispatch = {
            StartEnvHook.__name__: self._hook_registry.start_env,
            StopEnvHook.__name__: self._hook_registry.stop_env,
            StartTestletHook.__name__: self._hook_registry.start_testlet,
            StopTestletHook.__name__: self._hook_registry.stop_testlet,
        }
        for hook in hooks:
            lint = [
                h for h in self._metadata if hook.name == h[0] and hook.__class__.__name__ == h[1]
            ]
            if len(lint) > 0:
                raise DuplicateHookNameError(
                    f"Hook type {hook.__class__.__name__} with name {hook.name} already exists."
                )
            dispatch[hook.__class__.__name__].appendleft(hook)
            self._metadata.add((hook.name, hook.__class__.__name__))

    def deregister_hook(self, *hooks: str) -> None:
        dispatch = {
            StartEnvHook.__name__: self._hook_registry.start_env,
            StopEnvHook.__name__: self._hook_registry.stop_env,
            StartTestletHook.__name__: self._hook_registry.start_testlet,
            StopTestletHook.__name__: self._hook_registry.stop_testlet,
        }
        for hook_name in hooks:
            for hook in self._metadata:
                if hook_name == hook[0]:
                    dispatch[hook[1]].remove(hook_name)

    def get_start_env_hooks(self) -> Deque[StartEnvHook]:
        return copy.deepcopy(self._hook_registry.start_env)

    def get_stop_env_hooks(self) -> Deque[StopEnvHook]:
        return copy.deepcopy(self._hook_registry.stop_env)

    def get_start_testlet_hooks(self) -> Deque[StartTestletHook]:
        return copy.deepcopy(self._hook_registry.start_testlet)

    def get_stop_testlet_hooks(self) -> Deque[StopTestletHook]:
        return copy.deepcopy(self._hook_registry.stop_testlet)
