#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Abstractions for uploading and downloading files from test environments."""

import copy
import os
import pathlib
import textwrap
from io import BytesIO, StringIO
from typing import Dict, Union

from cleantest.meta import Injectable


class FileError(Exception):
    """Base error for File class."""


class InjectableModeError(Exception):
    """Raised when an invalid injection mode has been passed to `_injectable`."""


class File(Injectable):
    """Represents a file that can be shared between host and test environment.

    Args:
        src (Union[str, os.PathLike, StringIO, BytesIO]):
            Where to load file from.
        dest (Union[str, os.PathLike]): Where to dump file to.
        overwrite (bool):
            True - overwrite file if it already exists when dumping.
            False - raise error if file already exists when dumping.
    """

    def __init__(
        self,
        src: Union[str, os.PathLike, StringIO, BytesIO],
        dest: Union[str, os.PathLike],
        overwrite: bool = False,
    ) -> None:
        if type(src) == str or isinstance(src, os.PathLike):
            self.src = pathlib.Path(src)
        elif isinstance(src, StringIO) or isinstance(src, BytesIO):
            self.src = src.read().encode() if isinstance(src, StringIO) else src.read()
        else:
            raise FileError(
                (
                    "Expected type str,os.PathLike, StringIO, or BytesIO, "
                    f"not {type(src)}."
                )
            )
        self.dest = pathlib.Path(dest)
        self.overwrite = overwrite
        self.__data = None

    def dump(self) -> None:
        """Dump directory to specified destination.

        Raises:
            FileExistsError: Raised if directory already exists and overwrite=False.
            FileError: Raised if no data has been loaded prior to calling dump().
        """
        if self.dest.exists() and self.overwrite is False:
            raise FileExistsError(
                (
                    f"{self.dest} already exists. Set overwrite = True to "
                    f"overwrite {self.dest}."
                )
            )

        if self.__data is None:
            raise FileError("Nothing to write.")

        self.dest.write_bytes(self.__data)

    def load(self) -> None:
        """Load file from specified source.

        Raises:
            FileNotFoundError: Raised if file is not found.
            FileError: Raised if source is a directory rather than a file.
        """
        if isinstance(self.src, pathlib.Path):
            if self.src.exists() is False:
                raise FileNotFoundError(f"Could not find {self.src}.")

            if self.src.is_dir():
                raise FileError(f"{self.src} is a directory. Use Dir class instead.")

            self.__data = self.src.read_bytes()
        else:
            self.__data = copy.deepcopy(self.src)

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
            InjectableModeError(
                f"Invalid mode: {_}. Please set mode to either 'push' or 'pull'."
            )
        elif _ == "push":
            return textwrap.dedent(
                f"""
                #!/usr/bin/env python3
                
                from {self.__module__} import {self.__class__.__name__}
                
                _ = {self.__class__.__name__}._loads("{data['checksum']}", "{data['data']}")
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
                
                _ = {self.__class__.__name__}._loads("{data['checksum']}", "{data['data']}")
                _.load()
                print(json.dumps(_._dumps()), file=sys.stdout)
                """
            ).strip("\n")

    def __repr__(self) -> str:
        """String representation of File."""
        attrs = ", ".join(
            f"{k}={v}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({attrs})"
