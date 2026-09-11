
override define help_targets_message
${HIGHLIGHT}Help for the contribution-validator targets:${_END_BOLD}${_END}

${CODE}make contribution-validator-all${_END}   # Make all the following targets.
${CODE}make contribution-validator-demo${_END}  # Run the validation demo with one corrupted node.
${CODE}make contribution-validator-tests${_END} # Run only the contribution-validator tests.
endef
