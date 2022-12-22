#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing snap packages inside remote processes."""

import pathlib
import textwrap
from enum import Enum
from typing import List, Union

from cleantest.meta import BasePackage, BasePackageError, InjectableData
from cleantest.pkg.handler import snap

from ._mixins import SnapdSupport


class SnapPackageError(BasePackageError):
    """Base error for Snap package handler."""

    ...


class Confinement(Enum):
    """Confinement modes for snap packages."""

    STRICT = "strict"
    CLASSIC = "classic"
    DEVMODE = "devmode"


class Plug:
    """Represents a snap plug.

    Args:
        snap (str): Name of snap that provides plug.
        name (str): Name of plug.
    """

    def __init__(self, snap: str, name: str) -> None:
        self.snap = snap
        self.name = name


class Slot:
    """Represents a snap slot.

    Args:
        snap (str): Name of snap that provides slot.
        name (str): Name of slot.
    """

    def __init__(self, snap: str = None, name: str = None) -> None:
        self.snap = snap
        self.name = name


class Connection:
    """Represents `snap connect`.

    Args:
        plug (Plug): Plug to connect.
        slot (Slot): Slot to connect to (Default: None).
        wait (bool): Wait for `snap connect` operation to complete (Default: True).

    Raises:
        SnapPackageError: Raised if lint rule fails.
    """

    def __init__(self, plug: Plug, slot: Slot = None, wait: bool = True) -> None:
        self._plug = plug
        self._slot = slot
        self._wait = wait
        self._lint()

    def _lint(self) -> None:
        """Lint inputs passed to class constructor."""
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
        """Perform `snap connect` operation."""
        snap.connect(
            self._plug.snap,
            self._plug.name,
            self._slot.snap,
            self._slot.name,
            wait=self._wait,
        )


class Alias:
    """Represents `snap alias`.

    Args:
        snap_name (str): Name of snap that provides the app to alias.
        app_name (str): Name of the app to alias.
        alias_name (str): Name of alias to create.
        wait (bool): Wait for `snap alias` operation to complete (Default: True).

    Raises:
        SnapPackageError: Raised if lint rule fails.
    """

    def __init__(self, snap_name: str, app_name: str, alias_name: str, wait: bool = True) -> None:
        self._snap_name = snap_name
        self._app_name = app_name
        self._alias_name = alias_name
        self._wait = wait
        self._lint()

    def _lint(self) -> None:
        """Lint inputs passed to class constructor."""
        if self._snap_name is None or self._app_name is None or self._alias_name is None:
            holder = ", ".join(
                [f"{key} = {value}" for key, value in self.__dict__.items() if value is None]
            )
            raise SnapPackageError(f"Invalid alias: {holder} cannot be None.")

    def alias(self) -> None:
        """Perform `snap alias` operation."""
        snap.alias(self._snap_name, self._app_name, self._alias_name, self._wait)


class Snap(BasePackage, SnapdSupport):
    """Represents `snap install`.

    Args:
        snaps (List[str]): List of snaps to install (Default: None).
        local_snaps (List[str]): List of file paths to local snaps to install (Default: None).
        confinement (Confinement): Confinement mode to install snaps in
            (Default: Confinement.STRICT).
        channel (str): Channel to install snaps from (Default: None).
        cohort (str): Key of cohort that snap belongs to (Default: None).
        dangerous (bool): Install unsigned snaps (Default: False).
        connections (List[Connection]): List of connections to set up after snap is installed
            (Default: None).
        aliases (List[Alias]): List alias to create after snap is installed (Default: None).

    Raises:
        SnapPackageError: Raised if class creation fails.
    """

    def __init__(
        self,
        snaps: Union[str, List[str]] = None,
        local_snaps: Union[str, List[str]] = None,
        confinement: Confinement = Confinement.STRICT,
        channel: str = None,
        cohort: str = None,
        dangerous: bool = False,
        connections: List[Connection] = None,
        aliases: List[Alias] = None,
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
        """Run Snap package handler."""
        self._setup()
        self._handle_snap_install()

    def _setup(self) -> None:
        """Install snapd inside test environment."""
        self._install_snapd()

    def _handle_snap_install(self) -> None:
        """Install snap packages inside test environment."""
        if self.snaps is not None:
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

        if self.connections is not None:
            for connection in self.connections:
                connection.connect()

        if self.aliases is not None:
            for alias in self.aliases:
                alias.alias()

    def _dump(self) -> InjectableData:
        """Dump Snap package handler object.

        Raises:
            FileNotFoundError: Raised if local snap package is not found.

        Returns:
            (InjectableData): Path to dumped object and verification hash.
        """
        if self.local_snaps is not None:
            for local_snap in self.local_snaps:
                snap_path = pathlib.Path(local_snap)
                if not snap_path.exists() or not snap_path.is_file():
                    raise FileNotFoundError(f"Could not find local snap package {snap_path}")
                self._cached_local_snaps.add(snap_path.read_bytes())

        return super()._dump()

    def __injectable__(self, path: str, verification_hash: str) -> str:
        """Generate injectable script that will be used to install snap packages.

        Args:
            path (str): Path to pickled object inside the test environment.
            verification_hash: Hash to verify authenticity of pickled object.

        Returns:
            (str): Injectable script.
        """
        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3

            from {self.__module__} import {self.__class__.__name__}

            holder = {self.__class__.__name__}._load("{path}", "{verification_hash}")
            holder._run()
            """
        ).strip("\n")
