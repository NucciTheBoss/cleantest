#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing pip packages inside remote processes."""

import pathlib
import subprocess
import textwrap
from shutil import which
from typing import Dict, List, Union

from cleantest.meta import BasePackage, BasePackageError
from cleantest.meta.utils import detect_os_variant
from cleantest.utils import apt


class PipPackageError(BasePackageError):
    """Base error for Pip package handler."""


class Pip(BasePackage):
    """Represents `pip install`.

    Args:
        packages (List[str]): List of packages to install (Default: None).
        requirements (List[str]): List of paths to requirements.txt files (Default: None).
        constraints (List[str]): List of paths to constraints.txt files (Default: None).

    Raises:
        PipPackageError: Raised if lint rule fails at class creation.
    """

    def __init__(
        self,
        packages: Union[str, List[str]] = None,
        requirements: Union[str, List[str]] = None,
        constraints: Union[str, List[str]] = None,
    ) -> None:
        self.packages = [packages] if type(packages) == str else packages
        self.requirements = (
            [requirements] if type(requirements) == str else requirements
        )
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
        """Run Pip package handler."""
        self._setup()
        self._handle_pip_install()

    def _setup(self) -> None:
        """Set up and install dependencies needed by pip.

        Raises:
            PipPackageError: Raised if an error is encountered when installing pip.
            NotImplementedError: Raised if unsupported operating system is
                being used for a test environment.
        """
        os_variant = detect_os_variant()

        if which("pip") is None:
            if os_variant == "ubuntu":
                apt.install("python3-pip")
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )

    def _handle_pip_install(self) -> None:
        """Install packages inside test environment using pip.

        Raises:
            PipPackageError: Raised if error is encountered when installing packages with pip.
        """
        if self.packages is not None:
            cmd = ["python3", "-m", "pip", "install", " ".join(self.packages)]
            try:
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
            except subprocess.CalledProcessError:
                raise PipPackageError(
                    f"Failed to install packages {self.packages} "
                    f"using the following command {' '.join(cmd)}"
                )

        if self._constraints_store:
            for requirement, constraint in zip(
                self._requirements_store, self._constraints_store
            ):
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
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
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
                requirement_file = pathlib.Path(
                    pathlib.Path.home().joinpath("requirements.txt")
                )
                requirement_file.write_text(requirement)
                cmd = ["python3", "-m", "pip", "install", "-r", str(requirement_file)]
                try:
                    subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )
                except subprocess.CalledProcessError:
                    raise PipPackageError(
                        (
                            f"Failed to install packages listed in requirements.txt file {requirement} "
                            f"using the following command: {' '.join(cmd)}"
                        )
                    )

    def _dump(self) -> Dict[str, str]:
        """Prepare Pip object for injection.

        Raises:
            FileNotFoundError: Raised if a requirements or constraints file is not found.

        Returns:
            (Dict[str, str]):
                checksum (str): Checksum to verify authenticity of serialized Pip object.
                data (str): Base64 encoded string containing serialized Pip object.
                injectable (str): Injectable to run inside remote environment.
        """
        if self.requirements is not None:
            for requirement in self.requirements:
                fin = pathlib.Path(requirement)
                if not fin.exists() or not fin.is_file():
                    raise FileNotFoundError(
                        f"Could not find requirements file {requirement}."
                    )
                self._requirements_store.append(fin.read_text())

        if self.constraints is not None:
            for constraint in self.constraints:
                fin = pathlib.Path(constraint)
                if not fin.exists() or not fin.is_file():
                    raise FileNotFoundError(
                        f"Could not find constraints file {constraint}."
                    )
                self._constraints_store.append(fin.read_text())

        return super()._dump()

    def _injectable(self, data: Dict[str, str], **kwargs) -> str:
        """Generate injectable script that will be used to install packages with pip.

        Args:
            data (Dict[str, str]): Data that needs to be in injectable script.
                - checksum (str): SHA224 checksum to verify authenticity of Pip object.
                - data (str): Base64 encoded Pip object to inject.

        Returns:
            (str): Injectable script.
        """
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3

            from {self.__module__} import {self.__class__.__name__}

            holder = {self.__class__.__name__}._load("{data['checksum']}", "{data['data']}")
            holder._run()
            """
        ).strip("\n")
