# Copyright 2023 Jason C. Nucciarone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Abstractions for uploading and downloading files from test environments."""

import copy
import os
import pathlib
import shutil
import tarfile
import tempfile
import textwrap
from io import BytesIO, StringIO
from typing import Dict, Union

from cleantest.meta import BaseError, Injectable


class Error(BaseError):
    """Raise when File macro encounters an error."""


class File(Injectable):
    """Represents a file that can be shared between host and test environment.

    Args:
        src (Union[str, pathlib.Path, StringIO, BytesIO]):
            Where to load file from.
        dest (Union[str, pathlib.Path]): Where to dump file to.
        overwrite (bool):
            True - overwrite file if it already exists when dumping.
            False - raise error if file already exists when dumping.
    """

    def __init__(
        self,
        src: Union[str, pathlib.Path, bytes, StringIO, BytesIO],
        dest: Union[str, pathlib.Path],
        overwrite: bool = False,
    ) -> None:
        self.src = src
        self.dest = pathlib.Path(dest)
        self.overwrite = overwrite
        self._data = None

    def load(self) -> None:
        """Load file from specified source.

        Raises:
            FileNotFoundError: Raised if file is not found.
            FileError: Raised if source is a directory rather than a file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            _ = pathlib.Path(tmp_dir)
            with tarfile.open(pathlib.Path(tmp_dir) / "_", "w:gz") as tar:
                old_pwd = os.getcwd()
                os.chdir(_)
                if type(self.src) == str or isinstance(self.src, pathlib.Path):
                    data = pathlib.Path(self.src)
                    if data.exists() is False:
                        raise FileNotFoundError(f"Could not find {self.src}.")

                    if data.is_dir():
                        raise Error(
                            f"{self.src} is a directory. Use Dir class instead."
                        )
                    shutil.copy(data, _ / "data")
                    tar.add("data")
                elif isinstance(self.src, StringIO) or isinstance(self.src, BytesIO):
                    data = copy.deepcopy(self.src)
                    placeholder = pathlib.Path("data")
                    placeholder.write_text(data.read()) if isinstance(
                        self.src, StringIO
                    ) else placeholder.write_bytes(data.read())
                    tar.add(placeholder)
                else:
                    raise Error(
                        (
                            "Expected type str, os.PathLike, StringIO, or BytesIO, "
                            f"not {type(self.src)}."
                        )
                    )

                os.chdir(old_pwd)

            self._data = pathlib.Path(tar.name).read_bytes()

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

        if self._data is None:
            raise Error("Nothing to write.")

        with tempfile.TemporaryDirectory() as tmp_dir, tarfile.open(
            fileobj=BytesIO(self._data), mode="r:gz"
        ) as tar:
            tar.extractall(tmp_dir)
            shutil.copy((pathlib.Path(tmp_dir) / "data"), self.dest)

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
            Error(f"Invalid mode: {_}. Please set mode to either 'push' or 'pull'.")
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
