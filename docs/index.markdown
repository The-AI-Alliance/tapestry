---
layout: default
title: Home
nav_order: 10
has_children: false
tech_docs: https://github.com/The-AI-Alliance/tapestry/tree/main/tech-docs/work-groups/
---

# Project Tapestry: Technical Website

Welcome to the technical website for **The AI Alliance Project Tapestry**, representing the content from the [technical documentation and code repository](https://github.com/The-AI-Alliance/tapestry){:target="repo"} for [Project Tapestry](https://thealliance.ai/projects/tapestry){:target="aia-tapestry"}. 

{: .attention}
> For a general introduction to Project Tapestry, including its motivations and goals, see the [AI Alliance website Tapestry page](https://thealliance.ai/projects/tapestry){:target="aia-tapestry"}

![Project Tapestry Image]({{site.baseurl}}/assets/images/03-tapestry-logo-1000x545.png){: .tapestry-image .center}

The AI Alliance [launched](https://thealliance.ai/blog/ai-alliance-launches-project-tapestry-to-build-a-collaborative-foundation-for-open-and-sovereign-ai){:target="blog"} Project Tapestry to build a collaborative foundation for open and sovereign AI. Project Tapestry is an open-source platform designed to enable globally federated development of frontier, open models while preserving sovereignty, local control, and long-term independence.

**Why this matters:** People will not use models that underperform on their language, legal context, and domain knowledge. And countries, enterprises, and individuals need AI infrastructure they own and control — with guaranteed data residency, the right to exit, and the ability to operate independently. Tapestry addresses both problems simultaneously: sovereignty is the performance strategy, not a trade-off against it.

{: .note }
> * **Join Us!** We are looking for collaborators. See our [contributing]({{site.baseurl}}/contributing) page for details.
> * Use the search box at the top of this page to find specific content.
> * The links for Capitalized Terms go to [this glossary]({{site.glossaryurl}}){:target="_glossary"}.
 
This website is for technical contributors. As Project Tapestry evolves, this website will provide links to technical requirements, architecture and design documentation, and implementation source code.

Watch for announcements over the coming months about Project Tapestry’s architecture, roadmap, and model development priorities. 

## Project Tapestry Work Groups

Tapestry is designed with data sovereignty requirements first and foremost, leading to new approaches for distributed model training to build world-class foundation models, as well as support tuning domain-specific models using sensitive data with carefully governed access.

Work groups are organized in two tracks — requirements groups that define what must be built, and engineering groups that build it. [Participation is welcome!]({{site.baseurl}}/contributing)

### Requirements Work Groups

These groups identify and prioritize what Tapestry must do.

| Work Group | Focus |
|---|---|
| [Data Requirements]({{page.tech_docs}}/work-groups/data-requirements/){:target="repo-tech-docs"} | Data sovereignty, governance, and management requirements across national, cultural, and industrial sovereignty |
| [Model Training Requirements]({{page.tech_docs}}/work-groups/model-training-requirements/){:target="repo-tech-docs"} | Federated and distributed training requirements that satisfy data sovereignty constraints |
| [Evaluation Requirements]({{page.tech_docs}}/work-groups/evaluation-requirements/){:target="repo-tech-docs"} | Evaluation frameworks for both performance and sovereignty compliance |
| [Infrastructure Requirements]({{page.tech_docs}}/work-groups/infrastructure-requirements/){:target="repo-tech-docs"} | Infrastructure requirements for sovereign node deployment and federated operation |

### Engineering Work Groups

These groups design and implement what the requirements groups specify.

| Work Group | Focus |
|---|---|
| [Data Engineering]({{page.tech_docs}}/work-groups/data-engineering/){:target="repo-tech-docs"} | Data pipelines, sovereignty enforcement, and data management infrastructure |
| [Model Training Engineering]({{page.tech_docs}}/work-groups/model-training-engineering/){:target="repo-tech-docs"} | Federated training stack, privacy-preserving aggregation, and distributed training infrastructure |
| [Evaluation Engineering]({{page.tech_docs}}/work-groups/evaluation-engineering/){:target="repo-tech-docs"} | Evaluation tooling for domain performance and sovereignty compliance |
| [Infrastructure Engineering]({{page.tech_docs}}/work-groups/infrastructure-engineering/){:target="repo-tech-docs"} | Sovereign node infrastructure, deployment tooling, and operational systems |

## Other Technical Documentation

See also the following sections in the technical documentation:

* [Architectural Decision Records]({{page.tech_docs}}/adr/){:target="repo-tech-docs"}
* [Strategic Plan]({{page.tech_docs}}/strategic-plan/){:target="repo-tech-docs"}
* [Tapestry Reference]({{page.tech_docs}}/tapestry-reference/){:target="repo-tech-docs"}

## Additional links

Some additional links.

* [Contributing]({{site.baseurl}}/contributing): We welcome your contributions! Here's how you can contribute.
* [About Us]({{site.baseurl}}/about): More about the AI Alliance and this project.
* [Project GitHub Repo](https://github.com/The-AI-Alliance/tapestry){:target="repo"}
* [The AI Alliance](https://www.aialliance.org){:target="aia"}: The AI Alliance website.

---

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>
