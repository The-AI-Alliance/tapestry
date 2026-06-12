![The AI Alliance banner](https://the-ai-alliance.github.io/assets/images/ai-alliance-logo-horiz-pos-blue-cmyk-trans.png)

# Welcome to Project Tapestry

> _Project Tapestry is creating a global frontier foundation model with a new "consortium training" platform harnessing data, compute and contributors from around the world to enable sovereign AI._

This repo contains the code and technical documentation for the project. Check out the [Project Tapestry](https://thealliance.ai/projects/tapestry/) website for more information about partnering, events, and more.

![Project Tapestry Image](docs/assets/images/03-tapestry-logo-cropped-630x555.png)

The rest of this README provides information for contributors and users of this repository.

## Quick Paths

> [!NOTE]
> Make sure to read [**Getting Involved**](#getting-involved-anchor) below for information on contribution guidelines, etc.

### Our First Milestones

* [Cultural Alignment: help us develop techniques for cultural alignment](https://github.com/The-AI-Alliance/tapestry/issues/22) based on the [Inglehart–Welzel Cultural Map](https://en.wikipedia.org/wiki/Inglehart%E2%80%93Welzel_cultural_map_of_the_world) as a metric. This task will implement a corresponding evaluation and do a small model tuning exercise to see if improvement can be observed. Prior expertise in evaluation and tuning technologies are especially welcome.
* [Building Blocks of _consortium training_](https://github.com/The-AI-Alliance/tapestry/issues/24), the adaptation of federated learning that meets the unique requirements and constraints of Tapestry. Prior expertise in LLM training and federated learning technologies are especially welcome.
* [Global Training Data Corpus](https://thealliance.ai/projects/tapestry/training-data-proposals) What unique datasets exist that could be brought to Tapestry model training? They don't have to be fully open; we will work with you to define and enforce appropriate handling.
* A Model Development Roadmap - Coming soon.

### Working with the Source Code

The source code is under the [`src`](src/) directory.

* Use the [**`Makefile`**](Makefile) targets, e.g., `make help`. More details are in [**Development**](#development-anchor) below.
* Runnable demos in [**`examples/`**](examples/) (try `make consortium-demo`).
* Consortium training prototype in [**`src/tapestry/training/consortium/`**](src/tapestry/training/consortium/README.md) (try `make consortium-demo` and also `make consortium-tests`).

### Working with the Technical Documentation

The technical documentation lives under [**`tech-docs`**](tech-docs/README.md):

* [**Architecture**](tech-docs/architecture/README.md)
	* The _TVA methodology_: phased outputs (stakeholder map through design goals), architectural options and core thesis, plus:
		* [**Architecture Decision Records**](tech-docs/architecture/decisions/)
		* [**Diagrams**](tech-docs/architecture/diagrams/) 
* [**Governance**](tech-docs/governance/)
* [**Work Groups**](tech-docs/work-groups/)
* [**Strategic Plan**](tech-docs/strategic-plan/)
* [**Reference Materials**](tech-docs/reference/) (e.g. [**training paradigms**](tech-docs/reference/training-approaches.md))

For repo layout, conventions, and where to find implementation code, see [**`AGENTS.md`**](AGENTS.md).

<a id="development-anchor"></a>

## Development

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

The rest of the steps discussed next are automated using `make`. Try the following:

```shell
make one-time-setup
```

#### Create a Virtual Environment

The `one-time-setup` target runs the following command (but it only works on macOS or Linux). You can also do this manually:

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

The `one-time-setup` target runs the first of the following commands (but it only works on macOS or Linux). You can also run either command manually:

```shell
uv pip install -e ".[dev]"  # full development dependencies
uv pip install -e .         # minimum dependencies
```

### Running Tests

We use [unittest](https://docs.python.org/3/library/unittest.html) and [hypothesis](https://hypothesis.readthedocs.io/en/latest/) for testing. The easiest way to run the test suite is using `make`:

```shell
make unit-tests # or just tests; they are currently the same.
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

Before submitting a PR, please run the format, lint, and type checking commands, then run the tests. Make sure everything passes cleanly! Use the convenient `make` target `before-pr`, or run the individual commands above:

```shell
make before-pr               # Equivalent to 'make format lint type-check tests'
make format-lint-type-check  # Equivalent to 'make format lint type-check'
```

> [!NOTE]
> Make sure to read [**Getting Involved**](#getting-involved-anchor) below before submitting a PR.

## Project Code Structure

In addition to the top-level directories `tech-docs`, discussed above, `docs`, discussed below, and [`contrib`](contrib/README.md), the staging area for contributed ideas and techniques, the code structure is as follows. At this time, there are three major _subsystems_:

* `data` for all data governance and management capabilities.
* `training` for all distributed training and tuning capabilities.
* `infrastructure` for all underlying infrastructure.

```
tapestry/
├── contrib/        # Contributed ideas & techniques, proposed via PR
├── src/
│   └── tapestry/
│       └── data/
│       └── infrastructure/
│       └── training/
│   └── tests
│       └── tapestry/
│           └── data/
│           └── infrastructure/
│           └── training/
```

<a id="getting-involved-anchor"></a>

## Getting Involved

We welcome contributions as [pull requests](https://github.com/The-AI-Alliance/tapestry/pulls), [issues](https://github.com/The-AI-Alliance/tapestry/issues), and [discussions](https://github.com/The-AI-Alliance/tapestry/discussions). 

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. In particular, [read this section](CONTRIBUTING.md#developer-certificate-of-origin-dco) on using _DCO_ with any commits.

Have an idea, technique, or experiment you'd like the project to consider? The [**`contrib/`**](contrib/README.md) directory is a lightweight staging area where contributors can propose work via a PR into their own subdirectory. See [**`contrib/README.md`**](contrib/README.md) for the simple workflow and contribution policy.

You can also join one or more work groups that are being organized to identify requirements in several areas and to start the engineering work to prototype and test ideas, followed by the initial implementation iterations. Details are are being documented in [**`tech-docs/work-groups/`**](tech-docs/work-groups/).


### Licenses

All _code_ contributions are licensed under the [Apache 2.0 LICENSE](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.Apache-2.0) (which is also in this repo, [LICENSE.Apache-2.0](LICENSE.Apache-2.0)).

All _documentation_ contributions are licensed under the [Creative Commons Attribution 4.0 International](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.CC-BY-4.0) (which is also in this repo, [LICENSE.CC-BY-4.0](LICENSE.CC-BY-4.0)).

All _data_ contributions are licensed under the [Community Data License Agreement - Permissive - Version 2.0](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.CDLA-2.0) (which is also in this repo, [LICENSE.CDLA-2.0](LICENSE.CDLA-2.0)).

We use the "Developer Certificate of Origin" (DCO).

> [!WARNING]
> Before you make any git commits with changes, understand what's required for DCO.

See the contributing guide [section on DCO](CONTRIBUTING.md#developer-certificate-of-origin-dco) for details. In practical terms, supporting this requirement means you must use the `-s` flag with your `git commit` commands.

## About the Technical Website (GitHub Pages)

The [website](https://the-ai-alliance.github.io/tapestry/) for this repository provides another way to discover and navigate the technical documentation content in [`tech-docs`](/tech-docs). However, at this time, the site mostly just points to the content in [`tech-docs`](tech-docs/). The website sources are in the [`docs`](docs/) directory.

The website is published using [GitHub Pages](https://pages.github.com/), where the pages are written in Markdown and served using [Jekyll](https://github.com/jekyll/jekyll). See [GITHUB_PAGES.md](GITHUB_PAGES.md) for all the details.
