#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""LXD test environment provider functions and utilities."""

import functools
import os
from typing import Callable, Iterable, List, Optional, Tuple, Union

from cleantest.control import Configure, Env
from cleantest.control.lxd import ClientConfig
from cleantest.meta import Result

from .lxd_handler import LXDProviderEntrypoint


class lxd:  # noqa N801
    """LXD test environment provider.

    Args:
        name (str): Name for test environment (Default: "test").
        image (List[str]):
            LXD image to use for test environment (Default: ["ubuntu-jammy-amd64"]).
        preserve (bool): Preserve test environment after test has completed (Default: True).
        lxd_client_config (ClientConfig): Configuration to use for LXD client (Default: None).
        parallel (bool): Run test environment instances in parallel (Default: False).
        num_threads (int): Number of threads to use when running
            test environment instances in parallel (Default: None).
    """

    def __init__(
        self,
        name: str = "test",
        image: Union[str, List[str]] = ["ubuntu-jammy-amd64"],
        lxd_client_config: Optional[ClientConfig] = None,
        preserve: bool = True,
        parallel: bool = False,
        num_threads: Optional[int] = None,
    ) -> None:
        self._name = name
        self._image = [image] if type(image) == str else image
        self._lxd_client_config = lxd_client_config
        self._preserve = preserve
        self._env = Env()
        self._parallel = parallel
        self._lxd_provider_config = Configure("lxd")

        if (type(num_threads) != int or num_threads < 1) and self._parallel is True:
            env_var = os.getenv("CLEANTEST_NUM_THREADS")
            self._num_threads = (
                env_var
                if env_var is not None and type(env_var) == int
                else os.cpu_count()
            )
        elif type(num_threads) == int and self._parallel is True:
            self._num_threads = num_threads

    def __call__(self, func: Callable) -> Callable:
        """Callable for lxd decorator."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Iterable[Tuple[str, Result]]:
            handler = (
                LXDProviderEntrypoint(strategy="parallel", func=func, **self.__dict__)
                if self._parallel is True
                else LXDProviderEntrypoint(
                    strategy="serial", func=func, **self.__dict__
                )
            )
            return handler.run()

        return wrapper

    @classmethod
    def target(
        cls,
        *instances: str,
        lxd_client_config: Optional[ClientConfig] = None,
        parallel: bool = False,
        num_threads: Optional[int] = None,
    ) -> Callable:
        """Target specific LXD test environment instances by name.

        Args:
            *instances (str): Test environment instance name.
            lxd_client_config (ClientConfig):
                Configuration to use for LXD client (Default: None).
            parallel (bool):
                Run test environment instances in parallel (Default: False).
            num_threads (int): Number of threads to use when running
                test environment instances in parallel (Default: None).

        Returns:
            (Callable): Wrapped function.
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Iterable[Tuple[str, Result]]:
                ...

            return wrapper

        return decorator
