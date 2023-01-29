#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Mixin for objects that need to emulate a dictionary."""

from typing import Any, Dict, Iterable, Tuple


class DictLike:
    """Mixin for objects that need to emulate a dictionary."""

    def dict(self) -> Dict:
        """Return class as a unidirectional dictionary.

        Returns:
            (Dict): Class as a dictionary.
        """
        return self.__process_dict(self.__dict__)

    def keys(self, all_keys: bool = False) -> Iterable[Any]:
        """Get dictionary keys.

        Args:
            all_keys (bool):
                If False, only get top-level dictionary keys.
                If True, get all keys in the multi-node dictionary.
                (Default: False).

        Returns:
            (Iterable[Any]): Iterable containing dictionary keys.
        """
        if not all_keys:
            return iter(k for k in self.__dict__.keys())
        else:
            return self.__process_keys(self.dict())

    def values(self, all_values: bool = False) -> Iterable[Any]:
        """Get dictionary values.

        Args:
            all_values (bool):
                If False, only get top-level dictionary values.
                If True, get all values in the multi-node dictionary.
                (Default: False).

        Returns:
            (Iterable[Any]): Iterable containing dictionary values.
        """
        if not all_values:
            return iter(v for v in self.__dict__.values())
        else:
            return self.__process_values(self.dict())

    def items(self, all_items: bool = False) -> Iterable[Tuple[Any, Any]]:
        """Get dictionary items.

        Args:
            all_items (bool):
                If False, only get top-level dictionary items.
                If True, get all items in the multi-node dictionary.
                (Default: False).

        Returns:
            (Iterable[Tuple[Any, Any]]): Iterable containing dictionary items.
        """
        if not all_items:
            return iter(
                (k, v) for k, v in zip(self.__dict__.keys(), self.__dict__.values())
            )
        else:
            return iter(
                (k, v) for k, v in zip(self.keys(all_items), self.values(all_items))
            )

    def __process_dict(self, input_dict: Dict[Any, Any]) -> Dict[Any, Any]:
        """Process dictionary containing object with __dict__ attribute recursively.

        Args:
            input_dict (Dict): Dictionary containing object with __dict__ attribute.

        Returns:
            (Dict): Dictionary with containing objects converted to dictionaries.
        """
        result = {}
        for key, value in input_dict.items():
            if hasattr(value, "__dict__"):
                result.update({key: self.__process_dict(value.__dict__)})
            else:
                result.update({key: value})

        return result

    def __process_keys(self, input_dict: Dict[Any, Any]) -> Iterable[Any]:
        """Get all keys in a multi-node dictionary recursively.

        Args:
            input_dict (Dict[Any, Any]):
                Dictionary to get all keys from.

        Returns:
            (Iterable[Any]): All dictionary keys.
        """
        result = []
        for k, v in input_dict.items():
            if type(v) == dict:
                result.extend(self.__process_keys(v))
            else:
                result.append(k)

        return iter(result)

    def __process_values(self, input_dict: Dict[Any, Any]) -> Iterable[Any]:
        """Get all values in a multi-node dictionary recursively.

        Args:
            input_dict (Dict[Any, Any]):
                Dictionary to get all values from.

        Returns:
            (Iterable[Any]): All dictionary values.
        """
        result = []
        for k, v in input_dict.items():
            if type(v) == dict:
                result.extend(self.__process_values(v))
            else:
                result.append(v)

        return iter(result)
