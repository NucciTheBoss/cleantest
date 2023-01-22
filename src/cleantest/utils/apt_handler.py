#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Handler for installing and managing Debian packages inside test environment instances."""

# Note: Support for third-party repositories is not implemented yet.

import os
import pathlib
import re
import subprocess
from shutil import which
from typing import Iterable, List, Optional, Union

from cleantest.meta import Result
from cleantest.meta.utils import detect_os_variant


class AptHandlerError(Exception):
    """Raised when apt handler encounters any errors."""


def _is_apt_available() -> None:
    """Check if apt is available on test environment instance.

    Raises:
        AptHandlerError: Raised if apt is not available.
    """
    if which("apt") is None:
        raise AptHandlerError(
            (
                f"apt is not supported on {detect_os_variant()}. "
                f"`from cleantest.utils import run` can be used instead."
            )
        )


def _apt(
    command: str, packages: Union[str, List[str]], optargs: Optional[List[str]] = None
) -> Result:
    """Wrap package management commands from Debian/Ubuntu commands.

    Args:
        command (str): Command to execute.
        packages (Union[str, List[str]]): Names of packages to operate on.
        optargs (Optional[List[str]]): Optional arguments to pass to apt.

    Raises:
        AptHandlerError: Raised if executed command fails.

    Returns:
        (Result): Captured exit code, stdout, and stderr.
    """
    packages = [packages] if type(packages) == str else packages
    optargs = optargs if optargs is not None else []
    _cmd = ["apt", "-y", *optargs, command, *packages]
    try:
        process = subprocess.run(
            _cmd,
            env={"DEBIAN_FRONTEND": "noninteractive", "PATH": os.getenv("PATH")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return Result(process.returncode, process.stdout, process.stderr)

    except subprocess.CalledProcessError:
        raise AptHandlerError(
            f"Could not perform command {_cmd} on the following packages: {', '.join(packages)}"
        )


def update() -> None:
    """Update apt cache on the test environment instance.

    Raises:
        AptHandlerError: Raised if unable to update apt cache.
    """
    _is_apt_available()
    try:
        subprocess.check_call(
            ["apt", "-y", "update"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        raise AptHandlerError(f"Failed to update apt cache. Reason: {e}.")


def install(*packages: str, version: Optional[str] = None) -> None:
    """Install Debian package on test environment instance.

    Args:
        *packages (str): Names of packages to install.
        version (Optional[str]): Version of package to install.
            Only set if installing one package (Default: None).

    Raises:
        AptHandlerError: Raised if an error is encountered when installing packages.
    """
    _is_apt_available()
    if len(packages) == 0:
        raise AptHandlerError("No package names passed.")
    if len(packages) > 1 and version:
        raise AptHandlerError("Version should not be set if packages to install > 1.")

    # Note: Use --force-confold to keep old configuration file rather than generating a new one.
    if version:
        _apt(
            "install",
            f"{packages[0]}={version}",
            optargs=["--option=Dpkg::Options::=--force-confold"],
        )
    else:
        _apt(
            "install", [*packages], optargs=["--option=Dpkg::Options::=--force-confold"]
        )


def install_local(*package_paths: str) -> None:
    """Install local Debian package on test environment instance."""
    _is_apt_available()
    if len(package_paths) == 0:
        raise AptHandlerError("No file paths to packages passed.")
    for path in package_paths:
        if not pathlib.Path(path).exists():
            raise FileNotFoundError(f"Could not locate deb archive {path}.")
        _apt(
            "install", path, optargs=["--option=Dpkg::Options::=--force-confold", "-f"]
        )


def remove(*packages: str) -> None:
    """Remove package from test environment instance.

    Args:
        *packages (str): Names of packages to remove.

    Raises:
        AptHandlerError: Raised if an error is encountered when removing packages.
    """
    _is_apt_available()
    if len(packages) == 0:
        raise AptHandlerError("No package names passed.")
    _apt("remove", [*packages])


def purge(*packages: str) -> None:
    """Purge package from test environment instance.

    Args:
        *packages (str): Names of packages to purge.
    """
    _is_apt_available()
    if len(*packages) == 0:
        raise AptHandlerError("No package names passed.")
    _apt("purge", [*packages])


def installed(*packages: str) -> Iterable[bool]:
    """Check if packages are installed inside test environment instance.

    Args:
        *packages (str): Names of packages to check if they are installed.

    Yields:
        (Iterable[bool]): Status of package. True: Installed - False: Not Installed.
    """
    _is_apt_available()
    if len(*packages) == 0:
        raise AptHandlerError("No package names passed.")
    check_installed = re.compile(r"\[installed]")
    for package in packages:
        yield True if check_installed.match(_apt("list", package).stdout) else False
