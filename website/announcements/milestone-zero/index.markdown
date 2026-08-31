---
layout: default
title: Milestone Zero - M0
nav_order: 200
has_children: true
parent: Announcements
---

# Milestone Zero - &ldquo;M0&rdquo;

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

# Goals of Milestone Zero

As described on the [Announcement](../) page, milestone "zero" was about initial organization and consortium building. We started work in several key areas:

* Demonstrate the feasibility of _consortium training_, as defined in [Training Approaches: Centralized, Federated, and Consortium]({{site.repo_tech_docs_url}}/reference/training-approaches.md){:target="repo"} (where it is also compared to _federated learning_). M0 used two, geographically-distributed &ldquo;sovereign&rdquo; nodes (training clusters) collaborating to instruction-tune a model.
* Explore techniques for [cultural alignment]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md){:target="repo"}.
* Start defining the requirements for our data [governance]({{site.repo_tech_docs_url}}/work-groups/data-governance/data-governance-requirements.md){:target="repo"} and [management]({{site.repo_tech_docs_url}}/work-groups/data-governance/data-management-requirements.md){:target="repo"} strategy.
* Establish our software development policies and practices.

This page provides details for these work streams. Some of the M0 project teams will publish more detailed reports separately. We will update this page when more information becomes available for those reports. See also the [M0 release notes]({{site.repo_url}}/releases/tag/V0.1.0-M0){:target="m0-release"}.

# Consortium Training Proofs of Concept (PoCs)

Two separate PoCs explored consortium training techniques.

## BharatGen and Monash University

