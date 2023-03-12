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
