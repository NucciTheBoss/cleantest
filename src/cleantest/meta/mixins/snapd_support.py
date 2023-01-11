#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Common operations needed by classes to support snapd and snap."""

import subprocess
from shutil import which

from cleantest.meta.utils import detect_os_variant
from cleantest.utils import apt


class SnapdSupportError(Exception):
    """Base error for SnapdSupport mixin."""

    ...


class SnapdSupport:
    """
    Mixin that provides methods needed by pkg classes that
    require snapd to be installed inside the test environment.
    """

    @staticmethod
    def _install_snapd() -> None:
        """Install snapd inside test environment.

        Raises:
            SnapdSupportError: Raised if snapd fails to install inside test environment.
            NotImplementedError: Raised if unsupported operating system is
                being used for a test environment.
        """
        os_variant = detect_os_variant()

        if which("snap") is None:
            if os_variant == "ubuntu":
                apt.install("snapd")
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )
