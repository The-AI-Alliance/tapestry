---
layout: default
title: Announcements
nav_order: 20
has_children: true
has_grand_children: true
---

# Project Tapestry - Announcements

This section contains announcements about releases and other notable updates. See also the Tapestry repository's [Releases]({{site.repo_url}}/releases){:target="repo"} page,  announcements posted on the [Project Tapestry]({{site.tapestry_url}}){:target="aia-tapestry"} website, and the AI Alliance [blog](https://thealliance.ai/blog).

## Milestone Releases

Project Tapestry is managed on a three-month _milestone_ cycle, offset by one month so we don't have milestones ending during the holiday period at the end of December each year. Hence, this is our milestone schedule, through the end of 2027, with a summary of the goals for each past milestone and planned goals for each future milestone.

| Name | Abbrev. | Dates |
| :--- | :------ | :---- |
| [Milestone Zero](#milestone-zero-m0) | M0 | June - August, 2026 |
| [Milestone One](#milestone-one-m1)   | M1 | September - November, 2026 |
| [Milestone Two](#milestone-two-m2)   | M2 | December, 2026 - February, 2027 |
| Milestone Three                      | M3 | March - May, 2027 |
| Milestone Four                       | M4 | June - August, 2027 |
| Milestone Five                       | M5 | September - November, 2027 |

### Milestone Zero ("M0")

| :-- | :-- |
| **Dates**     | June - August, 2026 |
| **Details**   | [Milestone Zero - M0](./milestone-zero/) |
| **Release**   | [v0.1.0-M0]({{site.repo_url}}/releases/tag/v0.1.0-M0){:target="m0-release"} |
| **Dashboard** | [Tapestry Project - M0]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM0){:target="dash"}

This milestone was labelled "zero", because this period was about initial organization and consortium building. We demonstrated basic concepts of [consortium training]({{site.repo_tech_docs_url}}/reference/training-approaches.md) using two, geographically-distributed &ldquo;sovereign&rdquo; nodes (training clusters) collaborating to train a model. Other work in M0 explored the efficacy of [cultural alignment]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md) techniques, started defining requirements and work groups for our ambitious data governance and management strategy, and established our development policies and practices.

### Milestone One ("M1")

| :-- | :-- |
| **Dates**     | September - November, 2026 |
| **Details**   | TBD |
| **Release**   | TBD |
| **Dashboard** | [Tapestry Project - M1]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM1){:target="dash"}

M1 is building on the prototype work of M0 to expand the number of sovereign nodes, increase the available compute resources, explore the feasibility and limits of heterogeneous trainings (different hardware and software stacks), beginning building cultural alignment tools and techniques, and implement the first data governance, management, and processing capabilities. A primary goal is to tune an existing open-weights model to create a very capable model targeted at a particular domain and set of use cases.


### Milestone Two ("M2")

| :-- | :-- |
| **Dates**     | December, 2026 - February, 2027 |
| **Details**   | TBD |
| **Release**   | TBD |
| **Dashboard** | [Tapestry Project - M1]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM2){:target="dash"}

In the M2 time frame, we plan to complete an end-to-end, production quality and globally-distributed training and post-training infrastructure and software stack, with further progress on building domain-specific and culturally-specific models, based on open-weight models. We also plan to complete preparation for training our own foundation models &ldquo;from scratch&rdquo; and to begin that process.

---

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>
