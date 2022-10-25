#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing charm libraries inside remote processes."""

from __future__ import annotations

import hashlib
import os
import pathlib
import pickle
import platform
import subprocess
import tempfile
import uuid
from shutil import which
from typing import Dict, List


class CharmlibError(Exception):
    ...


class Charmlib:
    def __init__(
        self,
        auth_token_path: str = None,
        charmlibs: str | List[str] = None,
        manager: object | None = None,
    ) -> None:
        if manager is None:
            if auth_token_path is not None:
                self._auth_token = open(auth_token_path, "rt").read()
            else:
                raise CharmlibError(
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
                raise CharmlibError(
                    f"{type(charmlibs)} is invalid. charmlibs must either be str or List[str]."
                )

            self._result = {}

        else:
            self._auth_token = manager._auth_token
            self._charmlib_store = manager._charmlib_store
            self._result = manager._result

    @classmethod
    def _load(cls, manager: str | bytes, hash: str) -> object:
        if type(manager) == str and os.path.isfile(manager):
            fin = pathlib.Path(manager)
            if hash != hashlib.sha224(fin.read_bytes()).hexdigest():
                raise CharmlibError(
                    "SHA224 hashes do not match. Will not load untrusted object."
                )

            return cls(manager=pickle.loads(fin.read_bytes()))
        elif type(manager) == bytes:
            if hash != hashlib.sha224(manager).hexdigest():
                raise CharmlibError("SHA224 hashes do not match. Will not load untrusted object.")

            return cls(manager=manager)
        else:
            raise CharmlibError(
                f"Invalid type {type(manager)} received. Type must either be str or bytes."
            )

    def _dump(self) -> Dict[str, str]:
        """Return a path to a pickled object and hash for verification."""
        filepath = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.pkl")
        data = pickle.dumps(self)
        hash = hashlib.sha224(data).hexdigest()
        fout = pathlib.Path(filepath)
        fout.write_bytes(pickle.dumps(self))
        return {"path": filepath, "hash": hash}

    def _run(self) -> None:
        self.__setup()
        self.__handle_charm_lib_install()
        self._result.update({"PYTHONPATH": "/root/lib"})
        print(self._dump())

    def __setup(self) -> None:
        os_variant = self.__detect_os_variant()

        if which("snap") is None:
            if os_variant == "ubuntu":
                cmd = ["apt", "install", "-y", "snapd"]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise CharmlibError(
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
                raise CharmlibError(
                    f"Failed to install charmcraft using the following command: {' '.join(cmd)}"
                )

    def __handle_charm_lib_install(self) -> None:
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
                raise CharmlibError(
                    (
                        f"Failed to install charm library {charm} "
                        f"using the following command: {' '.join(cmd)}"
                    )
                )

    def __detect_os_variant(self) -> str:
        sys_data = platform.system().lower()
        if sys_data == "linux":
            info = [l.strip() for l in open("/etc/os-release", "rt")]
            for l in info:
                if l.startswith("ID="):
                    return l.split("=")[-1].lower()
        elif sys_data == "windows" or sys_data == "darwin" or sys_data == "java":
            return sys_data
        else:
            raise CharmlibError("Unknown platform.")
