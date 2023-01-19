#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading files from test environments."""

import os
import pathlib
import tarfile
import tempfile
import textwrap
from io import BytesIO
from typing import Dict

from cleantest.meta import Injectable


class FileError(Exception):
    """Base error for File class."""


class InjectableModeError(Exception):
    """Raised when an invalid injection mode has been passed to `_injectable`."""


class File(Injectable):
    """Represents a file that can be shared between host and test environment.

    Args:
        src (pathlib.Path): Where to load file from.
        dest (pathlib.Path): Where to dump file to.
        overwrite (bool):
            True - overwrite file if it already exists when dumping.
            False - raise error if file already exists when dumping.
    """

    def __init__(self, src: str, dest: str, overwrite: bool = False) -> None:
        self.src = pathlib.Path(src)
        self.dest = pathlib.Path(dest)
        self.overwrite = overwrite
        self._data = None

    def dump(self) -> None:
        """Dump directory to specified destination.

        Raises:
            FileExistsError: Raised if directory already exists and overwrite=False.
            FileError: Raised if no data has been loaded prior to calling dump().
        """
        if self.dest.exists() and self.overwrite is False:
            raise FileExistsError(
                f"{self.dest} already exists. Set overwrite = True to overwrite {self.dest}."
            )

        if self._data is None:
            raise FileError("Nothing to write.")

        with tarfile.open(
            fileobj=BytesIO(self._data), mode="r:gz"
        ) as tar, tempfile.TemporaryDirectory() as tmp_dir:
            tar.extractall(tmp_dir)
            self.dest.write_bytes(pathlib.Path(tmp_dir).joinpath(self.src.name).read_bytes())

    def load(self) -> None:
        """Load file from specified source.

        Raises:
            FileNotFoundError: Raised if file is not found.
            FileError: Raised if source is a directory rather than a file.
        """
        if self.src.exists() is False:
            raise FileNotFoundError(f"Could not find {self.src}.")

        if self.src.is_dir():
            raise FileError(f"{self.src} is a directory. Use Dir class instead.")

        _ = os.getcwd()
        os.chdir(os.sep.join(str(self.src).split(os.sep)[:-1]))
        with tempfile.NamedTemporaryFile() as fin:
            with tarfile.open(fin.name, "w:gz") as tar:
                tar.add(self.src.name)
            self._data = pathlib.Path(fin.name).read_bytes()
        os.chdir(_)

    def _injectable(self, data: Dict[str, str], **kwargs) -> str:
        """Generate injectable script that will be run inside the test environment.

        Args:
            data (Dict[str, str]): Data that needs to be in injectable script.
                - checksum (str): SHA224 checksum to verify authenticity of object.
                - data (str): Base64 encoded object to inject.
            **kwargs:
                mode (str): "push" or "pull" object to/from test environment instance.

        Raises:
            InjectableModeError: Raised if invalid mode has been passed.

        Returns:
            (str): Injectable script.
        """
        _ = kwargs.get("mode", None)
        if _ not in {"push", "pull"}:
            InjectableModeError(f"Invalid mode: {_}. Please set mode to either 'push' or 'pull'.")
        elif _ == "push":
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                
                from {self.__module__} import {self.__class__.__name__}
                
                _ = {self.__class__.__name__}._load("{data['checksum']}", "{data['data']}")
                _.dump()
                """
            ).strip("\n")
        else:
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                import json
                import sys
                
                from {self.__module__} import {self.__class__.__name__}
                
                _ = {self.__class__.__name__}._load("{data['checksum']}", "{data['data']}")
                _.load()
                print(json.dumps(_._dump()), file=sys.stdout)
                """
            ).strip("\n")
