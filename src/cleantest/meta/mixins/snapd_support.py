#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Common operations needed by classes to support snapd and snap."""

import subprocess
from shutil import which

from cleantest.utils import detect_os_variant


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
                cmd = ["apt", "install", "-y", "snapd"]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise SnapdSupportError(
                        f"Failed to install snapd using the following command: {' '.join(cmd)}."
                    )
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )
