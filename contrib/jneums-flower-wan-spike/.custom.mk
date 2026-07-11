# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-default type-check-default:
	@echo "${skip-contrib-target}"
	@true