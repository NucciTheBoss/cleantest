#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing snap packages inside remote processes."""

import pathlib
import subprocess
from enum import Enum
from shutil import which
from typing import List, Optional, Union

from cleantest.pkg._base import Package, PackageError
from cleantest.pkg.handler import snap
from cleantest.utils import detect_os_variant


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
            raise PackageError(
                f"Invalid plug: {self._plug.__dict__}. "
                "Plug must have an associated snap and name."
            )
        if self._slot is not None and self._slot.snap is None and self._slot.name is None:
            raise PackageError(
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
            raise PackageError(f"Invalid alias: {holder} cannot be None.")

    def alias(self) -> None:
        snap.alias(self._snap_name, self._app_name, self._alias_name, self._wait)


class Snap(Package):
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
        _manager: "Snap" = None,
    ) -> None:
        if _manager is None:
            if snaps is None and local_snaps is None:
                raise PackageError("No valid snap packages were passed.")
            else:
                self._snap_store = set()
                if type(snaps) == str:
                    self._snap_store.add(snaps)
                elif type(snaps) == list:
                    [self._snap_store.add(pkg) for pkg in snaps]

                self._local_snap_store = set()
                if type(local_snaps) == str:
                    path = pathlib.Path(local_snaps)
                    if path.exists():
                        self._local_snap_store.add(path.read_bytes())
                    else:
                        raise PackageError(f"Could not find local snap package at {local_snaps}")
                elif type(local_snaps) == list:
                    for pkg in local_snaps:
                        path = pathlib.Path(pkg)
                        if path.exists():
                            self._local_snap_store.add(path.read_bytes())
                        else:
                            raise PackageError(
                                f"Could not find local snap package at {local_snaps}"
                            )

                if hasattr(Confinement, confinement.name):
                    self._confinement = confinement
                else:
                    raise PackageError(
                        f"Invalid confinement {confinement.name}. "
                        f"Must be either {', '.join([i.name for i in Confinement])}"
                    )

                self._channel = channel
                self._cohort = cohort
                self._dangerous = dangerous
                self._connections = connections
                self._aliases = aliases
        else:
            self._snap_store = _manager._snap_store
            self._local_snap_store = _manager._local_snap_store
            self._confinement = _manager._confinement
            self._channel = _manager._channel
            self._cohort = _manager._cohort
            self._dangerous = _manager._dangerous
            self._connections = _manager._connections
            self._aliases = _manager._aliases

    def _run(self) -> None:
        self._setup()
        self._handle_snap_install()

    def _setup(self) -> None:
        os_variant = detect_os_variant()

        if which("snap") is None:
            if os_variant == "ubuntu":
                cmd = ["apt", "install", "-y", "snapd"]
                try:
                    subprocess.run(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except subprocess.CalledProcessError:
                    raise PackageError(
                        f"Failed to install snapd using the following command: {' '.join(cmd)}."
                    )
            else:
                raise NotImplementedError(
                    f"Support for {os_variant.capitalize()} not available yet."
                )

    def _handle_snap_install(self) -> None:
        if len(self._snap_store) > 0:
            snap.install(
                list(self._snap_store),
                channel=self._channel,
                classic=True if self._confinement == Confinement.CLASSIC else False,
                cohort=self._cohort if self._cohort is not None else "",
            )

        for pkg in self._local_snap_store:
            out = pathlib.Path("/root/tmp.snap")
            out.write_bytes(pkg)
            snap.install_local(
                "/root/tmp.snap",
                classic=True if self._confinement == Confinement.CLASSIC else False,
                devmode=True if self._confinement == Confinement.DEVMODE else False,
                dangerous=self._dangerous,
            )

        for connection in self._connections:
            connection.connect()

        for alias in self._aliases:
            alias.alias()
