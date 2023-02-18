#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Detect operating system of test environment."""

import platform


class UnknownOSError(Exception):
    """Raised when an unknown operating system is detected."""


def detect_os_variant() -> str:
    """Detect the operating system of a test environment.

    Raises:
        UnknownOSError: Raised if an unknown operating system has been detected.

    Returns:
        (str): ID of the test environment's operating system.
    """
    try:
        dispatch = {
            "linux": _determine_linux,
            "darwin": lambda: "darwin",
            "windows": lambda: "windows",
            "java": lambda: "java",
        }
        return dispatch[platform.system().lower()]()
    except KeyError:
        raise UnknownOSError("Could not determine base operating system.")


def _determine_linux() -> str:
    """Determine Linux distribution by reading /etc/os-release.

    Returns:
        (str): ID of the Linux distribution read from /etc/os-release.
    """
    os_release_data = [line.strip() for line in open("/etc/os-release", "rt")]
    for line in os_release_data:
        if line.startswith("ID="):
            return line.split("=")[-1].lower()
