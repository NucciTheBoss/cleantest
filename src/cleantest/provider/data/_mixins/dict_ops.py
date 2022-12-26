#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Common operations needed by classes that aim to emulate dictionaries."""

from typing import Dict


class DictOps:
    """Mixin that provides dictionary methods needed by data providers."""

    def dict(self) -> Dict:
        """Return class as a unidirectional dictionary.

        Returns:
            (Dict): Class as a dictionary.
        """
        return self._filterdict(self.__dict__)

    def _filterdict(self, input_dict: Dict) -> Dict:
        """Recursively filter dictionary containing classes with __dict__ attribute.

        Args:
            input_dict (Dict): Dictionary containing classes with __dict__ attribute.

        Returns:
            (Dict): Dictionary with containing parsed __dict__ attributes.
        """
        result = {}
        for key, value in input_dict.items():
            if hasattr(value, "__dict__"):
                result.update({key: self._filterdict(value.__dict__)})
            else:
                result.update({key: value})

        return result
