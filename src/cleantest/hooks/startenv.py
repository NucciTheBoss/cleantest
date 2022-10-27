#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hook run when test environment first starts."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class StartEnvHook(BaseModel):
    name: str = "default"
    packages: List[object] = []
