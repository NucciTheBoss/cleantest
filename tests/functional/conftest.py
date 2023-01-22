#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Configure functional test run."""

import pytest
from cleantest.control import Configure, Env


@pytest.fixture(autouse=True, scope="function")
def clean_slate() -> None:
    """Clean up state trackers before each test function is run."""
    Configure("lxd").reset()
    Env().reset()
