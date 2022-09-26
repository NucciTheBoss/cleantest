#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions and utilities for test environment providers."""

from __future__ import annotations

import inspect
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Callable, List

from pydantic import BaseModel


class Result(BaseModel):
    exit_code: int | None = None
    stdout: Any | None = None
    stderr: Any | None = None


class Provider(ABC):
    """Abstract super-class for all test environment providers."""

    @abstractmethod
    def _execute(self) -> Any:
        pass

    @abstractmethod
    def _process(self) -> Result:
        pass

    @abstractmethod
    def _handle_start_env_hooks(self) -> None:
        pass

    def _construct(self, func: Callable, remove: List[re.Pattern] | None) -> str:
        """Construct Python source file to be run in subroutine.

        Args:
            func (Callable): TODO
            remove (List[re.Pattern]): TODO

        Returns:
            str: TODO

        Future:
            This will need more advanced logic if tests accept arguments.
        """
        src = inspect.getsource(func)
        if remove is not None:
            for pattern in remove:
                src = re.sub(pattern, "", src)

        with tempfile.TemporaryFile(mode="w+t") as f:
            content = [
                "#!/usr/bin/env python3\n",
                f"{src}\n",
                f"{func.__name__}()\n",
            ]
            f.writelines(content)
            f.seek(0)
            scriptlet = f.read()

        return scriptlet
