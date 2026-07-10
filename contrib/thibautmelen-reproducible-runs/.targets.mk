# This file is included in the top-level Makefile

.PHONY: reproducible-runs-check reproducible-runs-demo

REPRODUCIBLE_RUNS_DIR := contrib/thibautmelen-reproducible-runs

override define help_targets_message
For the reproducible-runs contribution (requires the `nika` binary):

make reproducible-runs-check
                        # Static audit of the workflows (plan, tools, types, permits).
make reproducible-runs-demo
                        # Run the consortium demo as a permission-bound workflow; writes a JSON receipt.
endef

reproducible-runs-check::
	@echo "${INFO}Static audit of the reproducible-runs workflows...${_END}"
	nika check ${REPRODUCIBLE_RUNS_DIR}/workflows/consortium-demo-receipt.nika.yaml

reproducible-runs-demo::
	@echo "${INFO}Running the consortium demo as a permission-bound workflow...${_END}"
	nika run ${REPRODUCIBLE_RUNS_DIR}/workflows/consortium-demo-receipt.nika.yaml
