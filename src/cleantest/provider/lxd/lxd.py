#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""LXD test environment provider functions and utilities."""

import functools
from typing import Callable, Iterable, List, Optional, Tuple, Union

from cleantest.control import Configure, Env
from cleantest.meta import Result
from cleantest.meta.utils import thread_count

from ._lxd_harness import LXDProviderEntrypoint


class lxd:  # noqa N801
    """LXD test environment provider.

    Args:
        name (str): Name for test environment (Default: "test").
        image (List[str]):
            LXD image to use for test environment (Default: ["ubuntu-jammy-amd64"]).
        preserve (bool): Preserve test environment after test has completed (Default: True).
        parallel (bool): Run test environment instances in parallel (Default: False).
        num_threads (int): Number of threads to use when running
            test environment instances in parallel (Default: None).
    """

    def __init__(
        self,
        name: str = "test",
        image: Union[str, List[str]] = ["ubuntu-jammy-amd64"],
        preserve: bool = True,
        parallel: bool = False,
        num_threads: Optional[int] = None,
    ) -> None:
        self._name = name
        self._image = [image] if type(image) == str else image
        self._preserve = preserve
        self._env = Env()
        self._parallel = parallel
        self._lxd_config = Configure("lxd")

        if (type(num_threads) != int or num_threads < 1) and self._parallel is True:
            self._num_threads = thread_count()
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
        parallel: bool = False,
        num_threads: Optional[int] = None,
    ) -> Callable:
        """Target specific LXD test environment instances by name.

        Args:
            *instances (str): Test environment instance name.
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
                if (type(num_threads) != int or num_threads < 1) and parallel is True:
                    _num_threads = num_threads
                elif type(num_threads) == int and parallel is True:
                    _num_threads = num_threads
                else:
                    _num_threads = None
                _ = {
                    "_target_instances": [*instances],
                    "_env": Env(),
                    "_num_threads": _num_threads,
                }
                handler = (
                    LXDProviderEntrypoint(strategy="parallel_target", func=func, **_)
                    if parallel is True
                    else LXDProviderEntrypoint(strategy="serial_target", func=func, **_)
                )
                return handler.run()

            return wrapper

        return decorator
