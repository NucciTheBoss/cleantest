#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Metaclass for retrieving information about cleantest."""

import base64
import csv
import hashlib
import os
import pathlib
import tarfile
import tempfile
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Iterable, Tuple

import pkg_resources


class CleantestInfo:
    """Metaclass for getting information about the cleantest library."""

    def __new__(cls) -> "CleantestInfo":
        if not hasattr(cls, "instance"):
            cls.instance = super(CleantestInfo, cls).__new__(cls)
        return cls.instance

    @property
    def _src(self) -> Dict[str, bytes]:
        """Retrieve the source code of cleantest.

        Returns:
            (Dict[str, bytes]): Name and base64 encoded source code of cleantest module.
        """
        _ = os.getcwd()
        os.chdir(pkg_resources.get_distribution("cleantest").location)
        with tempfile.NamedTemporaryFile() as fin:
            with tarfile.open(fin.name, "w:gz") as tar:
                tar.add("cleantest")
            os.chdir(_)
            return {"cleantest": pathlib.Path(fin.name).read_bytes()}

    @property
    def _dependencies(self) -> Iterable[Tuple[str, bytes]]:
        """Retrieve the source code of cleantest's dependencies.

        Yields:
            (Dict[str, bytes]): Name and source code of dependencies.
        """
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            pool_results = pool.map(
                self._dependency_processor,
                pkg_resources.working_set.resolve(
                    pkg_resources.working_set.by_key["cleantest"].requires()
                ),
            )
            for res in pool_results:
                for k, v in res.items():
                    yield k, v

    def _dependency_processor(self, dependency: pkg_resources.Distribution) -> Dict[str, bytes]:
        """Collect source code of cleantest dependency.

        Args:
            dependency (pkg_resources.Distribution): Dependency of cleantest.

        Returns:
            (Dict[str, bytes]): Name and base64 encoded source code of dependency.
        """
        os.chdir(dependency.location)
        with tempfile.NamedTemporaryFile() as fin:
            with tarfile.open(fin.name, "w:gz") as tar, pathlib.Path(
                f"{dependency.key.replace('-', '_')}-{dependency.version}.dist-info"
            ).joinpath("RECORD").open(mode="rt") as dist_info_fin:
                for row in csv.reader(dist_info_fin):
                    tar.add(row[0])

            return {dependency.key: pathlib.Path(fin.name).read_bytes()}

    def _injectable(self, checksum: str, data: str) -> str:
        """Generate injectable script to install packages inside the test instance.

        Args:
            checksum (str): Checksum to verify base64 encoded object.
            data (str): Base64 encode tar archive containing source code for cleantest.

        Returns:
            (str): Injectable script.
        """
        with tempfile.TemporaryFile(mode="w+t") as fout:
            fout.writelines(
                [
                    "#!/usr/bin/env python3\n",
                    "import base64\n",
                    "import hashlib\n",
                    "import site\n",
                    "import tarfile\n",
                    "from io import BytesIO\n",
                    f"_ = base64.b64decode('{data}')\n",
                    f"if '{checksum}' != hashlib.sha224(_).hexdigest():\n"
                    "\traise Exception('Hashes do not match')\n",
                    "tar = tarfile.open(fileobj=BytesIO(_), mode='r:gz')\n",
                    "tar.extractall(site.getsitepackages()[0])\n",
                    "tar.close()\n",
                ]
            )
            fout.seek(0)
            return fout.read()

    def dump(self) -> Iterable[Tuple[str, Dict[str, str]]]:
        """Prepare cleantest for injection into test environment instance.

        Yields:
            (Iterable[Tuple[str, Dict[str, str]]]):
                name (str): Name of library being injected.
                checksum (str): Checksum to verify authenticity of archive.
                data (str): Base64 encoded tarball containing source code.
                injectable (str): Injectable to run inside remote instance.
        """
        packages = self._src
        packages.update(dict(self._dependencies))
        for k, v in packages.items():
            checksum = hashlib.sha224(v).hexdigest()
            data = base64.b64encode(v).decode()
            yield k, {
                "checksum": checksum,
                "data": data,
                "injectable": self._injectable(checksum, data),
            }
