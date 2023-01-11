#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test LXD environment capabilities using local LXD cluster."""

import os

from cleantest.control import Configure
from cleantest.control.hooks import StartEnvHook
from cleantest.data.pkg import Charmlib, Pip
from cleantest.provider import lxd

# Define the hooks and register them.
root = os.path.dirname(os.path.realpath(__file__))
lxd_provider_config = Configure("lxd")
startenv_hook = StartEnvHook(
    name="setup_deps",
    packages=[
        Charmlib(
            auth_token_path=os.path.join(root, "charmhub.secret"),
            charmlibs=["charms.operator_libs_linux.v0.apt"],
        ),
        Pip(requirements=os.path.join(root, "requirements.txt")),
    ],
)
lxd_provider_config.register_hook(startenv_hook)


# Define the testlets.
@lxd(image="ubuntu-jammy-amd64", preserve=False)
def install_snapd():
    import sys

    import charms.operator_libs_linux.v0.apt as apt

    try:
        apt.update()
        apt.add_package("snapd")
        print("snapd installed.", file=sys.stdout)
    except apt.PackageNotFoundError:
        print("Package could not be found in cache or system.", file=sys.stderr)
        sys.exit(1)
    except apt.PackageError as e:
        print(f"Could not install package. Reason: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        snapd = apt.DebianPackage.from_installed_package("snapd")
        print(f"snapd version {snapd.fullversion} is installed.", file=sys.stdout)
    except apt.PackageNotFoundError:
        print("Snapd failed to install.", file=sys.stderr)
        sys.exit(1)

    try:
        from tabulate import tabulate

        print("tabulate is installed.", file=sys.stdout)
    except ImportError:
        print("Failed to import tabulate package.", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


# Run the tests through pytest.
class TestLocalLXD:
    def test_local_lxd(self) -> None:
        results = install_snapd()
        for name, result in results.items():
            assert result.exit_code == 0
