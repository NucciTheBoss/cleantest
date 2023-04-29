[//]: # "Copyright 2023 Jason C. Nucciarone" 
[//]: # "See LICENSE file for licensing details."

# Working with directories

Directories can be uploaded to and downloaded from test environment instances as artifacts.

## Dir class

The `Dir` class represents a directory. Its constructor accepts three arguments:

* `src (str)`: File path to load directory from.
* `dest (str)`: File path for where to dump directory.
* `overwrite (bool)`: Overwrite the directory if it already exists at _dest_. Defaults to _False_.

???+ info "`Dir` versus `File`"

    When the `Dir` class's _load_ method is invoked, an exception will be raised if _src_ is determined to be a file
    and not a directory. This exception is raised because cleantest handles directories differently than files when
    dumping out to _dest_. If you are working with files, not directories, you should use the [`File`](./file.md)
    class instead.

### Supported hooks

The `Dir` class's behavior changes depending on the hook it is used with. Here is a list of hooks that support `Dir`
and how `Dir` behaves when accessed by them:

[`StartEnvHook`](../hooks.md#startenvhook) 

:   _src_ is loaded from local system and _dest_ is the location to dump the directory
    inside the test environment instance.

[`StopEnvHook`](../hooks.md#stopenvhook)

:   _src_ is loaded from the test environment instance and _dest_ is the location to dump the directory on the
    local system.

## Example usage

```python
#!/usr/bin/env python3

"""Example usage of Dir class."""

import os
import pathlib
import shutil

from cleantest.control import Configure
from cleantest.hooks import StartEnvHook, StopEnvHook
from cleantest.data import Dir
from cleantest.provider import lxd


@lxd(image="ubuntu-jammy-amd64", preserve=False)
def work_on_artifacts():
    import os
    import pathlib
    import sys

    print(pathlib.Path("/root/greetings").is_dir(), file=sys.stdout)

    os.mkdir("/root/dump")
    pathlib.Path("/root/dump/dump_1.txt").write_text("Oh I have been dumped again!")


def test_upload_download(clean_slate) -> None:
    root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    config = Configure("lxd")
    start_hook = StartEnvHook(
        name="upload_artifact",
        upload=[
            Dir(root / "greetings", "/root/greetings"),
        ],
    )
    stop_hook = StopEnvHook(
        name="download_artifact",
        download=[
            Dir("/root/dump", root / "dump", overwrite=True, ),
        ],
    )
    config.register_hook(start_hook, stop_hook)
    for name, result in work_on_artifacts():
        assert (root / "dump").is_dir() is True
    shutil.rmtree(root / "dump")
```