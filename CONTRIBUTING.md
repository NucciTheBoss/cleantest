[//]: # "Copyright 2023 Jason C. Nucciarone"
[//]: # "See LICENSE file for licensing details."

# Contributing to cleantest

Do you have something that you wish to contribute to cleantest? **If so, here is how you can help!**

Please take a moment to review this document so that the contribution process will be easy and effective for everyone
involved.

Following these guidelines helps you communicate that you respect the developers managing and developing cleantest. 
In return, they should reciprocate that respect while they are addressing your issue or assessing your submitted 
patches and features.

### Table of Contents

* [Using the issue tracker](#using-the-issue-tracker)
* [Issues and Labels](#issues-and-labels)
* [Bug Reports](#bug-reports)
* [Feature Requests](#feature-requests)
* [Pull Requests](#pull-requests)
* [Discussions](#discussions)
* [Code Guidelines](#code-guidelines)
* [License](#license)

## Using the issue tracker

The issue tracker is the preferred way for tracking [bug reports](#bug-reports), [feature requests](#feature-requests),
and [submitted pull requests](#pull-requests), but please follow these guidelines for the issue tracker:

* Please **do not** use the issue tracker for personal issues and/or support requests. 
The [Discussions](#discussions) page is a better place to get help for personal support requests.

* Please **do not** derail or troll issues. Keep the discussion on track and have respect for the other 
users/contributors of cleantest.

* Please **do not** post comments consisting solely of "+1", ":thumbsup:", or something similar. 
Use [GitHub's "reactions" feature](https://blog.github.com/2016-03-10-add-reactions-to-pull-requests-issues-and-comments/) 
instead.
  * The maintainers of cleantest reserve the right to delete comments that violate this rule.

* Please **do not** repost or reopen issues that have been closed. Please either 
submit a new issue or browser through previous issues.
  * The maintainers of cleantest reserve the right to delete issues that violate this rule.

## Issues and Labels

The cleantest issue tracker uses a variety of labels to help organize and identify issues. 
Here is a list of some of these labels, and how the maintainers of cleantest use them:

* `Type: Bug` - Issues reported in the cleantest source code that either produce errors or unexpected behavior.

* `Status: Confirmed` - Issues marked `Type: Bug` that have be confirmed to be reproducible on a separate system.

* `Type: Documentation` - Issues for improving or updating cleantest's documentation. 
Can also be used for pull requests.

* `Type: Refactor` - Issues that pertain to improving the existing cleantest code base.

* `Type: Idea Bank` - Issues that pertain to proposing potential improvement to cleantest.

* `Type: Enchancement` - Issues marked as an agreed upon enhancement to cleantest. Can also be used for pull requests.

* `Statues: Help wanted` - Issues where we need help from the greater cleantest community to solve.

For a complete look at cleantest's labels, see the 
[project labels page](https://github.com/NucciTheBoss/cleantest/labels).

## Bug Reports

A bug is a *demonstrable problem* that is caused by cleantest. Good bug reports make cleantest more robust, so thank 
you for taking the time to report issues in the source code!

Guidelines for reporting bugs in cleantest:

1. __Validate your testlet__ &mdash; ensure that your issue is not being caused by either a semantic or syntactic 
error in your testlet's code.

2. __Validate your hypervisor__ &mdash; ensure that your issue is not being caused by a misconfiguration in the
test environment provider that you are using with cleantest.

3. __Use the GitHub issue search__ &mdash; check if the issue you are encountering has already been reported by 
someone else.

4. __Check if the issue has already been fixed__ &mdash; try to reproduce your issue using the latest `main` 
in the cleantest repository.

5. **Isolate the problem** &mdash; the more pinpointed the issue is, the easier time the cleantest developers 
will have fixing it.

A good bug report should not leave others needing to chase you up for more information. 
Please try to be as detailed as possible in your report. What is your environment? What steps will reproduce the issue? 
What operating system are you experiencing the problem on? Have you had the same results on a different 
operating system? What would you expect to be the outcome? All these details will help the developers fix any 
potential bugs.

## Feature Requests

All feature requests should be posted to GitHub Discussions and tagged as `Type: Idea Bank`. The maintainers of
cleantest already know the features they want to incorporate into cleantest, but they are always open to 
new ideas and potential improvements. GitHub Discussions is the best place to post these types of requests 
because it allows for feedback from the entire community and does not bloat the issue tracker. Please note that not 
all feature requests will be incorporated into cleantest. Also, feature requests posted on the issue tracker 
will be tagged as `Type: Invalid` and closed. Lastly, please note that spamming the maintainers to incorporate a
feature you want into cleantest will not improve its likelihood of being implemented; it may result in you receiving
a temporary ban from the repository.

## Pull Requests

Good pull requests &mdash; patches, improvements, new features &mdash; are a huge help. These pull requests should 
remain focused in scope and should not contain unrelated commits.

__Ask first__ before embarking on any __significant__ pull request (e.g. implementing new features, refactoring code, 
incorporating a new test environment provider, etc.), otherwise you risk spending a lot of time working on something 
that cleantest's developers might not want to merge into the project! For trivial things, or things that do not require 
a lot of your time, you can go ahead and make a pull request.

Adhering to the following process is the best way to get your work
included in the project:

1. [Fork](https://help.github.com/articles/fork-a-repo/) the project, clone your fork,
   and configure the remotes:

   ```bash
   # Clone your fork of the repo into the current directory
   git clone https://github.com/<your-username>/cleantest.git
   # Navigate to the newly cloned directory
   cd cleantest
   # Assign the original repo to a remote called "upstream"
   git remote add upstream https://github.com/NucciTheBoss/cleantest.git
   ```

2. If you cloned a while ago, pull the latest changes from the upstream cleantest repository:

   ```bash
   git checkout main
   git pull upstream main
   ```

3. Create a new topic branch (off the main project development branch) to
   contain your feature, change, or fix:

   ```bash
   git checkout -b <topic-branch-name>
   ```

4. Commit your changes in logical chunks. Please adhere to these [git commit
   message guidelines](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
   or your code is unlikely be merged into the main project. Use Git's
   [interactive rebase](https://help.github.com/articles/about-git-rebase/)
   feature to tidy up your commits before making them public.

5. Locally merge (or rebase) the upstream development branch into your topic branch:

   ```bash
   git pull [--rebase] upstream main
   ```

6. Push your topic branch up to your fork:

   ```bash
   git push origin <topic-branch-name>
   ```

7. [Open a Pull Request](https://help.github.com/articles/about-pull-requests/)
    with a clear title and description against the `main` branch.

**IMPORTANT**: By submitting a patch, improvement, or new feature, you agree to allow the maintainers of cleantest to 
license your contributions under the terms of the [Apache 2.0 license](./LICENSE).

## Discussions

GitHub's discussions are a great place to connect with other users of cleantest as well as discuss potential 
features and resolve personal support questions. It is expected that the users of cleantest remain respectful of 
each other. Discussion moderators reserve the right to suspend discussions and/or delete posts that do not follow 
this rule.

## Code guidelines

### Python

The following guidelines must be adhered to if you are writing code to be merged into the main cleantest code base:

* Adhere to the Python code style guidelines outlined in [Python Enhancement Proposal 8](https://pep8.org/).

* Adhere to the Python docstring conventions outlined in 
[Python Enhancement Proposal 257](https://www.python.org/dev/peps/pep-0257/).
  * *cleantest docstrings follow the 
  [Google docstring format](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings)*.
  
* Adhere to the Python type hint guidelines outlined in 
[Python Enhancement Proposal 484](https://www.python.org/dev/peps/pep-0484/)

## License

By contributing your code to cleantest, you agree to license your contribution under the 
[Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0.html).
