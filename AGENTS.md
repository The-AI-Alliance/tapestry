# Tapestry Repo Guide

This repository is the technical home for Project Tapestry. Use this file as the fast path for orientation, navigation, and local conventions.

## Repository Map

- `README.md` is the top-level overview for contributors and developers.
- `Makefile` is the main task entry point for setup, tests, formatting, linting, type checking, and local docs serving.
- `docs/` is the GitHub Pages site. It is the user-facing technical website and follows Jekyll / Just the Docs conventions.
- `tech-docs/` is the main home for design and technical decision docs.
- `src/tapestry/` is the Python package under active development.
- `src/tests/` mirrors the package structure and holds the test suite.
- `examples/` contains runnable examples and demos.
- `ctn.local/` is local workspace material and is intentionally excluded from repo-wide navigation guidance unless a task explicitly says otherwise.

## Where To Look First

- For repo setup and contributor workflow: `README.md`
- For local build and verification commands: `Makefile`
- For the website structure and pages: `docs/index.markdown`, `docs/contributing.markdown`, `docs/about.markdown`
- For project-level design docs and technical direction: `tech-docs/README.md`
- For the current Python implementation surface: `src/tapestry/training/federated/`
- For the current tests: `src/tests/tapestry/training/federated/`

## `tech-docs/` Map

- `tech-docs/architecture/` holds the TVA methodology, the phase 1–5 outputs, the architectural options, the ADR index, and the diagram placeholders.
- `tech-docs/architecture/0-tva-methodology.md` is the process overview for the full TVA flow.
- `tech-docs/architecture/1-stakeholder-map.md` through `4-design-goals.md` are the requirements-side TVA phases.
- `tech-docs/architecture/5-architectural-options.md` is the option-space / decision analysis stage.
- `tech-docs/architecture/decisions/` holds the numbered ADRs.
- `tech-docs/governance/` holds governance design, including the anti-capture principle.
- `tech-docs/work-groups/` holds work-group-specific requirements and engineering notes.
- `tech-docs/strategic-plan/` holds higher-level execution strategy.
- `tech-docs/tapestry-reference/` is for reference material about deploying and using Tapestry software.

Start with `tech-docs/README.md` and `tech-docs/architecture/README.md` when you need the top-level doc taxonomy, then jump into the bucket that matches the task.

## Python Package Layout

The Python code is organized around three major subsystems:

- `data/` for data governance and management
- `training/` for distributed training and tuning
- `infrastructure/` for supporting infrastructure

The only implemented training slice in this snapshot is `training/federated/`, which contains:

- `aggregator.py` for FedAvg-style aggregation
- `node.py` for local training nodes and the demo transformer model
- `privacy.py` for differential privacy helpers
- `protocols.py` for shared dataclasses and the structural protocol

Keep new code aligned with that split. Add tests under the matching `src/tests/tapestry/...` path.

## Working Conventions

- Use Python 3.12 and `uv` for environment management.
- Prefer `make` targets for common tasks:
  - `make one-time-setup`
  - `make tests` or `make unit-tests`
  - `make format`
  - `make lint`
  - `make type-check`
  - `make view-local`
- The default repo test command is `make tests` / `make unit-tests`, which runs discovery from `src`.
- `pytest` is also configured in `pyproject.toml` and is useful for targeted test runs.
- Keep Python formatting consistent with `black` and the repo line length of 88.
- Keep lint/type annotations compatible with `ruff`, `pylint`, and `ty`.
- Preserve the docs site style in `docs/`: Markdown pages, Jekyll front matter, and Just the Docs structure.
- When editing documentation, keep the audience technical and contributor-focused rather than promotional.
- Treat governance documents as load-bearing design constraints, not after-the-fact policy notes.

## Practical Notes

- Match tests to the package layout instead of creating a separate test structure.
- Avoid broad refactors unless they are required to keep boundaries clear.
- Prefer small, focused changes that stay inside the subsystem you are touching.
- Treat `tech-docs/` as the first stop for architecture, requirements, and design context.
- For repo-wide navigation, ignore `ctn.local/` unless the task specifically asks for it.
