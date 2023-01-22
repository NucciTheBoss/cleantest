#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Common operations for Singletons that need to be resettable."""

from abc import ABC, abstractmethod


class Resettable(ABC):
    """Abstract mixin for Singletons that need to implement reset behavior."""

    @classmethod
    @abstractmethod
    def reset(cls) -> None:
        """Reset the current Singleton to its default state."""
