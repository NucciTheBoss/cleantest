#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Metaclass for retrieving information about cleantest."""

import csv
import os
import pathlib
import tarfile
import tempfile
import textwrap
from concurrent.futures import ProcessPoolExecutor
from typing import Dict

import pkg_resources


class CleantestInfo:
    def __new__(cls) -> "CleantestInfo":
        if not hasattr(cls, "instance"):
            cls.instance = super(CleantestInfo, cls).__new__(cls)
        return cls.instance

    @property
    def src(self) -> Dict[str, bytes]:
        """Source code of cleantest module.

        Returns:
            (Dict[str, bytes]): Name and source code of cleantest module.
        """
        old_dir = os.getcwd()
        os.chdir(pkg_resources.get_distribution("cleantest").location)
        tar_path = pathlib.Path(tempfile.gettempdir()).joinpath("cleantest")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add("cleantest")
        os.chdir(old_dir)

        return {"cleantest": tar_path.read_bytes()}

    @property
    def dependencies(self) -> Dict[str, bytes]:
        """Source code for dependencies of cleantest module.

        Returns:
            (Dict[str, bytes]): Name and source code of dependencies.
        """
        result = {}
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            pool_results = pool.map(
                self._get_dependencies,
                pkg_resources.working_set.resolve(
                    pkg_resources.working_set.by_key["cleantest"].requires()
                ),
            )
            for res in pool_results:
                [result.update({key: value}) for key, value in res.items()]

        return result

    def _get_dependencies(self, dependency: pkg_resources.Distribution) -> Dict[str, bytes]:
        """Collect source code of cleantest dependency.

        Args:
            dependency (pkg_resources.Distribution): Dependency of cleantest.

        Returns:
            (Dict[str, bytes]): Name and source code of dependency.
        """
        os.chdir(dependency.location)
        tar_path = pathlib.Path(tempfile.gettempdir()).joinpath(dependency.key)
        with tarfile.open(tar_path, "w:gz") as tar:
            with pathlib.Path(
                f"{dependency.key.replace('-', '_')}-{dependency.version}.dist-info"
            ).joinpath("RECORD").open(mode="rt") as fin:
                for row in csv.reader(fin):
                    tar.add(row[0])

        return {dependency.key: tar_path.read_bytes()}

    def make_pkg_injectable(self, pkg_path: str) -> str:
        """Create injectable to install cleantest packages inside test environment.

        Args:
            pkg_path (str): Path to package inside test environment.

        Returns:
            (str): Injectable script.
        """
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3
            import site
            import tarfile

            site.getsitepackages()[0]
            tarball = tarfile.open("{pkg_path}", "r:gz")
            tarball.extractall(site.getsitepackages()[0])
            """
        ).strip("\n")
