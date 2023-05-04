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

"""Hook run when test environment instance starts."""


from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from cleantest.meta.bases import BaseInjectable


@dataclass(frozen=True)
class StartEnvHook:
    """Hook run at the start of the test environment.

    Args:
        name: Unique name of hook.
        packages: Packages to inject into test environment.
        push: Objects to push into test environment.
    """

    name: str
    packages: List["BaseInjectable"] = None
    push: List["BaseInjectable"] = None
