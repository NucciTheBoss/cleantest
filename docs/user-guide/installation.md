# Installation

## Install cleantest

`cleantest` can be installed using __pip__:

```text
pip install cleantest
```

Before you can start writing tests using the `cleantest` framework, you also need to set up a testing environment provider.

## Set up testing environment providers

You can use the following instructions to set up a supported testing environment provider to be used with `cleantest`. Some providers need to be installed before they can be used by `cleantest`, while other providers can be used without any extra set up. Note that __you do not need to install every testing environment provider listed below__; you only need to install the providers you wish to use for testing.

### LXD

To use [LXD](https://ubuntu.com/lxd) as a test environment provider with `cleantest`, you will need to have the [__snap__](https://snapcraft.io/about) package manager and __snapd__ installed on your host system. Once you have snapd and the snap package manager on your host system, use the following command to install LXD:

```text
sudo snap install lxd
```

After LXD has finished installing on the host system, use the following command to initialize a basic LXD cluster:

```text
lxd init --auto
```

Once the LXD cluster finishes initializing, you can now use LXD as a test environment provider with `cleantest`.

### SSH

> Support for using remote environments via ssh is currently a work-in-progress.

### Local

> Support for destructive, local testing is currently a work-in-progress.
