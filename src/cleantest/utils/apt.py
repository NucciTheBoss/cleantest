#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Utility for interacting with the apt package manager."""

# Note: Support for third-party repositories is not implemented yet.

import os
import re
import shutil
import subprocess
from enum import Enum
from typing import Dict, Optional, Union


class Error(Exception):
    """Raised when apt encounters an execution error."""


class _PackageState(Enum):
    INSTALLED = "installed"
    AVAILABLE = "available"
    ABSENT = "absent"


class PackageInfo:
    """Dataclass representing APT package information."""

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
    def uri(self) -> Optional[str]:
        """Get URI for where package was downloaded from."""
        return self._data.get("uri", None)

    @property
    def channel(self) -> Optional[str]:
        """Get channel from which package was installed."""
        return self._data.get("channel", None)


def version() -> str:
    """Get version of `apt-get` executable."""
    return _apt("--version").splitlines()[0].split()[1]


def installed() -> bool:
    """Determine if the `apt-get` executable is available on PATH."""
    return shutil.which("apt-get") is not None


def update() -> None:
    """Update apt cache on the test environment instance."""
    _apt("update")


def upgrade(*packages: Optional[str]) -> None:
    """Upgrade one or more packages on test environment instance.

    Args:
        *packages (Optional[str]):
            Packages to upgrade on instance. If None, upgrade all packages.
    """
    update()
    if len(packages) == 0:
        _apt("upgrade")
    else:
        _apt("upgrade", *packages)


def install(*packages: Union[str, os.PathLike]) -> None:
    """Install one or more packages in test environment instance.

    Args:
        *packages (Union[str, os.PathLike]): Packages to install in instance.
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    _apt("install", *packages)


def remove(*packages: str) -> None:
    """Remove one or more packages from test environment instance.

    Args:
        *packages (str): Packages to remove from instance.
    """
    if len(packages) == 0:
        raise Error("No packages specified.")
    _apt("remove", *packages)


def purge(*packages: str) -> None:
    """Purge one or more packages from test environment instance.

    Args:
        *packages (str): Packages to purge from instance..
    """
    if len(*packages) == 0:
        raise TypeError("No packages specified.")
    _apt("purge", *packages)


def fetch(package: str) -> PackageInfo:
    """Fetch information about a package.

    Args:
        package (str): Package to get information about.

    Returns:
        (PackageInfo): Information about package.
    """
    try:
        # Compile regexes
        policy_matcher = re.compile(
            r"""
                (?P<priority>\d+?)\s+
                (?P<uri>.*?)\s+
                (?P<channel>.*?)\s+
                (?P<arch>\w+?)\s+
                (?P<content>.*)
            """,
            re.VERBOSE,
        )
        dpkg_matcher = re.compile(
            r"""
                ^(?P<status>\w+?)\s+
                (?P<name>.*?)(?P<throwaway>:\w+?)?\s+
                (?P<version>.*?)\s+
                (?P<arch>\w+?)\s+
                (?P<description>.*)
            """,
            re.VERBOSE,
        )
        version_matcher = re.compile(r"(?:(.*):)?(.*)-(.*)")

        # If policy parse passes, check if package is installed. Otherwise, absent.
        policy = _apt_cache("policy", package).splitlines()[5]
        policy_matches = policy_matcher.search(policy).groupdict()
        try:
            # Check if package is installed. If error, get info from `apt-cache show`.
            info = _dpkg("-l", package).splitlines()[5:]
            for line in info:
                dpkg_matches = dpkg_matcher.search(line).groupdict()
                if not dpkg_matches["status"].endswith("i"):
                    # Packages not installed. Move to `apt-cache show ...`
                    raise Error(
                        f"{package} in `dpkg -l {package}` output but not installed."
                    )

                epoch, version, release = version_matcher.match(
                    dpkg_matches["version"]
                ).groups()
                return PackageInfo(
                    {
                        "name": package,
                        "arch": "noarch"
                        if dpkg_matches["arch"] == "all"
                        else dpkg_matches["arch"],
                        "epoch": epoch,
                        "version": version,
                        "release": release,
                        "uri": policy_matches["uri"],
                        "channel": policy_matches["channel"],
                        "state": _PackageState.INSTALLED,
                    }
                )
        except Error:
            # Use `apt-cache show ...` to get package info if available.
            info = _apt_cache("show", package).splitlines()
            pkg_data = {}
            for line in info:
                if line.startswith(("Architecture", "Version")):
                    tmp = line.split(":", 1)
                    pkg_data.update({tmp[0].lower(): tmp[1].strip()})
                # Check if we have bot version and architecture present. If so, break.
                if (
                    pkg_data.get("architecture", None) is not None
                    and pkg_data.get("version", None) is not None
                ):
                    break

            epoch, version, release = version_matcher.match(
                pkg_data["version"]
            ).groups()
            return PackageInfo(
                {
                    "name": package,
                    "arch": "noarch"
                    if pkg_data["architecture"] == "all"
                    else pkg_data["architecture"],
                    "epoch": epoch,
                    "version": version,
                    "release": release,
                    "uri": policy_matches["uri"],
                    "channel": policy_matches["channel"],
                    "state": _PackageState.AVAILABLE,
                }
            )
    except IndexError:
        # Package is marked as absent if `apt-cache policy ...`
        # does not return any information. i.e. no index 5 with package information.
        return PackageInfo({"name": package, "state": _PackageState.ABSENT})


def _apt(*args: str) -> str:
    """Execute an APT command.

    Args:
        *args (str): Arguments to pass to `apt-get` executable.

    Raises:
        Error: Raised if APT command execution fails.

    Returns:
        (str): Captured stdout of executed APT command.
    """
    if not installed():
        raise Error(f"apt-get not found on PATH {os.getenv('PATH')}")

    try:
        return subprocess.run(
            ["apt-get", "-y", *args],
            env={"DEBIAN_FRONTEND": "noninteractive", "PATH": os.getenv("PATH")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        ).stdout.strip("\n")
    except subprocess.CalledProcessError as e:
        raise Error(f"{e} Reason:\n{e.stderr}")


def _apt_cache(*args: str) -> str:
    """Execute an APT cache command.

    Args:
        *args (str): Arguments to pass to `apt-cache` executable.

    Raises:
        Error: Raised if APT cache command execution fails.

    Returns:
        (str): Captured stdout of executed APT cache command.
    """
    if shutil.which("apt-cache") is None:
        raise Error(f"apt-cache not found on PATH {os.getenv('PATH')}")

    try:
        return subprocess.run(
            ["apt-cache", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        ).stdout.strip("\n")
    except subprocess.CalledProcessError as e:
        raise Error(f"{e} Reason:\n{e.stderr}")


def _dpkg(*args: str) -> str:
    """Execute a dpkg command.

    Args:
        *args (str): Arguments to pass to `dpkg` executable.

    Raises:
        Error: Raised if dpkg command execution fails.

    Returns:
        (str): Captured stdout of executed dpkg command.
    """
    if shutil.which("dpkg") is None:
        raise Error(f"dpkg not found on PATH {os.getenv('PATH')}")

    try:
        return subprocess.run(
            ["dpkg", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        ).stdout.strip("\n")
    except subprocess.CalledProcessError as e:
        raise Error(f"{e} Reason:\n{e.stderr}")
