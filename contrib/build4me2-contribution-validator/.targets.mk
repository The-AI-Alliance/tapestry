# This file is included in the top-level Makefile

.PHONY: contribution-validator-all contribution-validator-demo contribution-validator-tests

CONTRIBUTION_VALIDATOR_DIR := contrib/build4me2-contribution-validator

contribution-validator-all:: contribution-validator-demo contribution-validator-tests

contribution-validator-demo::
	@echo "${INFO} Running the contribution-validator demo... ${_END}"
	PYTHONPATH="${PWD}/${SRC_DIR}:${PWD}/${CONTRIBUTION_VALIDATOR_DIR}" uv run python ${CONTRIBUTION_VALIDATOR_DIR}/run.py

contribution-validator-tests::
	@echo "${INFO} Running the contribution-validator tests... ${_END}"
	PYTHONPATH="${PWD}/${SRC_DIR}:${PWD}/${CONTRIBUTION_VALIDATOR_DIR}" uv run python -m pytest ${CONTRIBUTION_VALIDATOR_DIR}/tests -q