The first PoC for consortium training, [&ldquo;epic&rdquo; #189]({{site.repo_url}}/issues/189){:target="repo"}, was conducted by a joint team from [BharatGen](https://bharatgen.com/){:target="bharatgen"}, in India, and [Monash University](https://www.monash.edu/){:target="monash"}, in Australia.

The contributors to this project include the following people:

* From [BharatGen](https://bharatgen.com/){:target="bharatgen"} (and affiliated institutions): [Maneesh Kumar Singh](mailto:maneesh.singh@bharatgen.com){:target="bharatgen"}, [Bapi Chatterjee](https://github.com/bapichatterjee){:target="bharatgen"} (also Indraprastha Institute of Information Technology Delhi - IIITD), [Anant Jain](mailto:anantj@iiitd.ac.in){:target="bharatgen"} (IIITD), [Gauranshi Gupta](mailto:gauranshig@iiitd.ac.in){:target="bharatgen"} (IITD), [Mounendra De Sarkar](mailto:mounendra@cse.iith.ac.in){:target="bharatgen"} (IIT Hyderabad), [Ganesh Ramakrishnan](https://www.cse.iitb.ac.in/~ganesh/){:target="bharatgen"} (IIT Bombay), and [Samrit Kumar Maity](mailto:samritm@cdac.in){:target="bharatgen"} (CDAC, India).
* From [Monash University](https://www.monash.edu/){:target="monash"}: [Lizhen Qu](https://github.com/qulizhen){:target="monash"}, [Trang Vu](mailto:trang.vu1@monash.edu){:target="monash"}, and [Minghan Wang](mailto:minghan.wang@monash.edu){:target="monash"}

The primary objective of this PoC was to work through practical details of coordinated, distributed training between autonomous data centers (“sovereign nodes”), with the secondary goal of beginning the exploration of instruction fine tuning (IFT) to perform cultural alignment in this geo-localized consortium training setting, using a reasonably sized LLM. The team completed the primary objective and made progress on the secondary objective, too.

After demonstrating interoperability, the team did a preliminary tuning experiment. Each sovereign node, one in India and one in Australia, tuned locally with separate, culturally-specific datasets, then they did periodic merges of the weight updates (no tuning data was exchanged). As expected, they confirmed that the local updates improved the local model’s performance on the corresponding cultural behaviors, but the preliminary results also demonstrated that the improvements were retained after merging the weight updates between them to create new, shared model checkpoints.

Figure 1 shows the experimental results for this trend, where trending down is the desired behavior, as shown:

![Cultural evaluation trajectory.]({{site.baseurl}}/assets/images/m0/bharatgen-monash-figure-1.png)

<center><em>Figure 1. Cultural evaluation trajectory using the `GlobalOpinionQA` dataset.</em></center>

An explanation of this graph and the rest of the details of this work are described in [BharatGen and Monash University Consortium Training Proof of Concept](bharatgen-monash/). (It is [Figure 2 there](bharatgen-monash/#evaluation-results).)

## Consortium Training Using the Flower Labs Federated AI Framework

A second, separate PoC, [epic #184]({{site.repo_url}}/issues/184){:target="repo"}, was started using [Flower Labs'](https://flower.ai/){:target="flower"} [ federated AI framework](https://github.com/flwrlabs/flower){:target="flower"}, also applied in a consortium training configuration using two geographically-separated clusters in AWS (to simulate sovereign nodes).

[OLMo3-7B](https://allenai.org/blog/olmo3){:target="olmo"} was used (instead of OLMo2) along with the [DOLMA dataset](https://huggingface.co/datasets/allenai/dolma){:target="dolma"} to do _continued pre-training_ (CPT) from one checkpoint to a successor with the same technique of many training loops local to each node, follewed by periodic outer merges of weight updates from the nodes. This PoC explored some operational concerns for consortium training, setting the stage for Milestone One (M1), where we plan to explore how to do consortium training where some sovereign nodes run the Flower Labs stack, others run the [Slakshna](https://github.com/dcll-iiitd/Slakshna){:target="slakshna"} stack, and still other sovereign nodes that will come online might use different stacks. We hope to also explore the efficacy of consortium training running nodes on different hardware accelerator platforms.

Collaborators on this project include [Elaine Chan](https://github.com/elainechan){:target="_blank"} (independent), [Joe Olson](mailto:joe.olson@ibm.com) (IBM and The AI Alliance), [Nic Lane](mailto:nic@flower.ai) (Flower Labs), and [Patrick Foley](mailto:patrick@flower.ai) (Flower Labs).

# Cultural Alignment

The [consortium training PoC #189]({{site.repo_url}}/issues/189){:target="repo"} just discussed did instruction fine tuning using data suitable for cultural alignment purposes, but this objective wasn't its focus. Two other experiments focused on cultural alignment were performed by separate teams during M0.

## Proof of Concept for alignment based on Inglehart-Welzel Cultural Map

This feasibility study on cultural alignment shift, [Issue #22]({{site.repo_url}}/issues/22){:target="repo"}, is part of
[TAP-003: Cultural Alignment as the Primary Differentiator]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md){:target="repo"}. The team used the LoRA fine-tuning with the goal of demonstrating simultaneous (a) socio-cultural alignment shift and (b) no performance loss in general capabilities (e.g., as measured by benchmarks like MMLU (see below).

A research paper with more details about this work will be available soon. The code for this investigation can be found in the repository location [`contrib/nguyennm1024-sociocultural-alignment`]({{site.repo_url}}/tree/develop/contrib/nguyennm1024-sociocultural-alignment/){:target="repo"}. [Christopher Nguyen](mailto:ctn@aitomatic.com) (Aitomatic) is the principal investigator, with the bulk of the work performed by [William Nguyen](mailto:william@aitomatic.com) (Aitomatic), with the assistance of [Joe Olson](mailto:joe.olson@ibm.com) (IBM and The AI Alliance) and [Anthony Annunziata](mailto:anthony.annunziata@ibm.com) (IBM and The AI Alliance).

The team chose the `Llama-3.2-3B-Instruct` model because it is familiar and it is simple to post-train, due to its permissive license and the fact it is a dense model (not MoE - mixture of experts - which is a harder architecture to tune), etc. The longer-term model choice ([issue #25]({{site.repo_url}}/issues/25){:target="repo"}) will be based in part on which options provide the lowest-resistance path towards the strategic objectives of (a) high/leading performance, while (b) affording sovereignty (national, socio-cultural, industrial). Ultimately, Project Tapestry plans to train foundation models from scratch.

For this work, a capability-rehearsal corpus was used to limit catastrophic forgetting, with the culturally-aligned and rehearsal members fused via weight-space averaging (50/50). Cultural position was measured via the _Inglehart-Welzel projection method_[^6] and capability was measured using MMLU[^7].

Figure 2 shows the preliminary tuning results showing a 26% improvement:

<img width="1600" height="885" alt="Image" src="{{site.baseurl}}/assets/images/m0/fine-tuning-vietnam-june-2026.png" />

<center><em>Figure 2. Tuning moves the model on the IW Cultural Map.</em></center>

Figure 3 shows the final results, in a different representation. The end of the tuning experiment showed a 45% improvement:

<img width="1600" height="885" alt="Image" src="{{site.baseurl}}/assets/images/m0/iw_cultural_map.png" />

<center><em>Figure 3. Final tuning results with movement of the model on the IW Cultural Map.</em></center>


| Model | Distance to Vietnam (Inglehart-Welzel) | Capability (full MMLU, n=14,042, zero-shot) |
| :---- | :-------------------------------------- | :------------------------------------------- |
| Base  | 2.46 | 63.2% |
| Tuned | 1.35 - 45% closer | 62.4% (not statistically significant, McNemar p ≈ 0.07) |

<center><em>Table 1. Tuning results for the IW Cultural Map.</em></center>

The non-significance finding is a direct quote from the [Preliminary results]({{site.repo_url}}/tree/develop/contrib/nguyennm1024-sociocultural-alignment/README.md#preliminary-results) section of the README. One model, one culture, staging-quality code — but a positive directional result on the axis [TAP-003]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md) identified as the differentiator: a measurable cultural shift with no significant capability drop.

### Project Tapestry's Novel Contribution Process

By the way, this work was provided using our novel _contribution process_, which allows interested parties to contribute ideas to Tapestry in a staged way that allows them to be more carefully considered by the larger collaboration and in some cases, adopted into the &ldquo;main&rdquo; Tapestry code base. Contributions live in a special [`contrib`]({{site.repo_url}}/tree/develop/contrib/){:target="repo"} directory tree in the [Tapestry repository]({{site.repo_url}}), such as the [`contrib/nguyennm1024-sociocultural-alignment`]({{site.repo_url}}/tree/develop/contrib/nguyennm1024-sociocultural-alignment/){:target="repo"} just discussed.

## Cultural-CPT Validation Harness

A second proof of concept contribution for cultural alignment was [Cultural-CPT Validation Harness]({{site.repo_url}}/tree/develop/contrib/jneums-cultural-cpt-validation/){:target="repo"}, contributed by Jesse Neumann ([@jneums](https://github.com/jneums){:target="github"}). It builds on an earlier contribution of his, [Consortium experiment metrics]({{site.repo_url}}/tree/develop/contrib/jneums-consortium-experiment/){:target="repo"}, which adds a deterministic measurement layer around an early [consortium-training proof of concept]({{site.repo_url}}/tree/develop/src/tapestry/training/consortium/){:target="repo"}.

This project also pursues the _Inglehart-Welzel projection method_ that the `contrib/nguyennm1024-sociocultural-alignment` project pursued, but from different perspectives. The latter was an alignment _recipe_ that used LoRA SFT (supervised fine tuning) on synthesized data, evaluated against the Tao et al. projection. The former is a _validation harness_, a pre-registered, control-structured, noise-banded test of whether a measured shift is genuine, deep, and capability-safe.

This project framed its hypothesis as follows:

> **H1.** Continued pretraining on culturally grounded data produces a shift in
> the model's expressed values, measured on the Inglehart-Welzel / World Values
> Survey (WVS) framework, that is:
> - **(a) real** — larger than seed/paraphrase noise;
> - **(b) attributable to cultural content** — larger than the shift from
>   language-matched, value-neutral data in the same language;
> - **(c) representational, not surface mimicry** — visible in open-ended
>   behavior, not only in survey-answering mode;
> - **(d) capability- and safety-preserving** — does not destroy general
>   capability or erode base-model safety.

The results of this preliminary work are discussed in [`FINDINGS.md`]({{site.repo_url}}/tree/develop/contrib/jneums-cultural-cpt-validation/FINDINGS.md){:target="repo"}. In summary, using an Arabic _value-laden_ corpus was more effective at shifting the cultural metric than an Arabic corpus that is more value-neutral. However, for H1c, the effect observed was more superficial alignment, better survey-answering results, but not sufficiently deep enough to change behavior significantly. This suggests more investigation of efficacy is required to ensure cultural alignment goals are truly met.

# Other Contributions

In addition to the two contributions related to cultural alignment, [six more contributions]({{site.repo_url}}/tree/develop/contrib/){:target="repo"} explored the following:

1. [Conflict-Aware Fusion: Training a Shared Base Model to Recognize Broken Premises]({{site.repo_url}}/tree/develop/contrib/14H034160212-conflict-aware-fusion){:target="repo"}) - Techniques for ensuring that models avoid making deductions with inconsistent logical premises. (Contributor: Qiming Bao ([@14H034160212](https://github.com/14H034160212){:target="github"}))
1. [Logically-Grounded DPO: Answer-Grounded Preference Optimization for Explanation Generation]({{site.repo_url}}/tree/develop/contrib/14H034160212-logically-grounded-dpo){:target="repo"}) - Using direct preference optimization to better ensure that explanations for correct answers are accurate. (Contributor: Qiming Bao ([@14H034160212](https://github.com/14H034160212){:target="github"}))
1. [Consortium Experiment Metrics]({{site.repo_url}}/tree/develop/contrib/jneums-consortium-experiment){:target="repo"}) - (Mentioned above) Adds metric to the consortium training demonstration code. (Contributor: Jesse Neumann ([@jneums](https://github.com/jneums){:target="github"}))
1. [Flower WAN Weight-Transfer Spike]({{site.repo_url}}/tree/develop/contrib/jneums-flower-wan-spike){:target="repo"}) - Measures the overhead of model weight exchanges between sovereign nodes running the Flower Labs stack in a semi-realistic experimental setting. (Contributor: Jesse Neumann ([@jneums](https://github.com/jneums){:target="github"}))
1. [Tapestry Formal Specs (Quint)]({{site.repo_url}}/tree/develop/contrib/luzanikita-formal-spec){:target="repo"}) - Demonstrates the use of the [Quint](https://quint.sh/){:target="quint"} formal specification language for defining and enforcing logical behavior specifications. (Contributor: Mykyta Luzan ([@luzanikita](https://github.com/luzanikita){:target="github"}))
1. [Sovereign Evaluation Evidence Layer]({{site.repo_url}}/tree/develop/contrib/oli-sovereign-eval-evidence){:target="repo"}) - Proposes a small evidence layer for Tapestry's evaluation and certification work. (Contributor: Mykyta Luzan ([@welttowelt](https://github.com/welttowelt){:target="github"}))


# Data Governance and Management Requirements

We started defining the requirements for our data governance and management strategy (&ldquo;V0.1&rdquo;) and we organized work groups for these areas.

* [Data governance requirements]({{site.repo_tech_docs_url}}/work-groups/data-governance/data-governance-requirements.md){:target="repo"}
* [Data management requirements]({{site.repo_tech_docs_url}}/work-groups/data-governance/data-management-requirements.md){:target="repo"}

# Software Development Policies and Practices

Finally, we established our software development policies and practices following standard best practices for GitHub repositories ([14 issues]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM0+label%3A%22project+management%22){:target="repo"}). Of note is our novel _contribution process_, which was described [above](#project-tapestrys-novel-contribution-process).

# Final Thoughts

We wish to thank all the contributors to Tapestry for M0. Besides the collaborators listed above, many people contributed code, issues, etc. to the [Tapestry repository]({{site.repo_url}}) including [@dean-wampler](https://github.com/deanwampler){:target="_blank"}, [@ctn](https://github.com/ctn){:target="_blank"}, [@jneums](https://github.com/jneums){:target="_blank"}, [@Rohithmatham12](https://github.com/Rohithmatham12){:target="_blank"}, [@kb-bhatta](https://github.com/kb-bhatta){:target="_blank"}, [@luzanikita](https://github.com/luzanikita){:target="_blank"}, [@AnthonyJAnnunziata](https://github.com/AnthonyJAnnunziata){:target="_blank"}, [@jolson-allianceai](https://github.com/jolson-allianceai){:target="_blank"}, [@ThibautMelen](https://github.com/ThibautMelen){:target="_blank"}, [@Milian0402](https://github.com/Milian0402){:target="_blank"}, [@EC](https://github.com/EC){:target="_blank"}, [@NovusEdge](https://github.com/NovusEdge){:target="_blank"}, [@14H034160212](https://github.com/14H034160212){:target="_blank"}, [@d3v07](https://github.com/d3v07){:target="_blank"}, [@welttowelt](https://github.com/welttowelt){:target="_blank"}, [@adampingel](https://github.com/adampingel){:target="_blank"}, [@nguyennm1024](https://github.com/nguyennm1024){:target="_blank"}, [@mzkarami](https://github.com/mzkarami){:target="_blank"}, [@Amertos](https://github.com/Amertos){:target="_blank"}, [@andrewmusselman](https://github.com/andrewmusselman){:target="_blank"}, [@ArjunSrivastava1](https://github.com/ArjunSrivastava1){:target="_blank"}, [@bapichatterjee](https://github.com/bapichatterjee){:target="_blank"}, [@billbrietstout](https://github.com/billbrietstout){:target="_blank"}, [@dbckz](https://github.com/dbckz){:target="_blank"}, [@elainechan](https://github.com/elainechan){:target="_blank"}, [@JulienAu](https://github.com/JulienAu){:target="_blank"}, [@kb-bhatta](https://github.com/kb-bhatta){:target="_blank"}, [@niclane7](https://github.com/niclane7){:target="_blank"}, [@psfoley](https://github.com/psfoley){:target="_blank"}, [@Phaethon1](https://github.com/Phaethon1){:target="_blank"}, and let us not forget the ever-present `@dependabot[bot]` and `@copilot-swe-agent[bot]` :grin:.


### What's Next?

Milestone One (M1) is our next objective, covering our work from September through November, 2026. [Our M1 dashboard]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM1){:target="repo"} shows the work planned and our progress. Like M0, the major themes will be expanding our capabilities in these areas:

* [Consortium Training]({{site.repo_url}}/issues/183){:target="_blank"}
* [Cultural Alignment]({{site.repo_url}}/issues/243){:target="_blank"}
* [Data Governance and Management]({{site.repo_url}}/issues/230){:target="_blank"}

We welcome your help! See the [project README]({{site.repo_url}}){:target="repo"} for individual contributor guidance and how your organization can join Project Tapestry.

---

[^1]: OLMo Team (2025). 2 OLMo 2 Furious. [arXiv:2501.00656](https://arxiv.org/abs/2501.00656){:target="arxiv"}.
[^2]: Pham, V. T., Li, Z., Qu, L., and Haffari, G. (2025). _CultureInstruct: Curating Multi-Cultural Instructions at Scale._ In Proceedings of NAACL 2025. ([PDF](https://aclanthology.org/2025.naacl-long.465.pdf){:target="_blank"}, [dataset](https://drive.google.com/file/d/139oNuyEVdvprEIWUBuBd4BcBrWMwp0Hw/view?usp=sharing){:target="_blank"})
[^3]: BharatGen Culture WVS Dataset. ([Google Drive link](https://drive.google.com/drive/folders/1Anxb1YWUfhkla5cOBucfaRGS557VLt5m){:target="google"})
[^4]: Durmus, E. et al. (2023). _Towards Measuring the Representation of Subjective Global Opinions in Language Models._ ([arXiv:2306.16388](https://arxiv.org/abs/2306.16388){:target="arxiv"})
[^5]: Jordan, K. et al. (2024). _Muon: An optimiser for hidden layers in neural networks._ ([blog post](https://kellerjordan.github.io/posts/muon/){:target="muon"} and [repo](https://github.com/KellerJordan/Muon){:target="muon"})
[^6]: Tao, Y. et al., _Cultural Bias and Cultural Alignment of Large Language Models_, 2024. ([arxiv](https://arxiv.org/abs/2311.14096v2){:target="arxiv"})
[^7]: Hendrycks, D. et al., _Measuring Massive Multitask Language Understanding_, 2021, ([arxiv](https://arxiv.org/abs/2009.03300){:target="arxiv"}).
