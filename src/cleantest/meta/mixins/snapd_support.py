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

"""Mixin for adding snapd support to classes."""

import shutil

from cleantest.meta.utils import detect_os_variant
from cleantest.utils import apt


class SnapdSupport:
    """Mixin for classes that need snapd support."""

    @staticmethod
    def _install_snapd() -> None:
        """Install snapd inside test environment.

        Raises:
            SnapdSupportError: Raised if snapd fails to install inside test environment.
            NotImplementedError: Raised if unsupported operating system is
                being used for a test environment.
        """
        os_variant = detect_os_variant()

        if shutil.which("snap") is None:
            if os_variant == "ubuntu":
                apt.install("snapd")
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )
