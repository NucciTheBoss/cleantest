#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Information needed for LXD test provider."""

from typing import Any, Dict, List

from pydantic import BaseModel


class BadLXDConfigError(Exception):
    """Raised when the newly entered configuration fails the lint check."""

    def __init__(self, config: Dict, desc: str = "Bad configuration for LXD instance.") -> None:
        self.config = config
        self.desc = desc
        super().__init__(self.desc)

    def __str__(self) -> str:
        return f"{self.config}: {self.message}"


class LXDConfigNotFoundError(Exception):
    """Raised when the requested configuration for an LXD instance is not found in the registry."""

    def __init__(self, name: str, desc: str = "Configuration not found in registry.") -> None:
        self.name = name
        self.desc = desc
        super().__init__(self.desc)

    def __str__(self) -> str:
        return f"{self.name}: {self.message}"


class LXDSource(BaseModel):
    type: str
    mode: str
    server: str
    protocol: str
    alias: str


class LXDConfig(BaseModel):
    name: str
    source: LXDSource
    project: str | None


class Defaults(BaseModel):
    jammy_amd64: Dict[str, Any] = {
        "name": "jammy-amd64",
        "source": {
            "type": "image",
            "mode": "pull",
            "server": "https://images.linuxcontainers.org",
            "protocol": "simplestreams",
            "alias": "ubuntu/jammy",
        },
        "project": "default",
    }
    focal_amd64: Dict[str, Any] = {
        "name": "focal-amd64",
        "source": {
            "type": "image",
            "mode": "pull",
            "server": "https://images.linuxcontainers.org",
            "protocol": "simplestreams",
            "alias": "ubuntu/focal",
        },
        "project": "default",
    }
    bionic_amd64: Dict[str, Any] = {
        "name": "bionic-amd64",
        "source": {
            "type": "image",
            "mode": "pull",
            "server": "https://images.linuxcontainers.org",
            "protocol": "simplestreams",
            "alias": "ubuntu/18.04",
        },
        "project": "default",
    }


class LXDDataStore:
    def __init__(self) -> None:
        self.__defaults = Defaults()
        self.__config_registry = []
        self.add_config(self.__defaults.jammy_amd64)
        self.add_config(self.__defaults.focal_amd64)
        self.add_config(self.__defaults.bionic_amd64)

    @property
    def _config(self) -> List[LXDConfig]:
        return self.__config_registry

    @property
    def _defaults(self) -> Defaults:
        return self.__defaults

    def get_config(self, config_name: str) -> LXDConfig:
        for c in self.__config_registry:
            if c.name == config_name:
                return c

        raise LXDConfigNotFoundError(config_name)

    def add_config(self, new_config: Dict[str, Any]) -> None:
        self._lint_config(new_config)
        source = new_config.get("source")
        self.__config_registry.append(
            LXDConfig(
                name=new_config.get("name"),
                source=LXDSource(
                    type=source.get("type"),
                    mode=source.get("mode"),
                    server=source.get("server"),
                    protocol=source.get("protocol"),
                    alias=source.get("alias"),
                ),
                project=new_config.get("project", None),
            )
        )

    def _lint_config(self, new_config: Dict[str, Any]) -> None:
        checks = ["name", "server", "alias", "protocol", "type", "mode"]
        config = self.__deconstruct(new_config)
        for i in checks:
            if i not in config:
                raise BadLXDConfigError(new_config)

    def __deconstruct(self, d: Dict[str, Any]) -> List[str]:
        config = []
        for k in d.keys():
            if isinstance(d[k], dict):
                config.extend(self.__deconstruct(d[k]))
            else:
                config.append(k)

        return config
