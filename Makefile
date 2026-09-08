define help-top-level-message
${HIGHLIGHT}For additional help:${_END_BOLD}${_END}

${CODE}make help-targets${_END}       # Print help on custom targets, e.g., demonstration commands, etc. (including "contribs").
endef

define help_top_level_targets_message

${HIGHLIGHT}Help for the consortium-training prototype targets:${_END_BOLD}${_END}

${CODE}make consortium-demo${_END}           # Run the N+1 consortium-training proof-of-concept demo.
endef

.PHONY: consortium-demo

consortium-demo::
	@echo "${INFO_LABEL}Running the consortium-training demo: ${CODE}examples/consortium_training_demo.py${_END}"
	uv run python examples/consortium_training_demo.py

# Finally, include the rest of the common targets.
include .common.mk
include .formal-spec.mk
include .vendored-scripts.mk

# Include the contributions' custom targets, if any. This must come after
# .common.mk, which defines $(CONTRIB_TARGETS_MKS), the list of every
# contrib/*/.targets.mk file. (Before .common.mk is read the variable is
# empty and the include silently does nothing.)
include ${CONTRIB_TARGETS_MKS}
