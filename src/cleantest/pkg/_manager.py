#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Manage package classes sent to test environment provider."""

import inspect


class Pkg:
    @staticmethod
    def construct() -> None:
        # TODO: Construct file that can be sent to remote process
        ...
