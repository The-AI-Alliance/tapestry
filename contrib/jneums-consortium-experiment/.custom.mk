
override define help_programs_message
For the consortium-training prototype:

make consortium-experiment
                        # Run deterministic PoC metrics for consortium-training rounds.
make consortium-tests   # Run only the consortium-training prototype tests.
endef

# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-default type-check-default:
	@echo "${WARN} ${skip-contrib-target}${_END}"
	@true
