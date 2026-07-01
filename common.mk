# See comment at the bottom of this file about "-include .custom.mk".

SRC_DIR      := src
CLEAN_DIRS   :=
CONTRIB_DIR  := contrib
CONTRIB_DIRS = $(patsubst %/.,%,$(wildcard ${CONTRIB_DIR}/*/.))

QUALITY_CHECKS := format ruff pylint type-check tests

# Environment variables
MAKEFLAGS     = --warn-undefined-variables
UNAME        ?= $(shell uname)
ARCHITECTURE ?= $(shell uname -m)

# Used for version tagging release artifacts.
GIT_HASH     ?= $(shell git show --pretty="%H" --abbrev-commit |head -1)
NOW          ?= $(shell date +"%Y%m%d-%H%M%S")

# Colors used to make some messages stand out more than others...
RED          := \033[31m
BOLD_RED     := \033[1;31m
GREEN        := \033[32m
BOLD_GREEN   := \033[1;32m
YELLOW       := \033[33m
BOLD_YELLOW  := \033[1;33m
BLUE         := \033[34m
BOLD_BLUE    := \033[1;34m
PURPLE       := \033[35m
BOLD_PURPLE  := \033[1;35m
CYAN         := \033[36m
BOLD_CYAN    := \033[1;36m

ERROR        := ${BOLD_RED}ERROR:
WARN         := ${BOLD_YELLOW}WARNING:
NOTE         := ${BOLD_PURPLE}NOTE:
INFO         := ${BOLD_PURPLE}
TIP          := ${BOLD_BLUE}TIP:
HIGHLIGHT    := ${BOLD_GREEN}
_END         := \033[0m


define help_message
Quick help for this make process.

make all                # Makes the 'help' and 'print-info' targets (see below).
make help               # Prints this output.
make print-info         # Print the current values of some make and env. variables.

Working with code:

make tests              # Run the test suite.
make clean              # Remove built artifacts, etc.
make format             # Format the Python code with 'black'.
make lint               # Lint the Python code by making the ruff and pylint targets.
make ruff               # Lint the Python code with 'ruff'.
make pylint             # Lint the Python code with 'pylint'.
make type-check         # Type check the Python code with 'ty'.
make type-check-watch   # Type check the Python code with 'ty' in "watch" mode,
                        # so you can fix mistakes and keep it updating.
make before-pr          # Make format, lint, type-check, and tests for "src" AND makes
                        # tests in every "contrib" directory (but not the other targets...).
                        # DO THIS BEFORE SUBMITTING A PR!

For contributed code in "contrib", any of the targets help, format, lint, ruff, pylint,
type-check, type-check-watch, and before-pr, can be invoked by prefixing the targets
name with "contrib-". This will run the corresponding target in all the contrib/* directories.

make help-programs      # Print help on executable tools, PoCs, etc. (including "contribs").
make help-website       # Print help for the documentation website.

endef

define missing_shell_command_error_message
is needed by ${PWD}/Makefile. Try 'make help' and look at the README.
endef


.PHONY: all help print-info clean
all:: help print-info

help::
	$(info ${help_message})
	@echo

help-%::
	$(info ${help_${@:help-%=%}_message})
	@echo

clean::
	rm -rf ${CLEAN_DIRS}

print-info::
	@echo "source               ${SRC_DIR}"
	@echo "tests                ${SRC_DIR}/tests"
	@echo "current dir:         ${PWD}"
	@echo "MAKEFLAGS:           ${MAKEFLAGS}"
	@echo "UNAME:               ${UNAME}"
	@echo "ARCHITECTURE:        ${ARCHITECTURE}"
	@echo "GIT_HASH:            ${GIT_HASH}"
	@echo "NOW:                 ${NOW}"

.PHONY: before-pr format format-default ruff ruff-default pylint pylint-default
.PHONY: type-check type-check-default type-check-watch type-check-watch-default
.PHONY: lint do-before-pr do-contrib-before-pr
.PHONY: tests unit-tests unit-tests-default

tests:: unit-tests
unit-tests:: unit-tests-default
unit-tests-default:
	@echo "${INFO}Running the unit tests in ${SRC_DIR}/tests:${_END}"
	@if [ ! -d "${SRC_DIR}/tests" ]; then echo "${WARN}No test directory ${SRC_DIR}/tests found!${_END}"; \
	else echo "cd ${SRC_DIR}; uv run python -m pytest tests -q"; \
		cd ${SRC_DIR}; uv run python -m pytest tests -q; \
	fi

before-pr:: do-before-pr do-contrib-before-pr
do-before-pr:: ${QUALITY_CHECKS}
do-contrib-before-pr:: ${QUALITY_CHECKS:%=contrib-%}

# Convenient short hand for the two linters.
lint:: ruff pylint

format:: format-default
format-default:
	@echo "${INFO}$@: Running 'black' on the code in ${SRC_DIR}.${_END}"
	uv run black ${SRC_DIR}

ruff:: ruff-default
ruff-default:
	@echo "${INFO}$@: Running 'ruff' to lint the code in ${SRC_DIR}.${_END}"
	uv run ruff check --fix ${SRC_DIR}

pylint:: pylint-default
pylint-default:
	@echo "${INFO}$@: Running 'pylint' on the code in ${SRC_DIR}.${_END} (configuration in pylintrc.toml)"
	uv run pylint ${SRC_DIR}

type-check:: type-check-default
type-check-default:
	@echo "${INFO}$@: Running 'ty' to type check the code in ${SRC_DIR}.${_END}"
	uv run ty check ${SRC_DIR}

type-check-watch:: type-check-watch-default
type-check-watch-default:
	@echo "${INFO}$@: Running 'ty' to type check the code in ${SRC_DIR} using 'watch' mode.${_END}"
	uv run ty check --watch ${SRC_DIR}

# Exists primarily for testing the contrib-% target pattern:
ls::
	@echo "${INFO}$@: Running ls -l in ${SRC_DIR}.${_END}"
	@ls -l ${SRC_DIR}

# Contains logic to skip any item in ${CONTRIB_DIRS} that is not a directory,
# although the construction of ${CONTRIB_DIRS} should prevent this from happening.
contrib-%::
	@for d in ${CONTRIB_DIRS}; \
	do [ -d "$$d" ] || continue; \
		echo "${MAKE} SRC_DIR=$$d --include-dir=$$d ${@:contrib-%=%}"; \
		${MAKE} SRC_DIR=$$d --include-dir=$$d ${@:contrib-%=%} || exit $$?; \
	done

.PHONY: one-time-setup clean-setup
.PHONY: command-check-uv install-uv uv-venv install-dev-dependencies install-requirements-txt-dependencies

setup one-time-setup:: install-uv uv-venv install-dev-dependencies

install-%::
	@cmd=${@:install-%=%} && command -v $$cmd > /dev/null && \
		echo "${INFO}$$cmd is already installed${_END}" || ${MAKE} help-command-$$cmd

uv-venv:: command-check-uv
	@test -d .venv && echo "'.venv' already exists; not running 'uv venv'." || uv venv
	@echo "run: 'source .venv/bin/activate' if subsequent commands fail!"

install-dev-dependencies::
	uv pip install -e ".[dev]"

# This target exists to support contributions that have a custom requirements.txt file
# that needs to be used for local setup. Otherwise, it isn't used by the main uv process.
install-requirements-txt-dependencies::
	uv pip install -f requirements.txt

command-check-uv::
	@command -v uv > /dev/null || ! ${MAKE} help-command-uv

help-command-uv help-command-uvx::
	$(info ${help-message-uv})
	@echo

define help-message-uv

The Python environment management tool "uv" is required.
See https://docs.astral.sh/uv/ for installation instructions.

If you want to uninstall uv and you used HomeBrew to install it,
use 'brew uninstall uv'. Otherwise, if you executed one of the
installation commands on the website above, find the installation
location and delete uv.

endef

define skip-contrib-target
Skipping target \"${@:%-default=%}\" in ${SRC_DIR}! Overridden in ${SRC_DIR}/.custom.mk (see target \"$@\").
endef

# Include a .custom.mk that _may or may not_ exist. The leading "-"
# means that make will ignore the error if a file isn't found. This
# idiom is used to support contrib customization of make targets,
# primarily adding additional dependencies to common targets like `tests`.
# When targets defined below, like the contrib-%, are executed, the
# argument "--include-dir $$dir" is passed to make, where "$$dir" will be
# set to the contribution's directory. So, if a particular contribution has
# a .custom.mk file, it will be found and read _for that directory only_.
# Note that because .custom.mk is loaded before anything else is defined
# (including in the top-level Makefile), if you add a dependency to a target
# it will be the _first_ dependency, so your addition will be made first.
# Similarly, if you add commands for a common target, those commands will be
# executed before the commands defined in this file.

-include .custom.mk
