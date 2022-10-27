#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Base package class for installing packages inside remote processes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class PackageError(Exception):
    ...


class Package(ABC):
    @classmethod
    @abstractmethod
    def _load(cls) -> object:
        ...

    @abstractmethod
    def _run(self) -> None:
        ...

    @abstractmethod
    def _setup(self) -> None:
        ...

    @abstractmethod
    def _dump(self) -> Dict[str, str]:
        ...
