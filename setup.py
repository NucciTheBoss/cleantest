#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from setuptools import setup, find_packages


setup(
    name="simpletest",
    version="0.1.0",
    description="Simple tests for developers in a hurry.",
    author="Jason C. Nucciarone",
    author_email="jason.nucciarone@canonical.com",
    license="Apache-2.0",
    python_requires=">=3.8",
    packages=find_packages(
        where="src",
        include=["simpletest*"],
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
        "Development Status :: 1 - Experimental",
        "Intended Audience :: System Administration",
        "License :: OSI Approved :: Apache-2.0",
        "Operating System :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
