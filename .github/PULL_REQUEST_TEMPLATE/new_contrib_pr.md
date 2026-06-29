# [New Contribution] YOUR TITLE

> Edit this template as appropriate. For example, if the PR doesn't contain code, it's okay to delete the content below that is specific to code contributions. Please also delete this paragraph!

## New Contribution Check List

Follow this check list for new contributions:

- [ ] I created a subdirectory named with the format `contrib/<my_github_user_name>-<feature_name>`, e.g. `contrib/h4x3r-sovereign-data-enforcement/`.
- [ ] I included a short `README.md` that describes the contribution, its motivation and status, and how to try/evaluate it.
- [ ] I added a `LICENSE`. (By default, the project uses Apache-2.0 for code, CC-BY-4.0 for docs, and CDLA-2.0 for data - discussed more below).
- [ ] (If contributing code) I put the code in a `<feature_name>` subdirectory and the unit tests in a `tests` subdirectory.

For the `LICENSE`, we recommend including content like the following: 

```
This contribution follows the repository default licenses:

- Code: Apache License, Version 2.0. See ../../LICENSE.Apache-2.0.
- Documentation: Creative Commons Attribution 4.0 International. See ../../LICENSE.CC-BY-4.0.
- Data, if added later: CDLA Permissive 2.0. See ../../LICENSE.CDLA-2.0.
```

Because having too many licenses can make managing the project difficult, please justify any choices that don't follow our defaults.

## Description of Contribution

Please provide a brief description of the contribution in this pull request:

* What is its purpose?
* What problem does it solve or otherwise how does it improve Tapestry?

## Related Issues

Related issues or PRs (#number, ...):

## If Code Is Included

### Code Description

Provide an overview of the most important details about the code:

* Important files and directories added
* Important data structures and algorithms used
* Important third-party libraries used

### Testing Performed

Describe key aspects of automated and/or manual testing of executable code that was performed to validate the contribution:

* Unit tests included in a `tests` subdirectory
* Integration tests performed
* Any other relevant testing or validation (including manual testing)

### Example Usage

Include an example of how to use the new function or feature:

* Code snippet demonstrating usage
* Expected output or results

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

For documentation contributions, including `docs`:

- [ ] I have followed the existing documentation styles and conventions.
- [ ] I have included helpful diagrams, screenshots, tables, etc.

Currently the content in `website` is for the Tapestry technical "microsite" ([the-ai-alliance.github.io/tapestry/](https://the-ai-alliance.github.io/tapestry/)) just points back to the repo's `docs` locations. Eventually, mature content will be copied or migrated from `docs` to this site for easier reading, searching, etc. **Hence, you should ignore `website` for new contributions.**

However, **if** you are proposing `website` changes:

- [ ] I have verified the microsite `make view-local` runs without errors and the changes render as expected.
- [ ] I have checked that external links (i.e., those going to different domains) have `target="..."` specifications by running `./check-external-links.sh` and fixing any flagged URLs. (This tool doesn't add missing links itself nor does it verify that the links found are valid.)
