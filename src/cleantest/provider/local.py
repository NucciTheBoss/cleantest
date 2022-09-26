#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Local test environment provider functions and utilities."""

from typing import Callable


class local:
    def __init__(self, func: Callable) -> None:
        self.func = func

    def __call__(self) -> None:
        pass
