override define help_targets_message
${HIGHLIGHT}Help for the Social Cultural Alignment targets:${_END_BOLD}${_END}

${CODE}make sociocultural-all${_END}         # Make the next two targets.
${CODE}make sociocultural-tests${_END}       # Run the unit tests.
${CODE}make sociocultural-iw-verify${_END}   # Run example verifications of the Inglehart-Welzel projection against ground truth.

${NOTE_LABEL}The following targets defined in this contribution's ${CODE}.targets.mk${_END}
${NOTE_LABEL}file require more setup, because they use inference, so they aren't invoked by
${NOTE_LABEL}${CODE}make sociocultural-all${_END}. See the ${CODE}README${_END} for details.

${CODE}make sociocultural-iw-score${_END}    # Run the scoring of the Inglehart-Welzel responses.
${CODE}make sociocultural-iw-plot${_END}     # Generate the Inglehart-Welzel cultural map plots.

endef

# Skip linters - this contrib's code style differs from top-level
ruff-command pylint-command type-check-command:
	@echo "${skip-command-target-message}"
	@true

