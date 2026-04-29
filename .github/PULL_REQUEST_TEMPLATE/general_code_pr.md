# PR Template: New Function or Feature

## Description of Changes
Please provide a brief description of the changes made in this pull request:

* What is the purpose of this PR?
* What new function or feature is being added?
* How does it improve the existing repository?

## Related Issues
List any related issues or PRs (#number, ...):

## Testing Performed
Describe the testing performed to validate the changes:

* Unit tests added or updated
* Integration tests performed
* Any other relevant testing or validation

## Code Changes
Provide an overview of the code changes made:

* Important new files or directories added
* Important modified files or functions
* Important deleted files or functions

## Example Usage
Include an example of how to use the new function or feature:

* Code snippet demonstrating usage
* Expected output or results

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
