#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading files from test environments."""

import os
import pathlib
import tarfile
import tempfile
import textwrap
import zipfile

from cleantest.meta import Injectable


class FileError(Exception):
    ...


class InjectableModeError(Exception):
    ...


class File(Injectable):
    def __init__(self, src: str, dest: str, compression: str = "gz") -> None:
        self.src = pathlib.Path(src)
        self.dest = pathlib.Path(dest)
        self.compression = compression
        self._data = None

        if self.src.is_dir():
            raise FileError(f"{self.src} is a directory. Use Dir class instead.")

        if self.compression not in ["gz", "zip", "bz2", "xz", None]:
            raise FileError(
                f"{self.compression} not valid compression format. "
                f"Format can be one of the following: {['gz', 'zip', 'bz2', 'xz', None]}"
            )

    def dump(self, overwrite: bool = False) -> None:
        if self.dest.exists() and overwrite is False:
            raise FileExistsError(
                f"{self.dest} already exists. Set overwrite = True to overwrite {self.dest}."
            )

        if self._data is None:
            raise FileError(f"Nothing to write.")

        if self.compression in ["gz", "bz2", "xz", None]:
            protocol = "r" if self.compression is None else f"r:{self.compression}"
            with tarfile.open(self._data, protocol) as tar:
                tar.extract(self.src.name, self.dest)
        else:
            with zipfile.ZipFile(self._data, "r") as zip_out:
                zip_out.extract(self.src.name, self.dest)

    def load(self) -> None:
        if self.src.exists() is False:
            raise FileNotFoundError(f"Could not find {self.src}.")

        old_dir = os.getcwd()
        os.chdir(os.sep.join(str(self.src).split(os.sep)[:-1]))
        archive_path = pathlib.Path(tempfile.gettempdir()).joinpath(self.src.name)
        if self.compression in ["gz", "bz2", "xz", None]:
            protocol = "w" if self.compression is None else f"w:{self.compression}"
            with tarfile.open(archive_path, protocol) as tar:
                tar.add(self.src.name)
        else:
            with zipfile.ZipFile(archive_path, "w") as zip_out:
                zip_out.write(self.src.name)
        os.chdir(old_dir)
        self._data = archive_path.read_bytes()

    def __injectable__(self, path: str, mode: str) -> str:
        if mode == "upload":
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                
                from {self.__module__} import {self.__class__.__name__}
                
                holder = {self.__class__.__name__}._load("{path}")
                holder.dump()
                """
            ).strip("\n")
        elif mode == "download":
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                
                from {self.__module__} import {self.__class__.__name__}
                
                holder = {self.__class__.__name__}._load("{path}")
                holder.load()
                holder._dump()
                """
            ).strip("\n")
        else:
            InjectableModeError(
                f"Invalid mode: {mode}. Please set mode to either 'upload' or 'download'."
            )
