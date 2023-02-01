#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Configure and control the LXD test environment provider."""

import copy
from typing import Any, Dict

from cleantest.meta._base_configurer import BaseConfigurer, BaseConfigurerError

from .lxd_config import ClientConfig, InstanceConfig, _DefaultSources


class BadClientConfigurationError(BaseConfigurerError):
    """Raised if given client configuration is bad."""


class DuplicateLXDInstanceConfigError(BaseConfigurerError):
    """Raised if two or more instance configurations share the same name."""


class LXDInstanceConfigNotFoundError(BaseConfigurerError):
    """Raised when LXD instance configuration is not found in the registry."""


class LXDConfigurer(BaseConfigurer):
    """Configurer for LXD test environment provider."""

    __configs = {
        InstanceConfig(name=name.replace("_", "-").lower(), source=source)
        for name, source in _DefaultSources.items()
    }
    __client_config = ClientConfig()

    def __new__(cls) -> "LXDConfigurer":
        """Create new LXDConfigurer instance.

        Returns:
            (LXDConfigurer): New LXDConfigurer instance.
        """
        if not hasattr(cls, f"_{cls.__name__}__instance"):
            cls.__instance = super(LXDConfigurer, cls).__new__(cls)
        return cls.__instance

    @property
    def client_config(self) -> ClientConfig:
        """Get LXD client configuration information.

        Returns:
            (ClientConfig): Current LXD client configuration.
        """
        return self.__client_config

    @client_config.setter
    def client_config(self, new_conf: Dict[str, Any]) -> None:
        """Set LXD client configuration.

        Raises:
            BadClientConfigurationError:
                Raised if new configuration contains invalid configuration option.
        """
        valid_config_options = self.__client_config.keys()
        for k in new_conf.keys():
            if k not in valid_config_options:
                raise BadClientConfigurationError(
                    (
                        f"Configuration {k} is not a valid client "
                        f"configuration option. Valid client configuration options are "
                        f"{', '.join(k for k in valid_config_options)}."
                    )
                )
        self.__client_config = ClientConfig(**new_conf)

    def reset(self) -> None:
        """Reset LXD test environment provider to default configuration."""
        self.__configs = {
            InstanceConfig(name=name.replace("_", "-").lower(), source=source)
            for name, source in _DefaultSources.items()
        }
        self.__client_config = ClientConfig()
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
            if config.name not in [c.name for c in self.__configs]:
                self.__configs.add(config)
            else:
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
            for config in self.__configs:
                if config_name == config.name:
                    self.__configs.remove(config)

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
        for config in self.__configs:
            if config.name == name:
                return copy.deepcopy(config)

        raise LXDInstanceConfigNotFoundError(f"Could not find instance {name}.")
