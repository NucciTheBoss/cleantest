#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing charm libraries inside remote processes."""

import json
import subprocess
from shutil import which
from typing import List, Union

from cleantest.pkg._base import Package, PackageError
from cleantest.utils import detect_os_variant


class Charmlib(Package):
    def __init__(
        self,
        auth_token_path: str = None,
        charmlibs: Union[str, List[str]] = None,
        _manager: "Charmlib" = None,
    ) -> None:
        if _manager is None:
            if auth_token_path is not None:
                self._auth_token = open(auth_token_path, "rt").read()
            else:
                raise PackageError(
                    (
                        "No file path to authentication token passed. ",
                        "Cannot authenticate with Charmhub.",
                    )
                )

            self._charmlib_store = set()
            if type(charmlibs) == str:
                self._charmlib_store.add(charmlibs)
            elif type(charmlibs) == list:
                for lib in charmlibs:
                    self._charmlib_store.add(lib)
            else:
                raise PackageError(
                    f"{type(charmlibs)} is invalid. charmlibs must either be str or List[str]."
                )
        else:
            self._auth_token = _manager._auth_token
            self._charmlib_store = _manager._charmlib_store

    def _run(self) -> None:
        self._setup()
        self._handle_charm_lib_install()
        print(json.dumps({"PYTHONPATH": "/root/lib"}))

    def _setup(self) -> None:
        os_variant = detect_os_variant()

        if which("snap") is None:
            if os_variant == "ubuntu":
                cmd = ["apt", "install", "-y", "snapd"]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PackageError(
                        f"Failed to install snapd using the following command: {' '.join(cmd)}."
                    )
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )

        if which("charmcraft") is None:
            cmd = ["snap", "install", "charmcraft", "--classic"]
            try:
                subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
            except subprocess.CalledProcessError:
                raise PackageError(
                    f"Failed to install charmcraft using the following command: {' '.join(cmd)}"
                )

    def _handle_charm_lib_install(self) -> None:
        env = {"CHARMCRAFT_AUTH": self._auth_token}
        for charm in self._charmlib_store:
            cmd = ["/snap/bin/charmcraft", "fetch-lib", charm]
            try:
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    env=env,
                    cwd="/root",
                )
            except subprocess.CalledProcessError:
                raise PackageError(
                    (
                        f"Failed to install charm library {charm} "
                        f"using the following command: {' '.join(cmd)}"
                    )
                )
