---
layout: default
title: Home
nav_order: 10
has_children: false
tech_docs: https://github.com/The-AI-Alliance/tapestry/tree/develop/tech-docs
---

# Project Tapestry: Technical Website

Welcome to the technical website for **The AI Alliance Project Tapestry**, representing the content from the [technical documentation and code repository](https://github.com/The-AI-Alliance/tapestry){:target="repo"} for [Project Tapestry]({{site.tapestryurl}}){:target="aia-tapestry"}. 

{: .attention}
> For a general introduction to Project Tapestry, including its motivations and goals, see the [AI Alliance website Tapestry page]({{site.tapestryurl}}){:target="aia-tapestry"}

![Project Tapestry Image]({{site.baseurl}}/assets/images/03-tapestry-logo-1000x545.png){: .tapestry-image .center}

The AI Alliance [launched](https://thealliance.ai/blog/ai-alliance-launches-project-tapestry-to-build-a-collaborative-foundation-for-open-and-sovereign-ai){:target="blog"} Project Tapestry to build a collaborative foundation for open and sovereign AI. Project Tapestry is an open-source platform designed to enable globally federated development of frontier, open models while preserving sovereignty, local control, and long-term independence.

**Why this matters:** People will not use models that underperform on their language, legal context, and domain knowledge. And countries, enterprises, and individuals need AI infrastructure they own and control — with guaranteed data residency, the right to exit, and the ability to operate independently. Tapestry addresses both problems simultaneously: sovereignty is the performance strategy, not a trade-off against it.

{: .note }
> * **Join Us!** We are looking for collaborators. See our [contributing]({{site.baseurl}}/contributing) page for details.
> * Use the search box at the top of this page to find specific content.
> * The links for Capitalized Terms go to [this glossary]({{site.glossaryurl}}){:target="_glossary"}. Tapestry-specific terms (e.g., *Consortium training*, *Shared-Base Loop*, *Sovereign Build*) are defined in the [in-repo glossary]({{page.tech_docs}}/reference/glossary.md){:target="repo-tech-docs"}.
 
This website is for technical contributors. As Project Tapestry evolves, this website will provide links to technical requirements, architecture and design documentation, and implementation source code.

Watch for announcements over the coming months about Project Tapestry’s architecture, roadmap, and model development priorities. 

## Project Tapestry Work Groups

Tapestry is designed with data sovereignty requirements first and foremost, leading to new approaches for distributed model training to build world-class foundation models, as well as support tuning domain-specific models using sensitive data with carefully governed access.

The following work groups are provisional. [Participation is welcome!]({{site.baseurl}}/contributing)

| Work Group | Focus |
| :--------- | :---- |
| [Base Model Training]({{page.tech_docs}}/work-groups/base-model-training/){:target="repo-tech-docs"} | Own the shared model capability path: selecting or adopting an initial open-weights base, defining how consortium training improves shared weights, and planning the transition toward consortium-owned base models when the project has sufficient compute, data, and operational maturity. |
| [Data Governance]({{page.tech_docs}}/work-groups/data-governance/){:target="repo-tech-docs"} | Define how sovereign data can participate in Tapestry without surrendering control. This group owns data sourcing, licensing, stewardship, residency constraints, provenance, contribution rights, and data-quality expectations for national, cultural, industrial, and institutional participants. |
| [Deployment and Adoption]({{page.tech_docs}}/work-groups/deployment-adoption/){:target="repo-tech-docs"} | Ensure Tapestry-derived models become usable systems, not just trained weights. This group owns serving patterns, product harnesses, integration guidance, participant rollout, developer experience, and adoption feedback loops. |
| [Evaluation Certification]({{page.tech_docs}}/work-groups/evaluation-certification/){:target="repo-tech-docs"} | Define the evidence that Tapestry models, pipelines, and participants must produce before claims of capability, sovereignty, cultural alignment, safety, or certification are accepted. |
| [Governance and Participation]({{page.tech_docs}}/work-groups/governance-participation/){:target="repo-tech-docs"} | Translate Tapestry's governance principles into operating mechanics for work groups, participants, contributions, decisions, certification processes, and anti-capture safeguards. |
| [Infrastructure and Operations]({{page.tech_docs}}/work-groups/infrastructure-operations/){:target="repo-tech-docs"} | Own the platform and operating model that lets participants run Tapestry workloads across heterogeneous compute, networks, security regimes, and organizational boundaries. |
| [Security and Privacy]({{page.tech_docs}}/work-groups/security-privacy/){:target="repo-tech-docs"} | Define the technical guarantees that make Tapestry sovereignty enforceable: privacy tiers, secure aggregation, differential privacy, trusted execution, threat models, model-update leakage analysis, and safety-preservation constraints. |
| [Sovereign Alignment]({{page.tech_docs}}/work-groups/sovereign-alignment/){:target="repo-tech-docs"} | Own the participant-specific pipeline that turns a shared capable base into models that reflect local knowledge, values, institutions, domains, and interaction norms. This includes culturally grounded continued pretraining, post-training alignment, instruction tuning, and portability of sovereign contributions. |

## Other Technical Documentation

The rest of the technical documentation is currently maintained in the project repository [`tech-docs`]({{page.tech_docs}}/){:target="repo-tech-docs"}:

* [Architecture]({{page.tech_docs}}/architecture/){:target="repo-tech-docs"}:
  * [Architecture Decision Records]({{page.tech_docs}}/architecture/decisions/){:target="repo-tech-docs"}:
* [Governance]({{page.tech_docs}}/governance/){:target="repo-tech-docs"}:
* [Reference]({{page.tech_docs}}/reference/){:target="repo-tech-docs"}:
* [Strategic Plan]({{page.tech_docs}}/strategic-plan/){:target="repo-tech-docs"}

## Additional links

Some additional links.

* [Contributing]({{site.baseurl}}/contributing): We welcome your contributions! Here's how you can contribute.
* [About Us]({{site.baseurl}}/about): More about the AI Alliance and this project.
* [Project GitHub Repo](https://github.com/The-AI-Alliance/tapestry){:target="repo"}
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
