#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone, Canonical Ltd.
# See LICENSE file for licensing details.

"""Configure the flow of cleantest based on the test environment provider used."""

from ._configurers import LXDConfigurer


class UnknownConfigurerError(Exception):
    """Raised when an unknown configurer option is passed to Configure."""


def Configure(configurer: str = "lxd") -> LXDConfigurer:
    """Configure cleantest based on the test environment provider being used.

    Args:
        configurer (str): Configurer to use. Defaults to "lxd".

    Raises:
       UnknownConfigurerError: Raised if unknown configurer is specified.

    Returns:
        (LXDConfigurer): Configurer for LXD test environment provider.
    """
    dispatch = {"lxd": LXDConfigurer}
    if configurer not in dispatch.keys():
        raise UnknownConfigurerError(f"{configurer} is not a valid configurer option.")

    return dispatch[configurer]()
