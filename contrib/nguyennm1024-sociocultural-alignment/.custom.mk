unit-tests-prerequisite::
	@cd ${SRC_DIR}; \
		if [ -d .venv ]; \
		then echo "'.venv' already exists; not running 'uv venv'."; \
		else \
			uv venv; \
			echo "running: uv pip install --requirements requirements.txt"; \
			uv pip install --requirements requirements.txt; \
		fi

# Override the default, even though we run similar commands as are used in
# ../../Makefile, because the unit-tests-default defined there runs in the
# project root directory, whereas we have to run the test commands in this
# directory, because a separate environment is setup here.
unit-tests-default:
	@cd ${SRC_DIR}; \
	echo "${INFO}Running the unit tests in ${PWD}/tests:${_END}"; \
	echo "running: source .venv/bin/activate"; \
	source .venv/bin/activate; \
	echo "running: uv run --active python -m pytest tests -q"; \
	uv run --active python -m pytest tests -q

# This definition effectively skips the, "ruff", "pylint" and "type-check"
# targets defined in the top-level Makefile.
ruff-default pylint-default type-check-default:
	@echo "${WARN} ${skip-contrib-target}${_END}"
	@true
