#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Test parallel testing capabilites of LXD provider using local LXD cluster."""

from cleantest import Configure
from cleantest.hooks import StartEnvHook
from cleantest.pkg import Pip
from cleantest.provider import lxd

cleantest_config = Configure()
start_hook = StartEnvHook(name="pip_injection", packages=[Pip(packages="tabulate")])
cleantest_config.register_hook(start_hook)


@lxd(
    image=["jammy-amd64", "focal-amd64", "bionic-amd64"],
    preserve=False,
    parallel=True,
    num_threads=2,
)
def install_tabulate():
    import sys

    try:
        from tabulate import tabulate

        print("tabulate is installed.", file=sys.stdout)
    except ImportError:
        print("Failed to import tabulate package.", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


class TestParallelLXD:
    def test_parallel_lxd(self) -> None:
        results = install_tabulate()
        for name, result in results.items():
            try:
                assert result.exit_code == 0
            except AssertionError:
                raise Exception(f"{name} failed. Result: {result}")
