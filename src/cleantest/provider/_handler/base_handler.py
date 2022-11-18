#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions and utilities for test environment providers."""

from __future__ import annotations

import inspect
import os
import pathlib
import re
import sys
import tarfile
import tempfile
import textwrap
from abc import ABC, abstractmethod
from typing import Any, Callable, List

from pydantic import BaseModel

import cleantest


class HandlerError(Exception):
    ...


class Result(BaseModel):
    exit_code: int | None = None
    stdout: Any | None = None
    stderr: Any | None = None


class Handler(ABC):
    """Abstract super-class for all test environment providers."""

    @abstractmethod
    def run(self) -> Result:
        ...

    @abstractmethod
    def _init(self) -> None:
        ...

    @abstractmethod
    def _execute(self) -> Any:
        ...

    @abstractmethod
    def _process(self) -> Result:
        ...

    @abstractmethod
    def _handle_start_env_hooks(self) -> None:
        ...

    def _get_cleantest_source(self) -> bytes:
        for root, directory, file in os.walk(cleantest.__path__[0]):
            src_path = pathlib.Path(root)
            if src_path.name == cleantest.__name__:
                old_dir = os.getcwd()
                os.chdir(os.sep.join(str(src_path).split(os.sep)[:-1]))
                tar_path = pathlib.Path(tempfile.gettempdir()).joinpath(cleantest.__name__)
                with tarfile.open(tar_path, "w:gz") as tarball:
                    tarball.add(cleantest.__name__)
                os.chdir(old_dir)

                return tar_path.read_bytes()

        raise HandlerError(f"Could not find source directory for {cleantest.__name__}.")

    def _construct_cleantest_injection(self, path: str) -> str:
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3
            import site
            import tarfile
    
            site.getsitepackages()[0]
            tarball = tarfile.open("{path}", "r:gz")
            tarball.extractall(site.getsitepackages()[0])
            """.strip(
                "\n"
            )
        )

    def _construct_testlet(self, func: Callable, remove: List[re.Pattern] | None) -> str:
        """Construct Python source file to be run in subroutine.

        Args:
            func (Callable): TODO
            remove (List[re.Pattern]): TODO

        Returns:
            str: TODO

        Future:
            This will need more advanced logic if tests accept arguments.
        """
        try:
            src = inspect.getsource(func)
            if remove is not None:
                for pattern in remove:
                    src = re.sub(pattern, "", src)

            with tempfile.TemporaryFile(mode="w+t") as f:
                content = [
                    "#!/usr/bin/env python3\n",
                    f"{src}\n",
                    f"{func.__name__}()\n",
                ]
                f.writelines(content)
                f.seek(0)
                scriptlet = f.read()

            return scriptlet
        except OSError:
            raise HandlerError(f"Could not locate source code for testlet {func.__name__}.")

    def _construct_pkg_installer(self, pkg: object, file_path: str, hash: str) -> str:
        src = inspect.getsourcefile(pkg.__class__)
        if src is None:
            raise HandlerError(f"Could not get the source file of object {pkg.__class__.__name__}")

        with tempfile.TemporaryFile(mode="w+t") as f:
            content = [
                f"{open(src, 'rt').read()}\n",
                f"holder = {pkg.__class__.__name__}._load('{file_path}', '{hash}')\n",
                "holder._run()\n",
            ]
            f.writelines(content)
            f.seek(0)
            pkg_installer = f.read()

        return pkg_installer
