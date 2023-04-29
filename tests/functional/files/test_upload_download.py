#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Test that cleantest can successfully upload and download files."""

import os
import pathlib
import shutil

from cleantest.control import Configure
from cleantest.hooks import StartEnvHook, StopEnvHook
from cleantest.data import Dir, File
from cleantest.provider import lxd


@lxd(image="ubuntu-jammy-amd64", preserve=False)
def work_on_artifacts():
    import os
    import pathlib
    import sys

    print(pathlib.Path("/root/greeting.txt").is_file(), file=sys.stdout)
    print(pathlib.Path("/root/greetings").is_dir(), file=sys.stdout)

    pathlib.Path("/root/dump.txt").write_text("Dumped like a sack of rocks")
    os.mkdir("/root/dump")
    pathlib.Path("/root/dump/dump_1.txt").write_text("Oh I have been dumped again!")


def test_upload_download(clean_slate) -> None:
    root = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    config = Configure("lxd")
    start_hook = StartEnvHook(
        name="upload_artifact",
        upload=[
            File(root / "greeting.txt", "/root/greeting.txt"),
            Dir(root / "greetings", "/root/greetings"),
        ],
    )
    stop_hook = StopEnvHook(
        name="download_artifact",
        download=[
            File(
                "/root/dump.txt",
                root / "dump.txt",
                overwrite=True,
            ),
            Dir(
                "/root/dump",
                root / "dump",
                overwrite=True,
            ),
        ],
    )
    config.register_hook(start_hook, stop_hook)
    for name, result in work_on_artifacts():
        assert (root / "dump.txt").is_file() is True
        assert (root / "dump").is_dir() is True
    (root / "dump.txt").unlink(missing_ok=True)
    shutil.rmtree(root / "dump")
