![The AI Alliance banner](https://the-ai-alliance.github.io/assets/images/ai-alliance-logo-horiz-pos-blue-cmyk-trans.png)

# Project Tapestry

> [Technical website](https://the-ai-alliance.github.io/tapestry/) · [Project page](https://events.thealliance.ai/tapestry)

![Project Tapestry Image](docs/assets/images/03-tapestry-logo-1000x545.png)

## Why This Matters

Two structural problems define today's AI landscape — and Tapestry exists to solve both simultaneously.

**Performance without trust is a dead end.** Sovereign nations, industries, and communities will not adopt AI systems that underperform on their languages, legal contexts, and domain knowledge. Tapestry's thesis is that sovereignty *is* the performance strategy: access to sovereign public-sector data, cultural alignment, and domain specialization produce advantages that centralized models cannot replicate. A healthcare AI that a French doctor does not trust for French patients will not be adopted, regardless of its benchmark scores.

**AI that can be taken away is not AI you can depend on.** Countries, enterprises, and individuals need AI infrastructure they own and control — with guaranteed data residency, the right to exit, and the ability to operate independently. Tapestry provides this across three sovereignty levels: national (data residency, island mode, 72-hour exit), socio-cultural (constitutional AI, sacred knowledge protections, community review), and industrial (on-premise deployment, proprietary data isolation, domain specialization).

## Where to Start

| If you want to... | Go to... |
| :--- | :--- |
| Understand the vision and goals | [tech-docs/strategic-plan/VISION.md](tech-docs/strategic-plan/VISION.md) |
| Read the full requirements | [tech-docs/strategic-plan/PRD.md](tech-docs/strategic-plan/PRD.md) |
| Understand the architecture | [tech-docs/tapestry-reference/ARCHITECTURE.md](tech-docs/tapestry-reference/ARCHITECTURE.md) |
| Find a work group to join | [tech-docs/work-groups/README.md](tech-docs/work-groups/README.md) |
| Set up a development environment | [Development](#development) below |

## Development

If you want to work with the Project Tapestry code, here is how to get started.

### Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for Python package management.

#### Install uv

On macOS/Linux:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows:

```shell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

The rest of the steps are partially automated using `make`, although `make` is not required. Try the following:

```shell
make one-time-setup
```

#### Create a Virtual Environment

If `make one-time-setup` didn't work or you want to set up the virtual environment manually:

On macOS/Linux:

```shell
uv venv
source .venv/bin/activate
```
On Windows:

```shell
uv venv
.venv\Scripts\activate
```

#### Install Dependencies

If `make one-time-setup` didn't work or you want to install the dependencies yourself run _one_ of the following commands:

```shell
uv pip install -e ".[dev]"  # full development dependencies
uv pip install -e .         # minimum dependencies
```

### Running Tests

We use [unittest](https://docs.python.org/3/library/unittest.html) and [hypothesis](https://hypothesis.readthedocs.io/en/latest/) for testing. The easiest way to run the test suite is using `make`:

```shell
make tests # or unit-tests; they are currently the same.
```

This runs the following commands, which you can run yourself if you prefer:

```shell
cd src
uv run python -m unittest discover \
    --pattern 'test_*.py' \
    --start-directory tests \
    --top-level-directory .
```

### Code Formatting

Use _either_ of the following commands to format the Python code with `black`:

```shell
make format
# or
uv run black src
```

### Linting

Use _either_ of the following commands to lint the Python code with `ruff` and `pylint`:

```shell
make lint
# or
uv run ruff check src
uv pylint src
```

### Type Checking

Use _either_ of the following commands to type check the Python code with `ty`:

```shell
make type-check
# or
uv run ty src
```

There is also a "watch" option that keeps `ty` running as you fix mistakes and save the files:

```shell
make type-check-watch
# or
uv run ty --watch src
```

### Before You Submit a PR...

Please run the tests, format, lint, and type checking commands and makes sure everything passes cleanly! Use the convenient command, `make before-pr`, or run the individual commands above:

```shell
make before-pr   # Equivalent to 'make tests format lint type-check'
```

## Project Structure

The directory structure is as follows. 

The code is organized into major _subsystems_: 
* `data` for all data governance and management capabilities.
* `training` for all distributed training and tuning capabilities.
* `infrastructure` for all underlying infrastructure.

The technical documentation is organized into sections on the strategic plan, reference information, and work groups.

The details shown here are preliminary and subject to change:

```
tapestry/
├── src/
│   └── tapestry/
│       └── data/
│       └── evaluation/
│       └── model-training/
│       └── infrastructure/
│   └── tests
│       └── tapestry/
│           └── data/
│           └── evaluation/
│           └── model-training/
│           └── infrastructure/
├── tech-docs/
│   └── strategic-plan/
│   └── tapestry-reference/
│   └── work-groups/
│       └── data-engineering/
│       └── data-requirements/
│       └── evaluation-engineering/
│       └── evaluation-requirements/
│       └── infrastructure-engineering/
│       └── infrastructure-requirements/
│       └── model-training-engineering/
│       └── model-training-requirements/
```

## Architectural Decision Records (ADRs)

Significant architectural decisions are recorded as ADRs under
[`tech-docs/adr/`](tech-docs/adr/). The system is two-level:

- **Iterations** (`TAP-YYYY`) are units of work that follow a 5-phase
  template: SCOPE → PLAN → EXECUTE → VERIFY → CLOSE. SCOPE and PLAN are
  written *before* implementation begins.
- **Component decisions** (`XXX-YYYY`) capture specific technical choices
  within a subsystem and reference their parent iteration. Prefixes:
  `DAT` (data), `TRN` (training), `INF` (infrastructure), `DOC` (docs site),
  `WG` (work groups).

Before changing architecture, dependencies, services, schemas, frameworks, or
durable project conventions, read [`tech-docs/adr/README.md`](tech-docs/adr/README.md)
for the full convention, file-naming rules, and evidence standard. Routine bug
fixes, local refactors, tests, and docs do not need an ADR.

<a id="getting-involved-anchor"></a>

## More About Getting Involved

We welcome contributions as PRs to this repository. Please see our [Alliance community repo](https://github.com/The-AI-Alliance/community/) for general information about contributing to any of our projects. This section provides some specific details you need to know.

First, see the AI Alliance [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) instructions. You will need to agree with the AI Alliance [Code of Conduct](https://github.com/The-AI-Alliance/community/blob/main/CODE_OF_CONDUCT.md).

### Licenses

All _code_ contributions are licensed under the [Apache 2.0 LICENSE](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.Apache-2.0) (which is also in this repo, [LICENSE.Apache-2.0](LICENSE.Apache-2.0)).

All _documentation_ contributions are licensed under the [Creative Commons Attribution 4.0 International](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.CC-BY-4.0) (which is also in this repo, [LICENSE.CC-BY-4.0](LICENSE.CC-BY-4.0)).

All _data_ contributions are licensed under the [Community Data License Agreement - Permissive - Version 2.0](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.CDLA-2.0) (which is also in this repo, [LICENSE.CDLA-2.0](LICENSE.CDLA-2.0)).

We use the "Developer Certificate of Origin" (DCO).

> [!WARNING]
> Before you make any git commits with changes, understand what's required for DCO.

See the Alliance contributing guide [section on DCO](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) for details. In practical terms, supporting this requirement means you must use the `-s` flag with your `git commit` commands. 

## About the Technical Website

The website for this repository, where some technical content will be published, is found in the `docs` directory. It is published as [GitHub Pages](https://pages.github.com/) using [Jekyll](https://github.com/jekyll/jekyll).

See [GITHUB_PAGES.md](GITHUB_PAGES.md) for more information.
