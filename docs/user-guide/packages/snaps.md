# Working with snap packages

Snap packages are a bundle of an app and its dependencies that work across a variety of Linux distributions
without modification. They are automatically managed and maintained by the [snapd](https://snapcraft.io/snapd) 
service running as a daemon in the background. Snaps can be run on servers, desktops, or internet-of-things devices; 
they greatly reduce the time-to-market of deploying applications to devices running Linux.

???+ note
    
    Comprehensive documentation on how to write and/or develop snap packages are beyond the scope of this
    documentation. If you are interested in learning more about snap packages, please refer to their official
    documentation here: [https://snapcraft.io/docs](https://snapcraft.io/docs)

## Confinement class

`Confinement` is an enum that represents the three possible confinement modes for a snap: _strict_, _classic_, 
and _devmode_. Snaps are commonly run in strict confinement, but certain snaps are granted classic confinement which
gives the snap unfettered access to the underlying host system. devmode is used when developing snaps to determine
which interfaces need to be defined and connected.

The class takes no arguments, but it has the following attributes:

* `STRICT`: Represents strict confinement.
* `CLASSIC`: Represents classic confinement.
* `DEVMODE`: Represents devmode confinement.

## Plug class

`Plug` is a metaclass that represents a snap plug. Plugs are used to connect a snap package to another snap package. Its
constructor accepts two arguments:

* `snap (str)`: Name of the snap that provides the plug. Defaults to _None_.
* `name (str)`: Name of the plug. Defaults to _None_.

## Slot class

`Slot` is a metaclass that represents a snap slot. Slots are to accept connections from other snap packages. Its
constructor accepts two arguments:

* `snap (str)`: Name of the snap that provides the slot.
* `name (str)`: Name of the slot.

## Connection class

`Connection` is a metaclass that represents the _snap connect_ command. It is used to connect plugs to slots after
the snap packages have been installed. Its constructor accepts three arguments:

* `plug (Plug)`: Plug to connect.
* `slot (Slot)`: Slot to connect to. Defaults to _None_.
* `wait (bool)`: Wait for _snap connect_ operation to complete before proceeding. Defaults to _True_.

`Connection` provides one private method:

* `_lint`: Lint inputs passed to the constructor to ensure that _snap connect_ will be a valid operation.

`Connection` provides one public method:

* `connect`: Execute _snap connect_ operation. Even though this method is public, __it should not be used when 
    configuring your hooks.__

## Alias class

`Alias` is a metaclass that represents the _snap alias_ command. It is used to create aliases after a snap package
has been installed. Its constructor accepts four arguments:

* `snap_name (str)`: Name of the snap that provides the app.
* `app_name (str)`: Name of the app to create an alias for.
* `alias_name (str)`: Name of alias to create.
* `wait (bool)`: Wait for _snap alias_ operation to complete before proceeding. Defaults to _True_.

`Alias` provides one private method:

* `_lint`: Lint inputs passed to the constructor to ensure that _snap alias_ will be a valid operation.

`Alias` provides one public method:

* `alias`: Execute _snap alias_ operation. Even though this method is public, __it should not be used when
    configuring your hooks.__

## Snap class

`Snap` is a package metaclass that represents the snap installation command `snap install`. Its constructor accepts
eight arguments:

* `snaps (List[str])`: List of snaps to install inside the test environment instance. These snaps are pulled from
    the public [Snap Store](https://snapcraft.io/store). Defaults to _None_.
* `local_snaps (List[str])`: List of file paths to local snap packages to be installed inside the test environment
    instance. Defaults to _None_.
* `confinement (Confinement)`: Confinement level to install snaps with. Defaults to _Confinement.STRICT_.
* `channel (str)`: Channel to install snap from. Only valid for snaps being pulled from store. Defaults to _None_.
* `cohort (str)`: Key of cohort that snap belongs to/should be installed with. Defaults to _None_.
* `dangerous (bool)`: Install unsigned snaps. Only valid for local snaps. Defaults to _False_.
* `connections (List[Connection])`: List of connections to set up after snaps have been installed. Defaults to _None_.
* `aliases (List[Alias])`: List of aliases to create after snaps have been installed. Defaults to _None_.

The `Snap` class will attempt to install snapd inside the test environment instance if the service is not detected
when the class goes to install the listed snap packages.

## Example usage

```python
#!/usr/bin/env python3

"""Example usage of Snap package metaclass with related classes."""

import os
import pathlib

from cleantest.control import Configure
from cleantest.control.hooks import StartEnvHook
from cleantest.data.pkg import Connection, Plug, Slot, Snap
from cleantest.provider import lxd


@lxd(image="ubuntu-jammy-amd64", preserve=False)
def functional_snaps():
    import sys
    from shutil import which

    if which("pypi-server") is None:
        sys.exit(1)
    elif which("marktext") is None:
        sys.exit(1)
    else:
        sys.exit(0)


def test_snap_package(clean_slate) -> None:
    root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    config = Configure("lxd")
    start_hook = StartEnvHook(
        name="test_snaps",
        packages=[
            Snap(
                snaps="pypi-server",
                connections=[
                    Connection(
                        Plug("pypi-server", "removable-media"),
                        Slot(name="removable-media"),
                    )
                ],
            ),
            Snap(
                local_snaps=[root / "marktext.snap"],
                dangerous=True,
            ),
        ],
    )
    config.register_hook(start_hook)
    for name, result in functional_snaps():
        assert result.exit_code == 0
```