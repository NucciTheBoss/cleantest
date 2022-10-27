#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from setuptools import setup, find_packages


setup(
    name="cleantest",
    version="0.2.0",
    description="Clean tests for developers in a hurry",
    author="Jason C. Nucciarone",
    author_email="jason.nucciarone@canonical.com",
    license="Apache-2.0",
    python_requires=">=3.8",
    packages=find_packages(
        where="src",
        include=["cleantest*"],
    ),
    package_dir={"": "src"},
    install_requires=[
        "pydantic",
        "pylxd",
    ],
    keywords=[
        "testing",
        "framework",
        "continuous integration",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
