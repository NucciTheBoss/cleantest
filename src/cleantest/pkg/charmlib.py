#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing charm libraries inside remote processes."""

from __future__ import annotations

import hashlib
import pathlib
import pickle
import uuid
from shutil import which
from typing import List, Tuple


class CharmLibManagerError(Exception):
    ...


# NOTE: After class has been constructed, serialize and wormhole over to remote agent.
class CharmLibManager:
    def __init__(self, charmlibs: str | List[str]) -> None:
        raise NotImplementedError("CharmLibManager not available until cleantest-0.2.0")
        self.__charmlib_store = set()
        if type(charmlibs) == str:
            self.__charmlib_store.add(charmlibs)
        elif type(charmlibs) == list:
            for lib in charmlibs:
                self.__charmlib_store.add(lib)
        else:
            raise CharmLibManagerError(
                f"{type(charmlibs)} is invalid. charmlibs must either be str or List[str]."
            )

    def _setup(self) -> None:
        # TODO: Check if charmcraft is installed. If not, install it.
        # Requires snap and snapd to be available on the host system.
        ...

    def _run(self, provider: str) -> None:
        # TODO: Invoke __handle_charm_lib_install.
        ...

    def _dump(self) -> Tuple[str, str]:
        """Return a path to a pickled object and hash for verification."""
        filepath = f"/tmp/{uuid.uuid4()}.dat"
        data = pickle.dumps(self)
        hash = hashlib.sha224(data).hexdigest()
        fout = pathlib.Path(filepath)
        fout.write_bytes(pickle.dumps(self))
        return filepath, hash

    def _verify(self, hash: str) -> bool:
        # TODO: Validate hash of sent charmlib manager
        ...

    def __handle_charm_lib_install(self) -> None:
        # TODO: Handle placing charm libraries on site-packages.
        ...
