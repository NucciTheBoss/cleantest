# Copyright 2023 Jason C. Nucciarone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility for interacting with the pacman package manager."""

# Note: Support for third-party repositories is not implemented yet.

import os
import re
import shutil
import subprocess
from enum import Enum
from typing import Dict, Optional, Union


class Error(Exception):
    """Raised when pacman encounters an execution error."""


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
    def version(self) -> Optional[str]:
        """Get version of package."""
        return self._data.get("version", None)

    @property
    def full_version(self) -> Optional[str]:
        """Get full version of package."""
        if self.absent:
            return None

        return f"{self.version}-{self.release}"

    @property
    def release(self) -> Optional[str]:
        """Get release of package."""
        return self._data.get("release", None)

    @property
    def repo(self) -> Optional[str]:
        """Get repository package is from."""
        return self._data.get("repo", None)


def version() -> str:
    """Get version of `pacman` executable."""
    version_matcher = re.compile(
        r"""
            (?P<throwaway>.*?)\s+
            (?P<frontend>.*?)\s+
            (?P<frontend_version>.*?)\s+
            (?P<spacer>-)\s+
            (?P<backend>.*?)\s+
            (?P<backend_version>.*)
        """,
        re.VERBOSE,
    )
    matches = version_matcher.search(
        _pacman("--version").splitlines()[0].strip()
    ).groupdict()
    return matches["frontend_version"][1:]


def installed() -> bool:
    """Determine if the `pacman` executable is available on PATH."""
    return shutil.which("pacman") is not None


def update() -> None:
    """Update package list on the test environment instance."""
    _pacman("-Sy")


def upgrade(*packages: Optional[str]) -> None:
    """Upgrade one or more packages on test environment instance.

    Args:
        *packages (Optional[str]):
            Packages to upgrade on instance. If None, upgrade all packages.
    """
    update()
    if len(packages) == 0:
        _pacman("-Syu", "--ask", "4")
    else:
        _pacman("-S", *packages, "--ask", "4")


def install(*packages: str) -> None:
    """Install one or more packages in test environment instance.

    Args:
        *packages (Union[str, os.PathLike]): Packages to install in instance.
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    # Need to append `--ask 4` because pacman does not have
    # a `-y`, `--yes`, or `--assume-yes` flag.
    _pacman("-S", *packages, "--ask", "4")


def remove(*packages: str) -> None:
    """Remove one or more packages from test environment instance.

    Args:
        *packages (str): Packages to remove from instance.
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    _pacman("-Rs", *packages, "--ask", "4")


def purge(*packages) -> None:
    """Purge one or more packages from test environment instance.

    Args:
        *packages (str): Packages to purge from instance..
    """
    if len(packages) == 0:
        raise TypeError("No packages specified.")
    _pacman("-Rns", *packages, "--ask", "4")


def fetch(package: str) -> PackageInfo:
    """Fetch information about a package.

    Args:
        package (str): Package to get information about.

    Returns:
        (PackageInfo): Information about package.
    """
    try:
        info = _pacman("-Si", package).splitlines()
        pkg_data = {}
        for line in info:
            if line.startswith(("Architecture", "Repository", "Version")):
                tmp = line.split(":", 1)
                pkg_data.update({tmp[0].strip().lower(): tmp[1].strip()})

        version, release = re.match(r"(.*)-(.*)", pkg_data["version"]).groups()
        try:
            _pacman("-Qs", package)
            state = _PackageState.INSTALLED
        except Error:
            state = _PackageState.AVAILABLE

        return PackageInfo(
            {
                "name": package,
                "arch": "noarch"
                if pkg_data["architecture"] == "any"
                else pkg_data["architecture"],
                "version": version,
                "release": release,
                "repo": pkg_data["repository"],
                "state": state,
            }
        )
    except Error:
        return PackageInfo({"name": package, "state": _PackageState.ABSENT})


def _pacman(*args: str) -> str:
    """Execute a pacman command.

    Args:
        *args (str): Arguments to pass to `pacman` executable.

    Raises:
        Error: Raised if pacman command execution fails.

    Returns:
        (str): Captured stdout of executed pacman command.
    """
    if not installed():
        raise Error(f"pacman not found on PATH {os.getenv('PATH')}")

    try:
        return subprocess.run(
            ["pacman", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        ).stdout.strip("\n")
    except subprocess.CalledProcessError as e:
        raise Error(f"{e} Reason:\n{e.stderr}")
