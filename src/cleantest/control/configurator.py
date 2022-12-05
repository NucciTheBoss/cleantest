#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manage the state and flow of cleantest."""

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

    __hook_registry = HookRegistry()
    __metadata = set()

    def __new__(cls) -> "Configure":
        if not hasattr(cls, "instance"):
            cls.instance = super(Configure, cls).__new__(cls)
        return cls.instance

    def register_hook(
        self, hook: Union[StartEnvHook, StopEnvHook, StartTestletHook, StopTestletHook]
    ) -> None:
        lint = [
            h for h in self.__metadata if hook.name == h[0] and hook.__class__.__name__ == h[1]
        ]
        if len(lint) > 0:
            raise DuplicateHookNameError(
                f"Hook type {hook.__class__.__name__} with name {hook.name} already exists."
            )

        dispatch = {
            StartEnvHook.__name__: self.__hook_registry.start_env,
            StopEnvHook.__name__: self.__hook_registry.stop_env,
            StartTestletHook.__name__: self.__hook_registry.start_testlet,
            StopTestletHook.__name__: self.__hook_registry.stop_testlet,
        }
        dispatch[hook.__class__.__name__].appendleft(hook)
        self.__metadata.add((hook.name, hook.__class__.__name__))

    def deregister_hook(self, hook_name: str) -> None:
        dispatch = {
            StartEnvHook.__name__: self.__hook_registry.start_env,
            StopEnvHook.__name__: self.__hook_registry.stop_env,
            StartTestletHook.__name__: self.__hook_registry.start_testlet,
            StopTestletHook.__name__: self.__hook_registry.stop_testlet,
        }
        for hook in self.__metadata:
            if hook_name == hook[0]:
                dispatch[hook[1]].remove(hook_name)

    def get_start_env_hooks(self) -> Deque[StartEnvHook]:
        return self.__hook_registry.start_env

    def get_stop_env_hooks(self) -> Deque[StopEnvHook]:
        return self.__hook_registry.stop_env

    def get_start_testlet_hooks(self) -> Deque[StartTestletHook]:
        return self.__hook_registry.start_testlet

    def get_stop_testlet_hooks(self) -> Deque[StopTestletHook]:
        return self.__hook_registry.stop_testlet

    @property
    def _hook_registry(self) -> HookRegistry:
        return self.__hook_registry
