#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Test that cleantest can successfully install and operate snap packages."""

import os

from cleantest.control import Configure
from cleantest.control.hooks import StartEnvHook
from cleantest.data.pkg import Connection, Plug, Slot, Snap
from cleantest.provider import lxd

root = os.path.dirname(os.path.realpath(__file__))
config = Configure()
start_hook = StartEnvHook(
    name="test_snaps",
    packages=[
        Snap(
            snaps="pypi-server",
            connections=[
                Connection(Plug("pypi-server", "removable-media"), Slot(name="removable-media"))
            ],
        ),
        Snap(local_snaps=os.path.join(root, "hello-world-gtk_0.1_amd64.snap"), dangerous=True),
    ],
)
config.register_hook(start_hook)


@lxd(image="ubuntu-jammy-amd64", preserve=False)
def functional_snaps():
    import sys
    from shutil import which

    if which("pypi-server") is None:
        sys.exit(1)
    elif which("hello-world-gtk") is None:
        sys.exit(1)
    else:
        sys.exit(0)


class TestLocalLXD:
    def test_snap_package(self) -> None:
        results = functional_snaps()
        for name, result in results.items():
            assert result.exit_code == 0
