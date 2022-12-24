# Welcome to cleantest's documentation!

`cleantest` is a testing framework for developers who need clean testing environments in a hurry.

## History

The first version of `cleantest` was authored by Jason Nucciarone when he was having trouble finding a safe way to 
test destructive code locally on his system. He needed to test some code that he wrote to install and manage 
the Slurm Workload Manager, but he did not want to install the Debian packages directly on his system, and he did not 
want to go through the environment of setting up a CI/CD pipeline on GitHub. Irked by the idea of potentially needing 
to run his IDE out of a virtual machine and test his code there, he had an idea: what if there was library that could 
grab the body of a test, bring up a container, run the test inside that container, and then report back the results as 
if it never left the current process?

With his idea in mind, he set out to scratch his itch, and eventually decided to name the collection of Python 
decorators he created `cleantest`. Over time, and after lots of feedback from colleagues and friends, `cleantest` is 
now the library you see before you.

## What is cleantest?

The sales pitch for `cleantest` is _a testing framework for developers who need clean testing environments in a hurry_,
but is more than just that. It aims to be an easy way to test code, whether you are on your laptop or an
exa-scale high-performance computing cluster. It provides tools to work with popular packaging formats, utilities 
for pushing or pulling artifacts, and ways to test code across multiple Linux distributions. It also enables you to 
simulate high-performance computing clusters to test software deployments and installation scripts.

If you are interested in learning more, then head on over to [installation](./user-guide/installation.md) page of this 
documentation!