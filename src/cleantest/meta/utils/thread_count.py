#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Detect thread count on host system."""

import os


def thread_count() -> int:
    """Get number of allowable threads on host system.

    Returns:
        (int): Number of allowable threads (Default: os.cpu_count())
    """
    env_var = os.getenv("CLEANTEST_NUM_THREADS")
    return env_var if env_var is not None and type(env_var) == int else os.cpu_count()
