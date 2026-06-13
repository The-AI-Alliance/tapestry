# Copilot instructions for Project Tapestry

These instructions guide GitHub Copilot when reviewing pull requests and
answering questions in this repository. The canonical, human-facing policy lives
in [`README.md`](../README.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md), and
[`contrib/README.md`](../contrib/README.md); this file is a reviewer aid that
summarizes the checks, not a replacement for those documents.

## About the project

Project Tapestry is building a consortium-trained foundation model system for
**sovereign AI**: data and compute ownership stays with partners, who can train
sovereign derivatives of a shared base model. Work centers on sovereign/
consortium training, data governance, evaluation, and supporting infrastructure.

## General review guidance

- Keep each PR focused on a single change; flag scope creep.
- Commits must carry a DCO `Signed-off-by` line (`git commit -s`), and—per branch
  protection—a verified signature before merge.
- Be specific and cite the relevant policy file when you flag something.

## Reviewing `contrib/` contributions

`contrib/` is a lightweight staging area ("front porch") for contributed ideas,
techniques, and experiments. The bar is intentionally low, but the following
must hold. Check each item and comment on anything that fails or is unclear.

### Scope & neutrality
- **On-mission.** The contribution is relevant to Tapestry's work. Adjacent-domain
  work is acceptable only when reframed around what it teaches Tapestry. Flag
  anything whose *primary purpose* is to promote an external project, product,
  token, or ecosystem.
- **No promotion.** No marketing language, no calls to action, and no links to
  commercial, rewards, airdrop, or token pages. Naming and attribution (including
  a contributor's own prior work) are fine; promotion is not. The line is whether
  the naming is the point.
- **Proportionate.** Examples illustrate a principle rather than serving as a
  contributor's portfolio; self-references are brief and in service of the idea.

### Structure
- Changes live in a single `contrib/<handle>-<topic>/` subdirectory.
- That subdirectory includes a `README.md` (idea, motivation, status, how to use
  or evaluate) and a `LICENSE` (or an explicit license reference).

### Licensing
- License is clear and compatible. Defaults: code → Apache 2.0, docs → CC BY 4.0,
  data → CDLA Permissive 2.0. Any non-default license must be permissive and
  stated explicitly in the subdirectory's `LICENSE` and `README.md`.

### Copyright & data clearance
- No copyrighted text, code, model weights, or data the contributor isn't
  licensed to redistribute.
- Datasets are cleared for the intended use; prefer a pointer + description over
  raw data, and flag handling constraints. No scraped/restricted/PII data without
  rights and handling notes.
- No apparent third-party ToS, NDA, or export-control violations.

### Security
- No secrets — no API keys, credentials, tokens, or private endpoints.
- No malicious or obfuscated code; external dependencies and any commands a
  reviewer would run are noted.
- Flag anything touching authentication, networking, or untrusted input for a
  closer look.

## Reviewing code changes (any PR that touches Python under `src/` or `contrib/`)

- Code should be formatted with `black`, lint clean under `ruff` and `pylint`, and
  type-check under `ty` (i.e. `make before-pr` would pass). Tests belong under the
  matching `src/tests/tapestry/...` path; suggest tests where they're missing.
- Keep new code aligned with the package split: `data/`, `training/`,
  `infrastructure/`. Avoid broad refactors outside the subsystem being touched.

## Reviewing documentation changes

- `docs/` is the Jekyll / Just the Docs site; preserve front matter and structure.
- `tech-docs/` holds design and decision docs; keep the audience technical and
  contributor-focused rather than promotional.
