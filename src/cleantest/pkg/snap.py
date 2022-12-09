#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing snap packages inside remote processes."""

import pathlib
import textwrap
from enum import Enum
from typing import Dict, List, Optional, Union

from cleantest.meta import BasePackage, BasePackageError
from cleantest.pkg.handler import snap

from ._mixins import SnapdSupport


class SnapPackageError(BasePackageError):
    ...


class Confinement(Enum):
    """Confinement modes for snap packages."""

    STRICT = "strict"
    CLASSIC = "classic"
    DEVMODE = "devmode"


class Plug:
    def __init__(self, snap: str, name: str) -> None:
        self.snap = snap
        self.name = name


class Slot:
    def __init__(self, snap: Optional[str] = None, name: Optional[str] = None) -> None:
        self.snap = snap
        self.name = name


class Connection:
    def __init__(self, plug: Plug, slot: Slot = None, wait: bool = True) -> None:
        self._plug = plug
        self._slot = slot
        self._wait = wait
        self._lint()

    def _lint(self) -> None:
        if self._plug.snap is None or self._plug.name is None:
            raise SnapPackageError(
                f"Invalid plug: {self._plug.__dict__}. "
                "Plug must have an associated snap and name."
            )
        if self._slot is not None and self._slot.snap is None and self._slot.name is None:
            raise SnapPackageError(
                f"Invalid slot: {self._slot.__dict__}. "
                "Slot must at least have an associated snap or name."
            )

    def connect(self) -> None:
        snap.connect(
            self._plug.snap,
            self._plug.name,
            self._slot.snap,
            self._slot.name,
            wait=self._wait,
        )


class Alias:
    def __init__(self, snap_name: str, app_name: str, alias_name: str, wait: bool = True) -> None:
        self._snap_name = snap_name
        self._app_name = app_name
        self._alias_name = alias_name
        self._wait = wait
        self._lint()

    def _lint(self) -> None:
        if self._snap_name is None or self._app_name is None or self._alias_name is None:
            holder = ", ".join(
                [f"{key} = {value}" for key, value in self.__dict__.items() if value is None]
            )
            raise SnapPackageError(f"Invalid alias: {holder} cannot be None.")

    def alias(self) -> None:
        snap.alias(self._snap_name, self._app_name, self._alias_name, self._wait)


class Snap(BasePackage, SnapdSupport):
    def __init__(
        self,
        snaps: Union[str, List[str]] = None,
        local_snaps: Union[str, List[str]] = None,
        confinement: Confinement = Confinement.STRICT,
        channel: str = None,
        cohort: str = None,
        dangerous: bool = False,
        connections: List[Connection] = None,
        aliases: List = None,
    ) -> None:
        self.snaps = [snaps] if type(snaps) == str else snaps
        self.local_snaps = [local_snaps] if type(local_snaps) == str else local_snaps
        self._cached_local_snaps = set()
        self.confinement = confinement
        self.channel = channel
        self.cohort = cohort
        self.dangerous = dangerous
        self.connections = connections
        self.aliases = aliases

        if snaps is None and local_snaps is None:
            raise SnapPackageError("No snaps specified.")

        if not hasattr(Confinement, confinement.name):
            raise SnapPackageError(
                f"Invalid confinement {confinement.name}. "
                f"Must be either {', '.join([i.name for i in Confinement])}"
            )

    def _run(self) -> None:
        self._setup()
        self._handle_snap_install()

    def _setup(self) -> None:
        self._install_snapd()

    def _handle_snap_install(self) -> None:
        if len(self.snaps) > 0:
            snap.install(
                self.snaps,
                channel=self.channel,
                classic=True if self.confinement == Confinement.CLASSIC else False,
                cohort=self.cohort if self.cohort is not None else "",
            )

        for pkg in self._cached_local_snaps:
            path = pathlib.Path.home().joinpath("tmp.snap")
            path.write_bytes(pkg)
            snap.install_local(
                str(path),
                classic=True if self.confinement == Confinement.CLASSIC else False,
                devmode=True if self.confinement == Confinement.DEVMODE else False,
                dangerous=self.dangerous,
            )

        for connection in self.connections:
            connection.connect()

        for alias in self.aliases:
            alias.alias()

    def _dump(self) -> Dict[str, str]:
        for local_snap in self.local_snaps:
            snap_path = pathlib.Path(local_snap)
            if not snap_path.exists() or not snap_path.is_file():
                raise FileNotFoundError(f"Could not find local snap package {snap_path}")
            self._cached_local_snaps.add(snap_path.read_bytes())

        return super()._dump()

    def __injectable__(self, path: str, verification_hash: str) -> str:
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3

            from {self.__module__} import {self.__class__.__name__}

            holder = {self.__class__.__name__}._load("{path}", "{verification_hash}")
            holder._run()
            """
        ).strip("\n")
