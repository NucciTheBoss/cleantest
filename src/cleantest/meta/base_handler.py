#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Abstract class for test environment instance handlers."""

import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .result import Result


class BaseHandlerError(Exception):
    """Base error for test environment handlers."""


class BaseEntrypoint(ABC):
    """Metaclass for test environment provider entrypoints.

    Entrypoints define the tooling stubs needed to start running tests.
    """

    @abstractmethod
    def run(self) -> Dict[str, Result]:
        """Run handler for test environment."""


class BaseHandler(ABC):
    """Metaclass for test environment handlers.

    Handlers define the tooling stubs needed to run tests inside the test environment.
    """

    @abstractmethod
    def exists(self) -> bool:
        """Check if test environment already exists."""

    @abstractmethod
    def init(self) -> None:
        """Build and initialize test environment instance."""

    @abstractmethod
    def execute(self) -> Result:
        """Execute testlet inside test environment instance."""

    @abstractmethod
    def teardown(self) -> None:
        """Destroy test environments if not told to preserve."""

    @abstractmethod
    def _handle_start_env_hooks(self) -> None:
        """Handle StartEnv hooks."""

    @abstractmethod
    def _handle_stop_env_hooks(self) -> None:
        """Handle StopEnv hooks."""

    def _make_testlet(self, src: str, name: str, remove: List[Any] = None) -> str:
        """Construct Python source file to be run in subroutine.

        Args:
            src (str): Source code of testlet.
            name (str): Name of testlet.
            remove (List[Any]): String patterns to remove from source code in regex form.

        Returns:
            (str): Injectable testlet.

        Future:
            This will need more advanced logic if tests accept arguments.
        """
        if remove is not None:
            for pattern in remove:
                src = re.sub(pattern, "", src)

        with tempfile.TemporaryFile(mode="w+t") as _:
            content = [
                "#!/usr/bin/env python3\n",
                f"{src}\n",
                f"{name}()\n",
            ]
            _.writelines(content)
            _.seek(0)
            testlet = _.read()

        return testlet
