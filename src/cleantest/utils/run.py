# Copyright 2023 Jason C. Nucciarone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run commands inside test environment instances."""

import shlex
import subprocess
from typing import Any, Dict, Iterable, Optional

from cleantest.meta import Result


class CommandExecutionError(Exception):
    """Raised if run fails to execute a command."""


def run(
    *commands: str,
    env: Optional[Dict[str, Any]] = None,
    cwd: Optional[str] = None,
) -> Iterable[Result]:
    """Run a command inside a test environment instance.

    Args:
        *commands (str): Commands to execute.
        env (Optional[Dict[str, Any]]): Environment to pass to commands (Default: None).
        cwd (Optional[str]): Directory to execute commands inside (Default: None).

    Yields:
        (Iterable[Result]): Captured results of executed commands.
    """
    if len(commands) == 0:
        raise CommandExecutionError("No commands passed.")

    for command in commands:
        try:
            res = subprocess.run(
                shlex.split(command),
                env=(env if env else None),
                cwd=(cwd if cwd else None),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise CommandExecutionError(
                f"Failed to execute command {command}. Reason: {e}."
            )

        yield Result(res.returncode, res.stdout, res.stderr)
