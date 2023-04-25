# Copyright 2023 Jason C. Nucciarone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration for the LXD test environment provider."""

import copy
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from cleantest.meta import BaseConfigurer, DictLike, Singleton

from ..env import Env


class Error(Exception):
    """Raise when there is an LXD test environment provider configuration error."""


@dataclass(frozen=True)
class ClientConfig(DictLike):
    """Define an LXD client connection.

    Args:
        endpoint:
            Endpoint can be an HTTP endpoint or a path to a unix socket.
            Default: None.
        version: API version string to use with LXD. Default: "1.0".
        cert:
            Certificate and key to use with the HTTP socket for client authentication.
            Default: None.
        verify:
            Either a boolean, in which case it controls
            whether we verify the server's TLS certificate, or a string, in
            which case it must be a path to a CA bundle to use.
            Default: True.
        timeout:
            How long to wait for the server to send data before giving up, as a float,
            or a (connect timeout, read timeout) tuple. Default: None.
        project: Name of the LXD project to interact with Default: None.
    """

    endpoint: Optional[str] = None
    version: str = "1.0"
    cert: Optional[Tuple[str, str]] = None
    verify: bool = True
    timeout: Optional[Union[float, Tuple[float, float]]] = None
    project: Optional[str] = None


@dataclass
class InstanceSource:
    """Define an LXD instance source to use for a test environment instance.

    Args:
        alias: Alias of source image.
        mode: Mode for accessing source image.
        protocol: Protocol to use when pulling source image.
        server: Server to get source image from.
        type: Type of source image.
        allow_inconsistent:
            Whether to ignore errors when copying.
            E.g. for volatile files. Default: None.
        base_image: Base image fingerprint for faster migration. Default: None.
        certificate: Certificate for remote images or migration. Default: None.
        fingerprint: Fingerprint of image source. Default: None.
        instance_only:
            Whether the copy should skip the snapshots for copy. Default: None.
        live: Whether this is a live migration. Default: None.
        operation: Remote operation URL for migration. Default: None.
        project: Source project name for copy and local image. Default: None.
        properties: Image filters for image source. Default: None.
        refresh:
            Whether this is refreshing an existing instance for migration and copy.
            Default: None.
        secret: Remote server secret for remote private images. Default: None.
        secrets: Map of migration websockets for migration. Default: None.
        source: Existing instance name or snapshot for copy. Default: None.
    """

    alias: str
    mode: str
    protocol: str
    server: str
    type: str
    allow_inconsistent: Optional[bool] = None
    base_image: Optional[str] = None
    certificate: Optional[str] = None
    fingerprint: Optional[str] = None
    instance_only: Optional[str] = None
    live: Optional[bool] = None
    operation: Optional[str] = None
    project: Optional[str] = None
    properties: Optional[Dict[str, str]] = None
    refresh: Optional[bool] = None
    secret: Optional[str] = None
    secrets: Optional[Dict[str, str]] = None
    source: Optional[str] = None


@dataclass
class InstanceConfig(DictLike):
    """Define an LXD instance that can be brought up for test environments.

    Args:
        name: Name to use for container or virtual machine.
        source: Source for LXD instance and where to get it from.
        architecture: Architecture of LXD instance. Default: None.
        config: Configuration for the LXD image. Default: None.
        description: Description of LXD instance. Default: None.
        devices: Devices to use with LXD instance. Default: None.
        ephemeral: Whether the LXD instance is ephemeral; deleted on shutdown.
            Default: False.
        instance_type: Cloud instance type (AWS, GCP, Azure, ...) to emulate with
            limits. Default: None.
        profiles: List of profiles apply to the instance. (Default: None).
        restore: If set, instance will be restored to the provided snapshot name.
            Default: None.
        stateful: Whether the instance currently has saved state on the host.
            Default: False.
        type: Type of instance. i.e. "container" or "vm".
            Default: "container".
    """

    name: str
    source: InstanceSource
    architecture: Optional[str] = None
    config = Optional[Dict[str, str]] = None
    description: Optional[str] = None
    devices: Optional[Dict[str, Dict[str, str]]] = None
    ephemeral: bool = False
    instance_type: Optional[str] = None
    profiles: Optional[List[str]] = None
    restore: Optional[str] = None
    stateful: bool = False
    type: str = "container"


