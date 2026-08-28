# .common.mk

# First, include a .custom.mk that _may or may not_ exist. The leading "-"
# means that make will ignore the error if a file isn't found.
# If this file is in a different directory, pass the option
# "--include-dir that_dir" to make, where "that_dir" is the file's
# location. This is another tool for customizing the make process,
# in addition to overrides and other definitions in the Makefile.
# One use is to add additional dependencies to standard targets defined
# in this file. This is why many targets are defined like this:
#   foo:: foo-prerequisite foo-command foo-postrequisite
#
# The "foo-command" is where the main work is done, such as running
# tests or linting code. If you need to do something before "foo-command",
# then add a dependency to "foo-prerequisite" and have it do the work
# required. Similarly, after "foo-command", use "foo-postrequisite" as a
# hook for any cleanup, etc.
#
# Similarly, you can *disable* a command by overriding the definition of
# foo-command, as discussed in a long comment below.
#
# For most projects, this sort of customization is easy enough to do in
# the main Makefile. We use the .custom.mk files in Tapestry "contrib"
# directories for customization of make targets *just in those directories*.
# When targets defined elsewhere in this file, like contrib-%, are
# executed, the argument "--include-dir $$dir" is passed to the nested
# invocation of make, where "$$dir" will be set to the contribution's
# directory. So, if a particular contribution has a .custom.mk file,
# it will be found and read _for that directory only_.

-include .custom.mk

# Definitions of RED, GREEN, etc., and INFO, ERROR, etc. for console output.
# To see them in action, try "make show-colors".
include .console-colors.mk

# Some of the following definitions may be overridden in Makefile. Some notes:
# SRC_DIR: Root of the source code. This is changed dynamically by the "contrib-%"
#   target pattern below.
# WHICH_TESTS: By default, it is ".", meaning that all tests found under the
#   current directory will be run. WHICH_TESTS can also be used on the command
#   line to specify a particular directory, test file or test to run. Specify
#   this value RELATIVE to ${SRC_DIR}! See the pytest docs for the syntax to use:
#   https://docs.pytest.org/en/stable/how-to/usage.html
SRC_DIR                  ?= src
WHICH_TESTS              ?= .
CLEAN_DIRS               ?=

