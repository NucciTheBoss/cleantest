#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing pip packages inside remote processes."""

from __future__ import annotations

import pathlib
import subprocess
from shutil import which
from typing import List

from cleantest._utils import detect_os_variant
from cleantest.pkg._base import Package, PackageError


class Pip(Package):
    def __init__(
        self,
        packages: str | List[str] = None,
        requirements: str | List[str] = None,
        constraints: str | List[str] = None,
        _manager: object | None = None,
    ) -> None:
        if _manager is None:
            self.__lint_inputs(packages, requirements, constraints)

            self._package_store = set()
            if type(packages) == str:
                self._package_store.add(packages)
            elif type(packages) == list:
                [self._package_store.add(p) for p in packages]

            self._requirements_store = []
            if type(requirements) == str:
                self._requirements_store.append(requirements)
            elif type(requirements) == list:
                self._requirements_store.extend(requirements)

            self._constraints_store = []
            if type(constraints) == str:
                self._constraints_store.append(constraints)
            elif type(constraints) == list:
                self._constraints_store.extend(constraints)

            self.__load_file_data()
        else:
            self._package_store = _manager._package_store
            self._requirements_store = _manager._requirements_store
            self._constraints_store = _manager._constraints_store

    def _run(self) -> None:
        self._setup()
        self.__handle_pip_install()

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
                    raise PackageError(
                        f"Failed to isntall pip using the following command: {' '.join(cmd)}"
                    )
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )

    def __handle_pip_install(self) -> None:
        for package in self._package_store:
            cmd = ["python3", "-m", "pip", "install", package]
            try:
                subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                )
            except subprocess.CalledProcessError:
                raise PackageError(
                    f"Failed to install package {package} "
                    f"using the following command {' '.join(cmd)}"
                )

        if self._constraints_store:
            for r, c in zip(self._requirements_store, self._constraints_store):
                r_file = pathlib.Path(pathlib.Path.home().joinpath("requirements.txt"))
                c_file = pathlib.Path(pathlib.Path.home().joinpath("constraints.txt"))
                r_file.touch()
                c_file.touch()
                with r_file.open(mode="w") as fout:
                    fout.writelines(r)
                with c_file.open(mode="w") as fout:
                    fout.writelines(c)
                cmd = ["python3", "-m", "pip", "install", "-r", str(r_file), "-c", str(c_file)]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PackageError(
                        (
                            f"Failed to install packages listed in requirements.txt file {r} "
                            f"with constraints.txt file {c} using the "
                            f"following command: {' '.join(cmd)}"
                        )
                    )
        else:
            for r in self._requirements_store:
                r_file = pathlib.Path(pathlib.Path.home().joinpath("requirements.txt"))
                r_file.touch()
                with r_file.open(mode="w") as fout:
                    fout.writelines(r)
                cmd = ["python3", "-m", "pip", "install", "-r", str(r_file)]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PackageError(
                        (
                            f"Failed to install packages listed in requirements.txt file {r} "
                            f"using the following command: {' '.join(cmd)}"
                        )
                    )

    def __lint_inputs(
        self,
        packages: str | List[str] | None,
        requirements: str | List[str] | None,
        constraints: str | List[str] | None,
    ) -> None:
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
                raise PackageError(
                    "Lint rule failed. ",
                    f"Ensure passed arguments to {self.__class__.__name__} are correct.",
                )

    def __load_file_data(self) -> None:
        for i in range(0, len(self._requirements_store)):
            file = pathlib.Path(self._requirements_store[i])
            if file.exists():
                self._requirements_store[i] = [l.strip() for l in file.open()]
            else:
                raise PackageError(f"Requirements file {self._requirements_store[i]} not found.")

        for i in range(0, len(self._constraints_store)):
            file = pathlib.Path(self._constraints_store[i])
            if file.exists():
                self._constraints_store[i] = [l.strip() for l in file.open()]
            else:
                raise PackageError(f"Constraints file {self._constraints_store[i]} not found.")
