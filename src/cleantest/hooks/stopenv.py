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

"""Hook run before test environment instance stops."""

from dataclasses import dataclass
from typing import List

from cleantest.meta.objects import injectable


@dataclass(frozen=True)
class StopEnvHook:
    """Hook run before stopping test environment.

    Args:
        name: Unique name of hook.
        download: Artifacts to download from test environment instance.
    """

    name: str
    download: List[injectable.Injectable] = None
