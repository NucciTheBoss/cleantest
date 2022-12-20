#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Test that cleantest can successfully upload and download files."""

import os
import pathlib
import tempfile

from cleantest import Configure
from cleantest.hooks import StartEnvHook, StopEnvHook
from cleantest.hooks.data import Dir, File
from cleantest.provider import lxd

root = os.path.dirname(os.path.realpath(__file__))
config = Configure()
start_hook = StartEnvHook(
    name="upload_artifact",
    upload=[
        File(os.path.join(root, "greeting.txt"), "/root/greeting.txt"),
        Dir(os.path.join(root, "greetings"), "/root/greetings"),
    ],
)
stop_hook = StopEnvHook(
    name="download_artifact",
    download=[
        File("/root/dump.txt", os.path.join(tempfile.gettempdir(), "dump.txt")),
        Dir("/root/dump", os.path.join(tempfile.gettempdir(), "dump")),
    ],
)
config.register_hook(start_hook)
config.register_hook(stop_hook)


@lxd(image="jammy-amd64", preserve=True)
def work_on_artifacts():
    import os
    import pathlib
    import sys

    print(pathlib.Path("/root/greeting.txt").is_file(), file=sys.stdout)
    print(pathlib.Path("/root/dump").is_dir(), file=sys.stdout)

    pathlib.Path("/root/dump.txt").write_text("Dumped like a sack of rocks")
    os.mkdir("/root/dump")
    pathlib.Path("/root/dump/dump_1.txt").write_text("Oh I have been dumped again!")


class TestUploadDownload:
    def test_upload_download(self) -> None:
        work_on_artifacts()
        assert pathlib.Path(tempfile.gettempdir()).joinpath("dump.txt").is_file() is True
        assert pathlib.Path(tempfile.gettempdir()).joinpath("dump").is_dir() is True
