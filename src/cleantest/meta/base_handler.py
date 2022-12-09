#!/usr/bin/env python3
# Copyright 2022 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Metaclass for objects that will serve as handlers for test environments."""

import re
import textwrap
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Any, Dict, List


class BaseHandlerError(Exception):
    ...


Result = namedtuple("Result", ["exit_code", "stdout", "stderr"])


class BaseEntrypoint(ABC):
    """Metaclass for test environment provider entrypoints.

    Entrypoints define the tooling stubs needed to start running tests.
    """

    @abstractmethod
    def run(self) -> Dict[str, Result]:
        ...


class BaseHandler(ABC):
    """Abstract super-class for test environment handlers.

    Handlers define the tooling stubs needed to run tests inside the test environment.
    """

    @abstractmethod
    def _exists(self) -> None:
        """Check if test environment already exists."""
        ...

    @abstractmethod
    def _build(self) -> None:
        """Build test environments."""
        ...

    @abstractmethod
    def _init(self) -> None:
        """Inject cleantest and dependencies into test environments."""
        ...

    @abstractmethod
    def _execute(self) -> Any:
        """Execute testlet inside container."""
        ...

    @abstractmethod
    def _process(self) -> Result:
        """Process result from testlet."""
        ...

    @abstractmethod
    def _teardown(self) -> None:
        """Destroy test environments if not told to preserve."""
        ...

    @abstractmethod
    def _handle_start_env_hooks(self) -> None:
        """Handle StartEnv hooks."""
        ...

    @abstractmethod
    def _handle_stop_env_hooks(self) -> None:
        """Handle StopEnv hooks."""
        ...

    def _make_testlet(self, src: str, name: str, remove: List[re.Pattern] = None) -> str:
        """Construct Python source file to be run in subroutine.

        Args:
            src (str): Source code of testlet.
            name (str): Name of testlet.
            remove (List[re.Pattern]): String patterns to remove from source code of testlet.

        Returns:
            (str): Injectable testlet.

        Future:
            This will need more advanced logic if tests accept arguments.
        """
        if remove is not None:
            for pattern in remove:
                src = re.sub(pattern, "", src)

        return textwrap.dedent(
            f"""
            #!/usr/bin/env python3
            
            {src}
            
            {name}()
            """
        ).strip("\n")
