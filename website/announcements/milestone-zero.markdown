---
layout: default
title: Milestone Zero
nav_order: 200
has_children: false
parent: Project Tapestry - Announcements
---

# Milestone Zero - &ldquo;M0&rdquo;

As described on the [Announcement](../) page, milestone "zero" was about initial organization and consortium building. We started work in several key areas:

* Demonstrated the feasibility of _consortium training_, as defined in [Training Approaches: Centralized, Federated, and Consortium]({{site.repo_tech_docs_url}}/reference/training-approaches.md) (where it is also compared to _federated learning_). This study used two, geographically-distributed &ldquo;sovereign&rdquo; nodes (training clusters) collaborating to instruction-tune a model.
* Explored techniques for [cultural alignment]({{site.repo_tech_docs_url}}/architecture/decisions/adr-003-cultural-alignment.md).
* Started defining the requirements for our data governance and management strategy and organized work groups for these areas.
* Established our software development policies and practices.

This page provides more details. See also the [M0 release notes]({{site.repo_url}}/releases/tag/v0.1.0-M0){:target="m0-release"}.

## Consortium Training Proofs of Concept (PoCs)

Two separate PoCs were defined to explore consortium training

### BharatGen and Monash University

The main PoC for consortium training, [&ldquo;epic&rdquo; #189](https://github.com/The-AI-Alliance/tapestry/issues/189){:target="repo"}, was conducted by a joint team from [BharatGen](https://bharatgen.com/){:target="bharatgen"}, in India, and [Monash University](https://www.monash.edu/){:target="monash"}, in Australia. The aim was to use instruction fine tuning (IFT) to perform cultural alignment in a geo-localized consortium training setting, using a reasonably sized LLM.

#### Experimental Setup

The team deployed BharatGen's [Slakshna](https://github.com/dcll-iiitd/Slakshna){:target="slakshna"} stack for &ldquo;geo-localized, decentralised, secure federated learning&rdquo; in two, small, geographically-separated GPU clusters, one in each organization.
The team initially verified the stack's connectivity across India and Australia by fine-tuning the LLama 1.1B model for several epochs.

The team performed a distributed run of instruction fine tuning of the OLMo 2 7B model[^1], where they evaluated the efficacy of local training loops with periodic &ldquo;outer loops&rdquo; of model weight merging between them. They confirmed that the loss function behaved as expected, monotonically decreasing with no signs of instability that could have emerged due to the distributed process of the local, independent training loops combined with periodic &ldquo;outer loop&rdquo; weight merges. Note that no training data was exchanged in these outer loop merges, only model weights.

OLMo 2 7B was chosen because the full details about its architecture, how it was trained, the data sets used, etc. are publicly available, which makes experimentation with the model family comparatively easy. Also, OLMo 2 7B was used in previous work by some of the team members, discussed next, for which this PoC was a natural extension.

#### Experimental Data

The `CultureInstruct` dataset[^2] was used, which contains data from multiple countries. The dataset was split into three parts:

| Partition | # Samples | # Tokens | Used By/For | Description |
| :-------- | --------: | -------: | :---------- | :---------- |
| **South Asia** | 15K | 4.2M | BharatGen | Data labeled for south Asian countries. including Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan, and Sri Lanka. |
| **Out-of-South-Asia** | 294K | 75.0M | Monash Univ. | We can split this part further by region. We estimate the Oceania region (Australia and New Zealand) has around 13K samples, 3.5M tokens. We exploited this knowledge to form useful subsets: |
| _(i) Australia and NZ only_ | 13K | 3.5M | | The 13K samples is roughly equal to BharatGen's 15K samples, which isolates cross-site behaviour from data-imbalance effects. |
| _(ii) Australia, NZ, and Western Europe_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| _(iii) Australia, NZ, and US, Canada, and UK_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| **Unlabeled** | 158K | 30M | Hyperparameter tuning | Culture-relevant instructions without a country label. Whether this pool is held out, mixed into both nodes as shared data, or excluded from M0 is an open decision for kick-off. |

The token counts come from the OLMo 2 tokenizer used. Each data point contains the system prompt, user instruction, and assistant answers.

The relevant comparison for federated training is token count rather than sample count. Hence, variant _(i)_ gives two nodes of comparable size, 4.2M tokens for the South Asian dataset vs. approximately 3.5M tokens for the Australia and NZ subset. Variants _(ii)_ and _(iii)_ break that balance deliberately, and the trade-off they probe is data volume against data relevance.

The M0 PoC used the same cultural benchmarks from the `CultureInstruct` paper, to evaluate the tuned models. The difference here was the use of distributed, consortium tuning, whereas the the original `CultureInstruct` performed tuning in a more conventional, centralised way.

#### Instruction Fine Tuning Details and Hyperparameter Tuning

LoRA fine tuning was done on OLMo 2 7B, so that only LoRA adapter deltas had to be exchanged between the two sites. The hyperparameters under study were the following:

1. The number of local steps that can be performed before the outer loop synchronization should be done.
1. The ideal update compression levels: sparsification and quantization.
1. The LR (learning rate) schedule for the optimizer.
1. The NS (Newton-Schulz) constants for the Muon optimizer[^3], or the (β₁, β₂) coefficients when using AdamW.
1. The rank of the LoRA adapter.

#### Tasks

T1 to T7 in the following table are the individual experimental tasks for the two teams. These labels are used as shorthand references in the rest of this document. Given time constraints, completing T3 was the minimum goal for M0, although the team hoped to complete as many of the remaining tasks as possible, continuing into M1 as required.

TODO: STATUS AS OF AUGUST 25

| Task | Description | Lead | Support | Status |
| :--- | :---------- | :--- | :------ | :----- |
| T1 | Verify cross-site connectivity. | Joint | — | Done |
| T2 | Hyperparameter tuning by one team. | BharatGen/Indian | Monash | In progress |
| T3 | Two-node smoke test: a short federated run (a few hundred steps, OLMo 2 1B or 7B LoRA) with updates exchanged in both directions. (Passing this constitutes the minimal M0 requirement.) | Joint | — | In progress |
| T4 | Full M0 federated run: OLMo 2 7B LoRA across both nodes, with varying data partitions on the Monash side. Log the training loss per round, the communication volume per synchronisation, and the wall-clock time. | Joint | — | Not started |
| T5 | Baselines: centralised training of OLMo 2 on the union of both partitions (upper bound), at 7B first and at 1B only if compute permits, plus local-only training at each node (no-federation reference). The base model without tuning is scored as the zero-cost reference. This task produces centralised results that don't exist yet. | Monash | BharatGen/Indian | Not started |
| T6 | Evaluation harness: `GlobalOpinionQA` with Australia/NZ, India, and rest-of-world splits. Monash builds the harness, BharatGen runs it on the checkpoints held at the Indian node. | Joint | - | Not started |
| T7 | Round-level evaluation: score the retained per-round checkpoints, the final synchronised checkpoint, and the checkpoint after one additional local update at each node. Report the gap to the T5 centralised baseline per round alongside the training-loss curve. | BharatGen/Indian | Monash | Not started |

#### Evaluation

Convergence of the federated training loss function was the most important result planned for M0, which was achieved. The loss curve was compared against the local-only curves from T5 (task 5 in the table above). If it fails to trend downward or diverges from the local-only curves by more than an order of magnitude, the run halts for diagnosis rather than proceeding to downstream evaluation.

Desirable, additional evaluation of the federated model checkpoints included these test datasets:

* `GlobalOpinionQA`[^4]. Built from the Pew Global Attitudes Survey and the World Values Survey, each item carries per-country response distributions rather than a single gold label. We evaluated the similarity between the model's answer distribution and the survey distributions for Australia/NZ, India, and other countries respectively.
* BharatGen Culture WVS Dataset[^5].

Baselines. (i) OLMo 2 trained centrally on the union of the South Asian and Monash-node partitions, as the no-privacy upper bound; (ii) local-only training at each node, as the no-federation reference; (iii) the base OLMo 2 instruct model without cultural tuning, as the zero-cost reference. Federated results are interpreted relative to the gap between (i) and (ii). No centralised results exist yet at either model size, so baseline (i) is produced inside M0. (T5): the 7B centralised run is attempted first as the cheaper of the two, and the 1B centralised run only if the compute at the Monash node permits.
Evaluation cadence. Adapter checkpoints are retained at every synchronisation round, and CulturalBench and GlobalOpinionQA are scored per round rather than only at the end of the run, so that the benchmark trajectory can be read against the training-loss curve and any divergence between the two is visible while the run is still in progress. Two further points are scored: the final synchronised checkpoint, and the checkpoint obtained after one additional local update at each node following the final synchronisation. The second separates what the aggregated model holds from what each node recovers by fitting its own partition last, which is the quantity of interest if the deployed artefact is a locally adapted model rather than the global one. Per-round scoring assumes checkpoint retention is affordable at both sites; if storage or evaluation cost makes it impractical, the fallback is scoring every k-th round, with the final synchronised checkpoint and the post-final-update checkpoints always scored.

### Using the Flower Labs Federated AI Framework

A second, separate PoC was started using the [Flower Labs](https://github.com/flwrlabs/flower) federated AI framework, also applied in a consortium training configuration, [epic #184](https://github.com/The-AI-Alliance/tapestry/issues/184){:target="repo"}. The plan was to use an OLMo 2 or 3 model and the DOLMA dataset to do _continued pre-training_ (CPT). Unfortunately, acquiring the necessary GPU resources could not be completed in the M0 time frame, so this PoC will be completed early in M1.

## Cultural Alignment

The [consortium training PoC #189](https://github.com/The-AI-Alliance/tapestry/issues/189){:target="repo"} just discussed did instruction fine tuning for cultural alignment. Two other experiments on cultural alignment were performed by separate teams during M0.

### 1


---

[^1]: OLMo Team (2025). 2 OLMo 2 Furious. arXiv:2501.00656.
[^2]: Pham, V. T., Li, Z., Qu, L., and Haffari, G. (2025). _CultureInstruct: Curating Multi-Cultural Instructions at Scale._ In Proceedings of NAACL 2025. ([PDF](https://aclanthology.org/2025.naacl-long.465.pdf){:target="_blank"}, [dataset](https://drive.google.com/file/d/139oNuyEVdvprEIWUBuBd4BcBrWMwp0Hw/view?usp=sharing){:target="_blank"})
[^3]: Jordan, K. et al. (2024). _Muon: An optimiser for hidden layers in neural networks._ [https://github.com/KellerJordan/Muon](https://github.com/KellerJordan/Muon){:target="muon"}.
[^4]: Durmus, E. et al. (2023). _Towards Measuring the Representation of Subjective Global Opinions in Language Models._ [arXiv:2306.16388](https://arxiv.org/abs/2306.16388){:target="arxiv"}.
[^5]: BharatGen Culture WVS Dataset. [link](https://drive.google.com/drive/folders/1Anxb1YWUfhkla5cOBucfaRGS557VLt5m){:target="google"}