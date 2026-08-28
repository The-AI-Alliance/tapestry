# .vendored-scripts.mk - Integrity checks for third-party scripts committed
# directly into this repo (not covered by CodeQL or `npm audit`).
#
# VENDOR_CHECKSUMS_FILE: sha256sum-format registry, one "<hash>  <path>" line
# per vendored file (no comments in it — not portable across sha256sum/shasum).
# FIRST_PARTY_SCRIPTS_FILE: plain list of first-party scripts, intentionally
# unpinned since they're expected to change.
#
# Registry:
#   docs/architecture/diagrams/chart.js/4.5.1/chart.umd.min.js
#     = official chart.js v4.5.1 release, byte-for-byte.
#   website/assets/js/vendor/lunr.min.js
#     = official lunr@2.3.6 npm release, byte-for-byte.
#   website/assets/js/just-the-docs.js
#     Trust-on-first-use — no confirmed upstream to verify against.
#
# Adding a vendored file: verify against upstream, then add a registry note
# above and append a line:
#   shasum -a 256 <path> >> vendor-checksums.sha256   (macOS)
#   sha256sum <path> >> vendor-checksums.sha256        (Linux)
# Updating an existing entry: re-verify against upstream before re-pinning.
#
# Prefer a real npm dependency over hand-vendoring when the file is an
# unmodified published package — gets lockfile integrity + npm audit +
# Dependabot for free (needs an install/copy step added to the website's
# publish workflow, which doesn't have one yet). Otherwise vendor + register
# here. Either way it must be registered, or verify-script-classification
# fails CI.
#
# verify-script-classification: every tracked *.js/*.ts/*.mjs/*.cjs file must
# be in one of the two registries, or CI fails — catches a new
# vendored/first-party script that was never registered.
# approve-first-party-scripts: appends unclassified scripts to
# FIRST_PARTY_SCRIPTS_FILE for you — only after confirming they're not
# vendored.

VENDOR_CHECKSUMS_FILE     ?= vendor-checksums.sha256
FIRST_PARTY_SCRIPTS_FILE  ?= first-party-scripts.txt
TRACKED_SCRIPT_GLOBS      := '*.js' '*.ts' '*.mjs' '*.cjs'

define help-vendored-scripts-message

${HIGHLIGHT} Help for vendored third-party script integrity checks: ${_END}

${CODE}make verify-vendored-scripts${_END}
${CODE}${_END}                        # Both of the below. Run as part of CI (${CODE}vendor-integrity.yml${_END}).
${CODE}make verify-vendored-checksums${_END}
${CODE}${_END}                        # Verify every file listed in ${CODE}${VENDOR_CHECKSUMS_FILE}${_END} still matches its
${CODE}${_END}                        # pinned SHA-256 checksum.
${CODE}make verify-script-classification${_END}
${CODE}${_END}                        # Verify every tracked ${CODE}${TRACKED_SCRIPT_GLOBS}${_END} file is listed in
${CODE}${_END}                        # ${CODE}${VENDOR_CHECKSUMS_FILE}${_END} or ${CODE}${FIRST_PARTY_SCRIPTS_FILE}${_END} — catches a new vendored
${CODE}${_END}                        # script that was never registered.
${CODE}make approve-first-party-scripts${_END}
${CODE}${_END}                        # Append every currently-unclassified script to ${CODE}${FIRST_PARTY_SCRIPTS_FILE}${_END}.
${CODE}${_END}                        # Only do this after confirming they're first-party, not vendored —
${CODE}${_END}                        # review the diff before committing.

endef

.PHONY: verify-vendored-scripts verify-vendored-checksums verify-script-classification
.PHONY: print-unclassified-scripts approve-first-party-scripts

verify-vendored-scripts:: verify-vendored-checksums verify-script-classification

verify-vendored-checksums::
	@echo "${INFO_LABEL}Verifying vendored script checksums in ${CODE}${VENDOR_CHECKSUMS_FILE}${_END}"
	@if command -v sha256sum > /dev/null 2>&1; then \
		sha256sum -c ${VENDOR_CHECKSUMS_FILE}; \
	else \
		shasum -a 256 -c ${VENDOR_CHECKSUMS_FILE}; \
	fi

# One unclassified script per line on stdout; empty output means none.
print-unclassified-scripts::
	@vendored="$$(awk '{print $$2}' ${VENDOR_CHECKSUMS_FILE})"; \
	first_party="$$(cat ${FIRST_PARTY_SCRIPTS_FILE})"; \
	for f in $$(git ls-files -- ${TRACKED_SCRIPT_GLOBS}); do \
		found=""; \
		for known in $$vendored $$first_party; do \
			[ "$$known" = "$$f" ] && found=1 && break; \
		done; \
		[ -z "$$found" ] && echo "$$f"; \
	done; \
	true

verify-script-classification::
	@echo "${INFO_LABEL}Checking every tracked script is classified in ${CODE}${VENDOR_CHECKSUMS_FILE}${_END} or ${CODE}${FIRST_PARTY_SCRIPTS_FILE}${_END}"
	@unclassified="$$(${MAKE} --no-print-directory print-unclassified-scripts)"; \
	if [ -n "$$unclassified" ]; then \
		echo "${ERROR_LABEL}Unclassified script file(s):${_END}"; \
		echo "$$unclassified" | sed 's/^/  /'; \
		echo "${ERROR_LABEL}If vendored: add to ${CODE}${VENDOR_CHECKSUMS_FILE}${_END} — verify against upstream first (see the top of ${CODE}.vendored-scripts.mk${_END}).${_END}"; \
		echo "${ERROR_LABEL}If first-party: run ${CODE}make approve-first-party-scripts${_END}, then review and commit the diff.${_END}"; \
		exit 1; \
	else \
		echo "${INFO_LABEL}All tracked scripts are classified.${_END}"; \
	fi

approve-first-party-scripts::
	@unclassified="$$(${MAKE} --no-print-directory print-unclassified-scripts)"; \
	if [ -z "$$unclassified" ]; then \
		echo "${INFO_LABEL}No unclassified scripts to approve.${_END}"; \
	else \
		echo "$$unclassified" >> ${FIRST_PARTY_SCRIPTS_FILE}; \
		sort -uo ${FIRST_PARTY_SCRIPTS_FILE} ${FIRST_PARTY_SCRIPTS_FILE}; \
		echo "${INFO_LABEL}Approved as first-party (added to ${CODE}${FIRST_PARTY_SCRIPTS_FILE}${_END}):${_END}"; \
		echo "$$unclassified" | sed 's/^/  /'; \
		echo "${WARNING_LABEL}Only commit this if you've confirmed each one is NOT vendored/third-party code.${_END}"; \
	fi
