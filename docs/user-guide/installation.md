# Installation

## Install cleantest

The latest stable release of `cleantest` can be installed using __pip__:

```commandline
pip install cleantest
```

You can also install the latest, bleeding-edge, and potentially _unstable_ development branch
from GitHub using the following commands:

```commandline
git clone https://github.com/NucciTheBoss/cleantest.git
cd cleantest
python3 -m pip install .
```

__Important:__ Before you can start writing tests using the `cleantest` framework, you also need to set up a 
testing environment provider.

## Setting up testing environment providers

You can use the following instructions to set up a supported test environment provider of your choice to be used with 
`cleantest`. Note that __you do not need to install every testing environment provider listed below__; you only 
need to install the providers you wish to use for testing.

???+ note "Important note about supported test environment providers"

    LXD is currently the only supported test environment provider. For the best experience, I encourage you to use LXD on
    Ubuntu. You can connect to the LXD server from other machines such as Mac, Windows, and Linux* using the LXC client. 
    How to set up the LXC client on Mac and Windows is beyond the scope of this documentation for now. I only
    currently have the means to use Ubuntu (and it is my favorite distro; sorry Arch/Fedora.) 
    
    I have plans to add more test environment provides (ssh, libvirt/kvm, vagrant, etc.) in the future, but for now I am
    focused on LXD.

### LXD

To use [LXD](https://ubuntu.com/lxd) as a test environment provider with `cleantest`, you will need to have the
[__snap__](https://snapcraft.io/about) package manager and __snapd__ installed on your host system. Once you have 
snapd and the snap package manager on your host system, use the following command to install LXD:

```text
sudo snap install lxd
```

After LXD has finished installing on the host system, use the following command to initialize a basic LXD cluster:

```text
lxd init --auto
```

Once the LXD cluster finishes initializing, you can now use LXD as a test environment provider with `cleantest`.
