# Getting started with cleantest

Now that you have the cleantest framework installed on your system, let's get you introduced to writing some basic 
tests. This example assumes that you have LXD installed and configured, and cleantest is installed correctly on 
your system. If not, please revisit the [installation](./installation.md) documentation.

Also, you will need to have [pytest](https://docs.pytest.org/en/7.1.x/) installed on your system as well. 
You can install it using the following command:

```text
pip install pytest
```

## Some background

The goal of the cleantest framework is to provide an easy way to bring up clean testing environments without a 
hassle. A "clean test" is a test written with cleantest that can drop on top of a pre-existing testing framework 
such as pytest or unittest. These "clean tests" can be broken down into three parts: 

1. Configuration statements
2. A collection of Testlets
3. One or more Test Suites

*Configuration statements* control the state and flow of cleantest, _testlets_ are the tests to be run in the testing environment, and the *test suites* define the order in which the testlets are executed.

## Defining a testlet

A *testlet* is essentially an entire Python script encapsulated in a function; it contains all the imports, 
definitions, and logic a program needs to run. Here is an example of a testlet below:

```python
from cleantest.provider import lxd


@lxd()
def do_something():
    import sys

    try:
        import urllib
        sys.exit(0)
    except ImportError:
        sys.exit(1)
``` 

An important thing to note about testlets is that they are not run in the same Python interpreter as the test suite. 
The testlets are actually picked up by the interpreter and run somewhere else, and a `Result` object is returned 
containing an exit code, stdout, and stderr. Therefore, you should always import the Python modules and assets you 
need within the body of the testlet, not in the main test files.

## Writing a test suite

To evaluate the results of a testlet, you need a *test suite*. This part should be invoked by your testing framework 
of choice. In our case, we used __pytest__:

```python
class TestSuite:
    def test_do_something(self) -> None:
        results = do_something()
        for name, result in results.items()
            assert result.exit_code == 0
```

The test suite should be focused solely on launching testlets and evaluating the results. You should never define 
testlets inside a test suite. They should always be a top-level, globally accessible function.

## Bringing it all together

To bring it all together, combine the testlet and test suite combined into a single Python file:

```python
#!/usr/bin/env python3

"""A basic test."""

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
        results = do_something()
        for name, result in results.items()
            assert result.exit_code == 0
```

Now use __pytest__ to run the test:

```text
pytest my_cleantest.py
```

You should see the following output from your test:

```test
=========== test session starts ===========
platform linux -- Python 3.10.4, pytest-7.1.3, pluggy-1.0.0
rootdir: /mnt/d/scratch
collected 1 item                                                                                                                                                                                                  

basic_test.py .                                                                                                                                                                                             [100%]


=========== 1 passed in 8.95s ===========

```

Congrats, you have written your first clean test!

## Next steps

Now that you have taken your first introductory steps with cleantest, you should now go through the rest of the
documentation and examples to learn about all the things that you can do with cleantest! Of course, learning
through trial and error also works.
