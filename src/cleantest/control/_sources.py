#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Default sources for test environment providers."""

from enum import Enum


class LXDDefaultSources(Enum):
    """Default sources for LXD test environment provider."""

    ALMALINUX_8_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "almalinux/8",
    }
    ALMALINUX_8_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "almalinux/8/arm64",
    }
    ALMALINUX_9_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "almalinux/9",
    }
    ALMALINUX_9_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "almalinux/9/arm64",
    }
    ARCHLINUX_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "archlinux",
    }
    ARCHLINUX_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "archlinux/arm64",
    }
    CENTOS_8_STREAM_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "centos/8-Stream",
    }
    CENTOS_8_STREAM_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "centos/8-Stream/arm64",
    }
    CENTOS_9_STREAM_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "centos/9-Stream",
    }
    CENTOS_9_STREAM_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "centos/9-Stream/arm64",
    }
    DEBIAN_10_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "debian/10",
    }
    DEBIAN_10_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "debian/10/arm64",
    }
    DEBIAN_11_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "debian/11",
    }
    DEBIAN_11_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "debian/11/arm64",
    }
    DEBIAN_12_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "debian/12",
    }
    DEBIAN_12_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "debian/12/arm64",
    }
    FEDORA_35_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "fedora/35",
    }
    FEDORA_35_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "fedora/35/arm64",
    }
    FEDORA_36_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "fedora/36",
    }
    FEDORA_36_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "fedora/36/arm64",
    }
    FEDORA_37_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "fedora/37",
    }
    FEDORA_37_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "fedora/37/arm64",
    }
    ROCKYLINUX_8_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "rockylinux/9",
    }
    ROCKYLINUX_8_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "rockylinux/8/arm64",
    }
    ROCKYLINUX_9_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "rockylinux/9",
    }
    ROCKYLINUX_9_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "rockylinux/9/arm64",
    }
    UBUNTU_JAMMY_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "ubuntu/jammy",
    }
    UBUNTU_JAMMY_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "ubuntu/jammy/arm64",
    }
    UBUNTU_FOCAL_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "ubuntu/focal",
    }
    UBUNTU_FOCAL_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "ubuntu/focal/arm64",
    }
    UBUNTU_BIONIC_AMD64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "ubuntu/18.04",
    }
    UBUNTU_BIONIC_ARM64 = {
        "type": "image",
        "mode": "pull",
        "server": "https://images.linuxcontainers.org",
        "protocol": "simplestreams",
        "alias": "ubuntu/18.04/arm64",
    }
