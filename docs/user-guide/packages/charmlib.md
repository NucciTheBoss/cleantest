# Working with charm libraries

Charm libraries are special Python modules used in charmed operators deployed by [__Juju__](https://juju.is). They
are an easy way to distribute reusable code without needing to involve any particular package build system.
Fundamentally, charm libraries are used to provide a means for charm developers to make the implementation of any 
relation they define as simple as possible for other charm developers.

???+ note

    Comphrensive documentation on how to write/develop/use charm libraries are beyond the scope of this documentation.
    If you are interested in learning more about charm libraries, please refer to their official documentation
    here: [https://juju.is/docs/sdk/libraries](https://juju.is/docs/sdk/libraries)

## Charmlib class

`Charmlib` is a package metaclass that represents the charm library installation command _charmcraft fetch-lib_.
Its constructor accepts two arguments:

1. `auth_token_path (str)`: File path to a Charmhub authentication token. This token is needed to download charm
    libraries from [charmhub.io](https://charmhub.io).
2. `charmlibs (List[str])`: List of charm libraries to install inside the test environment instance.

Charm libraries are not installed a special directory such as site-packages or dist-packages; they are directly
installed to a _lib/_ directory under your current working directory. Therefore, the `Charmlib` class modifies the
_PYTHONPATH_ environment variable to inform the Python interpreter that there are importable modules under _lib/_.

## Example usage

First, you need to create a Charmhub authentication token. This can be accomplished by using the following command
in your shell:

```commandline
charmcraft login --export charmhub.secret
```

After authenticating with Charmhub (you may need to create an Ubuntu One account), you can now use the example
test script below: 

```python
#!/usr/bin/env python3

"""Example usage of Charmlib package metaclass."""

import os

from cleantest import Configure
from cleantest.hooks import StartEnvHook
from cleantest.pkg import Charmlib
from cleantest.provider import lxd

root = os.path.dirname(os.path.realpath(__file__))
config = Configure()
start_hook = StartEnvHook(
    name="charmlib_start_hook",
    packages=[
        Charmlib(
            auth_token_path=os.path.join(root, "charmhub.secret"),
            charmlibs=["charms.operator_libs_linux.v0.apt"],
        ),
    ],
)
config.register_hook(start_hook)


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

    sys.exit(0)

    
class TestCharmlib:
    def test_charmlib(self) -> None:
        results = install_snapd()
        for name, result in results.items():
            assert result.exit_code == 0
```