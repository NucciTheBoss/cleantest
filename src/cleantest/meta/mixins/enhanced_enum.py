#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Mixin for enhancing Enum objects."""

from enum import Enum
from typing import Any, List, Tuple


class EnhancedEnum(Enum):
    """Mixin for giving enums extra methods for convenience."""

    @classmethod
    def items(cls) -> List[Tuple[str, Any]]:
        """Returns items of an Enum."""
        return [(c.name, c.value) for c in cls]
