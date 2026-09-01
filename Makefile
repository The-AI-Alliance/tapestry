define help-top-level-message
${HIGHLIGHT} For additional help: ${_END}

${CODE}make help-targets${_END}       # Print help on custom targets, e.g., demonstration commands, etc. (including "contribs").
endef

define help_top_level_targets_message

${HIGHLIGHT} Help for the consortium-training prototype targets: ${_END}

${CODE}make consortium-demo${_END}           # Run the N+1 consortium-training proof-of-concept demo.
endef

.PHONY: consortium-demo

consortium-demo::
	@echo "${INFO_LABEL}Running the consortium-training demo: ${CODE}examples/consortium_training_demo.py${_END}"
	uv run python examples/consortium_training_demo.py

# This construct uses the list of .targets.mk files in $(CONTRIB_TARGETS_MKS) and
# includes each one individually to define custom targets for the contributions.
#$(foreach prog_mk,$(CONTRIB_TARGETS_MKS),$(eval -include $(prog_mk)))
include ${CONTRIB_TARGETS_MKS}

# Finally, include all the common targets, including those not overridden above
include .common.mk
include .formal-spec.mk
include .vendored-scripts.mk
