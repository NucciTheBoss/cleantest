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

"""Fetch cleantest for injection into test environment instances."""

import base64
import csv
import hashlib
import pathlib
import re
import tarfile
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO, StringIO
from typing import Dict

import pkg_resources

from .thread_count import thread_count
from .tmpcwd import temporary_cwd

_pyc_ignore = re.compile(r"[.]pyc$")


def _injectable(checksum: str, data: str) -> str:
    """Generate injectable to install package distribution on test instance.

    Args:
        checksum: Checksum to verify base64 encoded object.
        data: Base64 encoded tarball containing source code of distribution.

    Returns:
        str: Injectable Python script.
    """
    injectable = StringIO()
    injectable.writelines(
        [
            "#!/usr/bin/env python3\n",
            "import base64\n",
            "import hashlib\n",
            "import site\n",
            "import tarfile\n",
            "from io import BytesIO\n",
            f"tmp = base64.b64decode('{data}')\n",
            f"if '{checksum}' != hashlib.sha224(tmp).hexdigest():\n"
            "\traise Exception('Hashes do not match')\n",
            "tar = tarfile.open(fileobj=BytesIO(tmp), mode='r:gz')\n",
            "tar.extractall(site.getsitepackages()[0])\n",
            "tar.close()\n",
        ]
    )
    injectable.seek(0)
    return injectable.read()


def _collect(dist: pkg_resources.Distribution) -> Dict[str, str]:
    """Collect source code of package distribution.

    Args:
        dist: Package distribution.

    Returns:
        Dict[str, str]: Name and base64 encoded tarball of distribution source code.
    """
    with temporary_cwd(dist.location):
        tarball = BytesIO()
        with tarfile.open(fileobj=tarball, mode="w:gz") as tar:
            root = f"{dist.key.replace('-', '_')}-{dist.version}.dist_info"
            record = pathlib.Path(root) / "RECORD"
            with record.open(mode="rt") as record_in:
                for row in csv.reader(record_in):
                    # Ignore .pyc files
                    if not _pyc_ignore.match(row[0]):
                        tar.add(row[0])

        tarball.seek(0)
        target = tarball.read()
        return {
            dist.key: {
                "checksum": (checksum := hashlib.sha224(target).hexdigest()),
                "data": (data := base64.b64encode(target).decode()),
                "injectable": _injectable(checksum, data),
            }
        }


def sourcefetch() -> Dict[str, Dict[str, str]]:
    """Fetch cleantest module and its dependencies for injection.

    Returns:
        Dict[str, Dict[str, str]]:
            Keys:
                - name: Name of library being injected.
            Values:
                - checksum: Checksum to verify authenticity of tarball.
                - data: Base64 encoded tarball containing source code.
                - injectable: Injectable Python script to unpack tarball.
    """
    result = {}
    dists = [pkg_resources.get_distribution("cleantest")]
    dists.extend(
        pkg_resources.working_set.resolve(
            pkg_resources.working_set.by_key["cleantest"].requires()
        )
    )
    with ProcessPoolExecutor(max_workers=thread_count()) as executor:
        source = executor.map(_collect, dists)
        for name, data in source:
            result.update({name: data})

    return result
