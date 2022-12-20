#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading files from test environments."""

import os
import pathlib
import tarfile
import tempfile
import textwrap
from io import BytesIO

from cleantest.meta import Injectable


class FileError(Exception):
    ...


class InjectableModeError(Exception):
    ...


class File(Injectable):
    def __init__(self, src: str, dest: str, overwrite: bool = False) -> None:
        self.src = pathlib.Path(src)
        self.dest = pathlib.Path(dest)
        self.overwrite = overwrite
        self._data = None

    def dump(self) -> None:
        if self.dest.exists() and self.overwrite is False:
            raise FileExistsError(
                f"{self.dest} already exists. Set overwrite = True to overwrite {self.dest}."
            )

        if self._data is None:
            raise FileError(f"Nothing to write.")

        with tarfile.open(
            fileobj=BytesIO(self._data), mode="r:gz"
        ) as tar, tempfile.TemporaryDirectory() as tmp_dir:
            tar.extractall(tmp_dir)
            self.dest.write_bytes(pathlib.Path(tmp_dir).joinpath(self.src.name).read_bytes())

    def load(self) -> None:
        if self.src.exists() is False:
            raise FileNotFoundError(f"Could not find {self.src}.")

        if self.src.is_dir():
            raise FileError(f"{self.src} is a directory. Use Dir class instead.")

        old_dir = os.getcwd()
        os.chdir(os.sep.join(str(self.src).split(os.sep)[:-1]))
        archive_path = pathlib.Path(tempfile.gettempdir()).joinpath(self.src.name)
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.src.name)
        os.chdir(old_dir)
        self._data = archive_path.read_bytes()

    def __injectable__(self, path: str, verification_hash: str, mode: str) -> str:
        if mode == "upload":
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                
                from {self.__module__} import {self.__class__.__name__}
                
                holder = {self.__class__.__name__}._load("{path}", "{verification_hash}")
                holder.dump()
                """
            ).strip("\n")
        elif mode == "download":
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                import json
                import sys
                
                from {self.__module__} import {self.__class__.__name__}
                
                holder = {self.__class__.__name__}._load("{path}", "{verification_hash}")
                holder.load()
                print(json.dumps(holder._dump()._asdict()), file=sys.stdout)
                """
            ).strip("\n")
        else:
            InjectableModeError(
                f"Invalid mode: {mode}. Please set mode to either 'upload' or 'download'."
            )
