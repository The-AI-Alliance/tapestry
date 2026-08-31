---
layout: default
title: BharatGen and Monash University Consortium Training PoC
nav_order: 2010
has_children: false
parent: Milestone Zero - M0
grand_parent: Announcements
---

# BharatGen and Monash University Consortium Training Proof of Concept

<details markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

The first PoC (proof of concept) for consortium training, [&ldquo;epic&rdquo; #189]({{site.repo_url}}/issues/189){:target="repo"}, was conducted by a joint team from [BharatGen](https://bharatgen.com/){:target="bharatgen"}, in India, and [Monash University](https://www.monash.edu/){:target="monash"}, in Australia.

This work was briefly summarized in the [M0 Announcement]({{site.baseurl}}/announcements/milestone-zero/).

The contributors to this project include the following people:

* From [BharatGen](https://bharatgen.com/){:target="bharatgen"} (and affiliated institutions): [Maneesh Kumar Singh](mailto:maneesh.singh@bharatgen.com){:target="bharatgen"}, [Bapi Chatterjee](https://github.com/bapichatterjee){:target="bharatgen"} (also Indraprastha Institute of Information Technology Delhi - IIITD), [Anant Jain](mailto:anantj@iiitd.ac.in){:target="bharatgen"} (IIITD), [Gauranshi Gupta](mailto:gauranshig@iiitd.ac.in){:target="bharatgen"} (IITD), [Mounendra De Sarkar](mailto:mounendra@cse.iith.ac.in){:target="bharatgen"} (IIT Hyderabad), [Ganesh Ramakrishnan](https://www.cse.iitb.ac.in/~ganesh/){:target="bharatgen"} (IIT Bombay), and [Samrit Kumar Maity](mailto:samritm@cdac.in){:target="bharatgen"} (CDAC, India).
* From [Monash University](https://www.monash.edu/){:target="monash"}: [Lizhen Qu](https://github.com/qulizhen){:target="monash"}, [Trang Vu](mailto:trang.vu1@monash.edu){:target="monash"}, and [Minghan Wang](mailto:minghan.wang@monash.edu){:target="monash"}

The primary objective of this PoC was to work through practical details of coordinated, distributed training between autonomous data centers (“sovereign nodes”), with the secondary goal of beginning the exploration of instruction fine tuning (IFT) to perform cultural alignment in this geo-localized consortium training setting, using a reasonably sized LLM. The team completed the primary objective and made progress on the secondary objective, too.

After demonstrating interoperability, the team did a preliminary tuning experiment. Each sovereign node, one in India and one in Australia, tuned locally with separate, culturally-specific datasets, then they did periodic merges of the weight updates (no tuning data was exchanged). As expected, they confirmed that the local updates improved the local model’s performance on the corresponding cultural behaviors, but the preliminary results also demonstrated that the improvements were retained after merging the weight updates between them to create new, shared model checkpoints.

## Experimental Setup

The team deployed BharatGen's [Slakshna](https://github.com/dcll-iiitd/Slakshna){:target="slakshna"} stack for &ldquo;geo-localized, decentralised, secure federated learning&rdquo; in two, small, geographically-separated GPU clusters, one in each organization. The team initially verified the stack's connectivity across India and Australia by fine-tuning the LLama 1.1B model for several epochs. This step completed the primary objective for M0.

Then the team performed a distributed run of instruction fine tuning of the OLMo 2 7B model[^1], where they evaluated the efficacy of local training loops with periodic &ldquo;outer loops&rdquo; of model weight merging between them. They confirmed that the loss function behaved as expected, monotonically decreasing with no signs of instability that could have emerged due to the distributed process of the local, independent training loops combined with periodic &ldquo;outer loop&rdquo; weight merges. Note that no training data was exchanged in these outer loop merges, only model weights.

OLMo 2 7B was chosen because comprehensive details about its architecture, training process, data sets used, etc. are openly available, which makes experimentation with the model family comparatively easy. Also, OLMo 2 7B was used in previous work by some of the team members, discussed next, for which this PoC was a natural extension.

## Experimental Data

The `CultureInstruct` dataset[^2] was used, including the GlobalOpinionQA evaluation dataset[^3]. It is a large-scale, cultural instruction-tuning dataset containing approximately 430,000 English-language instructions spanning 183 countries and 11 cultural domains. It is automatically constructed from public web data using an LLM-based generation pipeline and it is intended to improve model performance across a broad range of culturally-relevant tasks. It was previously developed by Monash University. The dataset was split into three main parts, with a further subdivision of one of those parts:

| Partition | # Samples | # Tokens | Used By/For | Description |
| :-------- | --------: | -------: | :---------- | :---------- |
| **South Asia** | 15K | 4.2M | BharatGen | Data labeled for south Asian countries. including Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan, and Sri Lanka. |
| **Out-of-South-Asia** | 294K | 75.0M | Monash Univ. | We can split this part further by region. We estimate the Oceania region (Australia and New Zealand) has around 13K samples, 3.5M tokens. We exploited this knowledge to form useful subsets: |
| _(i) Australia and NZ only_ | 13K | 3.5M | | The 13K samples is roughly equal to BharatGen's 15K samples, which isolates cross-site behaviour from data-imbalance effects. |
| _(ii) Australia, NZ, and Western Europe_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| _(iii) Australia, NZ, and US, Canada, and UK_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| **Unlabeled** | 158K | 30M | Hyperparameter tuning | Culture-relevant instructions without a country label. Whether this pool is held out, mixed into both nodes as shared data, or excluded from M0 is TBD. |

<center><em>Table 1. Partitioning of the `CultureInstruct` dataset.</em></center>

The token counts come from the OLMo 2 tokenizer used. Each data point contains the system prompt, user instruction, and assistant answers.

The relevant comparison for federated training is token count rather than sample count. Hence, variant _(i)_ gives two nodes of comparable size, 4.2M tokens for the South Asian data subset vs. approximately 3.5M tokens for the Australia and NZ subset. Variants _(ii)_ and _(iii)_ break that balance deliberately, and the trade-off they probe is data volume against data relevance.

The M0 PoC used the same cultural benchmarks from the `CultureInstruct` paper, to evaluate whether the fine-tuned models demonstrated improved cultural knowledge and reductions in measured cultural biases. The difference here was the use of distributed consortium tuning, whereas the the original `CultureInstruct` paper did tuning in a more conventional way, i.e., using one centralised environment.

In addition, the BharatGen WVS test dataset[^4].

## Instruction Fine Tuning Details and Hyperparameter Tuning

LoRA fine tuning was done on OLMo 2 7B, so that only LoRA adapter deltas had to be exchanged between the two sites. The hyperparameters being studied include the following:

1. The number of local steps that can be performed before the outer loop synchronization should be done.
1. The ideal update compression levels: sparsification and quantization.
1. The LR (learning rate) schedule for the optimizer.
1. The NS (Newton-Schulz) constants for the Muon optimizer[^5], or the (β₁, β₂) coefficients when using AdamW.
1. The rank of the LoRA adapter.
1. Any additional hyperparameters that the tasks below surface as important to study.

## Tasks

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

<center><em>Table 2. Experimental Tasks.</em></center>

### Baselines

1. OLMo 2 trained centrally on the union of the South Asian and Monash-node partitions, as the no-privacy upper bound.
2. Local-only training at each node, as the no-federation reference.
3. The base OLMo 2 instruct model without cultural tuning, as the zero-cost reference.

## Results

Let's explore the results achieved.

### Training trajectory and merge history

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

<center><em>Table 3. Statistics from the Australian Node.</em></center>

The recorded loss decreases both within rounds and across successive invocations. Round boundaries introduce small upward resets because a new [Bhaskera](https://medium.com/@somshekarm241/bhaskera-building-a-ray-native-distributed-llm-training-framework-from-scratch-2601d3529eba) process, optimizer state, and data iterator are created. Nevertheless, the Round 2 start loss is below the Round 1 start loss, and the same pattern continues into Rounds 3 and 4. Across the four local invocations, mean loss decreases by 35.8% and end loss decreases by 37.6%.

The operational cadence was approximately fifteen minutes per Australian invocation, despite a five-minute federation clock. Model loading, FSDP (fully sharded data parallel) initialization, six optimizer updates, DCP writing, delta construction, and aggregation together took longer than one clock window, so the next usable boundary was generally the third five-minute boundary. The six logged updates themselves occupied about 6.1–6.2 minutes; the remaining time was process startup, data setup, checkpointing, communication, and boundary waiting.

Round 4 illustrates an endpoint issue that should be handled explicitly in the future work. The Australian node extracted the latest Indian update at the round boundary, then the Indian endpoint disconnected while Australian local training was still active. The local trainer completed, but the session was stopped before `sync_round_4.pth` appeared. That local state is informative for the loss curve but is not a complete federated checkpoint and was not converted into an evaluation adapter.

### Preliminary GlobalOpinionQA Evaluation

Evaluation used the standalone `shared_evaluation/GOQA` package supplied for the M0 collaboration. The package is independent of Slakshna and Bhaskera. It retains questions with at least one valid Australia, New Zealand, or Indian human response distribution and does not impute missing groups.

#### Protocol and coverage

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

<center><em>Table 4. Evaluation coverage.</em></center>

The Australia/New Zealand primary metric is an equal macro average of the Australia and New Zealand question means. The India metric is an equal macro average of the current-national, non-national, and old-national sample-frame means. The two-region metric gives equal weight to these two regional values. All four states produced exactly 1,106 predictions, and the shared package validated the dataset hash, prediction coverage, model distributions, and target counts before scoring.

#### Evaluation Results

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

<center><em>Table 5. Evaluation results per round.</em></center>

Round 3 improves the Australia/New Zealand macro by 0.037213, or 7.61%, relative to base. It improves the India sample-frame macro by 0.025361, or 7.83%. The similar relative change on both sides is notable because the evaluated model is the Australian observer state and the prompt contains no country identity.

| Target group | Base JSD | Round 1 | Round 2 | Round 3 | Round 3 change vs base |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Australia | 0.448941 | 0.444684 | 0.431331 | 0.412869 | −0.036072 |
| New Zealand | 0.528839 | 0.523913 | 0.510349 | 0.490485 | −0.038354 |
| India — current national | 0.332037 | 0.328710 | 0.320112 | 0.311860 | −0.020177 |
| India — non-national | 0.312884 | 0.309652 | 0.299954 | 0.287418 | −0.025467 |
| India — old national | 0.326644 | 0.323945 | 0.312715 | 0.296204 | −0.030440 |

<center><em>Table 6. Evaluation results per target group and round.</em></center>

All five disaggregated groups improve monotonically through Round 3\. The largest absolute changes occur for New Zealand and Australia, while the largest relative change is observed for the smaller India old-national sample frame. No individual group moves against the aggregate trend.

The results do not by themselves separate local optimization from cross-site aggregation. Round 1 already improves on base before an Indian update is incorporated, demonstrating that Australian local adaptation contributes to the gain. The larger improvements after Rounds 2 and 3 are consistent with continued local training plus peer merging, but this single trajectory has no matched local-only control with the same restart schedule. It would therefore be premature to attribute the incremental gain solely to Indian updates.

Additional, subsequent evaluations are described [below](#globalopinionqa-evaluation), in the next section.

### M0 Third Cross-Country Federated Training Report

| Item | Australian-site setting |
| :---- | :---- |
| Base model | `allenai/OLMo-2-1124-7B` |
| Tokenizer / chat template | `allenai/OLMo-2-1124-7B-Instruct` |
| Adaptation | LoRA on `q_proj` and `v_proj` |
| LoRA rank / alpha / dropout | 16 / 64 / 0.03 |
| Precision / distributed strategy | BF16 / two-worker FSDP |
| Optimizer | 8-bit Muon |
| Learning rate / warmup | `3e-4` / 0 steps |
| Per-worker batch / gradient accumulation | 8 / 4 |
| Site-effective batch | 64 packed sequences per optimizer step |
| Maximum local steps per FL round | 9 |
| Sequence length / packing | 2,048 / enabled |
| Packed Australian dataset | 1,458 sequences |
| Training labels | Assistant responses only |
| Federation clock / sync deadline | 300 s / 300 s |
| Configured federated rounds | 16 |
| Delta transport | Top-10% sparsity, symmetric INT8 |
| Typical encoded model update | Approximately 5.43 MiB |

<center><em>Table 7. Third cross-country federated training report.</em></center>

The Australian process started at 23:07:23 on 30 August, 2026 and shut down normally after reaching Round 16 at 01:46:28 on 31 August. Total observer-side wall time was approximately 2 hours 39 minutes.

#### Training, Merge, and Data-epoch Record

Figure 3 was produced from the external Slakshna observation tool. The top panel concatenates optimizer-step losses while retaining FL-round and data-epoch boundaries. The middle panel summarizes start, mean, and end loss for each round. The bottom panel records the peer delta loaded by each round.

![Australian training loss, data-epoch boundaries, and peer-delta merge record]({{site.baseurl}}/assets/images/m0/bharatgen-monash-figure-3.png)

<center><em>Figure 3. Australian training loss, data-epoch boundaries, and peer-delta merge record.</em></center>

The data cursor now continues across Slakshna invocations. A complete pass consists of 22 optimizer steps distributed as 9 \+ 9 \+ 4 steps over three FL rounds. With a site-effective batch of 64, each pass consumes 1,408 of the 1,458 packed sequences. The final 50-sequence tail cannot form another complete distributed optimizer update and is dropped. Thus the run completed five real cursor passes and entered a sixth; the 16 federated rounds are not 16 data epochs.

| Data epoch | FL rounds | Optimizer steps | Consumed sequences | Completion / progress |
| ----: | :---- | ---: | ----: | :---- |
| 1 | R1–R3 | 22 | 1,408 | Complete |
| 2 | R4–R6 | 22 | 1,408 | Complete |
| 3 | R7–R9 | 22 | 1,408 | Complete |
| 4 | R10–R12 | 22 | 1,408 | Complete |
| 5 | R13–R15 | 22 | 1,408 | Complete |
| 6 | R16 | 9 | 576 | 39.5% of the dataset cursor |

<center><em>Table 8. Data epochs.</em></center>

The loss trajectory falls rapidly over the first two data epochs and then settles near 1.5–1.7. The apparent rises at Rounds 4, 7, 10, 13, and 16 coincide with the start of a new data pass rather than a loss of training state. Selected round summaries are shown below; the full 16-round record is retained with the figure assets.

| Round | Steps | Start loss | Mean loss | End loss | Peer delta |
| ----: | ----: | :---- | :---- | :---- | :---- |
| 1 | 9 | 3.6406 | 3.1267 | 3.1875 | None |
| 3 | 4 | 2.5938 | 2.6914 | 2.5781 | D1 |
| 6 | 4 | 1.9297 | 1.9609 | 1.8828 | D3 reused |
| **7** | 9 | 2.1719 | 1.8038 | 1.8281 | **D4, last active-peer round** |
| 9 | 4 | 1.5859 | 1.6426 | 1.6641 | D4 reused after departure |
| 12 | 4 | 1.4688 | 1.5371 | 1.5703 | D4 reused after departure |
| 15 | 4 | 1.3906 | 1.4785 | 1.5156 | D4 reused after departure |
| 16 | 9 | 1.6719 | 1.5096 | 1.6484 | D4 reused after departure |

<center><em>Table 9. Tuning rounds.</em></center>

Four distinct Indian deltas arrived. D1 was first used in Round 3, D2 in Round 4, D3 in Rounds 5–6, and D4 in Round 7\. No new Indian model update arrived after D4. The peer left at 00:15:44, between Rounds 7 and 8, but the persisted D4 file remained available and was loaded again in every subsequent round.

| Australian rounds | Delta used | Interpretation |
| :---- | :---- | :---- |
| R1–R2 | None | Australian local training before the first remote update was available |
| R3 | D1 | First distinct Indian update |
| R4 | D2 | Second distinct Indian update |
| R5 | D3 | Third distinct Indian update |
| R6 | D3 | Same update reused; D4 arrived later in the round |
| R7 | D4 | Fourth and final distinct Indian update; last active-peer checkpoint |
| R8–R16 | D4 | Stale update repeatedly loaded after the Indian peer departed |

<center><em>Table 10. Australian tuning rounds.</em></center>

#### GlobalOpinionQA Evaluation

Evaluation continued to use the standalone shared GOQA package and directly loaded the base model plus LoRA adapters. The dataset contains 1,106 questions with at least one Australia, New Zealand, or Indian human distribution. Five deterministic option-order prompts were evaluated per question. The score is Jensen–Shannon distance between the model option distribution and the available human distribution; lower is better. The evaluation covered 626 Australia pairs, 273 New Zealand pairs, and 932 Indian sample-frame pairs.

![Continued GlobalOpinionQA trajectory before and after the Indian peer departure]({{site.baseurl}}/assets/images/m0/bharatgen-monash-figure-4.png)

<center><em>Figure 4. Continued GOQA trajectory before and after the Indian peer departure.</em></center>

<br/>

| Model state | Delta | Australia/NZ JSD | India JSD | Equal two-region JSD | Relative change vs base |
| :---- | :---- | :---- | :---- | :---- | ----: |
| Base | None | 0.488578 | 0.323637 | 0.406107 | — |
| Round 1 | None | 0.485151 | 0.321212 | 0.403182 | −0.72% |
| Round 2 | None | 0.474369 | 0.313851 | 0.394110 | −2.95% |
| Round 3 | D1 | 0.468686 | 0.310113 | 0.389400 | −4.11% |
| Round 4 | D2 | 0.455833 | 0.302070 | 0.378951 | −6.69% |
| Round 5 | D3 | 0.442958 | 0.295083 | 0.369021 | −9.13% |
| Round 6 | D3 | 0.429509 | 0.290274 | 0.359891 | −11.38% |
| **Round 7** | **D4** | **0.414574** | **0.286702** | **0.350638** | **−13.66%** |
| Round 16 | D4 reused | 0.395048 | 0.291820 | 0.343434 | −15.43% |

<center></em>Table 11. GOQA evaluation.</em></center>

---

[^1]: OLMo Team (2025). 2 OLMo 2 Furious. [arXiv:2501.00656](https://arxiv.org/abs/2501.00656){:target="arxiv"}.
[^2]: Pham, V. T., Li, Z., Qu, L., and Haffari, G. (2025). _CultureInstruct: Curating Multi-Cultural Instructions at Scale._ In Proceedings of NAACL 2025. ([PDF](https://aclanthology.org/2025.naacl-long.465.pdf){:target="_blank"}, [dataset](https://drive.google.com/file/d/139oNuyEVdvprEIWUBuBd4BcBrWMwp0Hw/view?usp=sharing){:target="_blank"})
[^3]: Durmus, E. et al. (2023). _Towards Measuring the Representation of Subjective Global Opinions in Language Models._ ([arXiv:2306.16388](https://arxiv.org/abs/2306.16388){:target="arxiv"})
[^4]: BharatGen Culture WVS Dataset. ([Google Drive link](https://drive.google.com/drive/folders/1Anxb1YWUfhkla5cOBucfaRGS557VLt5m){:target="google"})
[^5]: Jordan, K. et al. (2024). _Muon: An optimiser for hidden layers in neural networks._ ([blog post](https://kellerjordan.github.io/posts/muon/){:target="muon"} and [repo](https://github.com/KellerJordan/Muon){:target="muon"})
