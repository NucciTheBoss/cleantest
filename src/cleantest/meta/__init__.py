#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

"""Public metaclasses used inside cleantest.

You can use these modules for developing third-party plugins.
"""

from .base_handler import BaseEntrypoint, BaseHandler, BaseHandlerError
from .base_package import BasePackage, BasePackageError
from .cleantest_info import CleantestInfo
from .injectable import Injectable
from .result import Result
