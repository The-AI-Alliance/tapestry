"""Stamp the CHANGELOG's Unreleased section with a date when main is cut.

Configured by ../workflows/changelog.yml (see issue #143). Idempotent:

- If the ``## [Unreleased]`` section carries no entries, exit 0 without
  touching the file (nothing to stamp; the workflow opens no PR).
- Otherwise, rename the section to ``## [YYYY-MM-DD]`` and insert a fresh
  empty ``## [Unreleased]`` above it, per keepachangelog conventions and
  the flow documented at the top of CHANGELOG.md (entries accumulate on
  ``develop``; the section gets stamped when ``main`` is cut).

Exit codes: 0 = stamped (file modified), 78 = nothing to stamp (neutral),
1 = CHANGELOG.md missing or has no Unreleased section.
"""

import datetime
import pathlib
import re
import sys

CHANGELOG = pathlib.Path("CHANGELOG.md")
UNRELEASED_RE = re.compile(r"^## \[Unreleased\]\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^## \[", re.MULTILINE)


def main() -> int:
    if not CHANGELOG.is_file():
        print("CHANGELOG.md not found", file=sys.stderr)
        return 1
    text = CHANGELOG.read_text(encoding="utf-8")

    match = UNRELEASED_RE.search(text)
    if match is None:
        print("no '## [Unreleased]' section found", file=sys.stderr)
        return 1

    # The Unreleased body runs from the end of its heading to the next
    # "## [" heading (or EOF). Entries = any non-blank line in that span.
    body_start = match.end()
    next_section = SECTION_RE.search(text, body_start)
    body_end = next_section.start() if next_section else len(text)
    body = text[body_start:body_end]
    if not any(line.strip() for line in body.splitlines()):
        print("Unreleased is empty; nothing to stamp")
        return 78

    today = datetime.date.today().isoformat()
    stamped = text[: match.start()] + f"## [Unreleased]\n\n## [{today}]" + text[match.end() :]
    CHANGELOG.write_text(stamped, encoding="utf-8")
    print(f"stamped Unreleased as [{today}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
