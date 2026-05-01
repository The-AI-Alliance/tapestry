
SRC_DIR      := src

PAGES_URL    := https://the-ai-alliance.github.io/tapestry/
DOCS_DIR     := docs
SITE_DIR     := ${DOCS_DIR}/_site
CLEAN_DIRS   := ${SITE_DIR} ${DOCS_DIR}/.sass-cache

# Environment variables
MAKEFLAGS            = --warn-undefined-variables
UNAME               ?= $(shell uname)
ARCHITECTURE        ?= $(shell uname -m)

# Override when running `make view-local` using e.g., `JEKYLL_PORT=8000 make view-local`
JEKYLL_PORT         ?= 4000

# Used for version tagging release artifacts.
GIT_HASH            ?= $(shell git show --pretty="%H" --abbrev-commit |head -1)
NOW                 ?= $(shell date +"%Y%m%d-%H%M%S")

# Colors used to make some messages stand out more than others...
RED          = \033[31m
BOLD_RED     = \033[1;31m
GREEN        = \033[32m
BOLD_GREEN   = \033[1;32m
YELLOW       = \033[33m
BOLD_YELLOW  = \033[1;33m
BLUE         = \033[34m
BOLD_BLUE    = \033[1;34m
PURPLE       = \033[35m
BOLD_PURPLE  = \033[1;35m
CYAN         = \033[36m
BOLD_CYAN    = \033[1;36m

ERROR        = ${BOLD_RED}ERROR:
WARN         = ${BOLD_YELLOW}WARNING:
NOTE         = ${BOLD_PURPLE}NOTE:
INFO         = ${BOLD_PURPLE}
TIP          = ${BOLD_BLUE}TIP:
HIGHLIGHT    = ${BOLD_GREEN}
_END         = \033[0m


define help_message
Quick help for this make process.

Building code:

make all                # Makes the 'help' and 'print-info' targets (see below). 
make tests              # Run the test suite.
make clean              # Remove built artifacts, etc.

make format             # Format the Python code with 'black'.
make lint               # Lint the Python code with 'ruff' and 'pylint.
make type-check         # Type check the Python code with 'ty'.
make type-check-watch   # Type check the Python code with 'ty' in "watch" mode,
                        # so you can fix mistakes and keep it updating.

For the documentation website:

make view-pages         # View the published GitHub pages in a browser.
make view-local         # View the pages locally (requires Jekyll).
                        # Makes the targets 'setup-jekyll' and 'run-jekyll'
                        # Tip: "JEKYLL_PORT=8000 make view-local" uses port 8000 instead of 4000!
make setup-jekyll       # Install Jekyll. Make sure Ruby is installed. 
                        # (Only needed for local viewing of the document.)
make run-jekyll         # Used by "view-local"; assumes everything is already built.
                        # Tip: Build this target instead of 'view-local' to avoid repeating 'setup-jekyll'.
                        # Tip: "JEKYLL_PORT=8000 make run-jekyll" uses port 8000 instead of 4000!

Help, etc.:

make help               # Prints this output.
make print-info         # Print the current values of some make and env. variables.
endef

define missing_shell_command_error_message
is needed by ${PWD}/Makefile. Try 'make help' and look at the README.
endef

ifndef DOCS_DIR
$(error ERROR: There is no ${DOCS_DIR} directory!)
endif


.PHONY: all help print-info clean
all:: help print-info

help::
	$(info ${help_message})
	@echo

clean::
	rm -rf ${CLEAN_DIRS} 

print-info:
	@echo "source               ${SRC_DIR}"
	@echo "tests                ${SRC_DIR}/tests"
	@echo "current dir:         ${PWD}"
	@echo "MAKEFLAGS:           ${MAKEFLAGS}"
	@echo "UNAME:               ${UNAME}"
	@echo "ARCHITECTURE:        ${ARCHITECTURE}"
	@echo "GIT_HASH:            ${GIT_HASH}"
	@echo "NOW:                 ${NOW}"
	@echo
	@echo "GitHub Pages URL:    ${PAGES_URL}"
	@echo "Website files:       ${DOCS_DIR}"
	@echo "JEKYLL_PORT:         ${JEKYLL_PORT}"


.PHONY: tests unit-tests
tests:: unit-tests

unit-tests::
	@echo "${INFO}Running the unit tests...${_END}"
	cd ${SRC_DIR} && \
	  uv run python -m unittest discover \
	    --pattern 'test_*.py' \
	    --start-directory tests \
	    --top-level-directory .

.PHONY: format lint type-check type-check-watch

format::
	@echo "${INFO}$@: Running 'black' on the code.${_END}"
	uv run black ${SRC_DIR}

lint::
	@echo "${INFO}$@: Running 'ruff' and 'pylint' on the code.${_END}"
	uv run ruff check ${SRC_DIR}
	uv run pylint ${SRC_DIR}

type-check::
	@echo "${INFO}$@: Running 'ty' to type check the code.${_END}"
	uv run ty check ${SRC_DIR} 
type-check-watch::
	@echo "${INFO}$@: Running 'ty' to type check the code in 'watch' mode.${_END}"
	uv run ty check --watch ${SRC_DIR} 

.PHONY: one-time-setup clean-setup 
.PHONY: install-uv uv-venv install-dev-dependencies command-check-uv

setup one-time-setup:: install-uv uv-venv install-dev-dependencies

install-%:: 
	@cmd=${@:install-%=%} && command -v $$cmd > /dev/null && \
		echo "${INFO}$$cmd is already installed${_END}" || ${MAKE} help-command-$$cmd

uv-venv:: command-check-uv 
	@test -d .venv && echo "'.venv' already exists; not running 'uv venv'." || uv venv
	@echo "run: 'source .venv/bin/activate' if subsequent commands fail!"

install-dev-dependencies::
	uv pip install -e ".[dev]"

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


.PHONY: view-pages view-local
.PHONY: setup-jekyll run-jekyll

view-pages::
	@python -m webbrowser "${PAGES_URL}" || \
		$(error "ERROR: I could not open the GitHub Pages URL. Try ⌘-click or ^-click on this URL instead: ${PAGES_URL}")

view-local:: setup-jekyll run-jekyll

# Passing --baseurl '' allows us to use `localhost:4000` rather than require
# `localhost:4000/The-AI-Alliance/tapestry` when running locally.
run-jekyll: clean
	@echo
	@echo "Once you see the http://127.0.0.1:${JEKYLL_PORT}/ URL printed, open it with command+click..."
	@echo
	cd ${DOCS_DIR} && \
		bundle exec jekyll serve --port ${JEKYLL_PORT} --baseurl '' --incremental || \
		${MAKE} jekyll-error

setup-jekyll:: ruby-installed-check ruby-gem-installation bundle-command-check bundle-installation

.PHONY: ruby-installed-check ruby-gem-installation bundle-command-check bundle-installation
.PHONY: jekyll-error ruby-missing-error gem-missing-error gem-error bundle-error bundle-missing-error

ruby-gem-installation::
	@echo "Updating Ruby gems required for local viewing of the docs, including jekyll."
	gem install jekyll bundler jemoji || ${MAKE} gem-error

bundle-installation::
	bundle install || ${MAKE} bundle-error
	bundle update html-pipeline || ${MAKE} bundle-error

ruby-installed-check:
	@command -v ruby > /dev/null || ${MAKE} ruby-missing-error
	@command -v gem  > /dev/null || ${MAKE} gem-missing-error

bundle-command-check:
	@command -v bundle > /dev/null || \
		${MAKE} bundle-missing-error 

# NOTE: We call make to run these %-error targets, because if you try
# some_command || $(error "didn't work"), the $(error ...) function is always
# invoked, independent of the shell script logic. Hence, the only way to make
# this invocation conditional is to use a make target invocation, as shown above.
jekyll-error:
	$(error "ERROR: Failed to run Jekyll. Try running 'make setup-jekyll'.")
ruby-missing-error:
	$(error "ERROR: 'ruby' is required. ${ruby_installation_message}")
gem-missing-error:
	$(error "ERROR: Ruby's 'gem' is required. ${ruby_installation_message}")
gem-error:
	$(error ${gem-error-message})
bundle-error:
	$(error ${bundle-error-message})
bundle-missing-error:
	$(error "ERROR: Ruby gem command 'bundle' is required. I tried 'gem install bundle', but it apparently didn't work!")


define gem-error-message

ERROR: Did the gem command fail with a message like this?
ERROR: 	 "You don't have write permissions for the /Library/Ruby/Gems/2.6.0 directory."
ERROR: To run the "gem install ..." command for the MacOS default ruby installation requires "sudo".
ERROR: Instead, use Homebrew (https://brew.sh) to install ruby and make sure "/usr/local/.../bin/gem"
ERROR: is on your PATH before "user/bin/gem".
ERROR:
ERROR: Or did the gem command fail with a message like this?
ERROR:   Bundler found conflicting requirements for the RubyGems version:
ERROR:     In Gemfile:
ERROR:       foo-bar (>= 3.0.0) was resolved to 3.0.0, which depends on
ERROR:         RubyGems (>= 3.3.22)
ERROR:   
ERROR:     Current RubyGems version:
ERROR:       RubyGems (= 3.3.11)
ERROR: In this case, try "brew upgrade ruby" to get a newer version.

endef

define bundle-error-message

ERROR: Did the bundle command fail with a message like this?
ERROR: 	 "/usr/local/opt/ruby/bin/bundle:25:in `load': cannot load such file -- /usr/local/lib/ruby/gems/3.1.0/gems/bundler-X.Y.Z/exe/bundle (LoadError)"
ERROR: Check that the /usr/local/lib/ruby/gems/3.1.0/gems/bundler-X.Y.Z directory actually exists. 
ERROR: If not, try running the clean-jekyll command first:
ERROR:   make clean-jekyll setup-jekyll
ERROR: Answer "y" (yes) to the prompts and ignore any warnings that you can't uninstall a "default" gem.

endef

define ruby_installation_message
See ruby-lang.org for installation instructions.
endef
