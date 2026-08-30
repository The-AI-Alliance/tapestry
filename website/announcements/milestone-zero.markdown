---
layout: default
title: Milestone Zero - M0
nav_order: 200
has_children: false
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

This page provides more details. See also the [M0 release notes]({{site.repo_url}}/releases/tag/V0.1.0-M0){:target="m0-release"}.

# Consortium Training Proofs of Concept (PoCs)

Two separate PoCs explored consortium training techniques.

## BharatGen and Monash University

The main PoC for consortium training, [&ldquo;epic&rdquo; #189]({{site.repo_url}}/issues/189){:target="repo"}, was conducted by a joint team from [BharatGen](https://bharatgen.com/){:target="bharatgen"}, in India, and [Monash University](https://www.monash.edu/){:target="monash"}, in Australia.

The primary objective of this PoC was to work through practical details of coordinated, distributed training between autonomous data centers (“sovereign nodes”), with the secondary goal of beginning the exploration of instruction fine tuning (IFT) to perform cultural alignment in this geo-localized consortium training setting, using a reasonably sized LLM. The team completed the primary objective and made progress on the secondary objective, too.

After demonstrating interoperability, the team did a preliminary tuning experiment. Each sovereign node, one in India and one in Australia, tuned locally with separate, culturally-specific datasets, then they did periodic merges of the weight updates (no tuning data was exchanged). As expected, they confirmed that the local updates improved the local model’s performance on the corresponding cultural behaviors, but the preliminary results also demonstrated that the improvements were retained after merging the weight updates between them to create new, shared model checkpoints.

The contributors to this project include the following:

* From [BharatGen](https://bharatgen.com/){:target="bharatgen"} (and affiliated institutions): [Maneesh Kumar Singh](mailto:maneesh.singh@bharatgen.com){:target="bharatgen"}, [Bapi Chatterjee](https://github.com/bapichatterjee){:target="bharatgen"} (also Indraprastha Institute of Information Technology Delhi - IIITD), [Anant Jain](mailto:anantj@iiitd.ac.in){:target="bharatgen"} (IIITD), [Gauranshi Gupta](mailto:gauranshig@iiitd.ac.in){:target="bharatgen"} (IITD), [Mounendra De Sarkar](mailto:mounendra@cse.iith.ac.in){:target="bharatgen"} (IIT Hyderabad), [Ganesh Ramakrishnan](https://www.cse.iitb.ac.in/~ganesh/){:target="bharatgen"} (IIT Bombay), and [Samrit Kumar Maity](mailto:samritm@cdac.in){:target="bharatgen"} (CDAC, India).
* From [Monash University](https://www.monash.edu/){:target="monash"}: [Lizhen Qu](https://github.com/qulizhen){:target="monash"}, [Trang Vu](mailto:trang.vu1@monash.edu){:target="monash"}, and [Minghan Wang](mailto:minghan.wang@monash.edu){:target="monash"}

### Experimental Setup

The team deployed BharatGen's [Slakshna](https://github.com/dcll-iiitd/Slakshna){:target="slakshna"} stack for &ldquo;geo-localized, decentralised, secure federated learning&rdquo; in two, small, geographically-separated GPU clusters, one in each organization. The team initially verified the stack's connectivity across India and Australia by fine-tuning the LLama 1.1B model for several epochs. This step completed the primary objective for M0.

Then the team performed a distributed run of instruction fine tuning of the OLMo 2 7B model[^1], where they evaluated the efficacy of local training loops with periodic &ldquo;outer loops&rdquo; of model weight merging between them. They confirmed that the loss function behaved as expected, monotonically decreasing with no signs of instability that could have emerged due to the distributed process of the local, independent training loops combined with periodic &ldquo;outer loop&rdquo; weight merges. Note that no training data was exchanged in these outer loop merges, only model weights.

OLMo 2 7B was chosen because the full details about its architecture, such as how it was trained, the data sets used, etc. are publicly available, which makes experimentation with the model family comparatively easy. Also, OLMo 2 7B was used in previous work by some of the team members, discussed next, for which this PoC was a natural extension.

### Experimental Data

The `CultureInstruct` dataset[^2] was used, which was previously developed by Monash University. It contains data from multiple countries. The dataset was split into three main parts, with subdivision of one of those parts:

| Partition | # Samples | # Tokens | Used By/For | Description |
| :-------- | --------: | -------: | :---------- | :---------- |
| **South Asia** | 15K | 4.2M | BharatGen | Data labeled for south Asian countries. including Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan, and Sri Lanka. |
| **Out-of-South-Asia** | 294K | 75.0M | Monash Univ. | We can split this part further by region. We estimate the Oceania region (Australia and New Zealand) has around 13K samples, 3.5M tokens. We exploited this knowledge to form useful subsets: |
| _(i) Australia and NZ only_ | 13K | 3.5M | | The 13K samples is roughly equal to BharatGen's 15K samples, which isolates cross-site behaviour from data-imbalance effects. |
| _(ii) Australia, NZ, and Western Europe_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| _(iii) Australia, NZ, and US, Canada, and UK_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| **Unlabeled** | 158K | 30M | Hyperparameter tuning | Culture-relevant instructions without a country label. Whether this pool is held out, mixed into both nodes as shared data, or excluded from M0 is TBD. |

<center><em>Table 1: Partitioning of the `CultureInstruct` dataset.</em></center>

The token counts come from the OLMo 2 tokenizer used. Each data point contains the system prompt, user instruction, and assistant answers.

The relevant comparison for federated training is token count rather than sample count. Hence, variant _(i)_ gives two nodes of comparable size, 4.2M tokens for the South Asian data subset vs. approximately 3.5M tokens for the Australia and NZ subset. Variants _(ii)_ and _(iii)_ break that balance deliberately, and the trade-off they probe is data volume against data relevance.

The M0 PoC used the same cultural benchmarks from the `CultureInstruct` paper, to evaluate the tuned models. The difference here was the use of distributed consortium tuning, whereas the the original `CultureInstruct` tuning work was performed in a more conventional way, i.e., using one centralised environment.

In addition, the BharatGen WVS test dataset[^3] and the GlobalOpinionQA evaluation dataset[^4] were used.

### Instruction Fine Tuning Details and Hyperparameter Tuning

LoRA fine tuning was done on OLMo 2 7B, so that only LoRA adapter deltas had to be exchanged between the two sites. The hyperparameters being studied include the following:

1. The number of local steps that can be performed before the outer loop synchronization should be done.
1. The ideal update compression levels: sparsification and quantization.
1. The LR (learning rate) schedule for the optimizer.
1. The NS (Newton-Schulz) constants for the Muon optimizer[^5], or the (β₁, β₂) coefficients when using AdamW.
1. The rank of the LoRA adapter.
1. Any additional hyperparameters that the tasks below surface as important to study.

### Tasks

T1 to T7 in the following table are the individual experimental tasks planned for the two teams. These labels are used as shorthand references in the rest of this document. Given time constraints, completing T3 was the minimum goal for M0, although the team made progress on the subsequent tasks, too. The remaining work will continue into M1.

| Task | Description | Lead | Support | Status |
| :--- | :---------- | :--- | :------ | :----- |
| T1 | Verify cross-site connectivity. | Joint | — | Done |
| T2 | Hyperparameter tuning by one team. | BharatGen/Indian | Monash | In progress |
| T3 | Two-node smoke test: a short federated run (a few hundred steps, OLMo 2 1B or 7B LoRA) with updates exchanged in both directions. (Passing this constitutes the minimal M0 requirement.) | Joint | — | Done |
| T4 | Full M0 federated run: OLMo 2 7B LoRA across both nodes, with varying data partitions on the Monash side. Log the training loss per round, the communication volume per synchronisation, and the wall-clock time. | Joint | — | In progress |
| T5 | Baselines: centralised training of OLMo 2 on the union of both partitions (upper bound), at 7B first and at 1B only if compute permits, plus local-only training at each node (no-federation reference). The base model without tuning is scored as the zero-cost reference. This task produces centralised results that don't exist yet. | Monash | BharatGen/Indian | Not started |
| T6 | Evaluation harness: `GlobalOpinionQA` with Australia/NZ, India, and rest-of-world splits. Monash builds the harness, BharatGen runs it on the checkpoints held at the Indian node. | Joint | - | In progress |
| T7 | Round-level evaluation: score the retained per-round checkpoints, the final synchronised checkpoint, and the checkpoint after one additional local update at each node. Report the gap to the T5 centralised baseline per round alongside the training-loss curve. | BharatGen/Indian | Monash | Not started |

<center><em>Table 2: Experimental Tasks.</em></center>

### Baselines

1. OLMo 2 trained centrally on the union of the South Asian and Monash-node partitions, as the no-privacy upper bound.
2. Local-only training at each node, as the no-federation reference.
3. The base OLMo 2 instruct model without cultural tuning, as the zero-cost reference.

### Results

#### Training trajectory and merge history

Figure 1 was generated directly with the external Slakshna progress tool. It concatenates positive-sample optimizer updates, summarizes each local invocation, and associates extracted peer updates with confirmed synchronized checkpoints. The `D` labels identify large remote update arrivals as observed locally. They are not guaranteed to equal the Indian site's own round number because repeated gossip protocol delivery does not carry an authoritative global round-trip label.

![Australian local loss and observed peer-update merge history]({{site.baseurl}}/assets/images/m0/bharatgen-monash-figure-1.png)

<center><em>Figure 1. Australian local loss and observed peer-update merge history.</em></center>

<br/>

| Australian round | Start loss | Mean loss | End loss | Updates | Sequences per rank | Step-to-step duration | Peer update at start | Durable result |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | 3.2344 | 3.1250 | 2.7812 | 6 | 672 | 370 s | None | `sync_round_1`, local-only |
| 2 | 3.1094 | 2.9349 | 2.5781 | 6 | 672 | 368 s | D2 | `sync_round_2`, merge confirmed |
| 3 | 2.7344 | 2.4375 | 2.0625 | 6 | 672 | 371 s | D3 | `sync_round_3`, merge confirmed |
| 4 | 2.2031 | 2.0052 | 1.7344 | 6 | 672 | 368 s | D5 extracted | Local work completed; no synchronized adapter |

<center><em>Table 3: Statistics from the Australian Node.</em></center>

The recorded loss decreases both within rounds and across successive invocations. Round boundaries introduce small upward resets because a new [Bhaskera](https://medium.com/@somshekarm241/bhaskera-building-a-ray-native-distributed-llm-training-framework-from-scratch-2601d3529eba) process, optimizer state, and data iterator are created. Nevertheless, the Round 2 start loss is below the Round 1 start loss, and the same pattern continues into Rounds 3 and 4. Across the four local invocations, mean loss decreases by 35.8% and end loss decreases by 37.6%.

The operational cadence was approximately fifteen minutes per Australian invocation, despite a five-minute federation clock. Model loading, FSDP (fully sharded data parallel) initialization, six optimizer updates, DCP writing, delta construction, and aggregation together took longer than one clock window, so the next usable boundary was generally the third five-minute boundary. The six logged updates themselves occupied about 6.1–6.2 minutes; the remaining time was process startup, data setup, checkpointing, communication, and boundary waiting.

Round 4 illustrates an endpoint issue that should be handled explicitly in the future work. The Australian node extracted the latest Indian update at the round boundary, then the Indian endpoint disconnected while Australian local training was still active. The local trainer completed, but the session was stopped before `sync_round_4.pth` appeared. That local state is informative for the loss curve but is not a complete federated checkpoint and was not converted into an evaluation adapter.

#### GlobalOpinionQA Evaluation

##### Protocol and coverage

Evaluation used the standalone `shared_evaluation/GOQA` package supplied for the M0 collaboration. The package is independent of Slakshna and Bhaskera. It retains questions with at least one valid Australia, New Zealand, or Indian human response distribution and does not impute missing groups.

Each question was presented under five deterministic option orders: the source order and four SHA-256-seeded permutations. Valid one-token option-label probabilities were normalized, mapped back to the source option order, and averaged. The resulting model distribution was compared independently with each available human distribution using base-2 Jensen–Shannon distance. Lower distance is better.

| Evaluation coverage | Count |
| :---- | :---- |
| Unique questions | 1,106 |
| Prompt variants per model | 5,530 |
| Valid human target pairs | 1,831 |
| Australia pairs | 626 |
| New Zealand pairs | 273 |
| India current-national pairs | 470 |
| India non-national pairs | 340 |
| India old-national pairs | 122 |
| Evaluated states | Base plus Rounds 1–3 |

<center><em>Table 4: Evaluation coverage.</em></center>

The Australia/New Zealand primary metric is an equal macro average of the Australia and New Zealand question means. The India metric is an equal macro average of the current-national, non-national, and old-national sample-frame means. The two-region metric gives equal weight to these two regional values. All four states produced exactly 1,106 predictions, and the shared package validated the dataset hash, prediction coverage, model distributions, and target counts before scoring.

##### Evaluation Results

Figure 2 shows a monotonic reduction in all three primary distances. Round 1 is the local-only Australian state. Rounds 2 and 3 are the first and second retained states with confirmed Indian update merges.

![GlobalOpinionQA trajectory for the unchanged base and three retained Australian observer adapters]({{site.baseurl}}/assets/images/m0/bharatgen-monash-figure-2.png)

<center><em>Figure 2. GlobalOpinionQA trajectory for the unchanged base and three retained Australian observer adapters.</em></center>

<br/>

| Model state | Peer merge in this state | Australia/NZ macro JSD | India macro JSD | Two-region macro JSD | Relative two-region change vs base |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Base | None | 0.488890 | 0.323855 | 0.406373 | — |
| Round 1 | None; local-only | 0.484298 | 0.320769 | 0.402534 | −0.94% |
| Round 2 | D2, confirmed | 0.470840 | 0.310927 | 0.390884 | −3.81% |
| **Round 3** | **D3, confirmed** | **0.451677** | **0.298494** | **0.375086** | **−7.70%** |

<center><em>Table 5: Evaluation results per round.</em></center>

Round 3 improves the Australia/New Zealand macro by 0.037213, or 7.61%, relative to base. It improves the India sample-frame macro by 0.025361, or 7.83%. The similar relative change on both sides is notable because the evaluated model is the Australian observer state and the prompt contains no country identity.

| Target group | Base JSD | Round 1 | Round 2 | Round 3 | Round 3 change vs base |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Australia | 0.448941 | 0.444684 | 0.431331 | 0.412869 | −0.036072 |
| New Zealand | 0.528839 | 0.523913 | 0.510349 | 0.490485 | −0.038354 |
| India — current national | 0.332037 | 0.328710 | 0.320112 | 0.311860 | −0.020177 |
| India — non-national | 0.312884 | 0.309652 | 0.299954 | 0.287418 | −0.025467 |
| India — old national | 0.326644 | 0.323945 | 0.312715 | 0.296204 | −0.030440 |

<center><em>Table 6: Evaluation results per target group and round.</em></center>

All five disaggregated groups improve monotonically through Round 3\. The largest absolute changes occur for New Zealand and Australia, while the largest relative change is observed for the smaller India old-national sample frame. No individual group moves against the aggregate trend.

The results do not by themselves separate local optimization from cross-site aggregation. Round 1 already improves on base before an Indian update is incorporated, demonstrating that Australian local adaptation contributes to the gain. The larger improvements after Rounds 2 and 3 are consistent with continued local training plus peer merging, but this single trajectory has no matched local-only control with the same restart schedule. It would therefore be premature to attribute the incremental gain solely to Indian updates.


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

Here are preliminary tuning results showing a 26% improvement:

<img width="1600" height="885" alt="Image" src="{{site.baseurl}}/assets/images/m0/fine-tuning-vietnam-june-2026.png" />

Here is the final, different representation at the end of the tuning experiment showing a 45% improvement:

<img width="1600" height="885" alt="Image" src="{{site.baseurl}}/assets/images/m0/iw_cultural_map.png" />

| Model | Distance to Vietnam (Inglehart-Welzel) | Capability (full MMLU, n=14,042, zero-shot) |
| :---- | :-------------------------------------- | :------------------------------------------- |
| Base  | 2.46 | 63.2% |
| Tuned | 1.35 - 45% closer | 62.4% (not statistically significant, McNemar p ≈ 0.07) |

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

We wish to thank all the contributors to Tapestry. In particular, contributors of code and comments to the [Tapestry repository]({{site.repo_url}}) include [@dean-wampler](https://github.com/deanwampler){:target="_blank"}, [@ctn](https://github.com/ctn){:target="_blank"}, [@jneums](https://github.com/jneums){:target="_blank"}, [@Rohithmatham12](https://github.com/Rohithmatham12){:target="_blank"}, [@kb-bhatta](https://github.com/kb-bhatta){:target="_blank"}, [@luzanikita](https://github.com/luzanikita){:target="_blank"}, [@AnthonyJAnnunziata](https://github.com/AnthonyJAnnunziata){:target="_blank"}, [@jolson-allianceai](https://github.com/jolson-allianceai){:target="_blank"}, [@ThibautMelen](https://github.com/ThibautMelen){:target="_blank"}, [@Milian0402](https://github.com/Milian0402){:target="_blank"}, [@EC](https://github.com/EC){:target="_blank"}, [@NovusEdge](https://github.com/NovusEdge){:target="_blank"}, [@14H034160212](https://github.com/14H034160212){:target="_blank"}, [@d3v07](https://github.com/d3v07){:target="_blank"}, [@welttowelt](https://github.com/welttowelt){:target="_blank"}, [@adampingel](https://github.com/adampingel){:target="_blank"}, [@nguyennm1024](https://github.com/nguyennm1024){:target="_blank"}, [@mzkarami](https://github.com/mzkarami){:target="_blank"}, [@Amertos](https://github.com/Amertos){:target="_blank"}, [@andrewmusselman](https://github.com/andrewmusselman){:target="_blank"}, [@ArjunSrivastava1](https://github.com/ArjunSrivastava1){:target="_blank"}, [@bapichatterjee](https://github.com/bapichatterjee){:target="_blank"}, [@billbrietstout](https://github.com/billbrietstout){:target="_blank"}, [@dbckz](https://github.com/dbckz){:target="_blank"}, [@elainechan](https://github.com/elainechan){:target="_blank"}, [@JulienAu](https://github.com/JulienAu){:target="_blank"}, [@kb-bhatta](https://github.com/kb-bhatta){:target="_blank"}, [@niclane7](https://github.com/niclane7){:target="_blank"}, [@psfoley](https://github.com/psfoley){:target="_blank"}, [@Phaethon1](https://github.com/Phaethon1){:target="_blank"}, and let us not forget the ever-present `@dependabot[bot]` and `@copilot-swe-agent[bot]` :grin:.


### What's Next?

Milestone One (M1) is our next objective, covering our work from September through November, 2026. [Our M1 dashboard]({{site.repo_project_dashboard_url}}?filterQuery=milestone%3AM1){:target="repo"} shows the work planned and our progress. Like M0, the major themes will be expanding our capabilities in these areas:

* [Consortium Training](https://github.com/The-AI-Alliance/tapestry/issues/183){:target="_blank"}
* [Cultural Alignment](https://github.com/The-AI-Alliance/tapestry/issues/243){:target="_blank"}
* [Data Governance and Management](https://github.com/The-AI-Alliance/tapestry/issues/230){:target="_blank"}

We welcome your help! See the [project README](https://github.com/The-AI-Alliance/tapestry#getting-involved-anchor){:target="repo"} for individual contributor guidance and how your organization can join Project Tapestry.

---

[^1]: OLMo Team (2025). 2 OLMo 2 Furious. [arXiv:2501.00656](https://arxiv.org/abs/2501.00656){:target="arxiv"}.
[^2]: Pham, V. T., Li, Z., Qu, L., and Haffari, G. (2025). _CultureInstruct: Curating Multi-Cultural Instructions at Scale._ In Proceedings of NAACL 2025. ([PDF](https://aclanthology.org/2025.naacl-long.465.pdf){:target="_blank"}, [dataset](https://drive.google.com/file/d/139oNuyEVdvprEIWUBuBd4BcBrWMwp0Hw/view?usp=sharing){:target="_blank"})
[^3]: BharatGen Culture WVS Dataset. ([Google Drive link](https://drive.google.com/drive/folders/1Anxb1YWUfhkla5cOBucfaRGS557VLt5m){:target="google"})
[^4]: Durmus, E. et al. (2023). _Towards Measuring the Representation of Subjective Global Opinions in Language Models._ ([arXiv:2306.16388](https://arxiv.org/abs/2306.16388){:target="arxiv"})
[^5]: Jordan, K. et al. (2024). _Muon: An optimiser for hidden layers in neural networks._ ([blog post](https://kellerjordan.github.io/posts/muon/){:target="muon"} and [repo](https://github.com/KellerJordan/Muon){:target="muon"})
[^6]: Tao, Y. et al., _Cultural Bias and Cultural Alignment of Large Language Models_, 2024. ([arxiv](https://arxiv.org/abs/2311.14096v2){:target="arxiv"})
[^7]: Hendrycks, D. et al., _Measuring Massive Multitask Language Understanding_, 2021, ([arxiv](https://arxiv.org/abs/2009.03300){:target="arxiv"}).
