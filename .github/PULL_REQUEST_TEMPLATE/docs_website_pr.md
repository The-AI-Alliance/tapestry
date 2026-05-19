# PR Template: Documentation Change

## Description of Changes
Provide a brief description of the documentation changes (`tech-docs/` directory), including website changes to the GitHub Pages website (`docs/` directory):

* What content was added/modified/removed?
* Why were these changes made?
* How do these changes improve the documentation?

## Related Issues
List any related issues or PRs (#number, ...): 

## Preview
Provide a link to a preview of the changes, if they are hard to understand when looking at the "raw" files. 

## Checklist

Confirm that the following have been completed, where applicable:

- [ ] I have read and understood the [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) guide.

For documentation changes:

- [ ] I have followed the documentation style guide.
- [ ] I have included appropriate screenshots, example code, etc.

For changes to the GitHub Pages website in the `docs/` directory:

- [ ] I have verified the website builds successfully, i.e., `make view-local` runs without errors.
- [ ] I have checked that external links have `target="..."` specifications by running `./check-external-links.sh` and fixed any missing cases. (This tool doesn't add missing links nor does it verify the links are valid.)

For code changes:

- [ ] I have tested the code changes in my local development environment.
- [ ] I have added and/or updated tests for all code changes.
- [ ] I have followed the existing code styles and conventions.
- [ ] I have removed all API keys and other sensitive information.
- [ ] I have updated any related documentation.
