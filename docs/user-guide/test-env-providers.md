# Test environment providers

Test environment providers are the backbone of cleantest; they provide the containers or virtual machines that
cleantest injects the testlets into. Test environment providers can be thought of as hypervisors that can be
controlled from Python. To control test environment providers, cleantest uses Python decorators. These decorators
accept arguments from the user and capture the body of the testlet.

The following is a list of all the supported test environment providers in cleantest and how to control them.

## LXD

The `lxd` decorator handles running testlets inside of containers and/or virtual machines controlled by the LXD
hypervisor. The decorator accepts the following arguments:

* `name (str)`: Prefix to use in name of test environment instances. Defaults to _"test"_.
* `image (List[str])`: List of LXD images to use for created test environments. Defaults to _["jammy-amd64"]_.
* `preserve (bool)`: Preserve test environment after testlet has completed. Defaults to _True_.
* `env (EnvDataStore)`: Environment to use in test environment. Defaults to base instance of _EnvDataStore_.
* `data (LXDDataStore)`: Data necessary for LXD hypervisor. Defaults to base instance of _LXDDataStore_.
* `image_config (List[Dict[str, Any]])`: List of image configurations to add to _LXDDataStore_.
* `client_config (LXDClientConfig)`: Configuration to use for LXD client. Defaults to _None_.
* `parallel (bool)`: Run test environments in parallel. Defaults to `False`.
* `num_threads (int)`: Number of threads to use when running test environment in parallel. Defaults to _None_.

### Example usage

```python
#!/usr/bin/env python3

"""Example usage of LXD test environment provider."""

import os

from cleantest import Configure
from cleantest.hooks import StartEnvHook
from cleantest.pkg import Charmlib, Pip
from cleantest.provider import lxd

# Define the hooks and register them.
root = os.path.dirname(os.path.realpath(__file__))
config = Configure()
start_hook = StartEnvHook(
    name="my_start_hook",
    packages=[
        Charmlib(
            auth_token_path=os.path.join(root, "charmhub.secret"),
            charmlibs=["charms.operator_libs_linux.v0.apt"],
        ),
        Pip(requirements=os.path.join(root, "requirements.txt")),
    ],
)
config.register_hook(start_hook)


# Define the testlets.
@lxd(image="jammy-amd64", preserve=False)
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

    
class TestLocalLXD:
    def test_local_lxd(self) -> None:
        results = install_snapd()
        for name, result in results.items():
            assert result.exit_code == 0
```
