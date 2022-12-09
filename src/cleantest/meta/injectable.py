#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Metaclass for objects that will be injected into environments."""

import hashlib
import pathlib
import pickle
import tempfile
import uuid
from abc import ABC, abstractmethod
from typing import Dict


class InjectionError(Exception):
    ...


class Injectable(ABC):
    @classmethod
    def _load(cls, data: str, verification_hash: str) -> object:
        """Alternative constructor to load previous created object.

        Args:
            data (str): Path to file containing serialized object.
            verification_hash (str): Hash to verify authenticity of serialized object.

        Returns:
            (object): Deserialized, verified object.
        """
        fin = pathlib.Path(data)
        if type(data) == str and fin.exists() and fin.is_file():
            if verification_hash != hashlib.sha224(fin.read_bytes()).hexdigest():
                raise InjectionError("Hashes do not match. Will not load untrusted object.")

            return cls(*pickle.loads(fin.read_bytes()).values())
        else:
            raise InjectionError(
                f"Cannot load object {data}. Cannot find pickle file or {type(data)} is not str."
            )

    def _dump(self) -> Dict[str, str]:
        """Serialize object and generate SHA224 hash for verification.

        Returns:
            (Dict[str, str]):
                path (str): Path to file containing serialized object.
                hash (str): Hash to verify authenticity of serialized object.
        """
        fout = pathlib.Path(tempfile.gettempdir()).joinpath(f"{uuid.uuid4()}.pkl")
        data = pickle.dumps(self)
        fout.write_bytes(data)
        verification_hash = hashlib.sha224(data).hexdigest()
        return {"path": str(fout), "hash": verification_hash}

    @abstractmethod
    def __injectable__(self) -> str:
        """Code to be injected into test environment provider."""
        ...
