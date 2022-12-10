#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing charm libraries inside remote processes."""

import json
import pathlib
import subprocess
import sys
import textwrap
from shutil import which
from typing import List, Union

from cleantest.meta import BasePackage, BasePackageError, InjectableData

from ._mixins import SnapdSupport


class CharmlibPackageError(BasePackageError):
    ...


class Charmlib(BasePackage, SnapdSupport):
    def __init__(
        self,
        auth_token_path: str,
        charmlibs: Union[str, List[str]],
    ) -> None:
        self.auth_token_path = pathlib.Path(auth_token_path)
        self.charmlibs = [charmlibs] if type(charmlibs) == str else charmlibs
        self._auth_token = None

        if auth_token_path is None:
            raise CharmlibPackageError("No authentication token for Charmhub specified.")

        if charmlibs is None:
            raise CharmlibPackageError("No charm libraries specified.")

    def _run(self) -> None:
        self._setup()
        self._handle_charm_lib_install()
        print(json.dumps({"PYTHONPATH": "/root/lib"}), file=sys.stdout)

    def _setup(self) -> None:
        self._install_snapd()
        if which("charmcraft") is None:
            cmd = ["snap", "install", "charmcraft", "--classic"]
            try:
                subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
            except subprocess.CalledProcessError:
                raise CharmlibPackageError(
                    f"Failed to install charmcraft using the following command: {' '.join(cmd)}"
                )

    def _handle_charm_lib_install(self) -> None:
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
                raise CharmlibPackageError(
                    (
                        f"Failed to install charm library {charm} "
                        f"using the following command: {' '.join(cmd)}"
                    )
                )

    def _dump(self) -> InjectableData:
        if not self.auth_token_path.exists() or not self.auth_token_path.is_file():
            raise FileNotFoundError(f"Could not find authentication token {self.auth_token_path}")

        self._auth_token = self.auth_token_path.read_text()

        return super()._dump()

    def __injectable__(self, path: str, verification_hash: str) -> str:
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3
            
            from {self.__module__} import {self.__class__.__name__}
            
            holder = {self.__class__.__name__}._load("{path}", "{verification_hash}")
            holder._run()
            """
        ).strip("\n")
