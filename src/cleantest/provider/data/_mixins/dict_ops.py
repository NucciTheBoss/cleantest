#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Common operations needed by classes that aim to emulate dictionaries."""

from typing import Dict


class DictOps:
    def dict(self) -> Dict:
        return self._filterdict(self.__dict__)

    def _filterdict(self, input_dict: Dict) -> Dict:
        result = {}
        for key, value in input_dict.items():
            if hasattr(value, "__dict__"):
                result.update({key: self._filterdict(value.__dict__)})
            else:
                result.update({key: value})

        return result
