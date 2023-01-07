#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hook run before test environment stops."""

from typing import List

from cleantest.meta import Injectable


class StopEnvHook:
    def __init__(self, name: str = "default", download: List[Injectable] = []) -> None:
        """Hook run before stopping test environment.

        Args:
            name (str): Unique name of hook.
            download (List[Injectable]): Artifacts to download from test environment.
        """
        self.name = name
        self.download = download
