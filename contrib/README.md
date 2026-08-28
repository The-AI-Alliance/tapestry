# Contributed Ideas & Techniques (`contrib/`)

This directory is a staging area for **contributed ideas, techniques, and experiments** offered to Project Tapestry for consideration. It is intentionally lightweight: a place to share work-in-progress proposals and prototypes (i.e., at various levels of maturity), notes, datasets-pointers, and references without first having to fit them into the main package or `docs/` taxonomy.

Think of `contrib/` as the front porch. Promising contributions may later be promoted into `src/`, `docs/`, or `examples/` after discussion and review. Material here is **not** part of the supported codebase and carries no stability guarantees.

## Current Contributions

| Contribution | Contributor(s) | Status | What it is |
| :----------- | :------------- | :----- | :--------- |
| [`14H034160212-conflict-aware-fusion`](14H034160212-conflict-aware-fusion/README.md) | [@14H034160212](https://github.com/14H034160212) | Candidate | LIRE + RLVF post-training stages that teach a base model to halt on logically inconsistent premises instead of deducing through them |
| [`14H034160212-logically-grounded-dpo`](14H034160212-logically-grounded-dpo/README.md) | [@14H034160212](https://github.com/14H034160212) | Candidate | Verifier-based DPO/PPO preference pipeline replacing reference-text similarity with an NLI-entailment reward for checkable explanations |
| [`jneums-consortium-experiment`](jneums-consortium-experiment/README.md) | [@jneums](https://github.com/jneums) | Speculative | Deterministic measurement layer around the consortium-training proof of concept |
| [`jneums-cultural-cpt-validation`](jneums-cultural-cpt-validation/README.md) | [@jneums](https://github.com/jneums) | Speculative | Runnable harness for EXP-001: does culturally grounded continued pretraining shift alignment beyond language exposure? |
| [`jneums-flower-wan-spike`](jneums-flower-wan-spike/README.md) | [@jneums](https://github.com/jneums) | Speculative | De-risk spike for #70: 2B-parameter weight round-trip through a Flower SuperLink over a real WAN |
| [`luzanikita-formal-spec`](luzanikita-formal-spec/README.md) | [@luzanikita](https://github.com/luzanikita) | Speculative | Using a formal specification system, [Quint](https://quint.sh) to carefully specify and verify systems. |
| [`nguyennm1024-sociocultural-alignment`](nguyennm1024-sociocultural-alignment/README.md) | [@nguyennm1024](https://github.com/nguyennm1024) | Speculative | LoRA + consortium learning + Inglehart–Welzel evaluation for sovereign cultural alignment (Vietnamese case study) |
| [`oli-sovereign-eval-evidence`](oli-sovereign-eval-evidence/README.md) | [@welttowelt](https://github.com/welttowelt) | Speculative | Evidence layer connecting cultural-alignment evaluation, data sovereignty, and certification claims |

Statuses are `Speculative`, `Candidate`, or `Promoted` — see
[State the Readiness Level](#state-the-readiness-level) and
[Promotion to Production](#promotion-to-production) below. The table is
maintained by hand for now: when you add a contribution, add your row.

## How to Contribute

We follow normal _GitOps_ practices (see the top-level [`CONTRIBUTING.md`](../CONTRIBUTING.md)). To add a contribution:

1. **Fork and branch** the repository.
2. **Create your own subdirectory** under `contrib/`, named with your handle/org and a short topic, e.g.:
   - `contrib/jane-doe-cultural-eval/`
   - `contrib/acme-labs-federated-tuning/`
3. **Add your contents** to that subdirectory. At minimum include:
   - A short `README.md` describing the idea, motivation, status, and how to use or evaluate it.
   - A `LICENSE` (or `LICENSE` reference) covering the contents — see [Licensing](#licensing) below.
4. **Check the reviewer checklist** below before opening the pull request.
5. **Open a Pull Request.** Keep each PR focused on a single contribution. Use the PR description to explain what you're proposing and what feedback you're looking for.
6. **Sign your commits** with DCO (`git commit -s ...`). See the [DCO section](../CONTRIBUTING.md#developer-certificate-of-origin-dco) for details.

A maintainer will review, discuss, and either request changes, merge for further consideration, or suggest a better home for the work. Merging into `contrib/` signals "accepted for consideration," not endorsement or production-readiness.

### Suggested Subdirectory Layout

The details about each file are discussed below.

```
contrib/
└── <your-handle>-<topic>/
    ├── README.md      # What it is, why, status, how to try it
    ├── LICENSE        # License for this contribution (optional)
    ├── .custom.mk     # Customize project-wide make targets, like "tests" (optional)
    ├── .targets.mk    # Add project-wide make targets for the contribution (optional)
    ├── Makefile       # Standalone make processes; not connected to the main make processes (optional)
    ├── src/...        # code and tests
    └── docs/...       # Other notes, diagrams, data pointers, etc.
```

## The Project-wide Make Processes

The files `.custom.mk` and `.targets.mk` are optional files that tie your contribution into the project-wide `make` processes. (Note the leading `.` in the names) They are _include_ files that will be read by the top-level `Makefile` and `.common.mk` files.

There are two files because they play two different roles and they are loaded in two different ways. We discuss the details below, but briefly, here is how they are used:

* `.custom.mk` - Override the behaviors of common targets like `tests`, `format`, etc.
* `.targets.mk` - Define targets for the contribution that will be visible in the top-level `make` process, such as commands to run the contribution's code.

You can find examples of these files in some of the `contrib/*` directories.

Optionally, you can include your own `Makefile` for other "standalone" purposes that don't need exposure in the top-level processes. If useful, your `Makefile` can include `.common.mk` using a relative path to it:

```makefile
include ../../.common.mk
```

Now lets discuss the quality enforcement and how to customize them using `.custom.mk`.

## Pass the Code Quality Enforcement

The top-level `Makefile` has a target `before-pr`, which we ask everyone to run before opening a pull request.

```shell
make before-pr
```

This target builds the following targets used to format the code and verify that **all** existing _production_ code under `src` meets our quality criteria:

| Targets | Purpose |
| :------ | :------ |
| `format` | Format the Python code consistently. |
| `ruff` and `pylint` | _Lint_ the code for potential problems. |
| `type-check` | Verify the optional type annotations are valid. |
| `tests` | Run the unit tests. |

All these targets are defined in the top-level `.common.mk` file.

> [!WARNING]
> The `format` target may modify your source code. Inspect those changes and commit them. If you think they are "wrong" in some way and the formatting should be changed globally for all source code, [post an issue](https://github.com/The-AI-Alliance/tapestry/issues). If you just want to disable the reformatting for your contribution, use the mechanisms described below.

**_By default, these same targets are built for every contribution, too!_** However, since `contrib` contributions are not necessarily production quality, and we want to encourage such contributions with minimal "friction", a make "protocol" is provided to customize which quality checks are skipped. This is how `.custom.mk` is used.

> If you intend for your contribution to become part of the production code, it will eventually be necessary for all these quality enforcement targets to work successfully for your contribution, so we recommend making them work ASAP.

Before discussing customization options, let's describe how you can build these quality `make` targets for your contribution, without running them for all code.

First, to run the checks for _all_ the contributions, start in the _top-level directory_ and run either of the following commands:

```shell
make before-pr-contrib  # Run all of the checks for all contrib/*
make contrib-pylint     # Run just `pylint` for all contrib/*
```

(Substitute `pylint` with any of the other quality checks mentioned above, as desired.)
To run checks for your contribution only, let's assume it is named `contrib/johndoe-foo`, then use the following command in the top-level directory to run all the quality targets:

```shell
make SRC_DIR=contrib/johndoe-foo --include-dir=contrib/johndoe-foo format ruff pylint type-check tests
```

The `SRC_DIR=...` definition points to the contribution's directory so the quality targets run from there. The `--include-dir=...` argument is used to tell `make` to search in the same directory for include files, in our case, the customization file `.custom.mk`.

The `do-contrib-before-pr` target mentioned above also uses this command, running it once for each contribution. Similarly, the `contrib-x` targets also use this command, with the `x` target being one of the list of all the quality targets: `format ruff pylint type-check unit-tests`.

> [!TIP]
> Problems found while type checking often take the most time to fix, use this command to continuously and automatically re-run the type checker as you fix issues and save the files:
> ```shell
> make SRC_DIR=contrib/johndoe-foo --include-dir=contrib/johndoe-foo type-check-watch
> ```
> Exit using control-C.

### How to Customize the Quality Checks

You can find examples in most of the `contrib/*` directories. Customization is done by creating a `.custom.mk` file. Here is an example, `contrib/jneums-consortium-experiment/.custom.mk` (at the time of this writing):

```makefile
override define help_targets_message
For the consortium-training prototype:

${CODE}make consortium-experiment${_END}
                        # Run deterministic PoC metrics for consortium-training rounds.
${CODE}make consortium-tests${_END}   # Run only the consortium-training prototype tests.
endef

# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-command type-check-command:
  @echo "${skip-command-target-message}"
  @true
```

Two of the supported customization mechanisms are shown here.

But first, note the `${CODE}` and `${_END}` `make` variables used in the help message. They provide color highlighting of the output. `${CODE}` starts a string of highlighting and `${_END}` stops it (returning to normal console output). They make messages more readable, but you can omit them in your help messages. See `../.console-colors.mk` for more details about these and other highlighting definitions. See other message definitions in `../.common.mk` for more examples, as well as the examples below that use `${INFO}`, which behaves similarly to `${CODE}` (it takes affect until `${_END}` is seen) and `${INFO_LABEL}`, which shows a highlighted leading "label", `INFO:`, and immediately resets to the normal output, so `${_END}` isn't necessary.

#### Help on Custom Targets You Define

We will see below, that you can define targets that can be executed to demonstrate your contribution using the `.targets.mk` file. You provide a brief description of all these commands in `.custom.mk`, where you _override_ the definition of `help_targets_message` as shown here.

This message will be printed whenever the user runs `make help-targets` (a target defined in the top level `.common.mk`), along with similar messages for all the other contributions. In this example, there are two program targets defined, `consortium-experiment` and `consortium-tests`.

> [!NOTE]
> Note the `override` keyword for the definition for `help_targets_message`. By default, the top-level `.common.mk` provides a default definition, but we override it here to customize it for this particular directory.

Try `make help-targets` in the top-level directory to see all the help messages about targets in contributions, as well as the main code base.

#### Disable Some Quality Checks

The second customization mechanism is shown for `pylint` and `type-check` in the example contribution. These quality targets don't currently pass (and don't really need to pass at this time). Hence, they are _disabled_ by _overriding_ the definitions of the `pylint-command` and `type-check-command` targets to print a warning message (as a reminder to the user), but not actually invoke `pylint` and `type-check`, respectively.

In the top level `.common.mk`, the `pylint` target is defined as follows (the other quality targets like `type-check` are similar):

```makefile
pylint:: pylint-prerequisite pylint-command pylint-postrequisite
pylint-prerequisite pylint-postrequisite::
pylint-command::
  @echo "${INFO} $@: Running 'pylint' on the code in ${SRC_DIR}.${_END} (configuration in pylintrc.toml)"
  uv run pylint ${SRC_DIR}
```

Actually, this is _conceptually_ what happens; the implementation is a little more involved. A more sophisticated technique is used to suppress some warnings from `make` about overriding targets like `pylint-command`. If you are interested in the details, read the long comments in `.common.mk` that explain what is done.

If you don't override the definition of `pylint-command` in your `.custom.mk`, the definition in `.common.mk` will be used to run `pylint` on your code.

> [!NOTE]
> Anytime you disable a quality check by overriding the definition of `*-command`, please use the _recipe_ shown in the example above, so the warning message is issued for the user's benefit!

The third and fourth customization mechanisms are "suggested" in the snippet from the top level `.common.mk` above. The `pylint-prerequisite` target does nothing by default, but if you need to do something _before_ `pylint` is invoked, you can add a definition for this target in your `.custom.mk` file. Similarly, `pylint-postrequisite` does nothing by default, but it can be defined to do work after `pylint` finishes, for example, cleaning up temporary files.

Let's look at an example, adapted from `contrib/nguyennm1024-sociocultural-alignment/`, of how a prerequisite hook can be used before tests are run to set up a custom environment in that _contribution_:

```makefile
unit-tests-prerequisite::
  @cd ${SRC_DIR}; \
    if [ -d .venv ]; \
    then echo "${INFO_LABEL}'.venv' already exists; not running 'uv venv'."; \
    else \
      uv venv; \
      echo "${INFO_LABEL}running: uv pip install --requirements requirements.txt"; \
      uv pip install --requirements requirements.txt; \
    fi
```

Recall from above that `SRC_DIR` will be defined to `contrib/nguyennm1024-sociocultural-alignment` in a recursive invocation of `make` for this contribution. The `${INFO_LABEL}` is optional. It renders a bright green `INFO:` prefix, so the messages stand out. Of course, these messages are optional.

In this recipe, `uv` installs some additional dependencies in `contrib/nguyennm1024-sociocultural-alignment/.venv`, used just for this contribution, _before_ any tests are executed by building the `tests-command` target.

### How to Add Custom Targets

An optional `.targets.mk` in your contribution directory allows you to define custom targets that will be visible to the top-level `make` process. For example, you should consider adding targets to run demonstrations of your contribution. _Also add help messages for them, as mentioned above, defined in `.custom.mk`._

Here is an example adapted from `contrib/jneums-consortium-experiment/.targets.mk`:

```makefile
.PHONY: consortium-experiment ...

CONSORTIUM_EXPERIMENT_DIR := contrib/jneums-consortium-experiment

consortium-experiment::
  @echo "${INFO} Running the consortium-training experiment metrics... ${_END}"
  PYTHONPATH="${PWD}/${SRC_DIR}:${PWD}/${CONSORTIUM_EXPERIMENT_DIR}" uv run python ${CONSORTIUM_EXPERIMENT_DIR}/run.py

...
```

> [!NOTE]
> These targets are meant to be built in the top-level directory, not the contribution's directory. Also, when they are built, `${SRC_DIR}`, if used, will refer to the production code's `src` directory. This is different from how this variable is defined when content in `.custom.mk` is used, where it will be defined to be the contribution's root directory.

Because the `.targets.mk` files are included in the top level `Makefile`, the `.targets.mk` files don't need to include the top level `.common.mk`. The definitions in `.common.mk` will be visible to it.

Once you have added one or more custom targets to a `.targets.mk`, verify they work by going to the project's top level directory and running `make my_target`, such as `make consortium-experiment` in the example just shown. Or, if the target takes a long time to run, try `make -n my_target` and verify that the correct commands that _would be run_ are printed out.

## Reviewer-Friendly Checklist

Contributions are much easier to review, discuss, and eventually adopt when
they are small, runnable, and explicit about their maturity. It is preferable to submit many small PRs for a single contribution.

### Keep the Review Manageable

- Prefer several focused submissions over one large PR that mixes ideas,
  experiments, data notes, and implementation changes.
- Make the `README.md` a "travel guide" through the contribution: what
  to read first, what to run, where the important code or data pointers live,
  and what result a reviewer should expect.
- Keep code and documentation readable enough that another contributor can
  continue the work without reverse-engineering your intent.

### Explain How to Run It

Tell reviewers how to run the contribution from beginning to end:

- Required hardware, accelerators, cloud resources, credentials, datasets, or
  model downloads.
- Setup commands, environment variables, and expected working directory.
- The exact command sequence for the main demo, experiment, or analysis.
- Expected runtime, approximate resource use, and expected outputs.
- Known limitations, shortcuts, skipped steps, or non-deterministic results.

Whenever possible, automate any workflow and command with definitions in `.targets.mk`, a custom `Makefile`, and/or shell scripts, so the reviewer does not have to reconstruct the command sequence manually.

### State the Readiness Level

Be clear about the kind of contribution you are making:

- **Speculative / exploratory:** a proof of concept, research sketch,
  comparison, or early experiment. These can be lightweight, but they should
  still be runnable or clearly marked as design-only.
- **Candidate for adoption:** code that could move into the production
  `src/` or `examples/`, or documentation that could move to `docs`.
  Try to minimize the follow-up work required. Code will need good test coverage
  type checking, etc.

For code that might be adopted later, reduce integration friction:

- Follow the repository's `uv` and `make` conventions.
- Match the package/test shape used under `src/` so the contribution can be
  moved later without many small rewrites.
- Use `argparse` or an equivalent CLI framework for command-line tools, with
  helpful descriptions for every argument.
- Include automated tests for behavior that Tapestry would rely on.
- Use type annotations for (almost) everything and make sure the `type-check` target passes, as well as the other quality checks discussed above.

## Promotion to Production

The exact promotion process is **TBD**, but the skeleton is what you would
expect:

- **Who decides:** the maintainers, after discussion on an issue or the
  contribution's PR.
- **What must be true:** the "candidate for adoption" criteria above — the
  full quality gates pass without skips (`format`, `lint`, `type-check`,
  `tests`), the package/test shape matches `src/`, and the contribution has
  demonstrated value worth supporting.
- **How it happens:** a normal PR that moves the code under `src/` (or the
  material under `docs/` / `examples/`), with its tests, and updates the
  contribution's status to `Promoted` in the index above.

## Contribution Policy

Keep it simple, but please respect the following:

### Scope & Neutrality

`contrib/` is a staging area for ideas that advance Project Tapestry — not a place to advertise products or steer the project toward a single vendor or ecosystem. Even a "merged for consideration" contribution lives permanently under the AI Alliance's name, so we keep this space vendor-neutral. This mirrors the [Kubernetes Documentation Content Guide](https://kubernetes.io/docs/contribute/style/content-guide/): _"feature docs aren't a place for vendors to advertise their products."_

- **On-mission.** Contributions should be relevant to Tapestry's work (sovereign/consortium training, data governance, evaluation, supporting infrastructure). Adjacent work from other domains is welcome when it's reframed around what it teaches Tapestry — but a contribution whose _primary purpose_ is to promote an external project, product, token, or ecosystem doesn't belong here.
- **Cite, don't promote.** Reference external tools, datasets, standards, or prior work — including your own — when they're genuinely relevant (e.g. evaluation harnesses, public benchmarks, published standards). Attribute them clearly and link to a canonical source. The line isn't whether something is named; it's whether the naming is the point: no marketing language, no calls to action, and no links to commercial, rewards, airdrop, or token pages.
- **Keep it proportionate.** Examples should illustrate a principle, not serve as a portfolio. Self-references are fine as honest provenance — just keep them brief and in service of the idea, and drop a brand name entirely if the point stands without it.

If you're unsure whether something fits, open a [Discussion](https://github.com/The-AI-Alliance/tapestry/discussions) before submitting a PR.

### Licensing

Every contribution must be clearly licensed. Unless you state otherwise, Tapestry's default licenses apply:

| Content type | Default license |
| :----------- | :-------------- |
| Code | [Apache 2.0](../LICENSES/LICENSE.Apache-2.0) |
| Documentation | [CC BY 4.0](../LICENSES/LICENSE.CC-BY-4.0) |
| Data | [CDLA Permissive 2.0](../LICENSES/LICENSE.CDLA-2.0) |

If your contribution uses a different (but compatible, permissive) license, state it explicitly in your subdirectory's `LICENSE` and `README.md`. Contributions without a clear, _compatible_ license cannot be accepted.

### Copyright and Data Clearance

By opening a PR you affirm (via DCO) that:

- The contribution is **yours to give**, or you have the rights/permission to contribute it.
- It does **not** include copyrighted text, code, model weights, or data that you are not licensed to redistribute.
- Any included or referenced **datasets are cleared** for the intended use — no scraped/restricted/PII-laden data without appropriate rights and handling. When in doubt, contribute a *pointer and description* rather than the raw data, and flag any handling constraints.
- It does not violate third-party terms of service, NDAs, or export-control restrictions.

### Security

- **Do not commit secrets** — no API keys, credentials, tokens, or private endpoints.
- Don't include malicious, obfuscated, or unsafe-to-run code. Note any external dependencies or commands a reviewer would execute.
- Flag anything that touches authentication, networking, or executes untrusted input so reviewers can take a closer look.

### Conduct

All activity here follows the [AI Alliance Code of Conduct](https://github.com/The-AI-Alliance/community/blob/main/CODE_OF_CONDUCT.md) and the policies in [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## Questions / Contacts

Not sure if something fits? Do you want to discuss an idea before opening a PR? Start a [GitHub Discussion](https://github.com/The-AI-Alliance/tapestry/discussions) or reach out to the maintainers:

- **Christopher Nguyen** ([@ctn](https://github.com/ctn))
- **Dean Wampler** ([@deanwampler](https://github.com/deanwampler))
