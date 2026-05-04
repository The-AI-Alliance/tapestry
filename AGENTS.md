# AGENTS.md

Quick-start guidance for AI agents working in this repository.

## Project snapshot

`tapestry` is the AI Alliance's [Project Tapestry](http://thealliance.ai/projects/tapestry)
technical repo. It is a Python 3 project (managed with [`uv`](https://docs.astral.sh/uv/))
organized around three subsystems plus a published technical website:

- `data` — data governance and management capabilities.
- `training` — distributed training and tuning capabilities.
- `infrastructure` — underlying infrastructure.

Start with:

- `README.md` for the project intro and developer setup.
- `tech-docs/README.md` for prose technical documentation (strategic plan,
  reference, work groups).
- `tech-docs/adr/README.md` before making architectural changes.
- `GITHUB_PAGES.md` if you are touching the published documentation site.

## Repository map

- `src/tapestry/data/` — data subsystem source.
- `src/tapestry/training/` — training / tuning subsystem source.
- `src/tapestry/infrastructure/` — infrastructure subsystem source.
- `src/tests/tapestry/{data,training,infrastructure}/` — unittest + hypothesis tests.
- `docs/` — Jekyll source for the published GitHub Pages site
  (https://the-ai-alliance.github.io/tapestry/). Treat as user-facing content.
- `tech-docs/` — internal prose documentation, not published.
  - `tech-docs/adr/` — Architectural Decision Records (see
    `tech-docs/adr/README.md`).
  - `tech-docs/strategic-plan/`, `tech-docs/tapestry-reference/`,
    `tech-docs/work-groups/` — planning and reference material.
- `Makefile` — common developer entry points.
- `pyproject.toml` — package metadata and tool config.
- `Gemfile` — Jekyll/GitHub Pages dependencies for local site preview.
- `check-external-links.sh` — link checker for the published docs.

## Local setup

This project uses [`uv`](https://docs.astral.sh/uv/) for Python package management.
Install `uv` first (see README), then:

```bash
make one-time-setup
```

Or manually:

```bash
uv venv
source .venv/bin/activate          # macOS/Linux
uv pip install -e ".[dev]"         # full development dependencies
```

## Common commands

```bash
# Tests (unittest + hypothesis)
make unit-tests

# Format with black
make format

# Lint with ruff and pylint
make lint

# Type-check with ty
make type-check
make type-check-watch              # watch mode
```

Direct equivalents (when not using make):

```bash
cd src && uv run python -m unittest discover \
    --pattern 'test_*.py' \
    --start-directory tests \
    --top-level-directory .

uv run black src
uv run ruff check src
uv run ty src
```

## Development workflow for agents

1. Run `git status` before editing. Do not revert unrelated changes from the
   user or other agents.
2. Read the relevant subsystem source and nearby tests before implementing.
3. Keep edits scoped. Follow existing local patterns rather than introducing
   new abstractions.
4. Add or update tests when behavior changes. Documentation-only changes
   usually do not need a test run; state that explicitly in the PR description.
5. Run focused tests first when possible, then the full `make unit-tests`,
   `make lint`, and `make type-check` when the change touches shared behavior.
6. Open PRs against `main` (or `develop` if the maintainers direct you there).

## ADR rules

Architectural changes require an ADR. Before changing architecture,
dependencies, services, schemas, frameworks, or durable project conventions,
read `tech-docs/adr/README.md`.

Key rules:

- ADRs are append-only. Do not rewrite historical decisions.
- Iteration ADRs use the SCOPE → PLAN → EXECUTE → VERIFY → CLOSE structure.
- Open iteration SCOPE and PLAN before implementation work begins.
- Use sequential numbers within the appropriate prefix and never reuse numbers.
- Component ADRs include a `Parent:` field referencing the parent iteration.
- Project / iteration prefix is `TAP`. Component prefixes: `DAT` (data),
  `TRN` (training), `INF` (infrastructure), `DOC` (docs site), `WG` (work groups).
  New prefixes require a component ADR.

Non-architectural bug fixes, local refactors, tests, and docs do not need an ADR.

## Testing notes

- Tests live under `src/tests/tapestry/` and are discovered by
  `python -m unittest discover` from the `src/` directory.
- Property-based tests use [hypothesis](https://hypothesis.readthedocs.io/).
- Avoid committing generated caches such as `__pycache__/` or `.pytest_cache/`.

## Publishing and the docs site

- `docs/` is published via GitHub Pages using Jekyll + the Just the Docs theme.
  Anything you put there becomes part of the public site — use `tech-docs/`
  for internal-only prose.
- For local site preview and link checking, see `GITHUB_PAGES.md` and
  `check-external-links.sh`.

## Licensing and DCO

This repo is triple-licensed by content type:

- Code: [Apache-2.0](LICENSE.Apache-2.0)
- Documentation: [CC-BY-4.0](LICENSE.CC-BY-4.0)
- Data: [CDLA-2.0](LICENSE.CDLA-2.0)

All commits **must** be signed off under the Developer Certificate of Origin.
Use `git commit -s` (the `-s` flag is required) so the trailer
`Signed-off-by: Your Name <email>` is added. See the AI Alliance
[CONTRIBUTING guide](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin)
for details.

## Safe operating constraints

- Treat the repository as the source of truth: code, docs, ADRs, and git
  history are all part of project memory.
- Do not introduce new dependencies without checking whether existing standard
  library or project utilities suffice; dependency additions generally need an
  ADR.
- Keep secrets out of commits.
- Do not edit `docs/` (the published site) when the task is about internal
  engineering notes — use `tech-docs/` instead, and vice versa.
