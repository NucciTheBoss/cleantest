#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hook run when test environment first starts."""

from typing import List


class StartEnvHook:
    def __init__(self, name: str = "default", packages: List[object] = []):
        self.name = name
        self.packages = packages
