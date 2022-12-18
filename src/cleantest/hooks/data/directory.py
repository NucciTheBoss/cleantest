#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading directories from test environments."""

import os
import pathlib
import tarfile
import tempfile
import zipfile

from .file import File


class DirectoryError(Exception):
    ...


class DirectoryExistsError(Exception):
    ...


class DirectoryNotFoundError(Exception):
    ...


class Dir(File):
    def __init__(
        self, src: str, dest: str, compression: str = "gz", overwrite: bool = False
    ) -> None:
        self.src = pathlib.Path(src)
        self.dest = pathlib.Path(dest)
        self.compression = compression
        self.overwrite = overwrite
        self._data = None

        if self.src.is_file():
            raise NotADirectoryError(f"{self.src} is a file. Use File class instead.")

        if self.compression not in ["gz", "zip", "bz2", "xz", None]:
            raise DirectoryError(
                f"{self.compression} not valid compression format. "
                f"Format can be one of the following: {['gz', 'zip', 'bz2', 'xz', None]}"
            )

    def dump(self) -> None:
        if self.dest.exists() and self.overwrite is False:
            raise DirectoryExistsError(
                f"{self.dest} already exists. Set overwrite = True to overwrite {self.dest}."
            )

        if self._data is None:
            DirectoryError("Nothing to write.")

        if self.compression in ["gz", "bz2", "xz", None]:
            protocol = "r" if self.compression is None else f"r:{self.compression}"
            with tarfile.open(self._data, protocol) as tar:
                tar.extractall(self.dest)
        else:
            with zipfile.ZipFile(self._data, "r") as zip_out:
                zip_out.extractall(self.dest)

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
            data = []
            for root, directory, file in os.walk(os.getcwd()):
                for filename in file:
                    data.append(os.path.join(root, filename))
            with zipfile.ZipFile(archive_path, "w") as zip_in:
                for file in data:
                    zip_in.write(file)
        os.chdir(old_dir)
        self._data = archive_path.read_bytes()
