
override define help_targets_message
${HIGHLIGHT}Help for the EXP-001 cultural-CPT validation harness (contrib) targets:${_END}

${CODE}make cultural-cpt-all${_END}          # Make all the following targets.

${CODE}make cultural-cpt-validation${_END}   # Run the arms experiment, single seed (smoke mode).
${CODE}make cultural-cpt-aggregation${_END}  # Run the FedAvg aggregation-survival experiment.
${CODE}make cultural-cpt-stats${_END}        # Run the multi-seed go/no-go decision (smoke mode).
${CODE}make cultural-cpt-tests${_END}        # Run the cultural-CPT harness tests.

${CODE}make cultural-cpt-fetch-seed${_END}   # Fetch the real EXP-001 demonstration seed corpus (needs network).
${CODE}make cultural-cpt-validate-corpus${_END}
                               # Validate the corpus against the EXP-001 controls.

endef

# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-default type-check-default:
	@echo "${skip-contrib-target}"
	@true
