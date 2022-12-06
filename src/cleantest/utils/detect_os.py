#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Detect operating system of test environment."""

import platform


class UnknownOSError(Exception):
    ...


def detect_os_variant() -> str:
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
    os_release_data = [line.strip() for line in open("/etc/os-release", "rt")]
    for line in os_release_data:
        if line.startswith("ID="):
            return line.split("=")[-1].lower()
