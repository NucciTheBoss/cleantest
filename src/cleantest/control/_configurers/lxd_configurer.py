#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Information needed by LXD test environment provider."""

import copy

from cleantest._meta import BaseConfigurer, LXDDefaultSources
from cleantest.control.lxd import InstanceConfig


class DuplicateLXDInstanceConfigError(Exception):
    """Raised if two or more instance configurations share the same name."""


class LXDInstanceConfigNotFoundError(Exception):
    """Raised when LXD instance configuration is not found in the registry."""


class LXDConfigurer(BaseConfigurer):
    """Configurer for LXD test environment provider."""

    _configs = set()

    def __new__(cls) -> "LXDConfigurer":
        if not hasattr(cls, "_instance"):
            cls._instance = super(LXDConfigurer, cls).__new__(cls)
        return cls._instance

    def reset(self) -> None:
        """Reset LXD test environment provider to default configuration."""
        self._configs = set()
        [
            self._configs.add(
                InstanceConfig(name=name.replace("_", "-").lower(), source=source)
            )
            for name, source in LXDDefaultSources.items()
        ]
        super().reset()

    def add_instance_config(self, *new_config: InstanceConfig) -> None:
        """Add a new LXD instance configuration to the registry.

        Args:
            new_config (Dict[str, Any]):
                New configurations to add to the instance configuration registry.

        Raises:
            DuplicateLXDInstanceConfigError:
                Raised if two or more configs have the same name.
        """
        for config in new_config:
            if config.name not in [c.name for c in self._configs]:
                self._configs.add(config)
            raise DuplicateLXDInstanceConfigError(
                f"Instance configuration with name {config.name} already exists."
            )

    def remove_instance_config(self, *name: str) -> None:
        """Remove an instance configuration by name.

        Do nothing if the instance configuration does not exist in the registry.

        Args:
            name (str): Names of the instance configurations to delete.
        """
        for config_name in name:
            for config in self._configs:
                if config_name == config.name:
                    self._configs.remove(config)

    def get_instance_config(self, name: str) -> InstanceConfig:
        """Return an LXD instance configuration.

        Args:
            name (str): Name of instance configuration to retrieve.

        Raises:
            LXDInstanceConfigNotFoundError:
                Raised if configuration does not exist in registry.

        Returns:
            (InstanceConfig): Retrieved LXD image configuration.
        """
        for config in self._configs:
            if config.name == name:
                return copy.deepcopy(config)

        raise LXDInstanceConfigNotFoundError(f"Could not find instance {name}.")
