---
layout: default
title: Home
nav_order: 10
has_children: true
---

# Project Tapestry: Technical Website

Welcome to the technical website for **The AI Alliance Project Tapestry**, representing the content from the [technical documentation and code repository]({{site.repo_url}}){:target="repo"} for [Project Tapestry]({{site.tapestry_url}}){:target="aia-tapestry"}.

{: .attention}
> For a general introduction to Project Tapestry, including its motivations and goals, see the [AI Alliance website Tapestry page]({{site.tapestry_url}}){:target="aia-tapestry"}

![Project Tapestry Image]({{site.baseurl}}/assets/images/03-tapestry-logo-1000x545.png){: .tapestry-image .center}

The AI Alliance [launched](https://thealliance.ai/blog/ai-alliance-launches-project-tapestry-to-build-a-collaborative-foundation-for-open-and-sovereign-ai){:target="blog"} Project Tapestry to build a collaborative foundation for open and sovereign AI. Project Tapestry is an open-source platform designed to enable globally federated development of frontier, open models while preserving sovereignty, local control, and long-term independence.

**Why this matters:** People will not use models that under perform on their language, legal context, and domain knowledge. And countries, enterprises, and individuals need AI infrastructure they own and control — with guaranteed data residency, the right to exit, and the ability to operate independently. Tapestry addresses both problems simultaneously: sovereignty is the performance strategy, not a trade-off against it.

{: .note }
> * **Join Us!** We are looking for collaborators. See our [contributing]({{site.baseurl}}/contributing) page for details.
> * Use the search box at the top of this page to find specific content.
> * The links for Capitalized Terms go to [this glossary]({{site.glossary_url}}){:target="_glossary"}. Tapestry-specific terms (e.g., *Consortium training*, *Shared-Base Loop*, *Sovereign Build*) are defined in the [in-repo glossary]({{site.repo_tech_docs_url}}/reference/glossary.md){:target="repo-docs"}.
 
This website is for technical contributors. As Project Tapestry evolves, this website will provide links to technical requirements, architecture and design documentation, and implementation source code.

## Contribute to Our First Work Streams

Project Tapestry has big plans. Here are the main areas of current focus.

* [LLM Cultural Alignment and Re-alignment]({{site.repo_url}}/issues/243){:target="issues"} - Help us develop techniques for cultural alignment, initially based on the [Inglehart–Welzel Cultural Map](https://en.wikipedia.org/wiki/Inglehart%E2%80%93Welzel_cultural_map_of_the_world){:target="iwcm"} as a metric, with more approaches to be added. This effort will continue to explore how to shift _cultural alignment_ without compromising general model performance. Prior expertise in evaluation and tuning technologies are especially welcome.
* [Consortium Training]({{site.repo_url}}/issues/183){:target="issues"} - Tapestry's approach to global model development relies on a balance between centralized and distributed training that ensures permissive use and privacy requirements for datasets. Help us adapt and develop optimal techniques with ideas from both federated learning and the latest LLM pre-training and post-training methods. Prior expertise in large scale LLM training, distributed infrastructure, and federated learning are especially welcome. In particular, we are starting to create domain-specific models, and we need expertise in healthcare, finance, industrial technologies, etc.
* [Data, Responsibly Used]({{site.repo_url}}/issues/230){:target="issues"} - Help us define the requirements for permissive use and privacy requirements for datasets, then implement them.
  * [Global Training Data Corpus](https://thealliance.ai/projects/tapestry/training-data-proposals){:target="_blank"}  - A core thesis of project Tapestry is that bringing together a much more diverse set of data can provide a path to a better frontier base model for all. What unique datasets exist that could be brought to Tapestry model training? They don't have to be fully open; we will work with you to define and enforce appropriate requirements.
* Your good ideas - Our [contribution mechanism]({{site.repo_tech_docs_url}}/contrib/#how-to-contribute){:target="repo-docs"} provides a way for you to suggest new technologies, solutions to design challenges we face, etc.

## Project Tapestry Work Groups

Tapestry is designed with data sovereignty requirements first and foremost, leading to new approaches for distributed model training to build world-class foundation models, as well as support tuning domain-specific models using sensitive data with carefully governed access.

The following work groups are provisional. [Participation is welcome!]({{site.baseurl}}/contributing)

| Work Group | Focus |
| :--------- | :---- |
| [Base Model Training]({{site.repo_tech_docs_url}}/work-groups/base-model-training/){:target="repo-docs"} | Own the shared model capability path: selecting or adopting an initial open-weights base, defining how [consortium training]({{site.repo_tech_docs_url}}/reference/training-approaches.md) improves shared weights, and planning the transition toward consortium-owned base models when the project has sufficient compute, data, and operational maturity. |
| [Data Governance]({{site.repo_tech_docs_url}}/work-groups/data-governance/){:target="repo-docs"} | Define how sovereign data can participate in Tapestry without surrendering control. This group owns data sourcing, licensing, stewardship, residency constraints, provenance, contribution rights, and data-quality expectations for national, cultural, industrial, and institutional participants. |
| [Deployment and Adoption]({{site.repo_tech_docs_url}}/work-groups/deployment-adoption/){:target="repo-docs"} | Ensure Tapestry-derived models become usable systems, not just trained weights. This group owns serving patterns, product harnesses, integration guidance, participant rollout, developer experience, and adoption feedback loops. |
| [Evaluation Certification]({{site.repo_tech_docs_url}}/work-groups/evaluation-certification/){:target="repo-docs"} | Define the evidence that Tapestry models, pipelines, and participants must produce before claims of capability, sovereignty, cultural alignment, safety, or certification are accepted. |
| [Governance and Participation]({{site.repo_tech_docs_url}}/work-groups/governance-participation/){:target="repo-docs"} | Translate Tapestry's governance principles into operating mechanics for work groups, participants, contributions, decisions, certification processes, and anti-capture safeguards. |
| [Infrastructure and Operations]({{site.repo_tech_docs_url}}/work-groups/infrastructure-operations/){:target="repo-docs"} | Own the platform and operating model that lets participants run Tapestry workloads across heterogeneous compute, networks, security regimes, and organizational boundaries. |
| [Security and Privacy]({{site.repo_tech_docs_url}}/work-groups/security-privacy/){:target="repo-docs"} | Define the technical guarantees that make Tapestry sovereignty enforceable: privacy tiers, secure aggregation, differential privacy, trusted execution, threat models, model-update leakage analysis, and safety-preservation constraints. |
| [Sovereign Alignment]({{site.repo_tech_docs_url}}/work-groups/sovereign-alignment/){:target="repo-docs"} | Own the participant-specific pipeline that turns a shared capable base into models that reflect local knowledge, values, institutions, domains, and interaction norms. This includes culturally grounded continued pretraining, post-training alignment, instruction tuning, and portability of sovereign contributions. |

## Other Technical Documentation

The rest of the technical documentation is currently maintained in the project repository [`docs`]({{site.repo_tech_docs_url}}/){:target="repo-docs"}:

* [Architecture]({{site.repo_tech_docs_url}}/architecture/){:target="repo-docs"}:
  * [Architecture Decision Records]({{site.repo_tech_docs_url}}/architecture/decisions/){:target="repo-docs"}:
* [Governance]({{site.repo_tech_docs_url}}/governance/){:target="repo-docs"}:
* [Reference]({{site.repo_tech_docs_url}}/reference/){:target="repo-docs"}:
* [Strategic Plan]({{site.repo_tech_docs_url}}/strategic-plan/){:target="repo-docs"}

## Additional links

Some additional links.

* [Contributing]({{site.baseurl}}/contributing): We welcome your contributions! Here's how you can contribute.
* [About Us]({{site.baseurl}}/about): More about the AI Alliance and this project.
* [Project GitHub Repo]({{site.repo_url}}){:target="repo"}
* [The AI Alliance](https://www.thealliance.ai){:target="aia"}: The AI Alliance website.

---

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>
