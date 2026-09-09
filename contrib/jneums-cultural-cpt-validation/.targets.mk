# This file is included in the top-level Makefile

CULTURAL_CPT_DIR := contrib/jneums-cultural-cpt-validation

.PHONY: cultural-cpt-all cultural-cpt-validation cultural-cpt-aggregation cultural-cpt-stats cultural-cpt-tests cultural-cpt-fetch-seed cultural-cpt-validate-corpus

cultural-cpt-all:: cultural-cpt-validation cultural-cpt-aggregation cultural-cpt-stats cultural-cpt-tests cultural-cpt-fetch-seed cultural-cpt-validate-corpus

cultural-cpt-validation::
	@echo "${INFO} Running the EXP-001 cultural-CPT validation (smoke mode)... ${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run.py

cultural-cpt-aggregation::
	@echo "${INFO} Running the cultural-CPT aggregation-survival experiment (smoke mode)... ${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run_aggregation.py

cultural-cpt-stats::
	@echo "${INFO} Running the cultural-CPT multi-seed go/no-go (smoke mode)... ${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run_stats.py

cultural-cpt-tests::
	@echo "${INFO} Running the cultural-CPT validation tests... ${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run pytest ${CULTURAL_CPT_DIR}/tests -q

# CORPUS=<path> selects the root to validate (default: the committed seed).
CORPUS ?= ${CULTURAL_CPT_DIR}/data/seed-example

cultural-cpt-fetch-seed::
	@echo "${INFO} Fetching the real EXP-001 demonstration seed corpus (needs network)... ${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/fetch_corpus.py --culture seed-example --lang en --per-domain 4

cultural-cpt-validate-corpus::
	@echo "${INFO} Validating corpus ${CORPUS} against the EXP-001 controls... ${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/fetch_corpus.py --validate ${CORPUS}
