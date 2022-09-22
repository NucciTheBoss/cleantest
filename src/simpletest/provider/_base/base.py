#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstractions and utilities for test environment providers."""

import inspect
import tempfile
from typing import Callable


class Provider:
    """Super-class for all test environment providers."""

    def __construct(self, func: Callable) -> str:
        """Construct Python source file to be run in subroutine.

        Args:
            func (Callable): TODO

        Returns:
            str: TODO

        Future:
            This will need more advanced logic if tests accept arguments.
        """
        with tempfile.TemporaryFile() as f:
            content = [
                "#!/usr/bin/env python3\n",
                f"{inspect.getsource(func)}\n",
                f"{func.__name__}()",
            ]
            f.writelines(content)
            f.seek(0)
            scriptlet = f.read()

        return scriptlet
