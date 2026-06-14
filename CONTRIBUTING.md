# Contributing to Project Tapestry

👍🎉 First off, thank you for your interest in Project Tapestry! 🎉👍

### Direct links:

* Project:
  * [Dashboard](https://github.com/orgs/The-AI-Alliance/projects/50/views/1?filterQuery=)
  * [Issues](https://github.com/The-AI-Alliance/tapestry/issues)
  * [Pull requests](https://github.com/The-AI-Alliance/tapestry/pulls)
  * [Discussions](https://github.com/The-AI-Alliance/tapestry/discussions)
  * [Main website](https://thealliance.ai/projects/tapestry)
* [More on the AI Alliance community](https://github.com/The-AI-Alliance/community)

## How to Contribute to Project Tapestry

We follow normal _GitOps_ practices. Contribute your work (code and docs) as a pull request where it will be go through the usual build and validation, review, etc. If you are new to _GitOps_ practices, see our community [Contributing Guide](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#processes-for-contributing-to-existing-projects) for an explanation.

There are two additional requirements that may be new to you:

* We use _DCO_, discussed [next](#developer-certificate-of-origin-dco).
* For new contributions, we ask that you put them in the `contrib` directory, discussed [below](#new-contributions)

### Developer Certificate of Origin (DCO)

The [Developer's Certificate of Origin 1.1][DCO] process is used by [the Linux Kernel community][Linux-DCO] and many other major open-source projects, including all AI Alliance projects. 

The DCO is your way of affirming to us that your contribution is legally yours to contribute, but it does not require you to give away ownership of the contribution - your IP remains yours and others' IP remains theirs.

We ask that all your commits include a sign-off statement in the commit message. Here is an example `Signed-off-by` line, which indicates that the submitter accepts the DCO:

```text
Signed-off-by: John Doe <john.doe@example.com>
```

Fortunately, this is easy to do automatically; just use the `-s` flag in your `git commit` commands, as in the following example:

```shell
git commit -s -m 'bug fix' ...
```

> **Tips:** 
>
> * If a commit is created that did not include the `-s` option, the original commit message can be edited by using the `git commit --amend --no-edit -s` command. Then do a "force push" to add the amended commit to a PR. See this [StackOverflow post](https://stackoverflow.com/questions/13043357/git-sign-off-previous-commits) for more information.
> * Since it is easy to forget to use the `-s` flag every time, create a git _alias_ that permanently adds the `-s` flag to all commits. For example, here is how to define and use a _global_ alias, `cs`, for this purpose:
> 
> ```shell
> git config --global alias.cs "commit -s"
> ...
> git cs -m 'bug fix' ...
> ```
> 
> The alias will be added to your `~/.gitconfig` file.

If you don't want to make this a global alias, omit `--global` and run the `git config` command in the root directory for your local copy of the `tapestry` repo. The alias will be added to the `.git/config` file.


### New Contributions

To stimulate submission and discussion of more "speculative" or "incomplete" ideas, we ask that PRs with new contributions be staged into the `contrib` directory, but otherwise follow the same practices for any code or documentation changes.

To facilitate this when you draft a PR, you will find two description templates from which to select, one of which is for new contributions, with a check list to help you do the requested steps, and a second template for updates to existing code and documentation.

In brief, for new contributions, we ask you to do the following.

1. Create a subdirectory named with the format `contrib/<your_github_user_name>-<feature_name>`, e.g. `contrib/h4x3r-sovereign-data-enforcement/`.
1. Include a short `README.md` that describes the contribution, its motivation and status, and how to try/evaluate it.
1. Add a `LICENSE`. By default, the project uses Apache-2.0 for code, CC-BY-4.0 for docs, and CDLA-2.0 for data (discussed more below).
1. If contributing code, put it in a `<feature_name>` subdirectory and the unit tests in a `tests` subdirectory.
1. Once these steps are done, open a focused PR.

For the `LICENSE`, we recommend including content like the following: 

```
This contribution follows the repository default licenses:

- Code: Apache License, Version 2.0. See ../../LICENSE.Apache-2.0.
- Documentation: Creative Commons Attribution 4.0 International. See ../../LICENSE.CC-BY-4.0.
- Data, if added later: CDLA Permissive 2.0. See ../../LICENSE.CDLA-2.0.
```

Because having too many licenses can make managing the project difficult, please justify any choices that don't follow our defaults.

## What Else to Know Before Contributing to Project Tapestry

We welcome contributions to all AI Alliance projects. However, we ask that all contributors accept certain agreements and conditions. See also the [AI Alliance governance](https://thealliance.ai/governance) for more general information about AI Alliance policies.

### The AI Alliance Code of Conduct

All projects and activities adhere to our [Code of Conduct](https://github.com/The-AI-Alliance/community/blob/main/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. If you observe unacceptable behavior, follow the instructions in the document to report it.

### AI Alliance Competition Law Guidelines

The AI Alliance and its members are committed to compliance with applicable antitrust and competition laws. See the [AI Alliance Competition Law Guidelines](https://ai-alliance.cdn.prismic.io/ai-alliance/ZnNNb5m069VX15Z1_AIAllianceCompetitionLawGuidelines.pdf) for details.

### Licenses

Unless specifically stated otherwise, all Alliance projects are
distributed under a suitable "open" license. We use the following guidelines:

| Purpose | License | Website | SPDX License Identifier |
| :------ | :------ | :------ | :---------------------- |
| Code and Model Weights | [Apache License, Version 2.0](LICENSE.Apache-2.0) | [link](http://www.apache.org/licenses/LICENSE-2.0) | [link](https://spdx.org/licenses/Apache-2.0) |
| Documentation and similar materials | [The Creative Commons License, Version 4.0 - `CC BY 4.0`](LICENSE.CC-BY-4.0) | [link](https://chooser-beta.creativecommons.org/) | [link](https://spdx.org/licenses/CC-BY-4.0.html) |
| Data | [CDLA Permissive 2.0](LICENSE.CDLA-2.0) | [link](https://cdla.dev/permissive-2-0/) | [link](https://spdx.org/licenses/CDLA-Permissive-2.0.html) |

The AI Alliance leaves open the possibility of additional terms concerning safe and responsible use for certain elements in special core projects. For example, some model weights may be open for use, except for harmful purposes. Any decision to use any such additional terms for a core project must be made by the AI Alliance Steering Committee and will be clearly identified in the core project's repository.

> **NOTE:** We discuss various open licenses for data extensively in the [Open Trusted Data Initiative](https://the-ai-alliance.github.io/open-trusted-data-initiative/), specifically [here](https://the-ai-alliance.github.io/open-trusted-data-initiative/dataset-requirements/#yaml-metadata-block) and [here](https://the-ai-alliance.github.io/open-trusted-data-initiative/catalog/#more-about-the-licenses).

[DCO]: https://developercertificate.org/
[Linux-DCO]: https://docs.kernel.org/process/submitting-patches.html#sign-your-work-the-developer-s-certificate-of-origin
