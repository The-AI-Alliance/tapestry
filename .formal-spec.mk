# Formal specification (Quint) targets. Run from the repo root.
# See contrib/luzanikita-formal-spec/README.md for the full workflow.
#
# SPEC_TOOLCHAIN_DIR: dir holding the shared package.json/node_modules (default ".").
# SPEC_DIR: dir tree to verify (default "spec"). Both are `?=`, so set them via
#   the environment or on the command line (command line wins). `make contrib-%`
#   (.common.mk) also sets SPEC_DIR to each contrib directory automatically, so
#   `make contrib-formal-spec-verify` checks every contrib/* for its own *.qnt
#   files with no override needed.
#
# formal-spec-verify, per "*.qnt" under SPEC_DIR: typecheck it; if "*_test.qnt",
# also "quint test" it; if it declares a top-level "val main", also
# "quint run --invariant main" it. Empty SPEC_DIR is a clean skip.

SPEC_TOOLCHAIN_DIR ?= .
SPEC_DIR ?= spec

define help-formal-spec-message

${HIGHLIGHT}Formal specification (Quint) targets:${_END}

${CODE}make formal-spec-install SPEC_TOOLCHAIN_DIR=<dir>${_END}
${CODE}${_END}                          # Install the pinned Quint toolchain in ${CODE}<dir>${_END} (default ${CODE}.${_END}; skips if no package.json).
${CODE}make formal-spec-verify SPEC_DIR=<dir>${_END}
${CODE}${_END}                          # Recursively typecheck every *.qnt under ${CODE}<dir>${_END} (default ${CODE}spec${_END}); run every
${CODE}${_END}                          # *_test.qnt via quint test; run "quint run --invariant main" on every
${CODE}${_END}                          # *.qnt that declares "val main".
endef

.PHONY: formal-spec-install formal-spec-verify contrib-formal-spec-install

# formal-spec-install is a single, repo-wide install (SPEC_TOOLCHAIN_DIR is not
# per-contrib) — this explicit rule overrides the generic "contrib-%" pattern
# in .common.mk so `make contrib-formal-spec-install` doesn't redundantly
# re-run `npm ci` once per contrib/* directory.
contrib-formal-spec-install::
	@echo "${WARNING_LABEL}Target ${CODE}formal-spec-install${_END} is shared across the whole repo. Run ${CODE}make formal-spec-install${_END} once instead of ${CODE}contrib-formal-spec-install${_END}.${_END}"

formal-spec-install::
	@if [ -f "$(SPEC_TOOLCHAIN_DIR)/package.json" ]; then \
		echo "${INFO_LABEL}Installing the Quint toolchain in ${CODE}$(SPEC_TOOLCHAIN_DIR)${_END}"; \
		cd $(SPEC_TOOLCHAIN_DIR) && npm ci; \
	else \
		echo "${WARNING_LABEL}No Quint toolchain in ${CODE}$(SPEC_TOOLCHAIN_DIR)${_END} (no ${CODE}package.json${_END} found) — skipping ${CODE}formal-spec-install${_END}."; \
	fi

formal-spec-verify::
	@if [ ! -d "$(SPEC_DIR)" ]; then \
		echo "${WARNING_LABEL}No such directory ${CODE}$(SPEC_DIR)${_END} — skipping ${CODE}formal-spec-verify${_END}."; \
	else \
		QNT_FILES="$$(find $(SPEC_DIR) -name '*.qnt' | sort)"; \
		if [ -z "$$QNT_FILES" ]; then \
			echo "${WARNING_LABEL}No formal specs in ${CODE}$(SPEC_DIR)${_END} — skipping ${CODE}formal-spec-verify${_END}."; \
		else \
			echo "${INFO_LABEL}Verifying formal specs in ${CODE}$(SPEC_DIR)${_END}"; \
			QUINT="$(SPEC_TOOLCHAIN_DIR)/node_modules/.bin/quint"; \
			for f in $$QNT_FILES; do \
				echo "${INFO_LABEL}Typechecking ${CODE}$$f${_END}"; \
				$$QUINT typecheck "$$f" || exit 1; \
			done; \
			for f in $$QNT_FILES; do \
				case "$$f" in \
					*_test.qnt) \
						echo "${INFO_LABEL}Testing ${CODE}$$f${_END}"; \
						$$QUINT test "$$f" || exit 1; \
						;; \
				esac; \
			done; \
			for f in $$QNT_FILES; do \
				if grep -Eq '^[[:space:]]*(pure[[:space:]]+)?val[[:space:]]+main[[:space:]]*[:=]' "$$f"; then \
					echo "${INFO_LABEL}Running invariant ${CODE}main${_END} on ${CODE}$$f${_END}"; \
					$$QUINT run --invariant main --verbosity=1 "$$f" || exit 1; \
				fi; \
			done; \
		fi; \
	fi
