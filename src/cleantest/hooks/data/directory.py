#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading directories from test environments."""

import os
import pathlib
import tarfile
import tempfile
from io import BytesIO
from typing import Iterable

from .file import File


class DirectoryError(Exception):
    ...


class DirectoryExistsError(Exception):
    ...


class DirectoryNotFoundError(Exception):
    ...


def _strip_tar(tar: tarfile.TarFile, n_components: int = 1) -> Iterable[tarfile.TarInfo]:
    for member in tar.getmembers():
        member_path = pathlib.Path(member.path)
        member.path = member_path.relative_to(*member_path.parts[:n_components])
        yield member


class Dir(File):
    def __init__(self, src: str, dest: str, overwrite: bool = False) -> None:
        super().__init__(src, dest, overwrite)

    def dump(self) -> None:
        if self.dest.exists() and self.overwrite is False:
            raise DirectoryExistsError(
                f"{self.dest} already exists. Set overwrite = True to overwrite {self.dest}."
            )

        if self._data is None:
            DirectoryError("Nothing to write.")

        with tarfile.open(fileobj=BytesIO(self._data), mode="r:gz") as tar:
            tar.extractall(self.dest, members=_strip_tar(tar))

    def load(self) -> None:
        if self.src.exists() is False:
            raise FileNotFoundError(f"Could not find {self.src}.")

        if self.src.is_file():
            raise NotADirectoryError(f"{self.src} is a file. Use File class instead.")

        old_dir = os.getcwd()
        os.chdir(os.sep.join(str(self.src).split(os.sep)[:-1]))
        archive_path = pathlib.Path(tempfile.gettempdir()).joinpath(self.src.name)
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.src.name)
        os.chdir(old_dir)
        self._data = archive_path.read_bytes()
