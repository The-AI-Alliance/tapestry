# Contributed Ideas & Techniques (`contrib/`)

This directory is a staging area for **contributed ideas, techniques, and experiments** offered to Project Tapestry for consideration. It is intentionally lightweight: a place to share work-in-progress proposals, prototypes, notes, datasets-pointers, and references without first having to fit them into the main package or `tech-docs/` taxonomy.

Think of `contrib/` as the front porch. Promising contributions may later be promoted into `src/`, `tech-docs/`, or `examples/` after discussion and review. Material here is **not** part of the supported codebase and carries no stability guarantees.

## How to Contribute

We follow normal _GitOps_ practices (see the top-level [`CONTRIBUTING.md`](../CONTRIBUTING.md)). To add a contribution:

1. **Fork and branch** the repository.
2. **Create your own subdirectory** under `contrib/`, named with your handle/org and a short topic, e.g.:
   - `contrib/jane-doe-cultural-eval/`
   - `contrib/acme-labs-federated-tuning/`
3. **Add your contents** to that subdirectory. At minimum include:
   - A short `README.md` describing the idea, motivation, status, and how to use or evaluate it.
   - A `LICENSE` (or `LICENSE` reference) covering the contents — see [Licensing](#licensing) below.
4. **Open a Pull Request.** Keep each PR focused on a single contribution. Use the PR description to explain what you're proposing and what feedback you're looking for.
5. **Sign your commits** with DCO (`git commit -s ...`). See the [DCO section](../CONTRIBUTING.md#developer-certificate-of-origin-dco) for details.

A maintainer will review, discuss, and either request changes, merge for further consideration, or suggest a better home for the work. Merging into `contrib/` signals "accepted for consideration," not endorsement or production-readiness.

### Suggested Subdirectory Layout

```
contrib/
└── <your-handle>-<topic>/
    ├── README.md      # what it is, why, status, how to try it
    ├── LICENSE        # license for this contribution (see below)
    └── ...            # code, notes, diagrams, data pointers, etc.
```

## Contribution Policy

Keep it simple, but please respect the following:

### Licensing

Every contribution must be clearly licensed. Unless you state otherwise (compatibly), Tapestry's default licenses apply:

| Content type | Default license |
| :----------- | :-------------- |
| Code | [Apache 2.0](../LICENSE.Apache-2.0) |
| Documentation | [CC BY 4.0](../LICENSE.CC-BY-4.0) |
| Data | [CDLA Permissive 2.0](../LICENSE.CDLA-2.0) |

If your contribution uses a different (but compatible, permissive) license, state it explicitly in your subdirectory's `LICENSE` and `README.md`. Contributions without a clear, compatible license cannot be accepted.

### Copyright & Data Clearance

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

All activity here follows the [AI Alliance Code of Conduct](https://github.com/The-AI-Alliance/community/blob/main/CODE_OF_CONDUCT.md) and the policies in [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Questions / Contacts

Not sure if something fits, or want to discuss before opening a PR? Start a [GitHub Discussion](https://github.com/The-AI-Alliance/tapestry/discussions) or reach out to the maintainers:

- **Christopher Nguyen** ([@ctn](https://github.com/ctn))
- **Dean Wampler** ([@deanwampler](https://github.com/deanwampler))
