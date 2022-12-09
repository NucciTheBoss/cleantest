#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing pip packages inside remote processes."""

import pathlib
import subprocess
import textwrap
from shutil import which
from typing import Dict, List, Union

from cleantest.meta import BasePackage, BasePackageError
from cleantest.utils import detect_os_variant


class PipPackageError(BasePackageError):
    ...


class Pip(BasePackage):
    def __init__(
        self,
        packages: Union[str, List[str]] = None,
        requirements: Union[str, List[str]] = None,
        constraints: Union[str, List[str]] = None,
    ) -> None:
        self.packages = [packages] if type(packages) == str else packages
        self.requirements = [requirements] if type(requirements) == str else requirements
        self._requirements_store = []
        self.constraints = [constraints] if type(constraints) == str else constraints
        self._constraints_store = []

        lint_rules = [
            lambda: True if packages is None and requirements is None else False,
            lambda: True if requirements is None and constraints is not None else False,
            lambda: True
            if type(requirements) == list
            and type(constraints) == list
            and len(requirements) != len(constraints)
            else False,
        ]
        for expr in lint_rules:
            if expr():
                raise PipPackageError(
                    "Lint rule failed. ",
                    f"Ensure passed arguments to {self.__class__.__name__} are correct.",
                )

    def _run(self) -> None:
        self._setup()
        self._handle_pip_install()

    def _setup(self) -> None:
        os_variant = detect_os_variant()

        if which("pip") is None:
            if os_variant == "ubuntu":
                cmd = ["apt", "install", "-y", "python3-pip"]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PipPackageError(
                        f"Failed to install pip using the following command: {' '.join(cmd)}"
                    )
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )

    def _handle_pip_install(self) -> None:
        if len(self.packages) > 0:
            cmd = ["python3", "-m", "pip", "install", " ".join(self.packages)]
            try:
                subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
            except subprocess.CalledProcessError:
                raise PipPackageError(
                    f"Failed to install packages {self.packages} "
                    f"using the following command {' '.join(cmd)}"
                )

        if self._constraints_store:
            for requirement, constraint in zip(self._requirements_store, self._constraints_store):
                requirement_file = pathlib.Path.home().joinpath("requirements.txt")
                requirement_file.write_text(requirement)
                constraint_file = pathlib.Path.home().joinpath("constraints.txt")
                constraint_file.write_text(constraint)
                cmd = [
                    "python3",
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirement_file),
                    "-c",
                    str(constraint_file),
                ]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PipPackageError(
                        (
                            f"Failed to install packages listed in requirements.txt file {requirement} "
                            f"with constraints.txt file {constraint} using the "
                            f"following command: {' '.join(cmd)}"
                        )
                    )
        else:
            for requirement in self._requirements_store:
                requirement_file = pathlib.Path(pathlib.Path.home().joinpath("requirements.txt"))
                requirement_file.write_text(requirement)
                cmd = ["python3", "-m", "pip", "install", "-r", str(requirement_file)]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PipPackageError(
                        (
                            f"Failed to install packages listed in requirements.txt file {requirement} "
                            f"using the following command: {' '.join(cmd)}"
                        )
                    )

    def _dump(self) -> Dict[str, str]:
        for requirement in self.requirements:
            fin = pathlib.Path(requirement)
            if not fin.exists() or not fin.is_file():
                raise FileNotFoundError(f"Could not find requirements file {requirement}.")
            self._requirements_store.append(fin.read_text())

        for constraint in self.constraints:
            fin = pathlib.Path(constraint)
            if not fin.exists() or not fin.is_file():
                raise FileNotFoundError(f"Could not find requirements file {constraint}.")
            self._constraints_store.append(fin.read_text())

        return super()._dump()

    def __injectable__(self, path: str, verification_hash: str) -> str:
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3

            from {self.__module__} import {self.__class__.__name__}

            holder = {self.__class__.__name__}._load("{path}", "{verification_hash}")
            holder._run()
            """
        ).strip("\n")