@dataclass(frozen=True)
class _DefaultInstances(DictLike):
    """Default test environment instances for the LXD test environment provider.

    Notes:
        All instances images support Python 3.8 or greater and
        have `cloud-init` preinstalled for launch configuration.
    """

    almalinux_9_amd64: InstanceConfig = InstanceConfig(
        name="almalinux-9-amd64",
        source=InstanceSource(
            alias="almalinux/9/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    almalinux_9_arm64: InstanceConfig = InstanceConfig(
        name="almalinux-9-arm64",
        source=InstanceSource(
            alias="almalinux/9/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    archlinux_amd64: InstanceConfig = InstanceConfig(
        name="archlinux-amd64",
        source=InstanceSource(
            alias="archlinux/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    archlinux_arm64: InstanceConfig = InstanceConfig(
        name="archlinux-arm64",
        source=InstanceSource(
            alias="archlinux/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    centos_9_stream_amd64: InstanceConfig = InstanceConfig(
        name="centos-9-stream-amd64",
        source=InstanceSource(
            alias="centos/9-Stream/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    centos_9_stream_arm64: InstanceConfig = InstanceConfig(
        name="centos-9-stream-arm64",
        source=InstanceSource(
            alias="centos/9-Stream/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    debian_11_amd64: InstanceConfig = InstanceConfig(
        name="debian-11-amd64",
        source=InstanceSource(
            alias="debian/11/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    debian_11_arm64: InstanceConfig = InstanceConfig(
        name="debian-11-arm64",
        source=InstanceSource(
            alias="debian/11/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    debian_12_amd64: InstanceConfig = InstanceConfig(
        name="debian-12-amd64",
        source=InstanceSource(
            alias="debian/12/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    debian_12_arm64: InstanceConfig = InstanceConfig(
        name="debian-12-arm64",
        source=InstanceSource(
            alias="debian/12/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    fedora_36_amd64: InstanceConfig = InstanceConfig(
        name="focal-36-amd64",
        source=InstanceSource(
            alias="fedora/36/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    fedora_36_arm64: InstanceConfig = InstanceConfig(
        name="fedora-36-arm64",
        source=InstanceSource(
            alias="fedora/36/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    fedora_37_amd64: InstanceConfig = InstanceConfig(
        name="fedora-37-amd64",
        source=InstanceSource(
            alias="fedora/37/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    fedora_37_arm64: InstanceConfig = InstanceConfig(
        name="focal-37-arm64",
        source=InstanceSource(
            alias="fedora/37/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    rockylinux_9_amd64: InstanceConfig = InstanceConfig(
        name="rockylinux-9-amd64",
        source=InstanceSource(
            alias="rockylinux/9/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    rockylinux_9_arm64: InstanceConfig = InstanceConfig(
        name="rockylinux-9-arm64",
        source=InstanceSource(
            alias="rockylinux/9/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    ubuntu_focal_amd64: InstanceConfig = InstanceConfig(
        name="ubuntu-focal-amd64",
        source=InstanceSource(
            alias="ubuntu/focal/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    ubuntu_focal_arm64: InstanceConfig = InstanceConfig(
        name="ubuntu-focal-arm64",
        source=InstanceSource(
            alias="ubuntu/focal/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    ubuntu_jammy_amd64: InstanceConfig = InstanceConfig(
        name="ubuntu-jammy-amd64",
        source=InstanceSource(
            alias="ubuntu/jammy/cloud/amd64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )
    ubuntu_jammy_arm64: InstanceConfig = InstanceConfig(
        name="ubuntu-jammy-arm64",
        source=InstanceSource(
            alias="ubuntu/jammy/cloud/arm64",
            mode="pull",
            protocol="simplestreams",
            server="https://images.linuxcontainers.org",
            type="image",
        ),
    )


class LXDConfigurer(BaseConfigurer, metaclass=Singleton):
    """Configurer for LXD test environment provider."""

    _client_config = ClientConfig()
    _instance_configs = dict(_DefaultInstances().items())

    @property
    def client(self) -> ClientConfig:
        """Get LXD client configuration information."""
        return self._client_config

    @client.setter
    def client(self, new_conf: ClientConfig) -> None:
        """Set new LXD client configuration.

        Raises:
            Error: Raised if new configuration contains invalid configuration option.
        """
        if not isinstance(new_conf, ClientConfig):
            raise TypeError(f"Expected ClientConfig, got {type(new_conf)} instead.")
        self._client_config = new_conf

    @property
    def env(self) -> Env:
        """Get environment configuration information."""
        return Env()

    def add_config(self, *new_config: InstanceConfig) -> None:
        """Add a new LXD instance configuration to the registry.

        Args:
            *new_config: New configurations to add to the
                instance configuration registry.

        Raises:
            Error: Raised if instance configurations have the same name.
        """
        for config in new_config:
            if config.name in self._instance_configs.keys():
                raise Error(
                    f"Instance configuration with name {config.name} already exists."
                )
            self._instance_configs[config.name] = config

    def remove_config(self, *name: str) -> None:
        """Remove an instance configuration by name.

        Args:
            *name: Names of the instance configurations to remove from registry.

        Notes:
            Does nothing if instance configuration does not exist in the registry.
        """
        for config_name in name:
            for config in self._instance_configs.keys():
                if config_name == config.name:
                    del self._instance_configs[config.name]

    def fetch_config(self, name: str) -> InstanceConfig:
        """Fetch an LXD instance configuration.

        Args:
            name: Name of instance configuration to retrieve.

        Raises:
            KeyError: Raised if configuration does not exist in registry.

        Returns:
            InstanceConfig: Retrieved LXD image configuration.
        """
        for config in self._instance_configs.values():
            if config.name == name:
                return copy.deepcopy(config)

        raise KeyError(f"Instance configuration {name} not found.")

    def clear(self) -> None:
        """Clear hook registry and registered instances."""
        self._instance_configs = dict(_DefaultInstances().items())
        super().clear()
