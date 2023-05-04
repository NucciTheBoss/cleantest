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

"""Base error class for cleantest."""


class BaseError(Exception):
    """Raise when cleantest encounters an error."""

    @property
    def name(self) -> str:
        """Get a string representation of the error plus class name."""
        return f"<{type(self).__module__}.{type(self).__name__}>"

    @property
    def message(self) -> str:
        """Return the message passed as an argument."""
        return self.args[0]

    def __repr__(self) -> str:
        """String representation of the error."""
        return f"<{type(self).__module__}.{type(self).__name__} {self.args}>"
