#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Information needed by LXD test environment provider."""

from typing import Any, Dict, List, Optional, Union

from ._mixins import DictOps


class BadLXDConfigError(Exception):
    """Raised when the newly entered configuration fails the lint check."""

    ...


class LXDConfigNotFoundError(Exception):
    """Raised when the requested configuration for an LXD instance is not found in the registry."""

    ...


class LXDSource:
    """Metaclass to define an LXD image to use for the test environment.

    Args:
        type (str): Type of artifact to pull.
        mode (str): Mode in which to access the artifact.
        server (str): Server to get the artifact from.
        protocol (str): Protocol to use when pulling/pushing the artifact.
        alias (str): Alias of the artifact.
    """

    def __init__(self, type: str, mode: str, server: str, protocol: str, alias: str) -> None:
        self.type = type
        self.mode = mode
        self.server = server
        self.protocol = protocol
        self.alias = alias


class LXDConfig(DictOps):
    """Metaclass to define an LXD container or virtual machine to bring up.

    Args:
        name (str): Name to use for container or virtual machine.
        source (LXDSource): Where to get the LXD image from.
        project (str): Project to make LXD container or virtual machine member of.
    """

    def __init__(self, name: str, source: LXDSource, project: Optional[str] = None) -> None:
        self.name = name
        self.source = source
        self.project = project


class Defaults:
    """Define default images that can be used with test environment provider.

    Notes:
        jammy_amd64: Ubuntu 22.04 LTS amd64
        focal_amd64: Ubuntu 20.04 LTS amd64
        bionic_amd64: Ubuntu 18.04 LTS amd64
    """

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
        """Get the configuration of an LXD image.

        Args:
            config_name (str): Name of configuration to get.

        Raises:
            LXDConfigNotFoundError: Raised if configuration does not exist in registry.

        Returns:
            (LXDConfig): Retrieved LXD image configuration.
        """
        for c in self._config_registry:
            if c.name == config_name:
                return c

        raise LXDConfigNotFoundError(config_name)

    def add_config(self, new_config: Dict[str, Any]) -> None:
        """Add a new LXD image configuration to the registry.

        Args:
            new_config (Dict[str, Any]): New configuration to add to the registry.
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
        """Lint a new LXD image configuration to ensure that it is valid.

        Args:
            new_config (Dict[str, Any]): New configuration to lint.

        Raises:
            BadLXDConfigError: Raised if the passed LXD image configuration is invalid.
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
