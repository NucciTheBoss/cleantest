[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

# Test environment providers

Test environment providers are the backbone of cleantest; they provide the containers or virtual machines that
cleantest injects the testlets into. Test environment providers can be thought of as hypervisors that can be
controlled from Python. To control test environment providers, cleantest uses Python decorators. These decorators
accept arguments from the user and capture the body of the testlet.

The following is a list of all the supported test environment providers in cleantest and how to control them.

## LXD

The `lxd` decorator handles running testlets inside of containers and/or virtual machines controlled by the LXD
hypervisor. The decorator accepts the following arguments:

* `name (str)`: Name for test environment (Default: "test").
* `image (List[str])`: LXD image to use for test environment (Default: ["ubuntu-jammy-amd64"]).
* `preserve (bool)`: Preserve test environment after test has completed (Default: True).
* `parallel (bool)`: Run test environment instances in parallel (Default: False).
* `num_threads (int)`: Number of threads to use when running test environment instances in parallel (Default: None).

### Example usage

```python
#!/usr/bin/env python3

"""Example usage of LXD test environment provider."""

import os
import pathlib

from cleantest.control import Configure
from cleantest.control.hooks import StartEnvHook
from cleantest.data.pkg import Charmlib, Pip
from cleantest.provider import lxd


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


def test_local_lxd(clean_slate) -> None:
    root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    config = Configure("lxd")
    start_hook = StartEnvHook(
        name="setup_deps",
        packages=[
            Charmlib(
                auth_token_path=root / "charmhub.secret",
                charmlibs=["charms.operator_libs_linux.v0.apt"],
            ),
            Pip(requirements=[root / "requirements.txt"]),
        ],
    )
    config.register_hook(start_hook)
    for name, result in install_snapd():
        assert result.exit_code == 0
```
