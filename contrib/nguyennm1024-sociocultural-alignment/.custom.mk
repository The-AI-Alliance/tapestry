tests:: local-setup

local-setup:: uv-venv install-requirements-txt-dependencies

# This definition effectively skips the, "ruff", "pylint" and "type-check"
# targets defined in the top-level Makefile.
ruff-default pylint-default type-check-default:
	@echo "${WARN} ${skip-contrib-target}${_END}"
	@true
