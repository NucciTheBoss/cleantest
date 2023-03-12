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

"""Temporarily change the current working directory."""

import contextlib
import os
from typing import Union


@contextlib.contextmanager
def temporary_cwd(tmp_cwd: Union[str, os.PathLike]) -> None:
    """Temporarily change the current working directory.

    Args:
        tmp_cwd: Directory to temporarily change too.
    """
    tmp = os.getcwd()
    os.chdir(tmp_cwd)
    yield
    os.chdir(tmp)
