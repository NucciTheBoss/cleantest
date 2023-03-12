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

"""Direct test environment providers."""

import importlib


class Error(Exception):
    """Raise when Archon encounters an error when loading an Archon."""


def _lxd_loader():
    """Load the LXD test environment provider Archon."""
    try:
        lxd = importlib.import_module("cleantest.lxd.archon")
        return lxd._LXDArchon()
    except ImportError:
        raise Error("Failed to load the LXD test environment provider archon.")


def Archon(archon: str):  # noqa N802
    """Load archon of target test environment provider.

    Args:
        archon: Archon to load.
    """
    dispatch = {"lxd": _lxd_loader}
    if archon not in (archon_opts := dispatch.keys()):
        raise Error(
            f"{archon} is not valid. Valid options are {', '.join(archon_opts)}"
        )

    return dispatch[archon]()
