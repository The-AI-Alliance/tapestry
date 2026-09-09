
override define help_targets_message
${HIGHLIGHT}Help for the consortium-training prototype targets:${_END_BOLD}${_END}

${CODE}make consortium-experiment-all${_END} # Make all the following targets.
${CODE}make consortium-experiment${_END}     # Run deterministic PoC metrics for consortium-training rounds.
${CODE}make consortium-tests${_END}          # Run only the consortium-training prototype tests.
endef

# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-command type-check-command:
	@echo "${skip-command-target-message}"
	@true
