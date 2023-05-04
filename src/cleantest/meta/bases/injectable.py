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

import base64
import hashlib
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseInjectable(ABC):
    """Abstract metaclass that provides core methods needed by all injectable objects."""

    @classmethod
    def _loads(cls, checksum: str, data: str) -> Any:
        """Alternative constructor to load previously initialized object.

        Args:
            checksum: Checksum to verify authenticity of serialized object.
            data: Path to file containing serialized object.

        Returns:
            Any: Deserialized, verified object.
        """
        if type(data) != str:
            raise Exception(f"Cannot load object {data}. {type(data)} != str")

        tmp = base64.b64decode(data)
        if checksum != hashlib.sha224(tmp).hexdigest():
            raise Exception("Hashes do not match. Will not load untrusted object.")

        tmp = pickle.loads(tmp)
        posargs = [
            value for key, value in tmp.__dict__.items() if not key.startswith("_")
        ]
        hiddenargs = {
            key: value for key, value in tmp.__dict__.items() if key.startswith("_")
        }
        new_cls = cls(*posargs)
        [setattr(new_cls, key, value) for key, value in hiddenargs.items()]
        return new_cls

    def _dumps(self, **kwargs) -> Dict[str, str]:
        """Prepare object for injection.

        Returns:
            (Dict[str, str]):
                checksum: Checksum to verify authenticity of serialized object.
                data: Base64 encoded string containing serialized object.
                injectable: Injectable Python script to run inside test instance.
        """
        pickle_data = pickle.dumps(self)
        checksum = hashlib.sha224(pickle_data).hexdigest()
        data = base64.b64encode(pickle_data).decode()
        return {
            "checksum": checksum,
            "data": data,
            "injectable": self._injectable(
                {"checksum": checksum, "data": data}, **kwargs
            ),
        }

    @abstractmethod
    def _injectable(self, data: Dict[str, str], **kwargs) -> str:
        """Injectable Python script to run inside of test environment provider."""
