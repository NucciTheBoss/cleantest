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

from cleantest import Configure
from cleantest.hooks import StartEnvHook
from cleantest.pkg import Connection, Plug, Slot, Snap
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


@lxd(image="jammy-amd64", preserve=False)
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
import tempfile

from cleantest import Configure
from cleantest.hooks import StopEnvHook
from cleantest.hooks.data import Dir, File
from cleantest.provider import lxd

config = Configure()
stop_hook = StopEnvHook(
    name="download_artifact",
    download=[
        File("/root/dump.txt", os.path.join(tempfile.gettempdir(), "dump.txt"), overwrite=True),
        Dir("/root/dump", os.path.join(tempfile.gettempdir(), "dump"), overwrite=True),
    ],
)
config.register_hook(stop_hook)

@lxd(image="jammy-amd64", preserve=True)
def work_on_artifacts():
    import os
    import pathlib

    pathlib.Path("/root/dump.txt").write_text("Dumped like a sack of rocks")
    os.mkdir("/root/dump")
    pathlib.Path("/root/dump/dump_1.txt").write_text("Oh I have been dumped again!")


class TestUploadDownload:
    def test_upload_download(self) -> None:
        work_on_artifacts()
        assert pathlib.Path(tempfile.gettempdir()).joinpath("dump.txt").is_file() is True
        assert pathlib.Path(tempfile.gettempdir()).joinpath("dump").is_dir() is True
```