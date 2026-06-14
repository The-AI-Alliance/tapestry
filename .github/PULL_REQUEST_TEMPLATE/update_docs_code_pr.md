# [Update] YOUR TITLE

> Edit this template as appropriate. For example, if the PR doesn't contain code, it's okay to delete the content below that is specific to code changes. Please also delete this paragraph!

## Description of the PR

Please provide a brief description of the changes in this pull request:

* What is its purpose?
* What problem does it solve or otherwise how does it improve Tapestry?

## Related Issues

Related issues or PRs (#number, ...):

## If Code Changes Are Included

### Description of Code Changes

Provide an overview of the most important details about the changes:

* Important files and directories added, modified, or removed under `src/tapestry`, `src/tests`, etc.
* Important data structures and algorithms used or changed
* Important third-party libraries used or changed

### Testing Performed

Describe key aspects of the testing performed to validate the changes:

* Unit tests added or modified
* Integration tests performed
* Any other relevant testing or validation (including manual testing)

### Example Usage

Include an example of how to use the changed function or feature:

* Code snippet demonstrating usage
* Expected output or results

## Checklist

Confirm that the following have been completed, where applicable:

- [ ] I have read and understood the [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) guide.

For code changes:

- [ ] I have tested the code changes in my local development environment.
- [ ] I have added or modified tests for all code changes.
- [ ] I have followed the existing code styles and conventions.
- [ ] I have removed all API keys and other sensitive information.
- [ ] I have updated any related documentation.

For documentation changes, including `tech-docs`:

- [ ] I have followed the existing documentation styles and conventions.
- [ ] I have included helpful diagrams, screenshots, tables, etc.

Currently the content in `docs` for the Tapestry technical "microsite" ([the-ai-alliance.github.io/tapestry/](https://the-ai-alliance.github.io/tapestry/)) just points back to the repo's `tech-docs` locations. Eventually, mature content will be copied or migrated from `tech-docs` to this site for easier reading, searching, etc. **Hence, you probably don't need to propose any changes to `docs`.**

However, **if** you are proposing `docs` changes:

- [ ] I have verified the microsite `make view-local` runs without errors and the changes render as expected.
- [ ] I have checked that external links (i.e., those going to different domains) have `target="..."` specifications by running `./check-external-links.sh` and fixing any flagged URLs. (This tool doesn't add missing links itself nor does it verify that the links found are valid.)
