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

"""BaseHarness for the LXD test environment provider."""

import functools
import os
import re
from typing import Callable, Dict, List, Optional, Union

from cleantest.data import File
from cleantest.meta import BaseHarness, Result
from cleantest.meta.utils import thread_count

from .archon import LXDArchon

_match_lxd = re.compile(r"^@lxd\.target\(([^)]+)\)|^@lxd\(([^)]+)\)|^@lxd\(?\)?")


class Error(Exception):
    """Raise when LXD harness encounters an error."""


class lxd(BaseHarness):  # noqa N801
    """LXD test environment provider.

    Args:
        name: Name for test environment. Default: "test".
        image: LXD image to use for test environment Default: "ubuntu-jammy-amd64".
        preserve: Preserve test environment after test has completed. Default: True.
        num_threads:
            Number of threads to use when running
            test environment instances in parallel. Default: 1.
    """

    def __init__(
        self,
        name: str = "test",
        image: Union[str, List[str]] = "ubuntu-jammy-amd64",
        preserve: bool = True,
        num_threads: Optional[int] = None,
    ) -> None:
        self._name = name
        self._images = [image] if type(image) == str else image
        self._preserve = preserve
        if type(num_threads) != int or num_threads < 1:
            os.environ["CLEANTEST_NUM_THREADS"] = str(thread_count())
        else:
            os.environ["CLEANTEST_NUM_THREADS"] = str(num_threads)

    def __call__(self, func: Callable) -> Callable:
        """Callable for lxd decorator."""

        @functools.wraps(func)
        def wrapper() -> Dict[str, Result]:
            """Create new test environment instances and execute testlet.

            Notes:
                Pre-existing instances will have new testlet uploaded, but
                StartEnvHooks will not be executed.
            """
            archon = LXDArchon()
            instances = []
            for image in self._images:
                instances.append(f"{self._name}-{image}")
            testlet = self._make_testlet(func, remove=[_match_lxd])
            for name, image in zip(instances, self._images):
                if archon.exists(name):
                    archon.push(name, testlet, "/root/testlet")
                else:
                    archon.deploy(
                        name, image, resources=[File(testlet, "/root/testlet")]
                    )
            results = archon.execute(instances, "python3 /root/testlet")
            if not self._preserve:
                archon.destroy()

            return results

        return wrapper

    @classmethod
    def target(
        cls,
        *instances: str,
        num_threads: Optional[int] = None,
    ) -> Callable:
        """Target specific LXD test environment instances by name.

        Args:
            *instances: Test environment instance name.
            num_threads: Number of threads to use for running testlets.
        """
        if type(num_threads) != int or num_threads < 1:
            os.environ["CLEANTEST_NUM_THREADS"] = str(thread_count())
        else:
            os.environ["CLEANTEST_NUM_THREADS"] = str(num_threads)

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper() -> Dict[str, Result]:
                """Execute testlet inside pre-existing instances."""
                archon = LXDArchon()
                for instance in instances:
                    if not archon.exists(instance):
                        raise Error(
                            f"Test environment instance {instance} does not exist"
                        )
                testlet = cls._make_testlet(func)
                archon.push([*instances], testlet, "/root/testlet")
                results = archon.execute([*instances], "python3 /root/testlet")

                return results

            return wrapper

        return decorator
