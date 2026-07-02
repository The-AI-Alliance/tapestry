# Contributed Ideas & Techniques (`contrib/`)

This directory is a staging area for **contributed ideas, techniques, and experiments** offered to Project Tapestry for consideration. It is intentionally lightweight: a place to share work-in-progress proposals, prototypes, notes, datasets-pointers, and references without first having to fit them into the main package or `docs/` taxonomy.

Think of `contrib/` as the front porch. Promising contributions may later be promoted into `src/`, `docs/`, or `examples/` after discussion and review. Material here is **not** part of the supported codebase and carries no stability guarantees.

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

```
contrib/
└── <your-handle>-<topic>/
    ├── README.md      # what it is, why, status, how to try it
    ├── LICENSE        # license for this contribution (optional - see below)
    ├── .custom.mk     # customize global make targets (optional - see below)
    ├── Makefile       # contains targets for running any custom executables (optional)
    └── ...            # code, notes, diagrams, data pointers, etc.
```

## Pass the Code Quality "Gates"

The top-level `Makefile` has a target `before-pr`, which we ask everyone to run before opening a pull request.

```shell
make before-pr
```

It verifies that all existing _production_ code under `src` is properly formatted (the `Makefile`'s `format` target), lints cleanly (the `ruff` and `pylint` targets), type checks (the `type-check` target), and the tests pass (the `tests` target). Note that all these targets are defined in `../.common.mk`.

**_By default, these same targets are built for every contribution!_** However, since `contrib` contributions are not necessarily production quality, and we want to encourage such contributions with minimal "friction", a make "protocol" is provided to customize which quality checks are skipped.

> However, if you intend for your contribution to become part of the production code, it will eventually be necessary for all the quality checks to pass for the code, including a comprehensive test suite. In this case, do as much as you can now...

First, let's describe how you can build these quality `make` targets for your contribution. First, you can just run the checks for all the contributions, although this wastes a little time. _In the top-level directory,_ run either of the following:

```shell
make do-contrib-before-pr  # run all of the checks for all contrib/*
make contrib-pylint        # run just `pylint` for all contrib/*
```

To just run checks for your contribution, let's assume it is named `contrib/johndoe-foo`, then use this command in the top-level directory to run all the quality targets:

```shell
make SRC_DIR=contrib/johndoe-foo --include-dir=contrib/johndoe-foo format ruff pylint type-check tests
```

The `SRC_DIR` definition and `--include-dir=...` shown are what the `do-contrib-before-pr` and `contrib-x` targets use to a) point to the contribution's directory and b) tell `make` to find the customization file `.custom.mk` in the same directory.

> [!TIP]
> Problems found while type checking often take the most time to fix, use this command to automatically re-run the type checker as you fix issues and save the files:
> ```shell
> make SRC_DIR=contrib/johndoe-foo --include-dir=contrib/johndoe-foo type-check-watch
> ```
> Exit using control-C.

### How to Customize the Quality Checks

You can find examples in most of the `contrib/*` directories. Customization is done by creating a `.custom.mk` file (note the leading `.`). Here is an example, `contrib/jneums-consortium-experiment/.custom.mk` (at the time of this writing):

```makefile
override define help_programs_message
For the consortium-training prototype:

make consortium-experiment
                        # Run deterministic PoC metrics for consortium-training rounds.
make consortium-tests   # Run only the consortium-training prototype tests.
endef

# This definition effectively skips the "pylint" and "type-check" targets defined
# in the top-level Makefile.
pylint-default type-check-default:
  @echo "${WARN} ${skip-contrib-target}${_END}"
  @true
```

Two of the supported customization mechanisms are shown here.

#### Help on "Programs" You Define

If you define programs that can be executed to demonstrate your contribution, you override the definition of `help_programs_message` to describe them. This message will be printed whenever the user runs `make help-programs` (a target defined in `../.common.mk`), along with similar messages for all the other contributions, if any. In this example, there are two program targets defined, `consortium-experiment` and `consortium-tests`.

Note the `override` keyword for the definition for `help_programs_message`. By default, `../.common.mk` provides an empty definition, but we override it here to customize it for this particular directory.

Try `make help-programs` in the top-level directory to see all the help messages about programs in contributions, as well as the main code base.

> [!NOTE]
> At this time, these custom make targets have to be defined in the top-level `Makefile`, but we plan to implement a mechanism that supports defining them in the contribution directory instead.

#### Disable Some Quality Checks

The second customization mechanism is shown for `pylint` and `type-check`. In this contribution, they don't currently pass (and don't really need to pass at this time). Hence, they are _disabled_ by _overriding_ the definitions of the `pylint-default` and `type-check-default` targets to print a warning message (as a reminder to the user), but not actually invoke `pylint` and `type-check`, respectively.