CONTRIB_DIR              := contrib
CONTRIB_DIRS             := $(patsubst %/.,%,$(wildcard ${CONTRIB_DIR}/*/.))
CONTRIB_TARGETS_MKS      := $(foreach dir,${CONTRIB_DIRS},$(wildcard $(dir)/.targets.mk))

# The quality targets we run as part of "before-pr".
# GITHUB_CI is set to a non-empty string in our .github/workflows/ci.yml
# when running "make before-pr". We use that flag to change some of flags
# defined below.
GITHUB_CI                :=
QUALITY_CHECKS_NO_TESTS  := format ruff pylint type-check
QUALITY_CHECKS           := ${QUALITY_CHECKS_NO_TESTS} unit-tests

# Commands as variables:
# Time execution of commands. Prefix the command invocation with "${TIME}":
TIME                     ?= time

# Common flags for "uv run" (--active may be useful for some warnings that
# can be seen during recursive uv invocations, but using it can cause
# conflicting versions of dependencies to be installed in the top-level
# environment, if the directories for those invocations have their own
# "pyproject.toml" files. Therefore, DON'T USE THIS FLAG!):
UV_RUN                   ?= uv run

# Common flags for various tools:
# *_OPT_ARGS:  Empty by default; define on invocation to customize behavior.
# *_ARGS:      Standard arguments you shouldn't override on the command line.
#              (Pytest uses different variables; see below.)
PYLINT_OPT_ARGS          ?=
RUFF_OPT_ARGS            ?=
TY_OPT_ARGS              ?=
BLACK_OPT_ARGS           ?=

PYLINT_ARGS              := --recursive=y --ignore=.venv --ignore-pattern='.*cache.*'
TY_ARGS                  := check
# Some of the *_ARGS have different settings for CI...
ifeq (${GITHUB_CI},)
	# No CI, i.e., run manually by the developer.
	BLACK_ARGS             :=
	RUFF_ARGS              := check --fix
else
	# In CI, only have black check if reformatting would happen,
	# not do any reformatting. It exits with code 1, if it would
	# make changes, causing the PR to fail.
	# Similarly, for ruff, only check, don't attempt to fix problems.
	BLACK_ARGS             := --check
	RUFF_ARGS              := check
endif

# Pytest-specific definitions. Note we still provide the "*_OPT_ARGS" hooks.
PYTEST_RUN_OPT_ARGS      ?=
PYTEST_COV_OPT_ARGS      ?=
PYTEST_RUN_CMD           := ${UV_RUN} coverage run -m pytest -v -s ${PYTEST_RUN_OPT_ARGS}
PYTEST_COV_REPORT_CMD    := ${UV_RUN} coverage report -m ${PYTEST_COV_OPT_ARGS}


# The environment:
MAKEFLAGS                ?= --warn-undefined-variables
UNAME                    ?= $(shell uname)
ARCHITECTURE             ?= $(shell uname -m)
LOCAL_REPO_PATH          ?= $(shell git rev-parse --show-toplevel)
REPO_NAME                ?= $(notdir ${LOCAL_REPO_PATH})
# Used for version tagging release artifacts, temporary directories, etc.
GIT_HASH                 ?= $(shell git show --pretty="%H" --abbrev-commit |head -1)
TIMESTAMP                ?= $(shell date +"%Y%m%d-%H%M%S")

# Model "appendix":
# For cases where model inference is done in local environments, e.g., laptops
# using ollama or llama.cpp, we define a variable that can be used to select
# appropriate versions of models, targeted at particular hardware architectures.
# E.g., if the architecture is "arm64" (Apple Silicon), then we define a
# MODEL_APPENDIX=-mlx, which Makefiles can append to variables that specify LLMs.
# Otherwise, this variable is empty. However, the value won't be changed if the
# variable is already set in the Makefile that includes this file, _before_ this
# file was included. So, for example, you could set MODEL_APPENDIX to specify a
# quantized version of a model that way.

ifeq (${ARCHITECTURE}, arm64)
	MODEL_APPENDIX ?= -mlx
else
	MODEL_APPENDIX ?=
endif

ifndef SRC_DIR
$(error ${ERROR} There is no ${SRC_DIR} directory! ${_END})
endif

# When you see ${CODE}${_end} without anything between them, it is there
# to make it easier to line up multi-line description comments.

define help-message-general
${HIGHLIGHT} Quick help for this make process: General Targets ${_END}

${CODE}make all${_END}                # Makes the ${CODE}help${_END} and ${CODE}print-info${_END} targets.
${CODE}make help${_END}               # Prints this output.
${CODE}make print-info${_END}         # Print the current values of some make and environment variables.

${HIGHLIGHT} Working with the code: ${_END}

${CODE}make one-time-setup${_END}     # "One time setup" of ${CODE}uv${_END} dependencies (in ${CODE}.venv${_END}).
${CODE}make setup${_END}              # Alias for ${CODE}one-time-setup${_END}.
${CODE}make force-one-time-setup${_END} # "Force" the one time setup to run again, by first deleting ${CODE}.venv${_END}.
${CODE}make force-setup${_END}        # Alias for ${CODE}force-one-time-setup${_END}.

${CODE}make unit-tests${_END}         # Run the unit test suite.
${CODE}make tests${_END}              # Alias for ${CODE}unit-tests${_END}.
${CODE}make clean${_END}              # Remove built artifacts, temporary files, etc.
${CODE}make format${_END}             # Format the Python code by making the ${CODE}black${_END} target.
${CODE}make black${_END}              # Alias for ${CODE}format${_END}.
${CODE}make lint${_END}               # Lint the Python code by making the ${CODE}ruff${_END} and ${CODE}pylint${_END} targets.
${CODE}make ruff${_END}               # Lint the Python code with ${CODE}ruff${_END}.
${CODE}make ruff-watch${_END}         # Lint the Python code with ${CODE}ruff${_END} in "watch" mode, re-linting whenever files are saved.
${CODE}make pylint${_END}             # Lint the Python code with ${CODE}pylint${_END}.
${CODE}make type-check${_END}         # Type check the Python code by making the ${CODE}ty${_END} target.
${CODE}make type-check-watch${_END}   # Type check the Python code by making the ${CODE}ty-watch${_END} target.
${CODE}make ty${_END}                 # Type check the Python code with ${CODE}ty${_END}.
${CODE}make ty-watch${_END}           # Type check the Python code with ${CODE}ty${_END} in "watch" mode, re-typing whenever files are saved.

${CODE}make before-pr${_END}          # Make ${CODE}format${_END}, ${CODE}lint${_END}, ${CODE}type-check${_END}, and ${CODE}unit-tests${_END} for ${CODE}src${_END}
${CODE}${_END}                        # AND every ${CODE}contrib/*${_END} directory. Equivalent to ${CODE}before-pr-top${_END}
${CODE}${_END}                        # and ${CODE}before-pr-contrib${_END}. ${RED}DO THIS BEFORE SUBMITTING A PR!${_END}
${CODE}make before-pr-top${_END}      # Make ${CODE}format${_END}, ${CODE}lint${_END}, ${CODE}type-check${_END}, and ${CODE}unit-tests${_END} for ${CODE}src${_END} only.
${CODE}make before-pr-contrib${_END}  # Make ${CODE}format${_END}, ${CODE}lint${_END}, ${CODE}type-check${_END}, and ${CODE}unit-tests${_END} for ${CODE}contrib/*${_END}.

${CODE}make before-pr-no-tests${_END} # Everything in ${CODE}before-pr${_END} except ${CODE}unit-tests${_END}.
${CODE}make before-pr-top-no-tests${_END}
${CODE}${_END}                        # Like ${CODE}before-pr-top${_END}, but without ${CODE}unit-tests${_END}, for ${CODE}src${_END} only.
${CODE}make before-pr-contrib-no-tests${_END}
${CODE}${_END}                        # Like ${CODE}before-pr-contrib${_END}, but without ${CODE}unit-tests${_END}, for ${CODE}contrib/*${_END}.

For contributed code in "contrib", any of the targets ${CODE}help${_END}, ${CODE}format${_END}, ${CODE}lint${_END}, ${CODE}ruff${_END}, ${CODE}pylint${_END},
${CODE}type-check${_END}, and ${CODE}type-check-watch${_END} can be invoked by prefixing the targets name with
${CODE}contrib-${_END}. This will run the corresponding target in all the ${CODE}contrib/*${_END} directories.

${CODE}make contrib-audit${_END}      # Show which contributions have make customization files, etc.

${help-top-level-message}
endef

define help_targets_message
${NOTE} No custom targets defined in ${CODE}${SRC_DIR}${_END}. ${_END}
endef

define no-help-for-command-message
${WARNING_LABEL}Sorry, no built-in help is available for CLI command '${CODE}${CMD}${_END}'.
endef

.PHONY: all print-info clean
.PHONY: help help-command-not-installed do-help-command

all:: help print-info

clean::
	rm -rf ${CLEAN_DIRS}

# When you see @true commands, like here, they ensure that the recipe ends
# with a "clean" successful status and no confusing messages are printed,
# like "make: Nothing to be done for `help'".
help::
	$(info )
	$(info ${help-message-general})
	@true

# NOTE: The order of declaration is important for the help-* targets, because
# the help-*-% targets should come last.

help-command-not-installed::
	$(info ${WARNING_LABEL}Command ${CODE}${CMD}${_END} is not installed.)
	@true

help-command-%::
	@${MAKE} CMD=${@:help-command-%=%} do-help-command
do-help-command::
	$(info ${${LABEL}_LABEL}Help on ${CODE}${CMD}${_END}:)
	$(info $(if ${help-command-${CMD}-message},${help-command-${CMD}-message},${no-help-for-command-message}))
	@true

help-targets:: help-top-level-targets-prefix help-top-level-targets help-formal-spec contrib-custom-program-help
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

help-%::
	$(info )
	$(info ${${@}-message})
	$(info )
	@true

.PHONY: error
error::
	@$(info ${ERROR_LABEL}${MSG} (exit status = ${RED}${STATUS}${_END}))
	@$(info ${${MSG_VARIABLE}})
	@$(error )

define command-failed-error-message
${ERROR_LABEL}${MSG} (exit status = ${RED}${STATUS}${_END})!!
endef

define command-check-failed-message
${TIP_LABEL}Installation help may be defined in this Makefile. Try ${CODE}make help-command-${CMD}${_END}
${TIP_LABEL}or try ${CODE}make install-${CMD}${_END}. See also the project's ${CODE}README.md${_END}.
endef

# Check if a command is on the path.
command-check-%:
	@CMD=${@:command-check-%=%} && command -v $$CMD > /dev/null || \
		${MAKE} CMD=$$CMD MSG="Command ${CODE}$$CMD${_END} not found! It is required for a make target." MSG_VARIABLE=command-check-failed-message STATUS=1 error

silent-command-check-%:
	cmd=${@:silent-command-check-%=%} && echo $$cmd && command -v $$cmd > /dev/null

.PHONY: print-info-env
print-info:: print-info-env
print-info-env::
	@echo "${HIGHLIGHT} Some 'environment' settings: ${_END}"
	@echo
	@echo "  ${DARK_GREEN}MAKEFLAGS:${_END}             ${CODE}${MAKEFLAGS}${_END}"
	@echo "  ${DARK_GREEN}UNAME:${_END}                 ${CODE}${UNAME}${_END}"
	@echo "  ${DARK_GREEN}ARCHITECTURE:${_END}          ${CODE}${ARCHITECTURE}${_END}"
	@echo "  ${DARK_GREEN}MODEL_APPENDIX:${_END}        ${CODE}${MODEL_APPENDIX}${_END}"
	@echo "  ${DARK_GREEN}TIMESTAMP:${_END}             ${CODE}${TIMESTAMP}${_END}"
	@echo "  ${DARK_GREEN}REPO_NAME:${_END}             ${CODE}${REPO_NAME}${_END}"
	@echo "  ${DARK_GREEN}GIT_HASH:${_END}              ${CODE}${GIT_HASH}${_END}"
	@echo "  ${DARK_GREEN}PWD:${_END}                   ${CODE}${PWD}${_END} (current Directory)"
	@echo "  ${DARK_GREEN}SRC_DIR:${_END}               ${CODE}${SRC_DIR}${_END}"
	@echo "  ${DARK_GREEN}WHICH_TESTS:${_END}           ${CODE}${WHICH_TESTS}${_END}"
	@echo

# In what follows, note the structure used for common tasks, like running the unit tests:
#   unit-tests:: unit-tests-prerequisite unit-tests-command unit-tests-postrequisite
# The *-prerequisite and *-postrequisite are hooks that permit a .custom.mk (or a Makefile)
# to add additional dependencies or recipes to execute before or after the "core" command is
# executed by the *-command target.  The *-prerequisite and *-postrequisite all have empty
# recipes in this file. So, if you want to define them with custom behaviors, you must use
# the double-colon syntax, "::", like this:
#
# unit-tests-prerequisite:: even-more
#   @echo "Doing some unit testing setup..."
# even-more::
#   @echo "Doing even more stuff!"
#
# In contrast, the *-command targets are designed to be OVERRIDDEN. A common usage is to
# disable a task. For example, if there are no unit tests in the project, then
# unit-tests-command will fail, because of how it is defined below. (This isn't true for
# ruff, black, pylint, and ty, which silently ignore when there is no python code.)
# So, projects without python tests should have the following definition in their Makefile:
#
# unit-tests-command::
#   @echo "${skip-command-target-message}"
#   @true
#
# The "skip-command-target-message" variable is defined in .common.mk to provide a
# useful notice to the reader that the target is skipped.
#
# There is one more point to explain for how this is implemented. The _default_ way
# *-command is actually declared is as follows:
#
# %-command::
#  	@${MAKE} ${@}-default
#
# Take for example, unit-tests-command. Because the .custom.mk file (if any) is read
# before this point in .common.mk, The target pattern "%-command" is _only_ used if
# .custom.mk (and Makefile) do not define unit-tests-command themselves. When
# this happens, the recipe calls `make unit-tests-command-default` to invoke the
# "default" command for unit tests.
#
# See the bottom of this file for a note about a previous, alternative
# implementation we used for this feature.

# The default implementation of any *-command target:
%-command:
	@${MAKE} ${@}-default

.PHONY: before-pr before-pr-top before-pr-contrib print-pwd
.PHONY: before-pr-no-tests before-pr-top-no-tests before-pr-contrib-no-tests

before-pr:: before-pr-top before-pr-contrib
before-pr-top:: print-pwd ${QUALITY_CHECKS}
before-pr-contrib:: ${QUALITY_CHECKS:%=contrib-%}

before-pr-no-tests:: before-pr-top-no-tests before-pr-contrib-no-tests
before-pr-top-no-tests:: print-pwd ${QUALITY_CHECKS_NO_TESTS}
before-pr-contrib-no-tests:: ${QUALITY_CHECKS_NO_TESTS:%=contrib-%}

print-pwd::
	$(info ${INFO_LABEL}In directory: ${CODE}${PWD}${_END})
	@true

# Note that *-command-default targets are declared phony, but the dependencies for * targets
# are *: *-prerequisite *-command *-postrequisite

.PHONY: tests unit-tests unit-tests-prerequisite unit-tests-command-default unit-tests-postrequisite
.PHONY: format format-prerequisite format-command-default format-postrequisite black
.PHONY: ruff ruff-prerequisite ruff-command-default ruff-postrequisite
.PHONY: ruff-watch ruff-watch-command-default
.PHONY: pylint pylint-prerequisite pylint-command-default pylint-postrequisite
.PHONY: type-check ty type-check-prerequisite type-check-command-default type-check-postrequisite
.PHONY: type-check-watch ty-watch type-check-watch-command-default
.PHONY: lint

tests:: unit-tests
unit-tests:: unit-tests-prerequisite unit-tests-command unit-tests-postrequisite
unit-tests-prerequisite unit-tests-postrequisite::
unit-tests-command-default::
	@echo "${INFO_LABEL}Target ${CODE}unit-tests${_END}: Running the unit tests (with coverage)."
	cd ${SRC_DIR} && ${PYTEST_RUN_CMD} ${WHICH_TESTS}
	cd ${SRC_DIR} && ${PYTEST_COV_REPORT_CMD}

# Convenient short hand for the two linters.
lint:: ruff pylint

format black:: format-prerequisite format-command format-postrequisite
format-prerequisite format-postrequisite::
format-command-default::
	@echo "${INFO_LABEL}Target ${CODE}format${_END}: Running ${CODE}black${_END} on the code in ${CODE}${SRC_DIR}${_END}."
	cd ${SRC_DIR} && ${UV_RUN} black ${BLACK_ARGS} ${BLACK_OPT_ARGS} .

ruff:: ruff-prerequisite ruff-command ruff-postrequisite
ruff-prerequisite ruff-postrequisite::
ruff-command-default::
	@echo "${INFO_LABEL}Target ${CODE}ruff${_END}: Running ${CODE}ruff${_END} to lint the code in ${CODE}${SRC_DIR}${_END}."
	cd ${SRC_DIR} && ${UV_RUN} ruff ${RUFF_ARGS} ${RUFF_OPT_ARGS} .
ruff-watch:: ruff-prerequisite ruff-watch-command-default ruff-postrequisite
ruff-watch-command-default::
	@echo "${INFO_LABEL}Target ${CODE}ruff${_END}: Running ${CODE}ruff${_END} to lint the code in ${CODE}${SRC_DIR}${_END} using 'watch' mode."
	cd ${SRC_DIR} && ${UV_RUN} ruff ${RUFF_ARGS} --watch ${RUFF_OPT_ARGS} .

pylint:: pylint-prerequisite pylint-command pylint-postrequisite
pylint-prerequisite pylint-postrequisite::
pylint-command-default::
	@echo "${INFO_LABEL}Target ${CODE}pylint${_END}: Running ${CODE}pylint${_END} on the code in ${CODE}${SRC_DIR}${_END} (configuration in ${CODE}pylintrc.toml${_END})"
	cd ${SRC_DIR} && ${UV_RUN} pylint ${PYLINT_ARGS} ${PYLINT_OPT_ARGS} .

type-check:: ty
ty:: type-check-prerequisite type-check-command type-check-postrequisite
type-check-prerequisite type-check-postrequisite::
type-check-command-default::
	@echo "${INFO_LABEL}Target ${CODE}type-check${_END}: Running ${CODE}ty${_END} to type check the code in ${CODE}${SRC_DIR}${_END}."
	cd ${SRC_DIR} && ${UV_RUN} ty ${TY_ARGS} ${TY_OPT_ARGS} .

type-check-watch:: ty-watch
ty-watch:: type-check-prerequisite type-check-watch-command type-check-postrequisite
type-check-watch-command-default::
	@echo "${INFO_LABEL}Target ${CODE}type-check-watch${_END}: Running ${CODE}ty${_END} to type check the code in ${CODE}${SRC_DIR}${_END} using 'watch' mode."
	cd ${SRC_DIR} && ${UV_RUN} ty ${TY_ARGS} --watch ${TY_OPT_ARGS} .

# Provide a concrete recipe for the contrib-help target, so the "contrib-%" target pattern below 
# doesn't get used, because it does the wrong thing in this special case...
.PHONY: contrib-help
contrib-help:: 
	@${MAKE} help-targets

# Show which contributions have make customization files, .custom.mk and
# .targets.mk, etc.
.PHONY: contrib-audit
contrib-audit::
	@echo "\n${HIGHLIGHT}  Which contrib/* have the required or optional files? ${_END}"
	@printf "  %-45s  ${CODE}README.md      LICENSE      .custom.mk   .targets.mk${_END}  \n" ""
	@printf "  %-45s  ${BLUE}(required)  (recommended)  (recommended) (optional)${_END}\n" ""
	@no="${RED}NO ${_END}"; yes="${GREEN}yes${_END}"; \
	for d in ${CONTRIB_DIRS}; do \
	  readme="$$no"; license="$$no"; targets="$$no"; custom="$$no"; \
	  [ -f $$d/README.md ]   && readme="$$yes"; \
	  [ -f $$d/LICENSE ]     && license="$$yes"; \
	  [ -f $$d/.custom.mk  ] && custom="$$yes"; \
	  [ -f $$d/.targets.mk ] && targets="$$yes"; \
		printf "  ${CODE}%-45s${_END}     %-3s           %-3s            %-3s          %-3s\n" "$$d:" "$$readme" "$$license" "$$custom" "$$targets"; \
	done
	@echo

# The next recipe contains logic to skip any item in ${CONTRIB_DIRS} that is not a directory,
# although the construction of ${CONTRIB_DIRS} should prevent this from happening.
# Test this target by running:
# make contrib-list  # list the contributions root directories.
# make contrib-ls    # should fail for first contribution, because there isn't an "ls" target!
contrib-%::
	@for d in ${CONTRIB_DIRS}; \
	do [ -d "$$d" ] || continue; \
		echo "\n${HIGHLIGHT} For directory ${CODE}$$d${_END}${HIGHLIGHT}, target ${CODE}${@:contrib-%=%}${_END}${HIGHLIGHT}: ${_END}\n"; \
		${MAKE} SRC_DIR=$$d SPEC_DIR=$$d --include-dir=$$d ${@:contrib-%=%} || exit $$?; \
	done 2>&1


# The following are really test targets for testing contrib-%, but they are
# reasonably useful, e.g., using "make contrib-list" to list all the contrib/*
# directories. Try "make LIST_FILTER='*.md' contrib-list", for example.
LIST_FILTER :=
.PHONY: list pwd
list:
	@cd ${SRC_DIR} && ls -al ${LIST_FILTER}
pwd:
	@cd ${SRC_DIR} && echo "Currently in directory: ${CODE}$$(pwd)${_END}"

.PHONY: one-time-setup clean-setup uninstall-uv
.PHONY: force-setup force-one-time-setup rm-venv
.PHONY: command-check-uv uv-venv install-dev-dependencies install-requirements-txt-dependencies

setup one-time-setup:: install-uv uv-venv install-dev-dependencies
force-setup force-one-time-setup:: rm-venv contrib-rm-venv setup
rm-venv::
	rm -rf .venv
	rm -f uv.lock

install-dev-dependencies::
	uv pip install -e ".[dev]"

# This target exists to support contributions that have a custom requirements.txt file
# that needs to be used for local setup. Otherwise, it isn't used by the main uv process.
install-requirements-txt-dependencies::
	uv pip install --requirements requirements.txt

# Check if a command is installed. If not, try to provide help on installing it.
# If make is invoked by the || clause, we unset MAKEFLAGS to hack around suppressing
# a warning about a potentially-undefined variable used in the targets
# help-command-not-installed and  help-command-$$cmd.
install-%::
	@cmd=${@:install-%=%} && command -v $$cmd > /dev/null && \
		echo "${INFO_LABEL}Command ${CODE}$$cmd${_END} is already installed." || \
		${MAKE} MAKEFLAGS= CMD=$$cmd LABEL=WARNING help-command-not-installed help-command-$$cmd
		@true

uv-venv:: command-check-uv
	@test -d .venv && echo "${INFO_LABEL}directory ${CODE}.venv${_END} already exists; not running ${CODE}uv venv${_END}." || uv venv
	@echo "${TIP_LABEL}Try running ${CODE}source .venv/bin/activate${_END} if subsequent make commands fail."
	@echo "${TIP_LABEL}If they ${RED}still${_END} don't work, try ${CODE}make force-setup${_END}, which deletes ${CODE}.venv${_END}"
	@echo "${TIP_LABEL}and runs ${CODE}setup${_END} again."

uninstall-uv::
	$(info ${help-command-${@}-message})
	@true

command-check-uv::
	@command -v uv > /dev/null || ! ${MAKE} help-command-uv

install-jq:: help-command-jq

%-error:
	$(info ${ERROR}${@:%-error=%} - Error ${_END})
	$(error ${${@}-message})

define help-command-uv-message
${INFO_LABEL}The Python environment management tool ${CODE}uv${_END} is required.
${INFO_LABEL}See ${CODE}https://docs.astral.sh/uv/${_END} for installation instructions.
endef

define help-command-uninstall-uv-message
${WARNING_LABEL}You have to uninstall ${CODE}uv${_END} manually.
${INFO_LABEL}If you used HomeBrew to install it, use ${CODE}brew uninstall uv${_END}.
${INFO_LABEL}Otherwise, if you executed one of the installation commands from
${INFO_LABEL}${CODE}https://docs.astral.sh/uv/${_END}, find the installation location and delete it.
endef

help-command-uvx-message = ${help-command-uv-message}

define help-command-jq-message
${INFO_LABEL}The CLI command ${CODE}jq${_END} is useful, but not required, for processing JSON file.
${INFO_LABEL}See ${CODE}https://jqlang.org/download/${_END} for installation instructions.
endef

open-url-message = ${TIP_LABEL}Try ${CODE}⌘+click${_END} or ${CODE}^+click${_END} on the URL.

define skip-command-target-message
${WARNING_LABEL}Skipping ${CODE}${@:%-command=%}${_END} in ${CODE}${SRC_DIR}${_END}! Target ${CODE}$@${_END} is overridden in ${CODE}${SRC_DIR}/.custom.mk${_END}.
endef

# Definitions for the website:
include .website.mk

# Note on a previous implementation of the %-command behavior:
#
# An earlier implementation of this feature used the fact that two or more
# definitions of the _same_ target with a _single_ colon act as overrides,
# rather than appending behavior, which is what the double colon does:
#
# foo: foo-dependency-one
#   @echo "Foo recipe 1"
#
# foo: foo-dependency-two
#   @echo "Foo recipe 2"
#
# As written, `make foo` would print "Foo recipe 2". Unfortunately, make
# would also print two warnings about overriding the previous definition!
# The current "hack" we use with a wild-card target "%-command" above
# effectively implements the same behavior, but without the annoying warnings.
