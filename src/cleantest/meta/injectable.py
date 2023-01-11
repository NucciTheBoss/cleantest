#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Abstract base class for injectable objects."""

import base64
import hashlib
import pickle
from abc import ABC, abstractmethod
from typing import Dict


class InjectionError(Exception):
    """Base error for classes that inherit from Injectable."""


class Injectable(ABC):
    """Abstract metaclass that provides core methods needed by all injectable objects."""

    @classmethod
    def _load(cls, checksum: str, data: str) -> object:
        """Alternative constructor to load previously initialized object.

        Args:
            checksum (str): Checksum to verify authenticity of serialized object.
            data (str): Path to file containing serialized object.

        Returns:
            (object): Deserialized, verified object.
        """
        if type(data) != str:
            raise InjectionError(f"Cannot load object {data}. {type(data)} != str")

        _ = base64.b64decode(data)
        if checksum != hashlib.sha224(_).hexdigest():
            raise InjectionError("Hashes do not match. Will not load untrusted object.")

        _ = pickle.loads(_)
        posargs = [value for key, value in _.__dict__.items() if not key.startswith("_")]
        hiddenargs = {key: value for key, value in _.__dict__.items() if key.startswith("_")}
        new_cls = cls(*posargs)
        [setattr(new_cls, key, value) for key, value in hiddenargs.items()]
        return new_cls

    def _dump(self, **kwargs) -> Dict[str, str]:
        """Prepare object for injection.

        Returns:
            (Dict[str, str]):
                checksum (str): Checksum to verify authenticity of serialized object.
                data (str): Base64 encoded string containing serialized object.
                injectable (str): Injectable to run inside remote environment.
        """
        pickle_data = pickle.dumps(self)
        checksum = hashlib.sha224(pickle_data).hexdigest()
        data = base64.b64encode(pickle_data).decode()
        return {
            "checksum": checksum,
            "data": data,
            "injectable": self._injectable({"checksum": checksum, "data": data}, **kwargs),
        }

    @abstractmethod
    def _injectable(self, data: Dict[str, str], **kwargs) -> str:
        """Python script to run inside of test environment provider."""
