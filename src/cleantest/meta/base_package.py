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

"""Metaclass for objects that handle installing packages inside test environments."""

from abc import abstractmethod

from .mixins import Injectable


class BasePackage(Injectable):
    """Metaclass for package handlers.

    Packages define tooling stubs needed to install packages inside test environments.
    """

    @abstractmethod
    def _run(self) -> None:
        """Run installer for package."""

    @abstractmethod
    def _setup(self) -> None:
        """Perform setup needed inside test environment to run installer."""
