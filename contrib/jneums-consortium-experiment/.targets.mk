# This file is included in the top-level Makefile

.PHONY: consortium-experiment-all consortium-experiment consortium-tests

CONSORTIUM_EXPERIMENT_DIR := contrib/jneums-consortium-experiment

consortium-experiment-all:: consortium-experiment consortium-tests

consortium-experiment::
	@echo "${INFO}Running the consortium-training experiment metrics...${_END}"
	PYTHONPATH="${PWD}/${SRC_DIR}:${PWD}/${CONSORTIUM_EXPERIMENT_DIR}" uv run python ${CONSORTIUM_EXPERIMENT_DIR}/run.py

consortium-tests::
	@echo "${INFO}Running the consortium-training tests...${_END}"
	PYTHONPATH=${PWD}/${SRC_DIR}:${PWD}/${CONSORTIUM_EXPERIMENT_DIR} uv run python -m pytest ${SRC_DIR}/tests/tapestry/training/consortium ${CONSORTIUM_EXPERIMENT_DIR}/tests -q
