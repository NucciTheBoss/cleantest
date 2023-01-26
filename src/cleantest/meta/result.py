#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Result class for cleantest methods that return data."""

from typing import Any


class Result:
    """Result containing exit code, stdout, and stderr.

    Args:
        exit_code (int): Captured exit code.
        stdout (Any): Captured data printed to standard output.
        stderr (Any): Captured data printed to standard error.
    """

    def __init__(self, exit_code: int, stdout: Any, stderr: Any):
        self.__exit_code = exit_code
        self.__stdout = stdout
        self.__stderr = stderr

    @property
    def exit_code(self) -> int:
        """Return captured exit_code."""
        return self.__exit_code

    @property
    def stdout(self) -> Any:
        """Return captured stdout."""
        return self.__stdout

    @property
    def stderr(self) -> Any:
        """Return captured stderr."""
        return self.__stderr

    def __repr__(self) -> str:
        """String representation of Result."""
        return (
            f"{self.__class__.__name__}(exit_code={self.__exit_code}, "
            f"stdout={self.__stdout}, stderr={self.__stderr})"
        )
