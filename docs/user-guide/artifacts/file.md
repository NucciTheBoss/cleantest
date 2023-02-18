[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

# Working with files

Files can be uploaded to and downloaded from test environment instances as artifacts.

## File class

The `File` class represents a file. Its constructor accepts three arguments:

* `src (str)`: File path to load file from.
* `dest (str)`: File path for where to dump file.
* `overwrite (bool)`: Overwrite the file if it already exists at `dest`. Defaults to _False_.

???+ info "`File` versus `Dir`"

    When the `File` class's load method is invoked, an exception will be raised if src is determined to be a directory 
    and not a file. This exception is raised because cleantest handles files differently than directories when 
    dumping out to _dest_. If you are working with directories, not files, you should use the [`Dir`](./directory.md) 
    class instead.

### Supported hooks

The `File` class's behavior changes depending on the hook it is used with. Here is a list of hooks that support `File`
and how `File` behaves when accessed by them:

[`StartEnvHook`](../hooks.md#startenvhook) 

:   _src_ is loaded from local system and _dest_ is the location to dump the file
    inside the test environment instance.

[`StopEnvHook`](../hooks.md#stopenvhook)

:   _src_ is loaded from the test environment instance and _dest_ is the location to dump the file on the
    local system.

## Example usage

```python
#!/usr/bin/env python3

"""Example usage of File class."""

import os
import pathlib

from cleantest.control import Configure
from cleantest.control.hooks import StartEnvHook, StopEnvHook
from cleantest.data import File
from cleantest.provider import lxd


@lxd(image="ubuntu-jammy-amd64", preserve=False)
def work_on_artifacts():
    import pathlib
    import sys

    print(pathlib.Path("/root/greeting.txt").is_file(), file=sys.stdout)

    pathlib.Path("/root/dump.txt").write_text("Dumped like a sack of rocks")


def test_upload_download(clean_slate) -> None:
    root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    config = Configure("lxd")
    start_hook = StartEnvHook(
        name="upload_artifact",
        upload=[
            File(root / "greeting.txt", "/root/greeting.txt"),
        ],
    )
    stop_hook = StopEnvHook(
        name="download_artifact",
        download=[
            File("/root/dump.txt", root / "dump.txt", overwrite=True,),
        ],
    )
    config.register_hook(start_hook, stop_hook)
    for name, result in work_on_artifacts():
        assert (root / "dump.txt").is_file() is True
    (root / "dump.txt").unlink(missing_ok=True)
```
