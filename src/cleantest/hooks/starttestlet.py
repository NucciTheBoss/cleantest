#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Hook run before testlet starts but after StartEnv hook."""

from pydantic import BaseModel


class StartTestletHook(BaseModel):
    """Not implemented yet as I do not know if hooks are the move."""

    def __init__(self) -> None:
        raise NotImplementedError("Hook not implemented yet.")
