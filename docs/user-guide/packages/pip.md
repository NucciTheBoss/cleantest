[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

# Working with pip packages

Pip is the package installer for the Python programming language. You can use it to install packages from the
[Python Package Index (PYPI)](https://pypi.org).

## Pip class

`Pip` is a package metaclass that represents the Python package installation command _pip install_. Its constructor
accepts three arguments:

* `packages (List[str])`: List of packages to install. Packages are pulled from PYPI. Defaults to _None_.
* `requirements (List[str])`: List of paths to requirements.txt files. Defaults to _None_.
* `constraints (List[str])`: List of paths to constraints.txt files. Defaults to _None_.

???+ warning "Warning about using multiple requirements and constraints files"

    The requirements and constraints fields in `Pip` are __one-to-one__. If you define multiple requirements files to
    use and want to use a constraints file with one of the requirements files, then you will need to define a
    constraints file for each of the requirements files in the list. __If the length of requirements files list does not
    match the length of the constraints files list, then an exception will be raised.__

    Therefore, if you have multiple requirements files and only one uses a constraints file, it is better to use
    instantiate two instances of `Pip` class rather than one. One instance can be used for the requirements and 
    constraints file pairing while the other can be used for the rest of the requirements files.

## Example usage

```python
#!/usr/bin/env python3

"""Example usage of Pip package metaclass."""

import os
import pathlib

from cleantest.control import Configure
from cleantest.control.hooks import StartEnvHook
from cleantest.data.pkg import Pip
from cleantest.provider import lxd


@lxd(image="ubuntu-jammy-amd64", preserve=False)
def install_snapd():
    import sys

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
            Pip(requirements=[root / "requirements.txt"]),
        ],
    )
    config.register_hook(start_hook)
    for name, result in install_snapd():
        assert result.exit_code == 0
```