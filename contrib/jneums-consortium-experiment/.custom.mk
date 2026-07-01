
# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-default type-check-default:
	@echo "${WARN} ${skip-contrib-target}${_END}"
	@true
