#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Dataclasses to assist with LXD provider and instance configuration."""

from typing import Any, Dict, List, Optional, Tuple, Union

from cleantest.meta.mixins import DictOps, EnhancedEnum


class BadLXDConfigError(Exception):
    """Raised when the newly entered configuration fails the lint check."""


class ClientConfig(DictOps):
    """Define an LXD client connection.

    Args:
        endpoint (Optional[str]): Endpoint can be an HTTP endpoint or
            a path to a unix socket (Default: None).
        version (str): API version string to use with LXD
        cert (Optional[Tuple[str, str]]): A tuple of (cert, key) to use with
            the HTTP socket for client authentication (Default: "1.0").
        verify (bool): Either a boolean, in which case it controls
            whether we verify the server's TLS certificate, or a string, in
            which case it must be a path to a CA bundle to use.
            (Default: True).
        timeout (Optional[Union[float, Tuple[float, float]]]):
            How long to wait for the server to send data before giving up, as a float,
            or a (connect timeout, read timeout) tuple.
        project (Optional[str]): Name of the LXD project to interact with (Default: None).
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        version: str = "1.0",
        cert: Optional[Tuple[str, str]] = None,
        verify: bool = True,
        timeout: Optional[Union[float, Tuple[float, float]]] = None,
        project: Optional[str] = None,
    ) -> None:
        self.endpoint = endpoint
        self.version = version
        self.cert = cert
        self.verify = verify
        self.timeout = timeout
        self.project = project


class InstanceSource:
    """Define an LXD instance source to use for a test environment instance.

    Args:
        alias (str): Alias of source.
        mode (str): Mode for accessing source.
        protocol (str): Protocol to use when pulling source.
        server (str): Server to get source from.
        type (str): Type of source.
        allow_inconsistent (bool):
            Whether to ignore errors when copying. e.g. for volatile files. (Default: None).
        base_image (str):
            Base image fingerprint for faster migration. (Default: None).
        certificate (str):
            Certificate for remote images or migration. (Default: None).
        fingerprint (str): Fingerprint of image source. (Default: None).
        instance_only (bool):
            Whether the copy should skip the snapshots for copy. (Default: None).
        live (bool): Whether this is a live migration. (Default: None).
        operation (str):
            Remote operation URL for migration. (Default: None).
        project (str):
            Source project name for copy and local image. (Default: None).
        properties (Dict[str, str]): Image filters for image source. (Default: None).
        refresh (bool):
            Whether this is refreshing an existing instance for migration and copy.
            (Default: None).
        secret (str):
            Remote server secret for remote private images. (Default: None).
        secrets (Dict[str, str]):
            Map of migration websockets for migration. (Default: None).
        source (str):
            Existing instance name or snapshot for copy. (Default: None)
    """

    def __init__(
        self,
        alias: str,
        mode: str,
        protocol: str,
        server: str,
        type: str,
        allow_inconsistent: bool = None,
        base_image: str = None,
        certificate: str = None,
        fingerprint: str = None,
        instance_only: bool = None,
        live: bool = None,
        operation: str = None,
        project: str = None,
        properties: Dict[str, str] = None,
        refresh: bool = None,
        secret: str = None,
        secrets: Dict[str, str] = None,
        source: str = None,
    ) -> None:
        self.alias = alias
        self.type = type
        self.mode = mode
        self.server = server
        self.protocol = protocol
        if allow_inconsistent is not None:
            setattr(self, "allow_inconsistent", allow_inconsistent)
        if base_image is not None:
            setattr(self, "base_image", base_image)
        if certificate is not None:
            setattr(self, "certificate", certificate)
        if fingerprint is not None:
            setattr(self, "fingerprint", fingerprint)
        if instance_only is not None:
            setattr(self, "instance_only", instance_only)
        if live is not None:
            setattr(self, "live", live)
        if operation is not None:
            setattr(self, "operation", operation)
        if project is not None:
            setattr(self, "project", project)
        if properties is not None:
            setattr(self, "properties", properties)
        if refresh is not None:
            setattr(self, "refresh", refresh)
        if secret is not None:
            setattr(self, "secret", secret)
        if secrets is not None:
            setattr(self, "secrets", secrets)
        if source is not None:
            setattr(self, "source", source)


class InstanceConfig(DictOps):
    """Define an LXD instance that can be brought up for test environments.

    Args:
        name (str): Name to use for container or virtual machine.
        source (InstanceSource): Source for LXD instance and where to get it from.
        architecture (str): Architecture name.
        config (Dict[str, str]): Instance configuration.
        description (str): Description of instance.
        devices (Dict[str, Dict[str, str]]): Devices to use with instance.
        ephemeral (bool):
            Whether the instance is ephemeral; deleted on shutdown. (Default: False).
        instance_type (str):
            Cloud instance type (AWS, GCP, Azure, ...) to emulate with limits. (Default: None).
        profiles (List[str]):
            List of profiles apply to the instance. (Default: None).
        restore (str):
            If set, instance will be restored to the provided snapshot name. (Default: None).
        stateful (bool):
            Whether the instance currently has saved state on the host. (Default: False).
        type (str):
            Type of instance. i.e. "container" or "vm". (Default: "container").
    """

    def __init__(
        self,
        name: str,
        source: InstanceSource,
        architecture: str = None,
        config: Dict[str, str] = None,
        description: str = None,
        devices: Dict[str, Dict[str, str]] = None,
        ephemeral: bool = None,
        instance_type: str = None,
        profiles: List[str] = None,
        restore: str = None,
        stateful: bool = None,
        type: str = "container",
    ) -> None:
        self.name = name
        self.source = source
        self.type = type
        if architecture is not None:
            setattr(self, "architecture", architecture)
        if config is not None:
            setattr(self, "config", config)
        if description is not None:
            setattr(self, "description", description)
        if devices is not None:
            setattr(self, "devices", devices)
        if ephemeral is not None:
            setattr(self, "ephemeral", ephemeral)
        if instance_type is not None:
            setattr(self, "instance_type", instance_type)
        if profiles is not None:
            setattr(self, "profiles", profiles)
        if restore is not None:
            setattr(self, "restore", restore)
        if stateful is not None:
            setattr(self, "stateful", stateful)

        self._lint(self.dict())

    def _lint(self, new_config: Dict[str, Any]) -> None:
        """Lint a new LXD instance configuration to ensure that it is valid.

        Args:
            new_config (Dict[str, Any]): New configuration to lint.

        Raises:
            BadLXDConfigError: Raised if the passed LXD instance configuration is invalid.
        """
        checks = ["name", "server", "alias", "protocol", "type", "mode"]
        config = self._deconstruct(new_config)
        for i in checks:
            if i not in config:
                raise BadLXDConfigError(
                    (
                        f"Bad instance configuration: {new_config}. "
                        "Please ensure instance configuration has the "
                        f"following values set: {checks}."
                    )
                )


class _DefaultSources(EnhancedEnum):
    """Default sources for LXD test environment provider."""

    ALMALINUX_8_AMD64 = InstanceSource(
        alias="almalinux/8/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ALMALINUX_8_ARM64 = InstanceSource(
        alias="almalinux/8/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ALMALINUX_9_AMD64 = InstanceSource(
        alias="almalinux/9/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ALMALINUX_9_ARM64 = InstanceSource(
        alias="almalinux/9/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ARCHLINUX_AMD64 = InstanceSource(
        alias="archlinux/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ARCHLINUX_ARM64 = InstanceSource(
        alias="archlinux/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    CENTOS_8_STREAM_AMD64 = InstanceSource(
        alias="centos/8-Stream/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    CENTOS_8_STREAM_ARM64 = InstanceSource(
        alias="centos/8-Stream/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    CENTOS_9_STREAM_AMD64 = InstanceSource(
        alias="centos/9-Stream/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    CENTOS_9_STREAM_ARM64 = InstanceSource(
        alias="centos/9-Stream/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    DEBIAN_10_AMD64 = InstanceSource(
        alias="debian/10/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    DEBIAN_10_ARM64 = InstanceSource(
        alias="debian/10/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    DEBIAN_11_AMD64 = InstanceSource(
        alias="debian/11/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    DEBIAN_11_ARM64 = InstanceSource(
        alias="debian/11/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    DEBIAN_12_AMD64 = InstanceSource(
        alias="debian/12/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    DEBIAN_12_ARM64 = InstanceSource(
        alias="debian/12/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    FEDORA_35_AMD64 = InstanceSource(
        alias="fedora/35/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    FEDORA_35_ARM64 = InstanceSource(
        alias="fedora/35/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    FEDORA_36_AMD64 = InstanceSource(
        alias="fedora/36/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    FEDORA_36_ARM64 = InstanceSource(
        alias="fedora/36/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    FEDORA_37_AMD64 = InstanceSource(
        alias="fedora/37/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    FEDORA_37_ARM64 = InstanceSource(
        alias="fedora/37/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ROCKYLINUX_8_AMD64 = InstanceSource(
        alias="rockylinux/8/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ROCKYLINUX_8_ARM64 = InstanceSource(
        alias="rockylinux/8/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ROCKYLINUX_9_AMD64 = InstanceSource(
        alias="rockylinux/9/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    ROCKYLINUX_9_ARM64 = InstanceSource(
        alias="rockylinux/9/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    UBUNTU_JAMMY_AMD64 = InstanceSource(
        alias="ubuntu/jammy/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    UBUNTU_JAMMY_ARM64 = InstanceSource(
        alias="ubuntu/jammy/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    UBUNTU_FOCAL_AMD64 = InstanceSource(
        alias="ubuntu/focal/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    UBUNTU_FOCAL_ARM64 = InstanceSource(
        alias="ubuntu/focal/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    UBUNTU_BIONIC_AMD64 = InstanceSource(
        alias="ubuntu/18.04/amd64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )

    UBUNTU_BIONIC_ARM64 = InstanceSource(
        alias="ubuntu/18.04/arm64",
        mode="pull",
        protocol="simplestreams",
        server="https://images.linuxcontainers.org",
        type="image",
    )
