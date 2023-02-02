#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading directories from test environments."""

import os
import pathlib
import tarfile
import tempfile
from io import BytesIO
from typing import Iterable, Union

from cleantest.data.file import File


class DirectoryError(Exception):
    """Base error for Dir class."""


class DirectoryExistsError(Exception):
    """Raised when a directory already exists on the host."""


class DirectoryNotFoundError(Exception):
    """Raised when a directory is not found on the host."""


def _strip_tar(
    tar: tarfile.TarFile, n_components: int = 1
) -> Iterable[tarfile.TarInfo]:
    """Strip components from a tarfile to a specified level.

    Args:
        tar (tarfile.TarFile): Opened tar archive to strip.
        n_components (int): Number of levels to strip from tar file (Default: 1).

    Yields:
        (Iterable[tarfile.TarInfo]): TarInfo object with its path property modified.
    """
    for member in tar.getmembers():
        member_path = pathlib.Path(member.path)
        member.path = member_path.relative_to(*member_path.parts[:n_components])
        yield member


class Dir(File):
    """Represents a directory that can be shared between host and test environment.

    Args:
        src (Union[str, os.PathLike]): Where to load directory from.
        dest (Union[str, os.PathLike]): Where to dump directory to.
        overwrite (bool):
            True - overwrite directory if it already exists when dumping.
            False - raise error if directory already exists when dumping.
    """

    def __init__(
        self,
        src: Union[str, os.PathLike],
        dest: Union[str, os.PathLike],
        overwrite: bool = False,
    ) -> None:
        super().__init__(pathlib.Path(src), dest, overwrite)

    def load(self) -> None:
        """Load directory from specified source.

        Raises:
            DirectoryNotFoundError: Raised if directory is not found.
            NotADirectoryError: Raised if source is a file rather than a directory.
        """
        if self.src.exists() is False:
            raise DirectoryNotFoundError(f"Could not find {self.src}.")

        if self.src.is_file():
            raise NotADirectoryError(f"{self.src} is a file. Use File class instead.")

        _ = os.getcwd()
        os.chdir(os.sep.join(str(self.src).split(os.sep)[:-1]))
        with tempfile.NamedTemporaryFile() as fin:
            with tarfile.open(fin.name, "w:gz") as tar:
                tar.add(self.src.name)
            self.__data = pathlib.Path(fin.name).read_bytes()
        os.chdir(_)

    def dump(self) -> None:
        """Dump directory to specified destination.

        Raises:
            DirectoryExistsError: Raised if directory already exists and overwrite=False.
            DirectoryError: Raised if no data has been loaded prior to calling dump().
        """
        if self.dest.exists() and self.overwrite is False:
            raise DirectoryExistsError(
                f"{self.dest} already exists. Set overwrite = True to overwrite {self.dest}."
            )

        if self.__data is None:
            DirectoryError("Nothing to write.")

        with tarfile.open(fileobj=BytesIO(self.__data), mode="r:gz") as tar:
            tar.extractall(self.dest, members=_strip_tar(tar))
