[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

# Using hooks

Hooks are used to run actions at various stages of the cleantest lifecycle. They can be used to configure test
environments after they have been created, upload dependencies into the test environment, or download artifacts
after the test has finished. Currently, there are two supported hook types. Their usage is described below.

## StartEnvHook

`StartEnvHook`, or __start environment hook__, is a hook that is run after a test environment instance has been 
created and initialized. It has two main usages:

1. Install dependencies needed by the testlet.
2. Uploading artifacts needed by the testlet to run.

Start environment hooks accept the following arguments:

* `name (str)`: Name of the hook. ___Must be unique.___
* `packages (List[Injectable])`: List of packages to install inside the test environment instance before running the 
   testlet.
* `upload (List[Injectable])`: List of artifacts to upload from the local system to the test environment instance.

### Example usage

```python
#!/usr/bin/env python3

"""Example usage of StartEnvHook."""

import os
import pathlib

from cleantest.control import Configure
from cleantest.hooks import StartEnvHook
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
                local_snaps=root / "marktext.snap",
                dangerous=True,
            ),
        ],
    )
    config.register_hook(start_hook)
    for name, result in functional_snaps():
        assert result.exit_code == 0
```

## StopEnvHook

`StopEnvHook`, or __stop environment hook__, is a hook that is run after the testlet has completed 
inside the test environment instance. It has one main usage:

1. Downloading artifacts after the testlet has completed.

Stop environment hooks accept the following arguments:

* `name (str)`: Name of the hook. ___Must be unique.___
* `download (List[Injectable])`: List of artifacts to download from the test environment instance to the local system.

### Example usage

```python
#!/usr/bin/env python3

"""Example usage of StopEnvHook."""

import os
import pathlib
import shutil

from cleantest.control import Configure
from cleantest.hooks import StopEnvHook
from cleantest.data import Dir, File
from cleantest.provider import lxd


@lxd(image="jammy-amd64", preserve=True)
def work_on_artifacts():
    import os
    import pathlib

    pathlib.Path("/root/dump.txt").write_text("Dumped like a sack of rocks")
    os.mkdir("/root/dump")
    pathlib.Path("/root/dump/dump_1.txt").write_text("Oh I have been dumped again!")


def test_download() -> None:
    root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    config = Configure("lxd")
    stop_hook = StopEnvHook(
        name="download_artifact",
        download=[
            File("/root/dump.txt", root / "dump.txt", overwrite=True, ),
            Dir("/root/dump", root / "dump", overwrite=True, ),
        ],
    )
    config.register_hook(stop_hook)
    for name, result in work_on_artifacts():
        assert (root / "dump.txt").is_file() is True
        assert (root / "dump").is_dir() is True
    (root / "dump.txt").unlink(missing_ok=True)
    shutil.rmtree(root / "dump")
```