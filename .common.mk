  # .common.mk
# See comment at the bottom of this file about "-include .custom.mk".

# Definitions of RED, GREEN, etc., and INFO, ERROR, etc. for console output.
# To see them in action, try "make show-colors".
include .console-colors.mk

SRC_DIR             ?= src
CLEAN_DIRS          :=
CONTRIB_DIR         := contrib
CONTRIB_DIRS        := $(patsubst %/.,%,$(wildcard ${CONTRIB_DIR}/*/.))
CONTRIB_TARGETS_MKS := $(foreach dir,${CONTRIB_DIRS},$(wildcard $(dir)/.targets.mk))

QUALITY_CHECKS      := format ruff pylint type-check tests
PYLINT_IGNORE_ARGS  := --ignore=.venv --ignore-pattern='.*cache.*'

PYTEST_RUN_CMD        := uv run --active coverage run -m pytest -q -v -s
PYTEST_COV_REPORT_CMD := uv run --active coverage report -m

# Environment variables
MAKEFLAGS     = --warn-undefined-variables
UNAME        ?= $(shell uname)
ARCHITECTURE ?= $(shell uname -m)

# Used for version tagging release artifacts.
GIT_HASH     ?= $(shell git show --pretty="%H" --abbrev-commit |head -1)
NOW          ?= $(shell date +"%Y%m%d-%H%M%S")

define help_message
Quick help for this make process.

${CODE}make all${_END}                # Makes the 'help' and 'print-info' targets (see below).
${CODE}make help${_END}               # Prints this output.
${CODE}make print-info${_END}         # Print the current values of some make env. variables.

Working with code:

${CODE}make one-time-setup${_END}     # "One time setup" of dependencies. Requires MacOS or Linux.
${CODE}make tests${_END}              # Run the test suite.
${CODE}make clean${_END}              # Remove built artifacts, etc.
${CODE}make format${_END}             # Format the Python code with ${CODE}black${_END}.
${CODE}make lint${_END}               # Lint the Python code by making the ${CODE}ruff${_END} and ${CODE}pylint${_END} targets.
${CODE}make ruff${_END}               # Lint the Python code with ${CODE}ruff${_END}.
${CODE}make pylint${_END}             # Lint the Python code with ${CODE}pylint${_END}.
${CODE}make type-check${_END}         # Type check the Python code with ${CODE}ty${_END}.
${CODE}make type-check-watch${_END}   # Type check the Python code with ${CODE}ty${_END} in "watch" mode,
                        # so you can fix mistakes and keep it updating.
${CODE}make before-pr${_END}          # Make ${CODE}format${_END}, ${CODE}lint${_END}, ${CODE}type-check${_END}, and ${CODE}tests${_END} for "src" AND
                        # every "contrib" directory.
                        # DO THIS BEFORE SUBMITTING A PR!

For contributed code in "contrib", any of the targets ${CODE}help${_END}, ${CODE}format${_END}, ${CODE}lint${_END}, ${CODE}ruff${_END}, ${CODE}pylint${_END},
${CODE}type-check${_END}, ${CODE}type-check-watch${_END}, and ${CODE}before-pr${_END}, can be invoked by prefixing the targets
name with ${CODE}contrib-${_END}. This will run the corresponding target in all the contrib/* directories.

${help_top_level_message}
endef


.PHONY: all help print-info clean
all:: help print-info

help::
	$(info )
	$(info ${help_message})
	$(info )
	@true

help-%::
	$(info )
	$(info ${help_${@:help-%=%}_message})
	$(info )
	@true

define help_targets_message
  ${NOTE}No custom targets defined.${_END}
endef

help-targets:: help-top-level-targets-prefix help-top-level-targets contrib-custom-program-help
	@true  # for some reason, this needs to be here to avoid some undesirable, extra output

help-top-level-targets-prefix:
	@echo "${INFO_LABEL}For the ${CODE}examples${_END}:"

help-top-level-targets:
	$(info ${help_top_level_targets_message})
	$(info )
	@true
custom-program-help:
	$(info )
	$(info ${help_targets_message})
	$(info )
	@true


clean::
	rm -rf ${CLEAN_DIRS}

print-info::
	@echo "${DARK_GREEN}MAKEFLAGS:${_END}          ${CODE}${MAKEFLAGS}${_END}"
	@echo "${DARK_GREEN}UNAME:${_END}              ${CODE}${UNAME}${_END}"
	@echo "${DARK_GREEN}ARCHITECTURE:${_END}       ${CODE}${ARCHITECTURE}${_END}"
	@echo "${DARK_GREEN}GIT_HASH:${_END}           ${CODE}${GIT_HASH}${_END}"
	@echo "${DARK_GREEN}NOW:${_END}                ${CODE}${NOW}${_END}"
	@echo
	@echo "${DARK_GREEN}Current Directory:${_END}  ${CODE}${PWD}${_END}"
	@echo "${DARK_GREEN}Sources:${_END}            ${CODE}${SRC_DIR}${_END}"
	@echo "${DARK_GREEN}Tests:${_END}              ${CODE}${SRC_DIR}/tests${_END}"
	@echo "${DARK_GREEN}Contributions:${_END}      ${CODE}${CONTRIB_DIRS}${_END}"

.PHONY: before-pr do-before-pr do-contrib-before-pr

before-pr:: do-before-pr do-contrib-before-pr
do-before-pr:: ${QUALITY_CHECKS}
do-contrib-before-pr:: ${QUALITY_CHECKS:%=contrib-%}

.PHONY: tests unit-tests unit-tests-prerequisite unit-tests-default unit-tests-postrequisite
.PHONY: format format-prerequisite format-default format-postrequisite
.PHONY: ruff ruff-prerequisite ruff-default ruff-postrequisite
.PHONY: pylint pylint-prerequisite pylint-default pylint-postrequisite
.PHONY: type-check type-check-prerequisite type-check-default type-check-postrequisite
.PHONY: type-check-watch type-check-watch-default
.PHONY: lint

tests:: unit-tests
unit-tests:: unit-tests-prerequisite unit-tests-default unit-tests-postrequisite
unit-tests-prerequisite unit-tests-postrequisite::
unit-tests-default:
	@echo "${INFO_LABEL} $@: Running the unit tests (with coverage) in ${CODE}${SRC_DIR}/tests${_END}:"
	@if [ ! -d "${SRC_DIR}/tests" ]; then echo "${WARN_LABEL} No test directory ${CODE}${SRC_DIR}/tests${_END} found!"; \
	else \
		cd ${SRC_DIR}; \
		echo "${INFO_LABEL} Running: ${CODE}${PYTEST_RUN_CMD} && ${PYTEST_COV_REPORT_CMD}${_END}"; \
		${PYTEST_RUN_CMD} && ${PYTEST_COV_REPORT_CMD}; \
	fi

# Convenient short hand for the two linters.
lint:: ruff pylint

format:: format-prerequisite format-default format-postrequisite
format-prerequisite format-postrequisite::
format-default:
	@echo "${INFO_LABEL} $@: Running ${CODE}black${_END} on the code in ${CODE}${SRC_DIR}${_END}."
	uv run black ${SRC_DIR}

ruff:: ruff-prerequisite ruff-default ruff-postrequisite
ruff-prerequisite ruff-postrequisite::
ruff-default:
	@echo "${INFO_LABEL} $@: Running ${CODE}ruff${_END} to lint the code in ${CODE}${SRC_DIR}${_END}."
	uv run ruff check --fix ${SRC_DIR}

pylint:: pylint-prerequisite pylint-default pylint-postrequisite
pylint-prerequisite pylint-postrequisite::
pylint-default:
	@echo "${INFO_LABEL} $@: Running ${CODE}pylint${_END} on the code in ${CODE}${SRC_DIR}${_END} (configuration in ${CODE}pylintrc.toml${_END})"
	uv run pylint ${PYLINT_IGNORE_ARGS} ${SRC_DIR}

type-check:: type-check-prerequisite type-check-default type-check-postrequisite
type-check-prerequisite type-check-postrequisite::
type-check-default:
	@echo "${INFO_LABEL} $@: Running ${CODE}ty${_END} to type check the code in ${CODE}${SRC_DIR}${_END}."
	uv run ty check ${SRC_DIR}

type-check-watch:: type-check-prerequisite type-check-watch-default type-check-postrequisite
type-check-watch-default:
	@echo "${INFO_LABEL} $@: Running ${CODE}ty${_END} to type check the code in ${CODE}${SRC_DIR}${_END} using 'watch' mode."
	uv run ty check --watch ${SRC_DIR}

# Provide a concrete recipe for the contrib-help target, so the "contrib-%" target pattern below 
# doesn't get used, because it does the wrong thing in this special case...
contrib-help:: 
	@${MAKE} help-targets

# The next recipe contains logic to skip any item in ${CONTRIB_DIRS} that is not a directory,
# although the construction of ${CONTRIB_DIRS} should prevent this from happening.
# Also, the output is filtered with egrep to remove unhelpful warnings from make when
# targets are redefined, which we exploit intentionally. These this target by running:
# make contrib-list  # list the contributions root directories.
# make contrib-ls    # should fail for first contribution, because there isn't an "ls" target!
#
# (Implementation note: this filtering is done on the whole for loop, not using a pipe on
# the nested make invocation. The reason is that "make ... | egrep ..." would always
# succeed if the make command fails! We tried using "set -o pipefail" to prevent this
# silent failure, but that isn't support by "/bin/sh" on Linux, which is the Bourne shell-
# compatible shell "dash".)
contrib-%::
	@for d in ${CONTRIB_DIRS}; \
	do [ -d "$$d" ] || continue; \
		echo "${INFO_LABEL}For directory ${CODE}$$d${_END}:"; \
			${MAKE} SRC_DIR=$$d --include-dir=$$d ${@:contrib-%=%} || exit $$?; \
	done 2>&1 | egrep -v -e '(overriding|ignoring old) (commands|recipe) for target' 

# These are really test targets for testing contrib-%, but they are reasonably useful,
# e.g., using "make contrib-list" to list all the contrib/* directories.
# Try "make LIST_FILTER='*.md' contrib-list", for example.
LIST_FILTER :=
.PHONY: list pwd
list:
	@cd ${SRC_DIR} && ls -al ${LIST_FILTER}
pwd:
	@cd ${SRC_DIR} && echo "Currently in directory: ${CODE}$$(pwd)${_END}"

.PHONY: one-time-setup clean-setup
.PHONY: command-check-uv install-uv uv-venv install-dev-dependencies install-requirements-txt-dependencies

setup one-time-setup:: install-uv uv-venv install-dev-dependencies

install-%::
	@cmd=${@:install-%=%} && command -v $$cmd > /dev/null && \
		echo "${INFO_LABEL}command ${CODE}$$cmd${_END} is already installed." || ${MAKE} help-command-$$cmd

uv-venv:: command-check-uv
	@test -d .venv && echo "${INFO_LABEL}directory ${CODE}.venv${_END} already exists; not running ${CODE}uv venv${_END}." || uv venv
	@echo "${INFO_LABEL}run ${CODE}source .venv/bin/activate${_END} if subsequent commands fail!"

install-dev-dependencies::
	uv pip install -e ".[dev]"

# This target exists to support contributions that have a custom requirements.txt file
# that needs to be used for local setup. Otherwise, it isn't used by the main uv process.
install-requirements-txt-dependencies::
	uv pip install --requirements requirements.txt

command-check-uv::
	@command -v uv > /dev/null || ! ${MAKE} help-command-uv

help-command-uv help-command-uvx::
	$(info ${help-message-uv})
	@echo

define help-message-uv
${NOTE_LABEL}The Python environment management tool ${CODE}uv${_END} is required.
${NOTE_LABEL}See ${CODE}https://docs.astral.sh/uv/${_END} for installation instructions.
${NOTE_LABEL}
${NOTE_LABEL}If you want to uninstall uv and you used HomeBrew to install it,
${NOTE_LABEL}use ${CODE}brew uninstall uv${_END}. Otherwise, if you executed one of the
${NOTE_LABEL}installation commands on the website above, find the installation
${NOTE_LABEL}location and delete uv.
endef

define skip-contrib-target
${WARNING_LABEL}Skipping target ${CODE}${@:%-default=%}${_END} in ${CODE}${SRC_DIR}${_END}! Support target ${CODE}$@${_END} is overridden in ${CODE}${SRC_DIR}/.custom.mk${_END}.
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
