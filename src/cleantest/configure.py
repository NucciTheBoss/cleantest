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

"""Configure cleantest and test environment providers ."""


class Error(Exception):
    """Raise when Configure encounters an error when loading a Configurer."""


def _lxd_loader():
    """Load the LXD test environment provider configurer."""
    try:
        from cleantest.lxd.config import LXDConfigurer

        return LXDConfigurer()
    except ImportError:
        raise Error("Failed to load the LXD test environment provider configurer.")


def Configure(configurer: str):  # noqa N802
    """Load configurer of target test environment provider.

    Args:
        configurer: Configurer to load.

    Raises:
        Error: Raised if error occurs when loading requested configurer.
    """
    dispatch = {"lxd": _lxd_loader}
    if configurer not in (conf_opts := dispatch.keys()):
        raise Error(
            f"{configurer} is not valid. Valid options are {', '.join(conf_opts)}"
        )

    return dispatch[configurer]()
