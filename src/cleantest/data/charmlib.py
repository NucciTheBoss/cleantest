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

"""Manager for installing charm libraries inside remote processes."""

import json
import pathlib
import subprocess
import sys
import textwrap
from shutil import which
from typing import Dict, List, Union

from cleantest.meta import BaseError, BasePackage, SnapdSupport
from cleantest.utils import snap


class Error(BaseError):
    """Base error for Charmlib package handler."""


class Charmlib(BasePackage, SnapdSupport):
    """Represents `charmcraft fetch-lib`. See: https://juju.is/docs/sdk/charm-libraries.

    Args:
        auth_token_path (pathlib.Path): Path to authentication token for Charmhub.
        charmlibs (List[str]): List of charmlibs to install.
    """

    def __init__(
        self,
        auth_token_path: str,
        charmlibs: Union[str, List[str]],
    ) -> None:
        self.auth_token_path = pathlib.Path(auth_token_path)
        self.charmlibs = [charmlibs] if type(charmlibs) == str else charmlibs
        self._auth_token = None

        if auth_token_path is None:
            raise Error("No authentication token for Charmhub specified.")

        if charmlibs is None:
            raise Error("No charm libraries specified.")

    def _run(self) -> None:
        """Run Charmlib package handler."""
        self._setup()
        self._handle_charm_lib_install()
        print(json.dumps({"PYTHONPATH": "/root/lib"}), file=sys.stdout)

    def _setup(self) -> None:
        """Set up and install dependencies needed for charm libraries."""
        self._install_snapd()
        if which("charmcraft") is None:
            snap.install("charmcraft", classic=True)

    def _handle_charm_lib_install(self) -> None:
        """Install charm libraries inside test environment.

        Raises:
            CharmlibPackageError: Raised if charm library fails to install.
        """
        for charm in self.charmlibs:
            cmd = ["/snap/bin/charmcraft", "fetch-lib", charm]
            try:
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    env={"CHARMCRAFT_AUTH": self._auth_token},
                    cwd="/root",
                )
            except subprocess.CalledProcessError:
                raise Error(
                    (
                        f"Failed to install charm library {charm} "
                        f"using the following command: {' '.join(cmd)}"
                    )
                )

    def _dumps(self) -> Dict[str, str]:
        """Prepare Charmlib object for injection.

        Raises:
            FileNotFoundError: Raised if authentication token is not found.

        Returns:
            (Dict[str, str]):
                checksum (str): Checksum to verify authenticity of serialized Charmlib object.
                data (str): Base64 encoded string containing serialized Charmlib object.
                injectable (str): Injectable to run inside remote environment.
        """
        if not self.auth_token_path.exists() or not self.auth_token_path.is_file():
            raise FileNotFoundError(
                f"Could not find authentication token {self.auth_token_path}"
            )

        self._auth_token = self.auth_token_path.read_text()

        return super()._dumps()

    def _injectable(self, data: Dict[str, str], **kwargs) -> str:
        """Generate injectable script that will be used to install charm libraries.

        Args:
            data (Dict[str, str]): Data that needs to be in injectable script.
                - checksum (str): SHA224 checksum to verify authenticity of Charmlib object.
                - data (str): Base64 encoded Charmlib object to inject.
            **kwargs: Optional arguments to pass to injectable script.

        Returns:
            (str): Injectable script.
        """
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3

            from {self.__module__} import {self.__class__.__name__}

            holder = {self.__class__.__name__}._loads("{data['checksum']}", "{data['data']}")
            holder._run()
            """
        ).strip("\n")