In `../.common.mk`, the `pylint` target is defined as follows (`type-check` is similar):

```makefile
pylint:: pylint-prerequsite pylint-default pylint-postrequisite
pylint-prerequsite pylint-postrequisite::
pylint-default:
  @echo "${INFO}$@: Running 'pylint' on the code in ${SRC_DIR}.${_END} (configuration in pylintrc.toml)"
  uv run pylint ${SRC_DIR}
```

So, if you don't override the definition of `pylint-default` in your `.custom.mk`, the definition in `../.common.mk` will be used to run `pylint` on your code.

> [!NOTE]
> Anytime you disable a quality check by overriding the definition of `x-default`, please use the commands shown in the example!

The third and fourth customization mechanisms are shown in this snippet from `../.common.mk`, but they aren't used in the `.custom.mk` file example. The `pylint-prerequisite` target does nothing by default, but if you need to do something _before_ `pylint` is invoked, you can add a definition for this target in your `.custom.mk` file. Similarly, `pylint-postrequisite` does nothing by default, but it can be defined to do work after `pylint` finishes, for example, cleaning up temporary files.

Let's look at how the prerequisite hook is used before tests are run to set up a custom environment in a different contribution, `contrib/nguyennm1024-sociocultural-alignment/`. In that directory's `.custom.mk` you will find this definition:

```makefile
unit-tests-prerequisite::
  @cd ${SRC_DIR}; \
    if [ -d .venv ]; \
    then echo "'.venv' already exists; not running 'uv venv'."; \
    else \
      uv venv; \
      echo "running: uv pip install --requirements requirements.txt"; \
      uv pip install --requirements requirements.txt; \
    fi
```

(Recall from above that `SRC_DIR` will be defined to `contrib/nguyennm1024-sociocultural-alignment` by `../.common.mk` before this target is built.) Here, `uv` installs some additional dependencies in `contrib/nguyennm1024-sociocultural-alignment/.venv`, used just for this contribution, _before_ any tests are executed by building the `tests-default` target.

> [!WARN] One or Two Trailing Colons??
>
> Did you notice that `../.common.mk` has `pylint-prerequsite::` (two trailing colons) and `pylint-default:` (one trailing colon)?? This is deliberate and reflects how we exploit the different behaviors in `make` for our purposes.
>
> When a target has two trailing colons, `make` allows _more than one_ definition of that target. This is a tool for adding additional dependencies to a target or additional commands to execute. consider this contrived example,
>
> ```makefile
> foo::
>   @echo "foo - no dependencies"
> foo:: a
>   @echo "foo - dependency: a"
> foo:: b
> a::
>   @echo "a"
> b::
>   @echo "b"
> foo::
>   @echo "finished!"
> ```
> If you run `make foo`, this is what gets printed:
> ```text
> foo - no dependencies
> a
> foo - dependency: a
> b
> finished!
> ```
> We exploit this feature to have a "no-op" default behavior for `pylint-prerequsite` and allow contributions to define any additional prerequisite behavior they want.
>
> In contrast, `pylint-default:` has one trailing colon; _the last definition overrides all previous definitions seen._ We only want a _single_ definition of this target to be used. For example,
> ```makefile
> bar:
>   @echo "bar V1!"
> bar:
>   @echo "bar V2!"
> ```
> Running `make bar` prints the following:
> ```text
> Makefile:32: warning: overriding commands for target `bar'
> Makefile:30: warning: ignoring old commands for target `bar'
> bar V2!
> ```
> Two warnings about printed about overriding a previous definition of `bar` (Ignore the line numbers shown...). We filter out these messages in our commands that use this idiom.
>
> You have to use `::` or `:` consistently for a given target or `make` will throw an error for the target definition. So, if and when you define a `x-prerequisite::`,  `x-postrequisite::`, or `x-default:` target, be careful to use one or two colons, as shown.


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

When possible, automate the workflow with scripts or a local `Makefile` so a
reviewer does not have to reconstruct the command sequence manually.

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
- Use type annotations for (almost) everything and make sure the `type-check` target passes.

### The Makefile "Contract"

If your contribution needs its own workflow commands, include a `Makefile` in your contribution directory. For consistency with the top-level `Makefile`, begin by including `../../.common.mk`. Use this `Makefile` to define your custom executables and build steps, but rely on the top-level `Makefile` for standard targets like `tests`, `lint`, etc., with possible customizations as discussed above.

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
| Code | [Apache 2.0](../LICENSE.Apache-2.0) |
| Documentation | [CC BY 4.0](../LICENSE.CC-BY-4.0) |
| Data | [CDLA Permissive 2.0](../LICENSE.CDLA-2.0) |

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
