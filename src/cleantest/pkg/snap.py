#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Manager for installing snap packages inside remote processes."""

from __future__ import annotations

import pathlib
import subprocess
from enum import Enum
from shutil import which
from typing import List

from cleantest.pkg._base import Package, PackageError
from cleantest.pkg.handler import snap
from cleantest.utils import detect_os_variant


class SnapConfinement(Enum):
    """Confinement modes for snap packages."""

    STRICT = "strict"
    CLASSIC = "classic"
    DEVMODE = "devmode"


class Snap(Package):
    def __init__(
        self,
        snaps: str | List[str] = None,
        local_snaps: str | List[str] = None,
        confinement: SnapConfinement = SnapConfinement.STRICT,
        channel: str = None,
        cohort: str = None,
        dangerous: bool = False,
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

                if hasattr(SnapConfinement, confinement.name):
                    self._confinement = confinement
                else:
                    raise PackageError(
                        f"Invalid confinement {confinement.name}. "
                        f"Must be either {', '.join([i.name for i in SnapConfinement])}"
                    )

                self._channel = channel
                self._cohort = cohort
                self._dangerous = dangerous
        else:
            self._snap_store = _manager._snap_store
            self._local_snap_store = _manager._local_snap_store
            self._confinement = _manager._confinement
            self._channel = _manager._channel
            self._cohort = _manager._cohort
            self._dangerous = _manager._dangerous

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
                classic=True if self._confinement == SnapConfinement.CLASSIC else False,
                cohort=self._cohort if self._cohort is not None else "",
            )

        for pkg in self._local_snap_store:
            out = pathlib.Path("/root/tmp.snap")
            out.write_bytes(pkg)
            snap.install_local(
                "/root/tmp.snap",
                classic=True if self._confinement == SnapConfinement.CLASSIC else False,
                devmode=True if self._confinement == SnapConfinement.DEVMODE else False,
                dangerous=self._dangerous,
            )
