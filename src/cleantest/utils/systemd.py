#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Utility for interacting with systemd."""

import re
import subprocess
from shutil import which
from typing import Iterable, List, Optional, Union

from cleantest.meta import Result
from cleantest.meta.utils import detect_os_variant


class SystemdError(Exception):
    """Raise when an error is encountered with systemctl."""


def _check_systemd_available() -> None:
    """Check if systemd is available on test environment instance.

    Raises:
        SystemdError: Raised if systemctl executable is not found.
    """
    if which("systemctl") is None:
        raise SystemdError(f"systemd is not available on {detect_os_variant()}")


def _systemctl(
    command: str,
    services: Optional[Union[str, List[str]]] = None,
    optargs: Optional[List[str]] = None,
) -> Result:
    """Wrap systemctl commands for unit management.

    Args:
        command (str): systemctl command to execute.
        services (Union[str, List[str]]): Names of units to operate on.
        optargs (Optional[List[str]]): Optional arguments to pass to systemctl.

    Raises:
        SystemdError: Raised if executed systemctl command fails.

    Returns:
        (Result): Captured exit code, stdout, and stderr from subprocess.
    """
    _check_systemd_available()
    services = (
        [] if services is None else [services] if services == type(str) else services
    )
    optargs = optargs if optargs is not None else []
    _cmd = ["systemctl", command, *optargs, *services]
    try:
        process = subprocess.run(
            _cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return Result(process.returncode, process.stdout, process.stderr)
    except subprocess.CalledProcessError:
        SystemdError(
            (
                f"Could not execute command {' '.join(_cmd)} on the following units: "
                ", ".join(services)
            )
        )


def is_active(*units: str) -> Iterable[bool]:
    """Check whether units are active.

    Args:
        *units (str): Units to operate on.

    Yields:
        (Iterable[bool]): Output of `systemctl is-active ...`.
            True if unit is active. False if unit is not active.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for res in (
        _systemctl("is-active", [*units], ["--quiet"]).stdout.strip("\n").split("\n")
    ):
        yield True if res == "active" else False


def start(*units: str) -> None:
    """Start (activate) one or more units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if unit fails to start.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for res in _systemctl("start", [*units]).stderr.strip("\n").split("\n"):
        if re.match(r"^Failed to start", res):
            raise SystemdError(res)


def stop(*units: str) -> None:
    """Stop (deactivate) one or more units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if unit fails to stop.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for res in _systemctl("stop", [*units]).stderr.strip("\n").split("\n"):
        if re.match(r"^Failed to stop", res):
            raise SystemdError(res)


def kill(*units: str) -> None:
    """Send kill signal to units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if systemd fails to kill unit.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for res in _systemctl("kill", [*units]).stderr.strip("\n").split("\n"):
        if re.match(r"^Failed to kill", res):
            raise SystemdError(res)


def clean(*units: str) -> None:
    """Clean runtime, cache, state, logs or configuration of units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if systemd fails to clean unit.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for res in _systemctl("clean", [*units]).stderr.strip("\n").split("\n"):
        if re.match(r"^Failed to clean", res):
            raise SystemdError(res)


def restart(*units: str) -> None:
    """Start or restart units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if unit fails to start or restart.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for res in _systemctl("restart", [*units]).stderr.strip("\n").split("\n"):
        if re.match(r"^Failed to restart", res):
            raise SystemdError(res)


def reload(*units: str, try_restart: bool = False) -> None:
    """Reload units.

    Args:
        *units (str): Units to operate on.
        try_restart (bool):
            Try `systemctl restart` if reload is not applicable for unit.

    Raises:
        SystemdError: Raised if unit fails to restart or reload.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    for unit in units:
        res = _systemctl("reload", unit).stderr.strip("\n")
        if re.match(r"^Failed to reload", res) and try_restart:
            restart(unit)
        else:
            raise SystemdError(res)


def pause(*units: str) -> None:
    """Pause units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if systemd fails to pause unit.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    _systemctl("disable", [*units], ["--now"])
    _systemctl("mask", [*units])
    for unit, status in zip([*units], is_active(*units)):
        if status:
            raise SystemdError(f"Failed to pause {unit}; it is still running.")


def resume(*units: str) -> None:
    """Resume units.

    Args:
        *units (str): Units to operate on.

    Raises:
        SystemdError: Raised if systemd fails to resume unit.
    """
    if len(units) == 0:
        raise SystemdError("No units to operate on.")
    _systemctl("unmask", [*units])
    _systemctl("enable", [*units], ["--now"])
    for unit, status in zip([*units], is_active(*units)):
        if not status:
            raise SystemdError(f"Failed to resume {unit}; it is not running.")


def daemon_reload() -> None:
    """Reload systemd configuration.

    Raises:
        SystemdError: Raised if systemd configuration fails to reload.
    """
    _systemctl("daemon-reload")
