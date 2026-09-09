# Skip linters - this contrib's code style differs from top-level
ruff-command pylint-command type-check-command:
	@echo "${skip-command-target-message}"
	@true
