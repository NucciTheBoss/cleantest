#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Utility for interacting with the dnf package manager."""

import os
import re
import shutil
import subprocess
from enum import Enum
from typing import Dict, Optional, Union


class Error(Exception):
    """Raise when dnf encounters an execution error."""


class _PackageState(Enum):
    INSTALLED = "installed"
    AVAILABLE = "available"
    ABSENT = "absent"


class PackageInfo:
    """Dataclass representing DNF package information."""

    def __init__(self, data: Dict[str, Union[str, _PackageState]]) -> None:
        self._data = data

    @property
    def installed(self) -> bool:
        """Determine if package is marked 'installed'."""
        return self._data["state"] == _PackageState.INSTALLED

    @property
    def available(self) -> bool:
        """Determine if package is marked 'available'."""
        return self._data["state"] == _PackageState.AVAILABLE

    @property
    def absent(self) -> bool:
        """Determine if package is marked 'absent'."""
        return self._data["state"] == _PackageState.ABSENT

    @property
    def name(self) -> str:
        """Get name of package."""
        return self._data["name"]

    @property
    def arch(self) -> Optional[str]:
        """Get architecture of package."""
        return self._data.get("arch", None)

    @property
    def epoch(self) -> Optional[str]:
        """Get epoch of package."""
        return self._data.get("epoch", None)

    @property
    def version(self) -> Optional[str]:
        """Get version of package."""
        return self._data.get("version", None)

    @property
    def full_version(self) -> Optional[str]:
        """Get full version of package."""
        if self.absent:
            return None

        full_version = [self.version, f"-{self.release}"]
        if self.epoch:
            full_version.insert(0, f"{self.epoch}:")

        return "".join(full_version)

    @property
    def release(self) -> Optional[str]:
        """Get release of package."""
        return self._data.get("release", None)

    @property
    def repo(self) -> Optional[str]:
        """Get repository package is from."""
        return self._data.get("repo", None)


def version() -> str:
    """Get version of `dnf` executable."""
    return _dnf("--version").splitlines()[0]


def installed() -> bool:
    """Determine if the `dnf` executable is available on PATH."""
    return shutil.which("dnf") is not None


def update() -> None:
    """Update all packages on the system."""
    _dnf("update")


def upgrade(*packages: Optional[str]) -> None:
    """Upgrade one or more packages.

    Args:
        *packages (Optional[str]):
            Packages to upgrade on system. If None, upgrade all packages.
    """
    if len(packages) == 0:
        _dnf("upgrade")
    else:
        _dnf("upgrade", *packages)


def install(*packages: Union[str, os.PathLike]) -> None:
    """Install one or more packages.

    Args:
        *packages (Union[str, os.PathLine]): Packages to install on the system.
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    _dnf("install", *packages)


def remove(*packages: str) -> None:
    """Remove one or more packages from the system.

    Args:
        *packages (str): Packages to remove from system.
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    _dnf("remove", *packages)


def purge(*packages: str) -> None:
    """Purge one or more packages from the system.

    Args:
        *packages (str): Packages to purge from system.
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    _dnf("remove", *packages)


def fetch(package: str) -> PackageInfo:
    """Fetch information about a package.

    Args:
        package (str): Package to get information about.

    Returns:
        (PackageInfo): Information about package.
    """
    try:
        status, info = _dnf("list", "-q", package).split("\n")[
            :2
        ]  # Only take top two lines.
        pkg_name, pkg_version, pkg_repo = info.split()
        name, arch = pkg_name.rsplit(".", 1)
        epoch, version, release = re.match(r"(?:(.*):)?(.*)-(.*)", pkg_version).groups()
        if "Installed" in status:
            state = _PackageState.INSTALLED
        elif "Available" in status:
            state = _PackageState.AVAILABLE
        else:
            state = _PackageState.ABSENT

        return PackageInfo(
            {
                "name": name,
                "arch": arch,
                "epoch": epoch,
                "version": version,
                "release": release,
                "repo": pkg_repo[1:] if pkg_repo.startswith("@") else pkg_repo,
                "state": state,
            }
        )

    except Error:
        return PackageInfo({"name": package, "state": _PackageState.ABSENT})


def add_repo(repo: str) -> None:
    """Add a new repository to DNF.

    Args:
        repo (str): URL of new repository to add.
    """
    if not fetch("dnf-plugins-core").installed:
        install("dnf-plugins-core")
    _dnf("config-manager", "--add-repo", repo)


def _dnf(*args: str) -> str:
    """Execute a DNF command.

    Args:
        *args (str): Arguments to pass to `dnf` executable.

    Raises:
        Error: Raised if DNF command execution fails.

    Returns:
        (str): Captured stdout of executed DNF command.
    """
    if not installed():
        raise Error(f"dnf not found on PATH {os.getenv('PATH')}")

    try:
        return subprocess.run(
            ["dnf", "-y", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        ).stdout.strip("\n")
    except subprocess.CalledProcessError as e:
        raise Error(f"{e} Reason:\n{e.stderr}")
