# [New Contribution] YOUR TITLE

> Edit this template as appropriate. For example, if the PR doesn't contain code, it's okay to delete the content below that is specific to code contributions. Please also delete this paragraph!

## New Contribution Check List

Follow this check list for new contributions:

- [ ] I created a subdirectory named with the format `contrib/<my_github_user_name>-<feature_name>`, e.g. `contrib/h4x3r-sovereign-data-enforcement/`.
- [ ] I included a short `README.md` that describes the contribution, its motivation and status, and how to try/evaluate it.
- [ ] I added a `LICENSE`. (By default, the project uses Apache-2.0 for code, CC-BY-4.0 for docs, and CDLA-2.0 for data - discussed more below).
- [ ] (If contributing code) I put the code in a `<feature_name>` subdirectory and the unit tests in a `tests` subdirectory.
- [ ] I confirmed that the command `make before-pr` successfully completes for my contribution (more below).

For the `LICENSE`, we recommend including content like the following: 

```
This contribution follows the repository default licenses:

- Code: Apache License, Version 2.0. See [LICENSES/LICENSE.Apache-2.0](LICENSES/LICENSE.Apache-2.0).
- Documentation: Creative Commons Attribution 4.0 International. See [LICENSES/LICENSE.CC-BY-4.0](LICENSES/LICENSE.CC-BY-4.0).
- Data, if added later: CDLA Permissive 2.0. See [LICENSES/LICENSE.CDLA-2.0](LICENSES/LICENSE.CDLA-2.0).
```

Because having too many licenses can make managing the project difficult, please justify any choices that don't follow our defaults.

## Description of Contribution

Lead in plain English with **Why** (problem/gap) then **What** (approach and result). Put detailed **How** after that; when a structural overview helps, start the how with one high-level Mermaid (see `AGENTS.md` § Pull request descriptions and `docs/architecture/diagrams/README.md`).

* What problem does it solve or otherwise how does it improve Tapestry? (**Why**)
* What is the approach, and what do reviewers/users get when this lands? (**What**)

## Related Issues

Related issues or PRs (#number, ...):

## If Code Is Included

### Code Description

Provide an overview of the most important details about the code:

* Important files and directories added
* Important data structures and algorithms used
* Important third-party libraries used

### Testing Performed

For any automated tests you provide, comment on key aspects of automated and/or manual testing of executable code that was performed to validate the contribution:

* Unit tests included in a `tests` subdirectory
* Integration tests performed
* Any other relevant testing or validation (including manual testing)

### Example Usage

Include an example of how to use the new function or feature:

* Code snippet demonstrating usage
* Expected output or results

## Ensure that the Quality Checks Pass

PRs with code require the command `make before-pr` to pass. This command runs the following nested `make` command for _each_ contribution, so you should specifically ensure that it runs successfully for your contribution, where `<my_github_user_name>-<feature_name>` is your contribution's name:

```makefile
make SRC_DIR=contrib/<my_github_user_name>-<feature_name> --include-dir=contrib/<my_github_user_name>-<feature_name> format ruff pylint type-check unit-tests
```

See the details in [`contrib/README.md`](https://github.com/The-AI-Alliance/tapestry/blob/develop/contrib/README.md#the-project-wide-make-processes), which also tells you how to disable any of these checks as necessary.

## Checklist

In addition to the **New Contribution Check List** above, confirm that the following have been completed.

- [ ] I have read and understood the [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) guide.

Ignore (or delete) any of the following check list sections or items that aren't applicable, like the code-related check list items when this is a documentation-only PR:

For code contributions:

- [ ] I have tested the code contributions in my local development environment.
- [ ] I have added tests for all code contributions.
- [ ] I have followed the existing code styles and conventions.
- [ ] I have removed all API keys and other sensitive information.
- [ ] I have updated any related documentation.
- [ ] I have confirmed that the command `make before-pr` completes successfully.

For documentation contributions, including `docs`:

- [ ] I have followed the existing documentation styles and conventions.
- [ ] I have included helpful diagrams, screenshots, tables, etc.

### The Tapestry _Microsite_

The content in `website` is for the Tapestry technical _microsite_ ([the-ai-alliance.github.io/tapestry/](https://the-ai-alliance.github.io/tapestry/)). Currently it just links back to the repo's `docs` locations. Eventually, mature content will be copied or migrated from `docs` to this site for easier reading, searching, etc. **Hence, you probably don't need to propose any changes to the `website` directory.**

However, **if** you are proposing `website` changes:

- [ ] I have verified the microsite `make view-local` runs without errors and the changes render as expected.
- [ ] I have checked that external links (i.e., those going to different domains) have `target="..."` specifications by running `./check-external-links.sh` and fixing any flagged URLs. (This tool doesn't fix missing `target="..."` links itself nor does it verify that the links found are not 404s!)
