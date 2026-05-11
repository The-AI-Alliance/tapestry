![The AI Alliance banner](https://the-ai-alliance.github.io/assets/images/ai-alliance-logo-horiz-pos-blue-cmyk-trans.png)

# Welcome to Project Tapestry

> _Project Tapestry is creating a global frontier foundation model with a new "consortium training" platform harnessing data, compute and contributors from around the world to enable sovereign AI._

This repo contains the code and technical documentation for the project. Check out the [Project Tapestry](https://thealliance.ai/projects/tapestry/) website for more information about partnering, events, and more.

![Project Tapestry Image](docs/assets/images/03-tapestry-logo-1000x545.png)

The rest of this README provides information for contributors, developers, and users of this repository.

## Quick Paths

* Working with the [source code](/src):
	* Use the [**`Makefile`**](Makefile) targets, e.g., `make help`. See also the details in [**Development**](#development-anchor) below.
	* Runnable demos in [**`examples/`**](examples/)
	* Consortium training prototype in [**`src/tapestry/training/consortium/`**](src/tapestry/training/consortium/README.md)

## Documentation

The technical documentation lives under [**`tech-docs`**](tech-docs/README.md):

* [**Architecture**](tech-docs/architecture/README.md)
	* The _TVA methodology_: phased outputs (stakeholder map through design goals), architectural options and core thesis, plus:
		* [**Architectural Decision Records**](tech-docs/architecture/decisions/)
		* [**Diagrams**](tech-docs/architecture/diagrams/) 
* [**Governance**](tech-docs/governance/)
* [**Work Groups**](tech-docs/work-groups/)
* [**Strategic Plan**](tech-docs/strategic-plan/)
* [**Reference Materials**](tech-docs/reference/) (e.g. [**training paradigms**](tech-docs/reference/training-approaches.md))

The [published technical website](https://the-ai-alliance.github.io/tapestry/) provides another way to navigate the technical documentation. The sources for this GitHub Pages website are found in [**`docs/`**](docs/).

For repo layout, conventions, and where to find implementation code, see [**`AGENTS.md`**](AGENTS.md).

## Getting Involved

Several work groups are being organized to identify requirements in several areas and to start the engineering work to prototype and test ideas, followed by the initial implementation iterations. Details are to be announced. The work group documentation is found under [**`tech-docs/work-groups/`**](tech-docs/work-groups/).

We welcome contributions as [pull requests](https://github.com/The-AI-Alliance/tapestry/pulls), [issues](https://github.com/The-AI-Alliance/tapestry/issues), and [discussions](https://github.com/The-AI-Alliance/tapestry/discussions). See [More about Getting Involved](#getting-involved-anchor) below for details about AI Alliance contribution guidelines, licenses, etc.

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

The rest of the steps are partially automated using `make`. Try the following:

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
uv run ty src
```

There is also a "watch" option that keeps `ty` running as you fix mistakes and save the files:

```shell
make type-check-watch
uv run ty --watch src
```

## Project Structure

The structure is as follows, where three major _subsystems_ are managed: 
* `data` for all data governance and management capabilities.
* `training` for all distributed training and tuning capabilities.
* `infrastructure` for all underlying infrastructure.

```
tapestry/
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

## More about Getting Involved

We welcome source code and technical documentation contributions. Use [pull requests](https://github.com/The-AI-Alliance/tapestry/pulls), [issues](https://github.com/The-AI-Alliance/tapestry/issues), or [discussions](https://github.com/The-AI-Alliance/tapestry/discussions). 

In particular, see the AI Alliance [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) instructions. You will need to agree with the AI Alliance [Code of Conduct](https://github.com/The-AI-Alliance/community/blob/main/CODE_OF_CONDUCT.md).

### Licenses

All _code_ contributions are licensed under the [Apache 2.0 LICENSE](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.Apache-2.0) (which is also in this repo, [LICENSE.Apache-2.0](LICENSE.Apache-2.0)).

All _documentation_ contributions are licensed under the [Creative Commons Attribution 4.0 International](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.CC-BY-4.0) (which is also in this repo, [LICENSE.CC-BY-4.0](LICENSE.CC-BY-4.0)).

All _data_ contributions are licensed under the [Community Data License Agreement - Permissive - Version 2.0](https://github.com/The-AI-Alliance/community/blob/main/LICENSE.CDLA-2.0) (which is also in this repo, [LICENSE.CDLA-2.0](LICENSE.CDLA-2.0)).

We use the "Developer Certificate of Origin" (DCO).

> [!WARNING]
> Before you make any git commits with changes, understand what's required for DCO.

See the Alliance contributing guide [section on DCO](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) for details. In practical terms, supporting this requirement means you must use the `-s` flag with your `git commit` commands.

## About the Technical Website

The website for this repo is found in the `docs` directory. It provides another way to navigate the content of [`tech-docs`](/tech-docs). The website is published using [GitHub Pages](https://pages.github.com/), where the pages are written in Markdown and served using [Jekyll](https://github.com/jekyll/jekyll). We use the [Just the Docs](https://just-the-docs.github.io/just-the-docs/) Jekyll theme.

See [GITHUB_PAGES.md](GITHUB_PAGES.md) for more information.
