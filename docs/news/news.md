[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

# Your hotspot for the latest and greatest news about the development of cleantest!

## __0.4.0-rc1 released__ -- February 18th, 2023

__What is new?__

Over the past two months, I have been hard at work adding a lot of new features for 0.4.0
in my quest to make cleantest a great testing framework. The 0.4.0-rc1 pre-release is so that
folks can start getting a feel for all the features that I have been adding. Not everything I want
to have has been added to cleantest yet, but I want to give folks something new to get their hands on
in the meantime. Here is what is new in 0.4.0-rc1:

* Added a CI/CD pipeline for linting and functional tests via GitHub Actions. No more hip firing here!
* Fixed mutability issues when running clean tests in sequence. Now singleton state can be rest between runs.
* Added a `run` utility for executing shell commands inside test environment instances.
* Added a `systemd` utility for controlling services inside test environment instances.
* Added a `apt` utility for interfacing with the apt package manager on Ubuntu/Debian-based test environment instances.
* General quality of life refactors. Removed methods that did not need to be there.
* New module structure - I tried to further refine imports from version 0.3.0.
* PRELIMINARY MULTI-DISTRIBUTION SUPPORT!!! You can know launch Rocky, AlmaLinux instances and more, but robust support
    is not fully there yet (i.e. package macros do not work yet).
* Fixed issue [#21](https://github.com/NucciTheBoss/cleantest/issues/21).
* Introduction of _Archon_ and _Harness_ classes. Archon can be used to manually direct the test environment provider
    and Harness is the new name for the legacy _Provider_ classes. _Harness_ is what wraps around testlets when
    invoking the provider decorators. _Archon_ can be used to set up more complex cloud deployments such as
    mini high-performance computing clusters.
* Enhanced documentation. There is now a News page (what you are reading currently), a reference page
    (to be completed by 0.6.0), and a community page that routes to GitHub Discussions. I also cleaned up
    the home page to make it more concise.
* An actual tutorial! I know I said I would not add them until 0.5.0, but I decided to share a sneak-peak ;)

__What still needs to be done for 0.4.0?__

I still need to do a bit of work before the final 0.4.0 release is ready. Here is what still needs to be done:

* Add a `dnf` utility for interfacing with the dnf package manager.
* Add a `pacman` utility for interfacing with the pacman package manager.
* Add a `passwd` utility for creating users and groups on test environment instances.
* Low-level refactor to improve LXD API socket interaction.
    See issue [#32](https://github.com/NucciTheBoss/cleantest/issues/32).
* Add some logging output to show cleantest's progress.
    See issue [#4](https://github.com/NucciTheBoss/cleantest/issues/4).
* Fix bug where cleantest will fail if using LXD virtual machines instead of containers.
    See issue [#12](https://github.com/NucciTheBoss/cleantest/issues/12).

__What comes after 0.4.0?__

I have big plans for cleantest 0.5.0. The focus of the 0.5.0 release will be cloud-interoperability,
test result reporting, and adding a CLI front-end to cleantest. Here is a sneak-peak of what I am
planning to do:

* Add Juju as a test environment provider.
* Add a REPL for interactively running cleantest.
* Add report generation abilities to cleantest.
* Add support for "gambols". More on that later ;)

As always, feel free to make a discussion post if you have any questions and I hope you continue to enjoy
using cleantest!

## __cleantest goes to FOSDEM'2023!__ -- February 6th, 2023

This past weekend I gave my talk __"Developing effective testing 
pipelines for HPC applications"__ in the HPC, Big Data, and Data Science devroom at FOSDEM
in Brussels. This was cleantest's first public appearance! In the talk, I showcased the
new features I have been adding to cleantest such as the _Archon_ (fancy term for director) 
class for directing test environment providers, the _Harness_ class for encapsulating
testlets, and general methods to my madness. The talk went off without a hitch except for
when I got bitten by YouTube autoplay being on.

Overall, I got a lot of great feedback about the current state of cleantest as well as
establishing connections with lots of amazing folks in the HPC industry. Hopefully I get
invited again next year! Check out the recording of my talk below if you are interested
to see what I talked about!

<p align="center">
  <iframe 
    width="620" height="375" src="https://www.youtube.com/embed/Ph3-WfaWBmE" 
    title="cleantest FOSDEM talk" frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
    allowfullscreen>
  </iframe>
</p>
