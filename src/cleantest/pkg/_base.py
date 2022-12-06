#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Base package class for installing packages inside remote processes."""

import hashlib
import os
import pathlib
import pickle
import tempfile
import uuid
from abc import ABC, abstractmethod
from typing import Dict


class PackageError(Exception):
    ...


class Package(ABC):
    @abstractmethod
    def _run(self) -> None:
        ...

    @abstractmethod
    def _setup(self) -> None:
        ...

    @classmethod
    def _load(cls, _manager: str, hash: str) -> object:
        if type(_manager) == str and os.path.isfile(_manager):
            fin = pathlib.Path(_manager)
            if hash != hashlib.sha224(fin.read_bytes()).hexdigest():
                raise PackageError("SHA224 hashes do not match. Will not load untrusted object.")

            return cls(_manager=pickle.loads(fin.read_bytes()))
        else:
            raise PackageError(f"Invalid type {type(_manager)} received. Type must be bytes.")

    def _dump(self) -> Dict[str, str]:
        """Return a path to a pickled object and hash for verification."""
        filepath = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.pkl")
        data = pickle.dumps(self)
        hash = hashlib.sha224(data).hexdigest()
        fout = pathlib.Path(filepath)
        fout.write_bytes(pickle.dumps(self))
        return {"path": filepath, "hash": hash}
