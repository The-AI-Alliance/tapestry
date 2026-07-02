
override define help_programs_message
For the EXP-001 cultural-CPT validation harness (contrib):

make cultural-cpt-validation   # Run the arms experiment, single seed (smoke mode).
make cultural-cpt-aggregation  # Run the FedAvg aggregation-survival experiment.
make cultural-cpt-stats        # Run the multi-seed go/no-go decision (smoke mode).
make cultural-cpt-tests        # Run the cultural-CPT harness tests.
endef

# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-default type-check-default:
	@echo "${WARN} ${skip-contrib-target}${_END}"
	@true
