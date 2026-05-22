# PR Template: Documentation/Website Change

## Description of Changes
Provide a brief description of the documentation or website changes:

* What content was added/modified/removed?
* Why were these changes made?
* How do these changes improve the documentation/website?

## Related Issues
List any related issues or PRs (#number, ...):

## Preview
Provide a link to a preview of the changes (if applicable) or just say that running `make view-local` is sufficient to see them. What should the reviewer check out, specifically?

## Checklist

Confirm that the following have been completed, where applicable:

- [ ] I have read and understood the [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) guide.

For "microsite" and other documentation changes:

- [ ] I have followed the documentation style guide.
- [ ] I have included appropriate screenshots, example code, etc.
- [ ] I have verified the microsite builds successfully, i.e., `make view-local` runs without errors.
- [ ] I have checked that external links have `target="..."` specifications by running `./check-external-links.sh` and fixed any missing cases. (This tool doesn't add missing links nor does it verify the links are valid.)

For code changes:

- [ ] I have tested the code changes in my local development environment.
- [ ] I have added and/or updated tests for all code changes.
- [ ] I have followed the existing code styles and conventions.
- [ ] I have removed all API keys and other sensitive information.
- [ ] I have updated any related documentation.
