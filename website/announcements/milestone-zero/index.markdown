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

* Demonstrate the feasibility of _consortium training_, as defined in [Training Approaches: Centralized, Federated, and Consortium]({{site.repo_tech_docs_url}}/reference/training-approaches.md){:target="repo"} (where it is also compared to _federated learning_). M0 included two PoCs (proofs of concept), each of which used two, geographically-distributed &ldquo;sovereign&rdquo; nodes (training clusters) collaborating to fine-tune a model.
* Explore techniques for [cultural alignment]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md){:target="repo"}.
* Start defining the requirements for our data [governance]({{site.repo_tech_docs_url}}/work-groups/data-governance/data-governance-requirements.md){:target="repo"} and [management]({{site.repo_tech_docs_url}}/work-groups/data-governance/data-management-requirements.md){:target="repo"} strategy.
* Establish our software development policies and practices.

This page provides details for these work streams. Some of the M0 project teams will publish more detailed reports separately. We will update this page when more information becomes available for those reports. See also the [M0 release notes]({{site.repo_url}}/releases/tag/V0.1.0-M0){:target="m0-release"}.

# Consortium Training Proofs of Concept (PoCs)

Two separate PoCs explored consortium training techniques.

## BharatGen and Monash University


The first PoC for consortium training, [“epic” #189](https://github.com/The-AI-Alliance/tapestry/issues/189){:target="issues"}, was conducted by a joint team from [BharatGen](https://bharatgen.com/){:target="bharatgen"}, in India, and [Monash University](https://www.monash.edu/){:target="monash"}, in Australia.

The contributors to this project include the following people:

* From [BharatGen](https://bharatgen.com/){:target="bharatgen"} (and affiliated institutions): [Maneesh Kumar Singh](mailto:maneesh.singh@bharatgen.com){:target="bharatgen"} (BharatGen), [Bapi Chatterjee](https://github.com/bapichatterjee){:target="bharatgen"} (BharatGen and  Indraprastha Institute of Information Technology Delhi - IIITD), [Anant Jain](mailto:anantj@iiitd.ac.in){:target="bharatgen"} (IIITD), [Gauranshi Gupta](mailto:gauranshig@iiitd.ac.in){:target="bharatgen"} (IIITD), [Mounendra Desarkar](mailto:mounendra@cse.iith.ac.in) (IIT Hyderabad), [Ganesh Ramakrishnan](https://www.cse.iitb.ac.in/~ganesh/){:target="bharatgen"} (IIT Bombay), [Piyush Sawarkar](https://in.linkedin.com/in/piyush-sawarkar){:target="bharatgen"} (BharatGen), [Aamod Thakur](https://www.linkedin.com/in/aamod-thakur?originalSubdomain=in){:target="bharatgen"} (BharatGen), [Samarth Pradhan](https://www.linkedin.com/in/samarth-pradhan-5aa668238/){:target="bharatgen"} (BharatGen, IIT Bombay), [Shubhankar Atre](https://www.linkedin.com/in/shubhankar-atre-859192b6/){:target="bharatgen"} (BharatGen, IIT Bombay), [Samrit Kumar Maity](mailto:samritm@cdac.in){:target="bharatgen"} (CDAC, India), and [Somshekhar M](https://www.linkedin.com/in/somshekar-m/){:target="bharatgen"}  (BharatGen).
* From [Monash University](https://www.monash.edu/){:target="monash"}: [Lizhen Qu](https://github.com/qulizhen){:target="monash"}, [Trang Vu](mailto:trang.vu1@monash.edu){:target="monash"}, [Minghan Wang](mailto:minghan.wang@monash.edu){:target="monash"}, [William Chien](mailto:william.chien@monash.edu){:target="monash"}, and [Reza Haffari](mailto:gholamreza.haffari@monash.edu){:target="monash"}.

The primary objective of this PoC was to work through practical details of coordinated, distributed training between autonomous data centers (“sovereign nodes”), with the secondary goal of beginning the exploration of instruction fine tuning (IFT) to perform cultural alignment in this geo-localized consortium training setting, using a reasonably sized LLM. The team completed the primary objective and made progress on the secondary objective, too.

After meeting the interoperability objectives, the team did a preliminary tuning experiment using the OLMo 2 7B model[^1]. Each sovereign node, one in India and one in Australia, tuned locally with separate, culturally-specific datasets (disjoint partitions of locally-relevant data extracted from a common dataset, CultureInstruct[^2]). They did periodic merges of compressed LoRA weight deltas (no tuning data was exchanged). As expected, they confirmed that the local updates improved the local model’s performance on the corresponding cultural behaviors.

To evaluate the effects of cultural alignment and the effects of merging model updates from the two sites, the Jensen-Shannon Distance (JSD) was measured with the `GlobalOpinionQA` [^3] (GOQA) evaluation data set. The JSD compares the model's option distribution with the available human response distribution; lower values are better.

For seven rounds of LoRA tuning, the base model was loaded plus each round's LoRA adapter (without merging adapters into full model copies). The evaluation retained 1,106 questions with at least one Australia, New Zealand, or Indian human distribution.

Figure 1 shows some of the experimental results:

![Cultural evaluation trajectory.]({{site.baseurl}}/assets/images/m0/GlobalOpinionQA-trajectory.png)

<center><em>Figure 1. GlobalOpinionQA trajectory for the base model and retained Round 1–7 adapters.</em></center>

Round 3 is the best checkpoint on the equal two-region metric and on the Australia/New Zealand component. Round 1 was narrowly best on the India component. The four checkpoints with confirmed distinct peer merges remained materially better than the base model, but none improved on Round 3. The two-region metric rose slightly from Round 3 to Round 7 while training loss continued to fall (not shown). In this short run, fitting the training data more closely therefore did not translate into monotonic improvement on GOQA.

However, these preliminary results should not be interpreted as evidence that federation harmed performance. The early rounds already contained substantial Australian local adaptation. Also, many system properties and _hyperparameters_ impact performance and all of them need to be studied in subsequent work.

The team also concluded the following:

1. **Robustness against connection instability:** Local training successfully continued even after peer disconnects, establishing an important robustness requirement for geo-distributed federated learning, that progress is tolerant to network disruptions.
2. **Making progress with asynchronous training:** The training stack is natively asynchronous. The last obtained delta is used for further synchronization and the nodes do not wait or block for deltas to be received from the peers beyond a preset maximum delay. The successful training convergence demonstrated the efficacy of the training framework.
3. **Impacts of system heterogeneity:** Although asynchrony helps, system heterogeneity plays an important role in determining the overall efficiency of federated training and requires extra care when merging weights with respect to their staleness. The GPU and networking environment on the Indian side had higher capacities than on the Australian side[^4]. Hence, the training over the available tokens on the Indian side completed in a much shorter time compared to the Australian side. This limited the number of updates exchanged between the peers, so that the Indian side didn't block. Hence, the Indian side only merged in a couple of model deltas. This indicates an area of future work: can we derive theoretical upper bounds on system heterogeneity so that before actual training we can estimate the likelihood of non-exchange of learned representations and implications for overall training progress? Despite this, we still found the robustness of the training framework prevented local training from diverging too much, even under the experiment's heterogeneity.
4. **The ratio of inner vs. outer loops:** As was expected, more frequent outer merges between environments improved the quality of training. Specifically, in two different experimental runs, the total number of passes over the available dataset was kept identical, but for the second run the number of weight synchronization rounds, i.e., outer loop merges, was *halved* while the number of inner loop steps between merges was *doubled*. This is the run shown in Figure 1 above. Note that the best value for the Australia-New Zealand number is about 0.40 in Figure 1. This is approximately 33% worse than the best value of approximately 0.29 that was observed in the first run with more frequent outer merges.

More details about their conclusions are in [this report](BharatGen_Monash_M0_Report.pdf){:target="bm"} (PDF).

## Consortium Training Using the Flower Federated Framework

This proof of concept, [epic #184](http://{{site.repo_url}}/issues/184){:target="issues"}, tested continued pre-training under the consortium learning approach and applied it to  OLMo 3 7B across two independently operated AWS GPU sites using the [Flower framework](https://github.com/flwrlabs/flower){:target="flower"}. Sites in Sydney and Virginia trained on disjoint local partitions of the [Dolma 3 mixture](https://huggingface.co/datasets/allenai/dolma3_mix-6T-1025-7B){:target="dolma"}, exchanged model parameters only, and combined their work through a coordination node in Ohio. The objective was to demonstrate that geographically separated organizations could contribute to a shared training run without moving their underlying data.

Collaborators on this project include [Elaine Chan](https://github.com/elainechan){:target="_blank"} (independent), [Joe Olson](mailto:joe.olson@ibm.com){:target="_blank"} (The AI Alliance and IBM), [Nic Lane](mailto:nic@flower.ai){:target="_blank"} (Flower Labs), [Patrick Foley](mailto:patrick@flower.ai){:target="_blank"} (Flower Labs), and [Lorenzo Sani](mailto:lorenzo@flower.ai){:target="_blank"} (Flower Labs).

### Model, Data, and Training Configuration

[OLMo 3 7B](https://huggingface.co/allenai/Olmo-3-1025-7B){:target="olmo"} is a decoder-only Transformer with 32 layers, a hidden dimension of 4,096, an intermediate dimension of 11,008, 32 attention heads, 32 key/value heads, and a vocabulary of 100,278 tokens. Although the model supports contexts of up to 65,536 tokens, the experiment used an 8,192-token sequence length.

Local training at each site ran with TorchTitan in BF16, using AdamW with an initial learning rate of 5 × 10⁻⁵, 100 warm-up steps followed by linear decay, FSDP across all eight GPUs, and selective activation checkpointing. Each optimizer step processed 400,000 tokens: a 10,000-token microbatch per GPU with five gradient-accumulation steps. Each site completed 7,500 local steps per round, or 3 billion tokens, before aggregation. Two rounds produced 6 billion tokens of training per site and 12 billion tokens across the consortium.

The already-tokenized Dolma 3 data remained at the training sites. Documents were assigned deterministically to disjoint partitions while approximately preserving the published mixture, terminated with an end-of-sequence token, and packed into 8,192-token sequences. After partitioning, no data was sent over the network during model training.

### Deployment and Model Exchange

Both the Sydney and Virginia training sites used AWS p5.48xlarge instances with 8 × NVIDIA H100 80 GB GPUs, 192 virtual CPUs, 2 TiB of host memory, and NVSwitch connectivity. The Ohio coordination node had 256 GB of memory to receive and combine the models. Measured bandwidth between Ohio and Sydney was approximately 0.53 Gbit/s upstream and 0.54 Gbit/s downstream, with 186 ms round-trip latency. Virginia reached approximately 7.9–8.9 Gbit/s upstream and 9.7 Gbit/s downstream, with 12.5 ms latency.

The communication design was adapted to these relatively slow link conditions. An initial test transferred the model layer by layer, reducing peak memory use but requiring many separate exchanges. Distributing the model to both sites took roughly 48 minutes and achieved about 164 Mbit/s across the two transfers; the repeated coordination was particularly costly on the higher-latency Sydney route. For the final run, each site instead sent its complete 14.6 GB BF16 model to Ohio in one continuous transfer. Flower aggregation averaged the two contributions equally and returned the merged weights  for the next round. This reduced latency-sensitive coordination and made round boundaries faster and more predictable. The longer local training interval (7,500 steps between exchanges) also amortized the high communication cost.

### Operational Resilience and Results

A 7,500-step local phase took approximately 19.3 hours, exceeding Flower’s default 12-hour message lifetime. Both sites nevertheless completed training and produced valid distributed checkpoints. The team extended the message lifetime to seven days and resumed directly from the saved state, avoiding another full local training phase. Checkpoints written every 1,000 steps provided clear recovery points and allowed the coordination layer to be reconfigured without losing expensive training progress.

Both sites sustained approximately 44,400 tokens per second, or 5,550 tokens per second per GPU, and their training curves tracked closely. The final aggregate checkpoint was persisted and independently verified with a cross-entropy loss of 2.28053 and perplexity of 9.78186.The training process and progress of loss and cross-entropy during training is illustrated in Figure 2. This result shows training progressing as normal despite the extreme physical distances between participating sites.

Overall, this trial demonstrated that Flower could coordinate full-parameter continued pre-training across widely separated GPU clusters while keeping training data local. It also showed that communication strategy, aggregation cadence, and checkpointing can be tuned to the infrastructure: the deployment accommodated a fifteen-fold latency difference between sites, recovered cleanly from a configuration change, and completed a reproducible two-round training run. If allowed to continue, this globally distributed topology would have reproduced the OLMo 3 7B training run after continuing pre-training from a midway starting position.

# Cultural Alignment

The [consortium training PoC #189]({{site.repo_url}}/issues/189){:target="repo"} discussed above did instruction fine tuning and evaluation using data for cultural alignment, although this objective wasn't its primary focus. Two other experiments focused on cultural alignment were performed by separate teams during M0.

## Proof of Concept for Alignment Based on Inglehart-Welzel Cultural Map

This feasibility study on cultural alignment shift, [Issue #22]({{site.repo_url}}/issues/22){:target="repo"}, is part of
[TAP-003: Cultural Alignment as the Primary Differentiator]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md){:target="repo"}. The team used the LoRA fine-tuning with the goal of demonstrating simultaneous (a) socio-cultural alignment shift and (b) no performance loss in general capabilities (e.g., as measured by benchmarks like MMLU (see below).

[Christopher Nguyen](mailto:ctn@aitomatic.com) (Aitomatic) is the principal investigator, with the bulk of the work performed by [William Nguyen](mailto:william@aitomatic.com) (Aitomatic), with the assistance of [Joe Olson](mailto:joe.olson@ibm.com) (IBM and The AI Alliance) and [Anthony Annunziata](mailto:anthony.annunziata@ibm.com) (IBM and The AI Alliance).

We summarize the results here. A research paper with more details about this work will be available soon. The code for this investigation can be found in the repository location [`contrib/nguyennm1024-sociocultural-alignment`]({{site.repo_url}}/tree/develop/contrib/nguyennm1024-sociocultural-alignment/){:target="repo"}.

The team chose the `Llama-3.2-3B-Instruct` model because it is familiar and it is simple to post-train, due to its permissive license and the fact it is a dense model (not MoE - mixture of experts - which is a harder architecture to tune), etc. The longer-term model choice ([issue #25]({{site.repo_url}}/issues/25){:target="repo"}) will be based in part on which options provide the lowest-resistance path towards the strategic objectives of (a) high/leading performance, while (b) affording sovereignty (national, socio-cultural, industrial). Ultimately, Project Tapestry plans to train foundation models from scratch.

For this work, a capability-rehearsal corpus was used to limit catastrophic forgetting, with the culturally-aligned and rehearsal members fused via weight-space averaging (50/50). Cultural position was measured via the _Inglehart-Welzel projection method_[^5] and capability was measured using MMLU[^6].

Figure 3 shows the preliminary tuning results showing a 26% improvement:

<img width="1600" height="885" alt="Image" src="{{site.baseurl}}/assets/images/m0/fine-tuning-vietnam-june-2026.png" />

<center><em>Figure 3. Tuning moves the model on the IW Cultural Map.</em></center>

Figure 4 shows the final results, in a different representation. The end of the tuning experiment showed a 45% improvement:

<img width="1600" height="885" alt="Image" src="{{site.baseurl}}/assets/images/m0/iw_cultural_map.png" />

<center><em>Figure 4. Final tuning results with movement of the model on the IW Cultural Map.</em></center>


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

# Acknowledgements

We wish to thank all the contributors to Tapestry for M0. Besides the collaborators listed above, many people contributed code, issues, etc. to the [Tapestry repository]({{site.repo_url}}) including [@dean-wampler](https://github.com/deanwampler){:target="_blank"}, [@ctn](https://github.com/ctn){:target="_blank"}, [@jneums](https://github.com/jneums){:target="_blank"}, [@Rohithmatham12](https://github.com/Rohithmatham12){:target="_blank"}, [@kb-bhatta](https://github.com/kb-bhatta){:target="_blank"}, [@luzanikita](https://github.com/luzanikita){:target="_blank"}, [@AnthonyJAnnunziata](https://github.com/AnthonyJAnnunziata){:target="_blank"}, [@jolson-allianceai](https://github.com/jolson-allianceai){:target="_blank"}, [@ThibautMelen](https://github.com/ThibautMelen){:target="_blank"}, [@Milian0402](https://github.com/Milian0402){:target="_blank"}, [@EC](https://github.com/EC){:target="_blank"}, [@NovusEdge](https://github.com/NovusEdge){:target="_blank"}, [@14H034160212](https://github.com/14H034160212){:target="_blank"}, [@d3v07](https://github.com/d3v07){:target="_blank"}, [@adampingel](https://github.com/adampingel){:target="_blank"}, [@nguyennm1024](https://github.com/nguyennm1024){:target="_blank"}, [@mzkarami](https://github.com/mzkarami){:target="_blank"}, [@Amertos](https://github.com/Amertos){:target="_blank"}, [@andrewmusselman](https://github.com/andrewmusselman){:target="_blank"}, [@ArjunSrivastava1](https://github.com/ArjunSrivastava1){:target="_blank"}, [@bapichatterjee](https://github.com/bapichatterjee){:target="_blank"}, [@billbrietstout](https://github.com/billbrietstout){:target="_blank"}, [@dbckz](https://github.com/dbckz){:target="_blank"}, [@elainechan](https://github.com/elainechan){:target="_blank"}, [@JulienAu](https://github.com/JulienAu){:target="_blank"}, [@kb-bhatta](https://github.com/kb-bhatta){:target="_blank"}, [@niclane7](https://github.com/niclane7){:target="_blank"}, [@psfoley](https://github.com/psfoley){:target="_blank"}, [@Phaethon1](https://github.com/Phaethon1){:target="_blank"}, and let us not forget the ever-present `@dependabot[bot]` and `@copilot-swe-agent[bot]` :grin:.

Special thanks to [Dean Wampler](mailto:dwampler@thealliance.ai){:target="aia"} (IBM / AI Alliance) for coordinating contributions, releases, and leading working groups, [Kaushik Bhatta](mailto:kb@b3alliance.com){:target="aia"} (B3 Alliance / AI Alliance) for recruiting partners, sovereign nodes, and compute resources, and [Agata Ferretti](mailto:aferretti@thealliance.ai){:target="aia"} (IBM / AI Alliance) for work with EMEA partners. [Anthony Annunziata](mailto:aannunziata@thealliance.ai){:target="aia"} (IBM / AI Alliance) provides overall Project Tapestry and AI Alliance leadership, [Christopher Nguyen](mailto:ctn@aitomatic.com){:target="atomatic"} (Aitomatic) is the lead architect for Project Tapestry, and [Yann Lecun](http://yann.lecun.com/){:target="yann"} (AMI Labs, Turing Award winner) provided the inspiration for Project Tapestry.

## What's Next?

Milestone One (M1) is our next objective, covering our work from September through November, 2026. [Our M1 dashboard]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM1){:target="repo"} shows the work planned and our progress. Like M0, the major themes will be expanding our capabilities in these areas:

* [Consortium Training]({{site.repo_url}}/issues/183){:target="_blank"}
* [Cultural Alignment]({{site.repo_url}}/issues/243){:target="_blank"}
* [Data Governance and Management]({{site.repo_url}}/issues/230){:target="_blank"}

We welcome your help! See the [project README]({{site.repo_url}}){:target="repo"} for individual contributor guidance and how your organization can join Project Tapestry.

---

[^1]:  OLMo Team (2025). 2 OLMo 2 Furious. ([arXiv:2501.00656](https://arxiv.org/abs/2501.00656)) The team had done prior work with this model, which is why a comparable OLMo 3 model wasn’t used. For their purposes, using the most recent model wasn’t essential.

[^2]:  Pham, V. T., Li, Z., Qu, L., and Haffari, G. (2025). *CultureInstruct: Curating Multi-Cultural Instructions at Scale.* In Proceedings of NAACL 2025\. ([PDF](https://aclanthology.org/2025.naacl-long.465.pdf), [dataset](https://drive.google.com/file/d/139oNuyEVdvprEIWUBuBd4BcBrWMwp0Hw/view?usp=sharing))

[^3]:  Durmus, E. et al. (2023). *Towards Measuring the Representation of Subjective Global Opinions in Language Models.* ([arXiv:2306.16388](https://arxiv.org/abs/2306.16388))

[^4]:  Two H200 GPUs (VRAM: 141 GB HBM3e apiece, Memory Bandwidth: 4.8 TB/s, Up to 1,671–1,979 TFlop/s per GPU) on the Indian side, versus two A100 GPUs (VRAM: 80 GB HBM apiece, Up to 312 TFlop/s per GPU). The Indian side had much higher network bandwidth, too.

[^5]: Tao, Y. et al., _Cultural Bias and Cultural Alignment of Large Language Models_, 2024. ([arxiv](https://arxiv.org/abs/2311.14096v2){:target="arxiv"})

[^6]: Hendrycks, D. et al., _Measuring Massive Multitask Language Understanding_, 2021, ([arxiv](https://arxiv.org/abs/2009.03300){:target="arxiv"}).
