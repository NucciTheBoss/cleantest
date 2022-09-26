#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hooks for configuring test providers and environments."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class StartEnvHook(BaseModel):
    name: str = "default"
    packages: List[str] | None = None
    requirements: str | List[str] | None = None
    constraints: str | List[str] | None = None
    python_path: List[str] | None = None


class StopEnvHook:
    """Not implemented yet as I do not know if hooks are the move."""

    def __init__(self) -> None:
        raise NotImplementedError("Hook not implemented yet.")


class StartTestletHook:
    """Not implemented yet as I do not know if hooks are the move."""

    def __init__(self) -> None:
        raise NotImplementedError("Hook not implemented yet.")


class StopTestletHook:
    """Not implemented yet as I do not know if hooks are the move."""

    def __init__(self) -> None:
        raise NotImplementedError("Hook not implemented yet.")
