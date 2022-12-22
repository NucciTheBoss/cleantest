#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Information needed for LXD test provider."""

from typing import Any, Dict, List, Optional, Union

from ._mixins import DictOps


class BadLXDConfigError(Exception):
    """Raised when the newly entered configuration fails the lint check."""

    ...


class LXDConfigNotFoundError(Exception):
    """Raised when the requested configuration for an LXD instance is not found in the registry."""

    ...


class LXDSource:
    def __init__(self, type: str, mode: str, server: str, protocol: str, alias: str) -> None:
        self.type = type
        self.mode = mode
        self.server = server
        self.protocol = protocol
        self.alias = alias


class LXDConfig(DictOps):
    def __init__(self, name: str, source: LXDSource, project: Optional[str] = None) -> None:
        self.name = name
        self.source = source
        self.project = project


class Defaults:
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
        self._defaults = Defaults()
        self._config_registry = []
        self.add_config(self._defaults.jammy_amd64)
        self.add_config(self._defaults.focal_amd64)
        self.add_config(self._defaults.bionic_amd64)

    def get_config(self, config_name: str) -> LXDConfig:
        """

        Args:
            config_name (str):

        Raises:
            LXDConfigNotFoundError:

        Returns:
            (LXDConfig)
        """
        for c in self._config_registry:
            if c.name == config_name:
                return c

        raise LXDConfigNotFoundError(config_name)

    def add_config(self, new_config: Dict[str, Any]) -> None:
        """

        Args:
            new_config (Dict[str, Any]):
        """
        self._lint_config(new_config)
        source = new_config.get("source")
        self._config_registry.append(
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
        """

        Args:
            new_config (Dict[str, Any]):

        Raises:
            BadLXDConfigError:
        """
        checks = ["name", "server", "alias", "protocol", "type", "mode"]
        config = self._deconstruct(new_config)
        for i in checks:
            if i not in config:
                raise BadLXDConfigError(new_config)

    def _deconstruct(self, d: Dict[str, Any]) -> List[str]:
        """Recursively deconstruct a dictionary to get all of its keys.

        Args:
            d (Dict[str, Any]): Dictionary to deconstruct.

        Returns:
            (List[str]): Keys of deconstructed dictionary.
        """
        config = []
        for k in d.keys():
            if isinstance(d[k], dict):
                config.extend(self._deconstruct(d[k]))
            else:
                config.append(k)

        return config
