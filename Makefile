include common.mk

PAGES_URL    := https://the-ai-alliance.github.io/tapestry/
WEBSITE_DIR  := website
SITE_DIR     := ${WEBSITE_DIR}/_site
CLEAN_DIRS   += ${SITE_DIR} ${WEBSITE_DIR}/.sass-cache

# Override when running `make view-local` using e.g., `JEKYLL_PORT=8000 make view-local`
JEKYLL_PORT  ?= 4000

ifndef WEBSITE_DIR
$(error ERROR: There is no ${WEBSITE_DIR} directory!)
endif

define help_website_message

Help for the documentation website:

make view-pages         # View the published GitHub pages in a browser.
make view-local         # View the pages locally (requires Jekyll).
                        # Makes the targets 'setup-jekyll' and 'run-jekyll'
                        # Tip: "JEKYLL_PORT=8000 make view-local" uses port 8000 instead of 4000!
make setup-jekyll       # Install Jekyll. Make sure Ruby is installed. 
                        # (Only needed for local viewing of the document.)
make run-jekyll         # Used by "view-local"; assumes everything is already built.
                        # Tip: Build this target instead of 'view-local' to avoid repeating 'setup-jekyll'.
                        # Tip: "JEKYLL_PORT=8000 make run-jekyll" uses port 8000 instead of 4000!
endef

define help_programs_message

For the EXP-001 cultural-CPT validation harness (contrib):

make cultural-cpt-validation   # Run the arms experiment, single seed (smoke mode).
make cultural-cpt-aggregation  # Run the FedAvg aggregation-survival experiment.
make cultural-cpt-stats        # Run the multi-seed go/no-go decision (smoke mode).
make cultural-cpt-tests        # Run the cultural-CPT harness tests.

For the consortium-training prototype:

make consortium-demo    # Run the N+1 consortium-training proof-of-concept demo.
make consortium-experiment
                        # Run deterministic PoC metrics for consortium-training rounds.
make consortium-tests   # Run only the consortium-training prototype tests.
endef

print-info::
	@echo
	@echo "GitHub Pages URL:    ${PAGES_URL}"
	@echo "Website files:       ${WEBSITE_DIR}"
	@echo "JEKYLL_PORT:         ${JEKYLL_PORT}"

.PHONY: consortium-demo consortium-tests consortium-experiment cultural-cpt-validation cultural-cpt-aggregation cultural-cpt-stats cultural-cpt-tests cultural-cpt-fetch-seed cultural-cpt-validate-corpus

CULTURAL_CPT_DIR := contrib/jneums-cultural-cpt-validation

consortium-demo::
	@echo "${INFO}Running the consortium-training demo...${_END}"
	uv run python examples/consortium_training_demo.py

consortium-experiment::
	@echo "${INFO}Running the consortium-training experiment metrics...${_END}"
	PYTHONPATH="${PWD}/${SRC_DIR}:${PWD}/contrib/jneums-consortium-experiment" uv run python contrib/jneums-consortium-experiment/run.py

consortium-tests::
	@echo "${INFO}Running the consortium-training tests...${_END}"
	PYTHONPATH=${PWD}/${SRC_DIR}:${PWD}/contrib/jneums-consortium-experiment uv run python -m pytest ${SRC_DIR}/tests/tapestry/training/consortium contrib/jneums-consortium-experiment/tests -q

cultural-cpt-validation::
	@echo "${INFO}Running the EXP-001 cultural-CPT validation (smoke mode)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run.py

cultural-cpt-aggregation::
	@echo "${INFO}Running the cultural-CPT aggregation-survival experiment (smoke mode)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run_aggregation.py

cultural-cpt-stats::
	@echo "${INFO}Running the cultural-CPT multi-seed go/no-go (smoke mode)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/run_stats.py

cultural-cpt-tests::
	@echo "${INFO}Running the cultural-CPT validation tests...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run pytest ${CULTURAL_CPT_DIR}/tests -q

# CORPUS=<path> selects the root to validate (default: the committed seed).
CORPUS ?= ${CULTURAL_CPT_DIR}/data/seed-example

cultural-cpt-fetch-seed::
	@echo "${INFO}Fetching the real EXP-001 demonstration seed corpus (needs network)...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/fetch_corpus.py --culture seed-example --lang en --per-domain 4

cultural-cpt-validate-corpus::
	@echo "${INFO}Validating corpus ${CORPUS} against the EXP-001 controls...${_END}"
	PYTHONPATH="${PWD}/src:${PWD}/${CULTURAL_CPT_DIR}" \
		uv run python ${CULTURAL_CPT_DIR}/fetch_corpus.py --validate ${CORPUS}


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
	cd ${WEBSITE_DIR} && \
		bundle exec jekyll serve --port ${JEKYLL_PORT} --baseurl '' --incremental || \
		${MAKE} jekyll-error

setup-jekyll:: ruby-installed-check ruby-gem-installation bundle-command-check bundle-installation

.PHONY: ruby-installed-check ruby-gem-installation bundle-command-check bundle-installation
.PHONY: jekyll-error ruby-missing-error gem-missing-error gem-error bundle-error bundle-missing-error

ruby-gem-installation::
	@echo "Updating Ruby gems required for local viewing of the ${WEBSITE_DIR}, including jekyll."
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
