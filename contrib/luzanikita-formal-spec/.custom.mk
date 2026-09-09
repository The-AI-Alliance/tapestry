# This contribution is a Quint formal specification (see README.md) — it contains
# no Python, so the top-level Python quality gates (format, ruff, pylint,
# type-check, unit-tests) do not apply. Validation is done with Quint instead:
# `SPEC_DIR=contrib/luzanikita-formal-spec make formal-spec-verify`
#
# Skip all Python quality targets so `make before-pr` passes for this contrib.
format-command ruff-command pylint-command type-check-command unit-tests-command:
	@echo "${skip-command-target-message}"
	@true
