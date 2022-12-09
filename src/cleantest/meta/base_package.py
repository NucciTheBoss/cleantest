#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Metaclass for objects that handle installing packages inside test environments."""

from abc import ABC, abstractmethod

from .injectable import Injectable


class BasePackageError(Exception):
    ...


class BasePackage(ABC, Injectable):
    """Metaclass for package handlers.

    Packages define tooling stubs needed to install packages inside test environments.
    """

    @abstractmethod
    def _run(self) -> None:
        """Run installer for package."""
        ...

    @abstractmethod
    def _setup(self) -> None:
        """Perform setup needed inside test environment to run installer."""
        ...
