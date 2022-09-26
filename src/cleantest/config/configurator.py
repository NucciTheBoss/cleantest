#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

""""""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel

from cleantest.config.hooks import StartEnvHook, StartTestletHook, StopEnvHook, StopTestletHook


class HookRegistry(BaseModel):
    start_env: Dict[str, StartEnvHook] = {}
    stop_env: Dict[str, StopEnvHook] = {}
    start_testlet: Dict[str, StartTestletHook] = {}
    stop_testlet: Dict[str, StopTestletHook] = {}


class Simple(object):

    __hook_registry = HookRegistry()
    __metadata = set()

    def __new__(cls) -> None:
        if not hasattr(cls, "instance"):
            cls.instance = super(Simple, cls).__new__(cls)
        return cls.instance

    def register_hook(
        self, hook: StartEnvHook | StopEnvHook | StartTestletHook | StopTestletHook
    ) -> None:
        dispatch = {
            StartEnvHook.__name__: self.__hook_registry.start_env,
            StopEnvHook.__name__: self.__hook_registry.stop_env,
            StartTestletHook.__name__: self.__hook_registry.start_testlet,
            StopTestletHook.__name__: self.__hook_registry.stop_testlet,
        }
        dispatch[hook.__class__.__name__].update({hook.name: hook})
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
                dispatch[hook[1]].pop(hook_name)

    def get_start_env_hooks(self) -> Dict[str, StartEnvHook]:
        return self.__hook_registry.start_env

    def get_stop_env_hooks(self) -> Dict[str, StopEnvHook]:
        return self.__hook_registry.stop_env

    def get_start_testlet_hooks(self) -> Dict[str, StartTestletHook]:
        return self.__hook_registry.start_testlet

    def get_stop_testlet_hooks(self) -> Dict[str, StopTestletHook]:
        return self.__hook_registry.stop_testlet

    @property
    def _hooks(self) -> HookRegistry:
        return self.__hook_registry
