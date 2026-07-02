include common.mk
include website.mk

define help_top_level_message
For additional help:

make help-programs      # Print help on executable tools, PoCs, etc. (including "contribs").
make help-website       # Print help for the documentation website.
endef

define help_top_level_programs_message
For the consortium-training prototype:

make consortium-demo    # Run the N+1 consortium-training proof-of-concept demo.
endef

print-info::

.PHONY: consortium-demo

consortium-demo::
	@echo "${INFO}Running the consortium-training demo...${_END}"
	uv run python examples/consortium_training_demo.py

# TODO: figure out how to move these to a make file in contrib/jneums-consortium-experiment
.PHONY: consortium-experiment consortium-tests

CONSORTIUM_EXPERIMENT_DIR := contrib/jneums-consortium-experiment

consortium-experiment::
	@echo "${INFO}Running the consortium-training experiment metrics...${_END}"
	PYTHONPATH="${PWD}/${SRC_DIR}:${PWD}/${CONSORTIUM_EXPERIMENT_DIR}" uv run python ${CONSORTIUM_EXPERIMENT_DIR}/run.py

consortium-tests::
	@echo "${INFO}Running the consortium-training tests...${_END}"
	PYTHONPATH=${PWD}/${SRC_DIR}:${PWD}/${CONSORTIUM_EXPERIMENT_DIR} uv run python -m pytest ${SRC_DIR}/tests/tapestry/training/consortium ${CONSORTIUM_EXPERIMENT_DIR}/tests -q

# TODO: figure out how to move these to make file in contrib/jneums-cultural-cpt-validation
.PHONY: cultural-cpt-validation cultural-cpt-aggregation cultural-cpt-stats cultural-cpt-tests cultural-cpt-fetch-seed cultural-cpt-validate-corpus

CULTURAL_CPT_DIR := contrib/jneums-cultural-cpt-validation

cultural-cpt-validation::
	@echo "${INFO}Running the EXP-001 cultural-CPT validation (smoke mode)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run.py

cultural-cpt-aggregation::
	@echo "${INFO}Running the cultural-CPT aggregation-survival experiment (smoke mode)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run_aggregation.py

cultural-cpt-stats::
	@echo "${INFO}Running the cultural-CPT multi-seed go/no-go (smoke mode)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run_stats.py

cultural-cpt-tests::
	@echo "${INFO}Running the cultural-CPT validation tests...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run pytest ${CULTURAL_CPT_DIR}/tests -q

# CORPUS=<path> selects the root to validate (default: the committed seed).
CORPUS ?= ${CULTURAL_CPT_DIR}/data/seed-example

cultural-cpt-fetch-seed::
	@echo "${INFO}Fetching the real EXP-001 demonstration seed corpus (needs network)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/fetch_corpus.py --culture seed-example --lang en --per-domain 4

cultural-cpt-validate-corpus::
	@echo "${INFO}Validating corpus ${CORPUS} against the EXP-001 controls...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/fetch_corpus.py --validate ${CORPUS}

