[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

<h3 align="center">cleantest</h3>

<p align="center">
A testing framework for developers who need clean environments in a hurry
<br>
<a href="https://nuccitheboss.github.io/cleantest/"><strong>Explore cleantest docs »</strong></a>
</p>

## About

cleantest is a testing framework for quickly bringing up testing environments using the test authors hypervisor of choice. It was created out of NucciTheBoss's desire to efficiently test snap packages, Python code, and Juju charms without needing to make potentially system breaking modifications to the underlying host operating system.

Below is an outline of currently supported operating systems, Python versions, and hypervisors:

|||
| :--- | :---: |
| Supported operating systems | ![Linux - yes](https://img.shields.io/badge/Linux-yes-green) ![Windows - not tested](https://img.shields.io/badge/Windows-not%20tested-red) ![Mac - not tested](https://img.shields.io/badge/Mac-not%20tested-red) |
| Supported python versions | ![Python 3.8, 3.9, and 3.10](https://img.shields.io/pypi/pyversions/cleantest) ![Wheel - yes](https://img.shields.io/pypi/wheel/cleantest)|
| Supported hypervisors | ![LXD - yes](https://img.shields.io/badge/LXD-yes-green) |

## Getting started

### Installing cleantest

The recommended way to install cleantest is by downloading the published package on PyPI:

```commandline
pip install cleantest
```

For those who wish to use the latest, bleeding-edge, and potentially *unstable* version cleantest of cleantest, the
following command can be used to install cleantest from the main branch of this repository:

```commandline
git clone https://github.com/NucciTheBoss/cleantest.git
cd cleantest
python3 -m pip install .
```

### Configuring a test environment provider

Before you can start using cleantest to run tests, you need to set up a test environment provider. Currently, the only 
supported environment provider is [LXD](https://ubuntu.com/lxd). You can set LXD up on your system using the following 
commands:

```commandline
sudo snap install lxd
lxd init --auto
```

### Run your first test

You can use any testing framework of your choice with cleantest, but this example will use 
[pytest](https://docs.pytest.org/en/7.2.x/):

```
pip install pytest
```

Here is a test written using cleantest that you can download:

<details>
  <summary> :clipboard: <code>test.py</code> </summary>

```python
#!/usr/bin/env python3

"""A basic test"""

from cleantest.provider import lxd


@lxd(preserve=False)
def do_something():
    import sys

    try:
        import urllib
        sys.exit(0)
    except ImportError:
        sys.exit(1)


class TestSuite:
    def test_do_something(self) -> None:
        for name, result in do_something():
            assert result.exit_code == 0
```
</details>

With the test file downloaded, run the test using pytest:

```commandline
pytest test.py
```

### Where to next?

Please the see the [documentation](https://nuccitheboss.github.io/cleantest/) for more information on all that you can 
do with cleantest.

## Contributing

Please read through the [contributing guidelines](https://github.com/NucciTheBoss/cleantest/blob/main/CONTRIBUTING.md) 
if you are interested in contributing to cleantest. Included are guidelines for opening issues, code formatting 
standards, and how to submit contributions to cleantest.

## License

Code and documentation copyright &copy; 2023 Jason C. Nucciarone. Please see the 
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0.html) license for more details.

## Roadmap

Here are my (NucciTheBoss's) goals to get cleantest to release version 1.0.0:

> We are sort of the way there on fully support multiple Linux distributions.
> The big hang-up now is just ensuring that the current macros and utilities are
> compatible with the new distributions and writing integration tests to ensure that
> the distributions actually work with cleantest.
> 
> __Note:__ cleantest can boot these new distributions but support might be slightly flaky.

* ~~Add support for injecting tests into LXD~~
* ~~Add support for multiple distros:~~
  * ~~Ubuntu~~
  * ~~Debian~~
  * ~~CentOS~~
  * ~~Rocky~~
  * ~~Fedora~~
  * ~~Arch~~
* ~~Enable support for running parallel tests with LXD~~
* Better test logging capabilities
* Support for a select few popular packaging formats:
  * ~~Snap~~
  * ~~Pip~~
  * ~~Charm libraries~~
  * Debs, Rpms, Pacs, etc.
  * ~~Apptainer~~
* Robust hook mechanism -> i.e. an actual specification for hooks.
* Comprehensive documentation
