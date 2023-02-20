#!/usr/bin/env python3
# Copyright 2023 Jason C. Nucciarone
# See LICENSE file for licensing details.

import pathlib

from setuptools import find_packages, setup

top_dir = pathlib.Path(__file__).parent
long_description = top_dir.joinpath("README.md").read_text()


setup(
    name="cleantest",
    version="0.4.0-rc1",
    description="Clean tests for developers in a hurry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jason C. Nucciarone",
    author_email="jason.nucciarone@canonical.com",
    license="Apache-2.0",
    url="https://github.com/NucciTheBoss/cleantest",
    python_requires=">=3.6",
    packages=find_packages(
        where="src",
        include=["cleantest*"],
    ),
    package_dir={"": "src"},
    install_requires=[
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
