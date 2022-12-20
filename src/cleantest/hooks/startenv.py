#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Hook run when test environment first starts."""

from typing import List

from cleantest.meta import Injectable


class StartEnvHook:
    def __init__(
        self,
        name: str = "default",
        packages: List[Injectable] = [],
        upload: List[Injectable] = [],
    ) -> None:
        """Hook run at the start of the test environment.

        Args:
            name (str): Unique name of hook.
            packages (List[object]): Packages to inject into test environment.
            upload (List[Injectable]): Artifacts to upload into test environment.
        """
        self.name = name
        self.packages = packages
        self.upload = upload
