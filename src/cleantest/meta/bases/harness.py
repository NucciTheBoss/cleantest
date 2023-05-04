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

"""Base class for test environment provider BaseHarness's."""

import inspect
from io import StringIO
from typing import Callable, List, Pattern


class BaseHarness:
    """Base class for test environment provider harnesses."""

    @staticmethod
    def _make_testlet(func: Callable, remove: List[Pattern] = None) -> str:
        """Make injectable testlet from defined function.

        Args:
            func: Testlet function.
            remove: Compiled regex pattern to remove from testlet.
        """
        src_code = inspect.getsource(func)
        if remove is not None:
            for regex in remove:
                src_code = regex.sub("", src_code)

        testlet = StringIO()
        testlet.writelines(
            [
                "#!/usr/bin/env python3\n",
                f"{src_code}\n",
                f"{func.__name__}()\n",
            ]
        )
        testlet.seek(0)
        return testlet.read()
