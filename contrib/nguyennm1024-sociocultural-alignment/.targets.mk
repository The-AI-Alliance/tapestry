# This file is included in the top-level Makefile

SOCIOCULTURAL_DIR := contrib/nguyennm1024-sociocultural-alignment
TAPESTRY_IW_DIR   ?= ${SOCIOCULTURAL_DIR}/evaluation/iw
TAPESTRY_ANS_DIR  ?= ${SOCIOCULTURAL_DIR}/results/iw/answers
TAPESTRY_FIG_DIR  ?= ${SOCIOCULTURAL_DIR}/results/iw/figures
TAPESTRY_MMLU_DIR ?= ${SOCIOCULTURAL_DIR}/results/mmlu

.PHONY: sociocultural-all sociocultural-tests sociocultural-iw-verify sociocultural-iw-score sociocultural-iw-plot

sociocultural-all:: sociocultural-tests sociocultural-iw-verify

sociocultural-tests::
	@echo "${INFO} Running sociocultural-alignment tests... ${_END}"
	PYTHONPATH="${PWD}/${SOCIOCULTURAL_DIR}:${PWD}/${TAPESTRY_IW_DIR}" \
		uv run python -m pytest ${SOCIOCULTURAL_DIR}/tests -q

sociocultural-iw-verify::
	@echo "${INFO} Verifying Inglehart-Welzel projection against ground truth... ${_END}"
	TAPESTRY_IW_DIR="${PWD}/${TAPESTRY_IW_DIR}" TAPESTRY_ANS_DIR="${PWD}/${TAPESTRY_ANS_DIR}" \
		uv run python ${TAPESTRY_IW_DIR}/iw_project.py

sociocultural-iw-score::
	@echo "${INFO} Scoring Inglehart-Welzel responses... ${_END}"
	TAPESTRY_IW_DIR="${PWD}/${TAPESTRY_IW_DIR}" \
		uv run python ${TAPESTRY_IW_DIR}/iw_score.py

sociocultural-iw-plot::
	@echo "${INFO} Generating Inglehart-Welzel cultural map plots... ${_END}"
	TAPESTRY_IW_DIR="${PWD}/${TAPESTRY_IW_DIR}" TAPESTRY_ANS_DIR="${PWD}/${TAPESTRY_ANS_DIR}" TAPESTRY_FIG_DIR="${PWD}/${TAPESTRY_FIG_DIR}" \
		uv run python ${TAPESTRY_IW_DIR}/plot_iw10.py
