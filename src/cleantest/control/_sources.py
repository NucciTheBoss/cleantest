#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Default sources for test environment providers."""

from enum import Enum
from typing import Any, List, Tuple

from cleantest.provider.lxd import InstanceSource


class EnhancedEnum(Enum):
    """Enums with extra methods for convenience."""

    @classmethod
    def items(cls) -> List[Tuple[str, Any]]:
        """Returns items of an Enum."""
        return [(c.name, c.value) for c in cls]


class LXDDefaultSources(EnhancedEnum):
    """Default sources for LXD test environment provider."""

    ALMALINUX_8_AMD64 = InstanceSource(
        alias="almalinux/8",
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
        alias="almalinux/9",
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
        alias="archlinux",
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
        alias="centos/8-Stream",
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
        alias="centos/9-Stream",
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
        alias="debian/10",
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
        alias="debian/11",
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
        alias="debian/12",
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
        alias="fedora/35",
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
        alias="fedora/36",
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
        alias="fedora/37",
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
        alias="rockylinux/8",
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
        alias="rockylinux/9",
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
        alias="ubuntu/jammy",
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
        alias="ubuntu/focal",
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
        alias="ubuntu/18.04",
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
