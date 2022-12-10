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
from collections import namedtuple


class InjectionError(Exception):
    ...


InjectableData = namedtuple("InjectableData", ["path", "hash"])


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

            cls_data = pickle.loads(fin.read_bytes())
            posargs = [
                value for key, value in cls_data.__dict__.items() if not key.startswith("_")
            ]
            hiddenargs = {
                key: value for key, value in cls_data.__dict__.items() if key.startswith("_")
            }
            new_cls = cls(*posargs)
            [setattr(new_cls, key, value) for key, value in hiddenargs.items()]
            return new_cls
        else:
            raise InjectionError(
                f"Cannot load object {data}. Cannot find pickle file or {type(data)} is not str."
            )

    def _dump(self) -> InjectableData:
        """Serialize object and generate SHA224 hash for verification.

        Returns:
            (InjectableData):
                path (str): Path to file containing serialized object.
                hash (str): Hash to verify authenticity of serialized object.
        """
        fout = pathlib.Path(tempfile.gettempdir()).joinpath(f"{uuid.uuid4()}.pkl")
        data = pickle.dumps(self)
        fout.write_bytes(data)
        verification_hash = hashlib.sha224(data).hexdigest()
        return InjectableData(str(fout), verification_hash)

    @abstractmethod
    def __injectable__(self) -> str:
        """Code to be injected into test environment provider."""
        ...
