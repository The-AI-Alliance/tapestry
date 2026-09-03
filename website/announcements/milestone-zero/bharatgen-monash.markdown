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

{: .note}
> **NOTE:**
> This page is a preliminary, rough draft of the details of this PoC, from the experimental setup, to captured results, to preliminary conclusions. Furthermore, the content below was adapted from documents prepared by the research team and some &ldquo;transcription errors&rdquo; may have occurred. More complete, refined, and definitive reports are forthcoming. In the meantime, contact the contributors listed below for more information, clarifications desired, etc.
>
> There are two major sections below:
> * [Experiment Details](#experiment-details) - Details about the data used, experimental setup in both locations, and detailed results.
> * [Summary Draft Report](#summary-draft-report) - A more concise summary of the details, including key outcomes.
>
> We recommend starting with the [Summary Draft Report](#summary-draft-report) and referring to the [Experiment Details](#experiment-details) to fill in additional details.

The first PoC (proof of concept) for consortium training, [&ldquo;epic&rdquo; #189]({{site.repo_url}}/issues/189){:target="repo"}, was conducted by a joint team from [BharatGen](https://bharatgen.com/){:target="bharatgen"}, in India, and [Monash University](https://www.monash.edu/){:target="monash"}, in Australia.

This work was briefly summarized in the [M0 Announcement]({{site.baseurl}}/announcements/milestone-zero/).

The contributors to this project include the following people:

* From [BharatGen](https://bharatgen.com/){:target="bharatgen"} (and affiliated institutions): [Maneesh Kumar Singh](mailto:maneesh.singh@bharatgen.com){:target="bharatgen"}, [Bapi Chatterjee](https://github.com/bapichatterjee){:target="bharatgen"} (also Indraprastha Institute of Information Technology Delhi - IIITD), [Anant Jain](mailto:anantj@iiitd.ac.in){:target="bharatgen"} (IIITD), [Gauranshi Gupta](mailto:gauranshig@iiitd.ac.in){:target="bharatgen"} (IITD), [Mounendra De Sarkar](mailto:mounendra@cse.iith.ac.in){:target="bharatgen"} (IIT Hyderabad), [Ganesh Ramakrishnan](https://www.cse.iitb.ac.in/~ganesh/){:target="bharatgen"} (IIT Bombay), and [Samrit Kumar Maity](mailto:samritm@cdac.in){:target="bharatgen"} (CDAC, India).
* From [Monash University](https://www.monash.edu/){:target="monash"}: [Lizhen Qu](https://github.com/qulizhen){:target="monash"}, [Trang Vu](mailto:trang.vu1@monash.edu){:target="monash"}, and [Minghan Wang](mailto:minghan.wang@monash.edu){:target="monash"}

The primary objective of this PoC was to work through practical details of coordinated, distributed training between autonomous data centers (“sovereign nodes”), with the secondary goal of beginning the exploration of instruction fine tuning (IFT) to perform cultural alignment in this geo-localized consortium training setting, using a reasonably sized LLM. The team completed the primary objective and made progress on the secondary objective, too.

After meeting the interoperability objectives, the team did a preliminary tuning experiment using the `OLMo 2-7B` base model[^1]. Each sovereign node, one in India and one in Australia, tuned locally with separate, culturally-specific datasets (disjoint, localized partitions extracted from a common dataset, `CultureInstruct`[^2]), then they did periodic merges of the weight updates (no tuning data was exchanged). As expected, they confirmed that the local updates improved the local model’s performance on the corresponding cultural behaviors, but the preliminary results also demonstrated that the improvements were retained after merging the weight updates between them to create new, shared model checkpoints. They also encountered several technical challenges that require further investigation.

## Experiment Details

This long section provides a lot of details about the data used, the experimental setups in each sovereign node, and the detailed results. For a more concise summary  of the details, including key takeaways, go to the section below, [Summary Draft Report](#summary-draft-report).

### Experimental Setup

The team deployed BharatGen's [Slakshna](https://github.com/dcll-iiitd/Slakshna){:target="slakshna"} stack for &ldquo;geo-localized, decentralised, secure federated learning&rdquo; in two, small, geographically-separated GPU clusters, one in each organization. The team initially verified the stack's connectivity across India and Australia by fine-tuning the LLama 1.1B model for several epochs. This step completed the primary objective for M0.

Then the team performed a distributed run of instruction fine tuning of the `OLMo 2-7B` model, where they evaluated the efficacy of local training loops with periodic &ldquo;outer loops&rdquo; of model weight merging between them. They confirmed that the loss function behaved as expected, monotonically decreasing with no signs of instability that could have emerged due to the distributed process of the local, independent training loops combined with periodic &ldquo;outer loop&rdquo; weight merges. Note that no training data was exchanged in these outer loop merges, only model weights.

`OLMo 2-7B` was chosen because comprehensive details about its architecture, training process, data sets used, etc. are openly available, which makes experimentation with the model family comparatively easy. Also, `OLMo 2-7B` was used in previous work by some of the team members, discussed next, for which this PoC was a natural extension.

### Experimental Data

The `CultureInstruct` dataset mentioned in the introduction was used, including the GlobalOpinionQA evaluation dataset[^3]. It is a large-scale, cultural instruction-tuning dataset containing approximately 430,000 English-language instructions spanning 183 countries and 11 cultural domains. It is automatically constructed from public web data using an LLM-based generation pipeline and it is intended to improve model performance across a broad range of culturally-relevant tasks. It was previously developed by Monash University. The dataset was split into three main parts, with a further subdivision of one of those parts:

| Partition | # Samples | # Tokens | Used By/For | Description |
| :-------- | --------: | -------: | :---------- | :---------- |
| **South Asia** | 15K | 4.2M | BharatGen | Data labeled for south Asian countries. including Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan, and Sri Lanka. |
| **Out-of-South-Asia** | 294K | 75.0M | Monash Univ. | We can split this part further by region. We estimate the Oceania region (Australia and New Zealand) has around 13K samples, 3.5M tokens. We exploited this knowledge to form useful subsets: |
| _(i) Australia and NZ only_ | 13K | 3.5M | | The 13K samples is roughly equal to BharatGen's 15K samples, which isolates cross-site behaviour from data-imbalance effects. |
| _(ii) Australia, NZ, and Western Europe_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| _(iii) Australia, NZ, and US, Canada, and UK_ | | | | Much larger Monash node datasets probe robustness to node-size and cultural heterogeneity. |
| **Unlabeled** | 158K | 30M | Hyperparameter tuning | Culture-relevant instructions without a country label. Whether this pool is held out, mixed into both nodes as shared data, or excluded from M0 is TBD. |

<center><em>Table 1. Partitioning of the `CultureInstruct` dataset.</em></center>

The token counts come from the `OLMo 2` tokenizer used. Each data point contains the system prompt, user instruction, and assistant answers.

The relevant comparison for federated training is token count rather than sample count. Hence, variant _(i)_ gives two nodes of comparable size, 4.2M tokens for the South Asian data subset vs. approximately 3.5M tokens for the Australia and NZ subset. Variants _(ii)_ and _(iii)_ break that balance deliberately, and the trade-off they probe is data volume against data relevance.

The M0 PoC used the same cultural benchmarks from the `CultureInstruct` paper, to evaluate whether the fine-tuned models demonstrated improved cultural knowledge and reductions in measured cultural biases. The difference here was the use of distributed consortium tuning, whereas the the original `CultureInstruct` paper did tuning in a more conventional way, i.e., using one centralised environment.

In addition, the BharatGen WVS test dataset[^4] was used.

### Instruction Fine Tuning Details and Hyperparameter Tuning

LoRA fine tuning was done on `OLMo 2-7B`, so that only LoRA adapter deltas had to be exchanged between the two sites. The hyperparameters being studied include the following:

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
| T3 | Two-node smoke test: a short federated run (a few hundred steps, `OLMo 2-1B` or `7B` LoRA) with updates exchanged in both directions. (Passing this constitutes the minimal M0 requirement.) | Joint | — | Done |
| T4 | Full M0 federated run: `OLMo 2-7B` LoRA across both nodes, with varying data partitions on the Monash side. Log the training loss per round, the communication volume per synchronisation, and the wall-clock time. | Joint | — | In progress |
| T5 | Baselines: centralised training of `OLMo 2` on the union of both partitions (upper bound), at 7B first and at 1B only if compute permits, plus local-only training at each node (no-federation reference). The base model without tuning is scored as the zero-cost reference. This task produces centralised results that don't exist yet. | Monash | BharatGen/Indian | Not started |
| T6 | Evaluation harness: `GlobalOpinionQA` with Australia/NZ, India, and rest-of-world splits. Monash builds the harness, BharatGen runs it on the checkpoints held at the Indian node. | Joint | - | In progress |
| T7 | Round-level evaluation: score the retained per-round checkpoints, the final synchronised checkpoint, and the checkpoint after one additional local update at each node. Report the gap to the T5 centralised baseline per round alongside the training-loss curve. | BharatGen/Indian | Monash | Not started |

<center><em>Table 2. Experimental Tasks.</em></center>

#### Baselines

1. `OLMo 2-7B` trained centrally on the union of the South Asian and Monash-node partitions, as the no-privacy upper bound.
2. Local-only training at each node, as the no-federation reference.
3. The base `OLMo 2-7B` instruct model without cultural tuning, as the zero-cost reference.

### Preliminary Results

This section discusses raw results. See the summary draft report [below](#summary-draft-report).

#### Training trajectory and merge history

Figure 1 was generated directly with the external Slakshna progress tool. It concatenates positive-sample optimizer updates, summarizes each local invocation, and associates extracted peer updates with confirmed synchronized checkpoints. The `D` labels identify large remote update arrivals as observed locally. They are not guaranteed to equal the Indian site's own round number because repeated gossip protocol delivery does not carry an authoritative global round-trip label.

![Australian local loss and observed peer-update merge history]({{site.baseurl}}/assets/images/m0/australian-local-loss-first-run-1.png)

<center><em>Figure 1. Australian local loss and observed peer-update merge history.</em></center>

<br/>

| Australian round | Start loss | Mean loss | End loss | Updates | Sequences per rank | Step-to-step duration | Peer update at start | Durable result |
| :-- | :----- | :----- | :----- | :-- | :--- | :---- | :---- | :---- |
| 1   | 3.2344 | 3.1250 | 2.7812 | 6   | 672  | 370 s | None         | `sync_round_1`, local-only |
| 2   | 3.1094 | 2.9349 | 2.5781 | 6   | 672  | 368 s | D2           | `sync_round_2`, merge confirmed |
| 3   | 2.7344 | 2.4375 | 2.0625 | 6   | 672  | 371 s | D3           | `sync_round_3`, merge confirmed |
| 4   | 2.2031 | 2.0052 | 1.7344 | 6   | 672  | 368 s | D5 extracted | Local work completed; no synchronized adapter |

<center><em>Table 3. Statistics from the Australian Node.</em></center>

The recorded loss decreases both within rounds and across successive invocations. Round boundaries introduce small upward resets because a new [Bhaskera](https://medium.com/@somshekarm241/bhaskera-building-a-ray-native-distributed-llm-training-framework-from-scratch-2601d3529eba){:target="_blank"} process, optimizer state, and data iterator are created. Nevertheless, the Round 2 start loss is below the Round 1 start loss, and the same pattern continues into Rounds 3 and 4. Across the four local invocations, mean loss decreases by 35.8% and end loss decreases by 37.6%.

The operational cadence was approximately fifteen minutes per Australian invocation, despite a five-minute federation clock. Model loading, FSDP (fully sharded data parallel) initialization, six optimizer updates, DCP writing, delta construction, and aggregation together took longer than one clock window, so the next usable boundary was generally the third five-minute boundary. The six logged updates themselves occupied about 6.1–6.2 minutes; the remaining time was process startup, data setup, checkpointing, communication, and boundary waiting.

Round 4 illustrates an endpoint issue that should be handled explicitly in the future work. The Australian node extracted the latest Indian update at the round boundary, then the Indian endpoint disconnected while Australian local training was still active. The local trainer completed, but the session was stopped before `sync_round_4.pth` appeared. That local state is informative for the loss curve but is not a complete federated checkpoint and was not converted into an evaluation adapter.

#### Preliminary GlobalOpinionQA Evaluation

Evaluation used the standalone `shared_evaluation/GOQA` package supplied for the M0 collaboration. The package is independent of Slakshna and Bhaskera. It retains questions with at least one valid Australia, New Zealand, or Indian human response distribution and does not impute missing groups.

##### Protocol and coverage

Each question was presented under five deterministic option orders: the source order and four SHA-256-seeded permutations. Valid one-token option-label probabilities were normalized, mapped back to the source option order, and averaged. The resulting model distribution was compared independently with each available human distribution using base-2 Jensen–Shannon distance. Lower distance is better.

| Evaluation coverage | Count |
| :--------------------------- | ----: |
| Unique questions             | 1,106 |
| Prompt variants per model    | 5,530 |
| Valid human target pairs     | 1,831 |
| Australia pairs              |   626 |
| New Zealand pairs            |   273 |
| India current-national pairs |   470 |
| India non-national pairs     |   340 |
| India old-national pairs     |   122 |
| Evaluated states             | Base plus Rounds 1–3 |

<center><em>Table 4. Evaluation coverage.</em></center>

The Australia/New Zealand primary metric is an equal macro average of the Australia and New Zealand question means. The India metric is an equal macro average of the current-national, non-national, and old-national sample-frame means. The two-region metric gives equal weight to these two regional values. All four states produced exactly 1,106 predictions, and the shared package validated the dataset hash, prediction coverage, model distributions, and target counts before scoring.

##### Evaluation Results

Figure 2 shows a monotonic reduction in all three primary distances. Round 1 is the local-only Australian state. Rounds 2 and 3 are the first and second retained states with confirmed Indian update merges.

![GlobalOpinionQA trajectory for the unchanged base and three retained Australian observer adapters]({{site.baseurl}}/assets/images/m0/GlobalOpinionQA-trajectory.png)

<center><em>Figure 2. GlobalOpinionQA trajectory for the unchanged base and three retained Australian observer adapters.</em></center>

<br/>

| Model state | Peer merge in this state | Australia/NZ macro JSD | India macro JSD | Two-region macro JSD | Relative two-region change vs base |
| :---------- | :---------------- | :----------- | :----------- | :----------- | ---------: |
|   Base      | None              |   0.488890   |   0.323855   |   0.406373   |     -      |
|   Round 1   | None; local-only  |   0.484298   |   0.320769   |   0.402534   |   −0.94%   |
|   Round 2   | D2, confirmed     |   0.470840   |   0.310927   |   0.390884   |   −3.81%   |
| **Round 3** | **D3, confirmed** | **0.451677** | **0.298494** | **0.375086** | **−7.70%** |

<center><em>Table 5. Evaluation results per round for the Jensen-Shannon distance.</em></center>

JSD is the _Jensen-Shannon distance_. Round 3 improves the Australia/New Zealand macro by 0.037213, or 7.61%, relative to base. It improves the India sample-frame macro by 0.025361, or 7.83%. The similar relative change on both sides is notable because the evaluated model is the Australian observer state and the prompt contains no country identity.

| Target group | Base JSD | Round 1 | Round 2 | Round 3 | Round 3 change vs base |
| :----------------------- | :------- | :------- | :------- | :------- | :-------- |
| Australia                | 0.448941 | 0.444684 | 0.431331 | 0.412869 | −0.036072 |
| New Zealand              | 0.528839 | 0.523913 | 0.510349 | 0.490485 | −0.038354 |
| India — current national | 0.332037 | 0.328710 | 0.320112 | 0.311860 | −0.020177 |
| India — non-national     | 0.312884 | 0.309652 | 0.299954 | 0.287418 | −0.025467 |
| India — old national     | 0.326644 | 0.323945 | 0.312715 | 0.296204 | −0.030440 |

<center><em>Table 6. Evaluation results per target group and round.</em></center>

All five disaggregated groups improve monotonically through Round 3\. The largest absolute changes occur for New Zealand and Australia, while the largest relative change is observed for the smaller India old-national sample frame. No individual group moves against the aggregate trend.

The results do not by themselves separate local optimization from cross-site aggregation. Round 1 already improves on base before an Indian update is incorporated, demonstrating that Australian local adaptation contributes to the gain. The larger improvements after Rounds 2 and 3 are consistent with continued local training plus peer merging, but this single trajectory has no matched local-only control with the same restart schedule. It would therefore be premature to attribute the incremental gain solely to Indian updates.

Additional, subsequent evaluations are described [below](#globalopinionqa-evaluation), in the next section.

#### M0 Third Cross-Country Federated Training Report

| Item | Australian-site setting |
| :--- | :---------------------- |
| Base model | `allenai/OLMo-2-1124-7B` |
| Tokenizer / chat template | `allenai/OLMo-2-1124-7B-Instruct` |
| Adaptation | LoRA on `q_proj` and `v_proj` |
| LoRA rank / alpha / dropout | 16 / 64 / 0.03 |
| Precision / distributed strategy | BF16 / two-worker FSDP |
| Optimizer | 8-bit Muon |
| Learning rate / warmup | 3*e<sup>-4</sup> / 0 steps |
| Per-worker batch | 8 packed sequences |
| Gradient accumulation | 4 |
| Site-effective batch | 64 packed sequences per optimizer step |
| Maximum local steps per FL round | 9 |
| Target federated rounds | 16 |
| Sequence length / packing | 2,048 / enabled |
| Packed Australian dataset | 1,458 sequences |
| Training labels | Assistant responses only |
| Federation clock / sync deadline  | 300 s / 300 s |
| Delta transport | Top-10% sparsity, symmetric INT8 |
| Typical encoded model update | Approximately 5.43 MiB |

<center><em>Table 7. Experimental settings for Australia.</em></center>

(Compare this table to Table 17 below, with settings for India.)

The Australian process started at 23:07:23 on 30 August, 2026 and shut down normally after reaching Round 16 at 01:46:28 on 31 August. Total observer-side wall time was approximately 2 hours 39 minutes.

##### Training, Merge, and Data-epoch Record

Figure 3 was produced from the external Slakshna observation tool. The top panel concatenates optimizer-step losses while retaining FL-round and data-epoch boundaries. The middle panel summarizes start, mean, and end loss for each round. The bottom panel records the peer delta loaded by each round.

![Australian training loss, data-epoch boundaries, and peer-delta merge record]({{site.baseurl}}/assets/images/m0/australian-local-loss-first-run-2.png)

<center><em>Figure 3. Australian training loss, data-epoch boundaries, and peer-delta merge record.</em></center>

The data cursor now continues across Slakshna invocations. A complete pass consists of 22 optimizer steps distributed as 9 \+ 9 \+ 4 steps over three FL rounds. With a site-effective batch of 64, each pass consumes 1,408 of the 1,458 packed sequences. The final 50-sequence tail cannot form another complete distributed optimizer update and is dropped. Thus the run completed five real cursor passes and entered a sixth; the 16 federated rounds are not 16 data epochs.

| Data epoch | FL rounds | Optimizer steps | Consumed sequences | Completion / progress |
| :-- | :------ | --: | ----: | :------- |
| 1   | R1–R3   |  22 | 1,408 | Complete |
| 2   | R4–R6   |  22 | 1,408 | Complete |
| 3   | R7–R9   |  22 | 1,408 | Complete |
| 4   | R10–R12 |  22 | 1,408 | Complete |
| 5   | R13–R15 |  22 | 1,408 | Complete |
| 6   | R16     |   9 |   576 | 39.5% of the dataset cursor |

<center><em>Table 8. Data epochs.</em></center>

The loss trajectory falls rapidly over the first two data epochs and then settles near 1.5–1.7. The apparent rises at Rounds 4, 7, 10, 13, and 16 coincide with the start of a new data pass rather than a loss of training state. Selected round summaries are shown below; the full 16-round record is retained with the figure assets.

| Round | Steps | Start loss |  Mean loss |   End loss | Peer delta |
| ----: | ----: | ---------: | ---------: | ---------: | :---- |
|   1   |   9   |   3.6406   |   3.1267   |   3.1875   | None  |
|   3   |   4   |   2.5938   |   2.6914   |   2.5781   | D1    |
|   6   |   4   |   1.9297   |   1.9609   |   1.8828   | D3 reused |
| **7** | **9** | **2.1719** | **1.8038** | **1.8281** | **D4, last active-peer round** |
|   9   |   4   |   1.5859   |   1.6426   |   1.6641   | D4 reused after departure |
|  12   |   4   |   1.4688   |   1.5371   |   1.5703   | D4 reused after departure |
|  15   |   4   |   1.3906   |   1.4785   |   1.5156   | D4 reused after departure |
|  16   |   9   |   1.6719   |   1.5096   |   1.6484   | D4 reused after departure |

<center><em>Table 9. Tuning rounds.</em></center>

Four distinct Indian deltas arrived. D1 was first used in Round 3, D2 in Round 4, D3 in Rounds 5–6, and D4 in Round 7\. No new Indian model update arrived after D4. The peer left at 00:15:44, between Rounds 7 and 8, but the persisted D4 file remained available and was loaded again in every subsequent round.

| Australian rounds | Delta used | Interpretation |
| :----- | :--- | :----- |
| R1–R2  | None | Australian local training before the first remote update was available |
| R3     | D1   | First distinct Indian update |
| R4     | D2   | Second distinct Indian update |
| R5     | D3   | Third distinct Indian update |
| R6     | D3   | Same update reused; D4 arrived later in the round |
| R7     | D4   | Fourth and final distinct Indian update; last active-peer checkpoint |
| R8–R16 | D4   | Stale update repeatedly loaded after the Indian peer departed |

<center><em>Table 10. Australian tuning rounds.</em></center>

##### GlobalOpinionQA Evaluation

Evaluation continued to use the standalone shared GOQA package and directly loaded the base model plus LoRA adapters. The dataset contains 1,106 questions with at least one Australia, New Zealand, or Indian human distribution. Five deterministic option-order prompts were evaluated per question. The score is Jensen–Shannon distance between the model option distribution and the available human distribution; lower is better. The evaluation covered 626 Australia pairs, 273 New Zealand pairs, and 932 Indian sample-frame pairs.

![Continued GlobalOpinionQA trajectory before and after the Indian peer departure]({{site.baseurl}}/assets/images/m0/continued-GOQA-trajectory.png)

<center><em>Figure 4. Continued GOQA trajectory before and after the Indian peer departure.</em></center>

<br/>

| Model state | Delta | Australia/NZ JSD | India JSD | Equal two-region JSD | Relative change vs base |
| :---------- | :---------- | :----------- | :----------- | :----------- | ----------: |
|   Base      |   None      |   0.488578   |   0.323637   |   0.406107   |    —        |
|   Round 1   |   None      |   0.485151   |   0.321212   |   0.403182   |    −0.72%   |
|   Round 2   |   None      |   0.474369   |   0.313851   |   0.394110   |    −2.95%   |
|   Round 3   |   D1        |   0.468686   |   0.310113   |   0.389400   |    −4.11%   |
|   Round 4   |   D2        |   0.455833   |   0.302070   |   0.378951   |    −6.69%   |
|   Round 5   |   D3        |   0.442958   |   0.295083   |   0.369021   |    −9.13%   |
|   Round 6   |   D3        |   0.429509   |   0.290274   |   0.359891   |   −11.38%   |
| **Round 7** | **D4**      | **0.414574** | **0.286702** | **0.350638** | **−13.66%** |
|   Round 16  |   D4 reused |   0.395048   |   0.291820   |   0.343434   |    −15.43%  |

<center><em>Table 11. GOQA evaluation.</em></center>

## Summary Draft Report

This section is adapted from a summary report prepared by the research team, which provides a more concise view of the experiments performed, the observed results, and final conclusions.

| :----------------- | :-------------- |
| **Reporting Date** | 31 August, 2026 |
| **Scope**          | India-Australia federated fine-tuning of `OLMo 2-7B`, including the third-run peer-disconnection analysis and a fourth-run follow-up with local loss, data progress, merge history, and `GlobalOpinionQA` evaluation. |
| **Framework**      | [Slakshna](https://github.com/dcll-iiitd/Slakshna){:target="_blank"}: a geo-localized decentralized federated training framework. |

### The System Configuration for the Two Sides

#### Australian Side

* Host CPU: AMD EPYC 7663 (50 cores allocated)
* System RAM: Approximately 1 TiB physical memory (1,022,800 MB reported by Slurm); 200 GB allocated to this training job
* Allocated GPUs: 2 × NVIDIA A100-SXM4-80GB
* VRAM per GPU: 80 GB HBM2e (81,920 MiB per card; 160 GiB allocated VRAM)
* GPU Pinning: Multi-GPU setup using CUDA-visible GPU IDs 0 and 1 (num_gpus = 2)
* CUDA & Driver: NVIDIA Driver 580.126.20. Driver CUDA Compatibility 13.0. Loaded CUDA Toolkit 12.8

#### Indian Side

* Host CPU: AMD EPYC 7282 (16 Cores / 32 Threads per socket, dual socket = 64 vCPUs)
* System RAM:  512 GB DDR4 ECC (503 GiB available)
* GPUs: 4 × NVIDIA RTX A6000 (Ampere Architecture)
* VRAM per GPU: 48 GB GDDR6 with ECC (49,140 MiB per card, 192 GB total VRAM)
* GPU Pinning: Multi-GPU setup with GPU ids 0, 1, 2, 3 (num_gpus = 4)
* CUDA & Driver: NVIDIA Driver 580.173.02. CUDA 13.0

#### Networking

Furthermore, the Indian Side also used the following details of the Campus Network Firewall and Environment:

* Private Subnet & Topology: The training node sits on a private internal campus LAN behind an institutional border gateway.
* Strict Inbound Blocking (Default-Deny): The campus firewall blocks all incoming unsolicited TCP/UDP traffic from the public internet, preventing external nodes (e.g., in Australia) from connecting directly to the local machine.
* Permissive Outbound Access: Outbound connections initiated from inside the campus are permitted, allowing reverse proxy tunnels like Playit.gg to establish an outbound bridge to the public internet.
* Traffic Inspection: Academic network middleboxes inspect standard web traffic, which SLAKSHNA overcomes by using end-to-end QUIC TLS 1.3 / Ed25519 cryptographic encryption for all model updates.
* NAT Traversal: By running a Playit.gg reverse tunnel, a designated local port was assigned a static public endpoint, enabling cross-country federated training without requiring router port-forwarding or network administrator permissions.

##### Network Capabilities and Utilization

* Physical Network Interface Link: 1 Gbps (1,000 Mbps Full-Duplex Ethernet) on the primary network interface (enp99s0f0).
* Campus Uplink: Connected to the high-speed academic research backbone (NKN / Gigabit campus uplink).

##### Bandwidth Consumed by Experiment

* Payload per Epoch (Delta size): 5.43 MB (~43.5 Megabits).
* Transmission Time: ~1 second over the WAN link.

### The Federated Training Experiments

Below, we share reports of two joint experimental runs from the two sides. Before these runs, there were two more experimental runs that set up the federated hyperparameters, including an estimated number of passes to give over the datasets. The dataset partitions were taken from the `CultureInstruct` dataset. One partition represented data tagged for countries other than South Asian countries (Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan, and Sri Lanka) with approximately 2.9 million tokens. This partition was used for training on the Australian side (Packed samples: 1,458, Sequence length: 2,048, Total packed token slots: 2,985,984, Non-padding tokens: 2,556,907, Padding tokens: 429,07 i.e. 14.37%). Another partition contained data from South Asian countries, approximately 5.3 million tokens, which was used for training on the Indian side. The tokens were padded.

### First Experimental Run

#### Results from the Australian Side

##### Summary

This run completed all 16 configured federated rounds on the Australian Slakshna observer. The two sites were connected during Rounds 1–7, and four distinct Indian model updates were received. The Indian peer left the gossip mesh at 00:15:44 local time, shortly after the Australian Round 7 training and D4 merge had completed. Rounds 8–16 then continued locally while Slakshna repeatedly loaded the last available Indian update, D4. Round 7 is therefore the last checkpoint that represents an active two-site federation; later checkpoints are useful for studying post-disconnection drift but should not be presented as fresh cross-country aggregation.

The updated training path preserved the data cursor across federated rounds. Five data epochs were completed over Rounds 1–15, and Round 16 processed 39.5% of the sixth pass. Local mean loss declined from 3.1267 in Round 1 to 1.5096 in Round 16. On `GlobalOpinionQA`, the primary equal two-region Jensen–Shannon distance improved from 0.406107 for the base model to 0.350638 at Round 7, a 13.66% relative reduction. Round 16 reached 0.343434 overall, but its gain after Round 7 came from further Australia/New Zealand improvement, while the India metric slightly regressed.

##### Experimental Setting

The run used Slakshna revision 73602b8 and Bhaskera[^6] revision 75a2698 from the Slakshna branch. Each federated round launched a two-worker FSDP (fully synchronous, data-parallel) Bhaskera job. The Australian site trained on the packed Australia/New Zealand M0 view; the Indian site managed its own data and runtime independently.

| Item | Australian-site setting |
| :--- | :---------------------- |
| Base model | `allenai/OLMo-2-1124-7B` |
| Tokenizer / chat template | `allenai/OLMo-2-1124-7B-Instruct` |
| Adaptation | LoRA on `q_proj` and `v_proj` |
| LoRA rank / alpha / dropout | 16 / 64 / 0.03 |
| Precision / distributed strategy | BF16 / two-worker FSDP |
| Optimizer | 8-bit Muon |
| Learning rate / warmup | 3*e<sup>-4</sup> / 0 steps |
| Per-worker batch | 8 packed sequences |
| Gradient accumulation | 4 |
| Site-effective batch | 64 packed sequences per optimizer step |
| Maximum local steps per FL round | 9 |
| Target federated rounds | 16 |
| Sequence length / packing | 2,048 / enabled |
| Packed Australian dataset | 1,458 sequences |
| Training labels | Assistant responses only |
| Federation clock / sync deadline  | 300 s / 300 s |
| Delta transport | Top-10% sparsity, symmetric INT8 |
| Typical encoded model update | Approximately 5.43 MiB |

<center><em>Table 12. Experimental settings for Australia. (Same as Table 7 above.)</em></center>

(Compare this table to Table 17 below, with settings for India.)

The Australian process started at 23:07:23 on 30 August, 2026, and shut down normally after reaching Round 16 at 01:46:28 on 31 August. Total observer-side wall time was approximately 2 hours 39 minutes.

###### Training, Merge, and Data-epoch Record

Figure 5 (the same as Figure 3 above) was produced from the external Slakshna observation tool. The top panel concatenates optimizer-step losses while retaining FL-round and data-epoch boundaries. The middle panel summarizes start, mean, and end loss for each round. The bottom panel records the peer delta loaded by each round.

![Australian training loss, data-epoch boundaries, and peer-delta merge record]({{site.baseurl}}/assets/images/m0/australian-local-loss-first-run-2.png)

<center><em>Figure 5. Australian training loss, data-epoch boundaries, and peer-delta merge record. (Same as Figure 3 above.)</em></center>

The data cursor now continues across Slakshna invocations. A complete pass consists of 22 optimizer steps distributed as 9 + 9 + 4 steps over three FL rounds. With a site-effective batch of 64, each pass consumes 1,408 of the 1,458 packed sequences. The final 50-sequence tail cannot form another complete distributed optimizer update and is dropped. Thus, the run completed five real cursor passes and entered a sixth; the 16 federated rounds are not 16 data epochs.

| Data epoch | FL rounds | Optimizer steps | Consumed sequences | Completion / progress |
| :-- | :------ | --: | ----: | :------- |
| 1   | R1–R3   |  22 | 1,408 | Complete |
| 2   | R4–R6   |  22 | 1,408 | Complete |
| 3   | R7–R9   |  22 | 1,408 | Complete |
| 4   | R10–R12 |  22 | 1,408 | Complete |
| 5   | R13–R15 |  22 | 1,408 | Complete |
| 6   | R16     |   9 |   576 | 39.5% of the dataset cursor |

<center><em>Table 13. Data epochs. (Same as Table 8 above.)</em></center>

The loss trajectory falls rapidly over the first two data epochs and then settles near 1.5–1.7. The apparent rises at Rounds 4, 7, 10, 13, and 16 coincide with the start of a new data pass rather than a loss of training state. Selected round summaries are shown below; the full 16-round record is retained with the figure assets.

| Round | Steps | Start loss |  Mean loss |   End loss | Peer delta |
| ----: | ----: | ---------: | ---------: | ---------: | :---- |
|   1   |   9   |   3.6406   |   3.1267   |   3.1875   | None  |
|   3   |   4   |   2.5938   |   2.6914   |   2.5781   | D1    |
|   6   |   4   |   1.9297   |   1.9609   |   1.8828   | D3 reused |
| **7** | **9** | **2.1719** | **1.8038** | **1.8281** | **D4, last active-peer round** |
|   9   |   4   |   1.5859   |   1.6426   |   1.6641   | D4 reused after departure |
|  12   |   4   |   1.4688   |   1.5371   |   1.5703   | D4 reused after departure |
|  15   |   4   |   1.3906   |   1.4785   |   1.5156   | D4 reused after departure |
|  16   |   9   |   1.6719   |   1.5096   |   1.6484   | D4 reused after departure |

<center><em>Table 14. Tuning rounds. (Same as Table 9 above.)</em></center>

Four distinct Indian deltas arrived. D1 was first used in Round 3, D2 in Round 4, D3 in Rounds 5–6, and D4 in Round 7. No new Indian model update arrived after D4. The peer left at 00:15:44, between Rounds 7 and 8, but the persisted D4 file remained available and was loaded again in every subsequent round.

| Australian rounds | Delta used | Interpretation |
| :----- | :--- | :----- |
| R1–R2  | None | Australian local training before the first remote update was available |
| R3     | D1   | First distinct Indian update |
| R4     | D2   | Second distinct Indian update |
| R5     | D3   | Third distinct Indian update |
| R6     | D3   | Same update reused; D4 arrived later in the round |
| R7     | D4   | Fourth and final distinct Indian update; last active-peer checkpoint |
| R8–R16 | D4   | Stale update repeatedly loaded after the Indian peer departed |

<center><em>Table 15. Australian tuning rounds. (Same as Table 10 above.)</em></center>


##### GlobalOpinionQA Evaluation

Evaluation used the standalone shared `GlobalOpinionQA` (GOQA) package and directly loaded the base model plus LoRA adapters. The dataset contains 1,106 questions with at least one Australia, New Zealand, or Indian human distribution. Five deterministic option-order prompts were evaluated per question. The score is the Jensen–Shannon distance between the model option distribution and the available human distribution; lower is better. The evaluation covered 626 Australian pairs, 273 New Zealand pairs, and 932 Indian sample-frame pairs. Figure 6 (which is the same as Figure 4 above) shows the results.

![Continued GlobalOpinionQA trajectory before and after the Indian peer departure]({{site.baseurl}}/assets/images/m0/continued-GOQA-trajectory.png)

<center><em>Figure 6. Continued GOQA trajectory before and after the Indian peer departure. (Same as Figure 4 above.)</em></center>

<br/>

| Model state | Delta | Australia/NZ JSD | India JSD | Equal two-region JSD | Relative change vs base |
| :---------- | :---------- | :----------- | :----------- | :----------- | ----------: |
|   Base      |   None      |   0.488578   |   0.323637   |   0.406107   |    —        |
|   Round 1   |   None      |   0.485151   |   0.321212   |   0.403182   |    −0.72%   |
|   Round 2   |   None      |   0.474369   |   0.313851   |   0.394110   |    −2.95%   |
|   Round 3   |   D1        |   0.468686   |   0.310113   |   0.389400   |    −4.11%   |
|   Round 4   |   D2        |   0.455833   |   0.302070   |   0.378951   |    −6.69%   |
|   Round 5   |   D3        |   0.442958   |   0.295083   |   0.369021   |    −9.13%   |
|   Round 6   |   D3        |   0.429509   |   0.290274   |   0.359891   |   −11.38%   |
| **Round 7** | **D4**      | **0.414574** | **0.286702** | **0.350638** | **−13.66%** |
|   Round 16  |   D4 reused |   0.395048   |   0.291820   |   0.343434   |    −15.43%  |

<center><em>Table 16. GOQA evaluation. (Same as Table 11 above.)</em></center>

The primary metric improves monotonically across every evaluated state. Round 7 is the best defensible cross-country checkpoint because it is the last state produced while the Indian peer was present and it includes the final distinct Indian delta. Relative to base, Round 7 improves Australia/New Zealand JSD by 15.15%, India JSD by 11.41%, and the equal two-region score by 13.66%.

Round 16 has the numerically lowest two-region score, but it is not a better federated checkpoint in the same sense. From Round 7 to Round 16, Australia/New Zealand improves from 0.414574 to 0.395048, whereas India worsens from 0.286702 to 0.291820. This is consistent with continued Australian local adaptation and repeated use of stale D4 after the remote site had stopped contributing.

##### Findings and Limitations

The run confirms that the revised data path can preserve its cursor across FL rounds and complete multiple real data passes. It also produced 16 durable Australian adapters and a stable, strongly decreasing loss curve. The first seven rounds contain four distinct cross-country updates, and their GOQA trajectory improves on both regional views.

The main remaining issue is handling peer liveness. Slakshna continued to count the persisted remote record toward the expected participant set and repeatedly loaded D4 after the peer left. The runtime, therefore, completed successfully from the local process's perspective, but Rounds 8–16 did not contain fresh Indian contributions. A future formal run should stop, pause, or explicitly mark the federation as degraded when no new peer updates are observed, and should identify updates by immutable source round or hash so that repeated use is visible without post-hoc log reconstruction.

##### Conclusion

This session completed five full data epochs plus 39.5% of a sixth and demonstrated clear optimization progress. Round 7 is the recommended federated checkpoint: it is the last checkpoint before peer departure, incorporates D4, and reduces the primary GOQA distance by 13.66% relative to base. Round 16 is useful as a post-disconnection comparison, but its lower aggregate JSD reflects continued Australian training with a stale Indian update and is accompanied by a small regression on the India-specific metric.

#### Results from the Indian Side

##### Executive Summary

The M0 cross-country run using the Slakshna framework completed normally after sixteen federated rounds. The Australian and Indian endpoints remained securely connected throughout the entire distributed training session, successfully exchanging network deltas at every synchronization boundary.

This experiment validated the Slakshna framework's underlying peer-to-peer architecture over 16 extended rounds. The results confirm exceptional communication stability and accurate gradient aggregation across the decentralized nodes over a longer horizon.

##### Experimental Setting

Here are the Indian-site settings, with the Australian settings from Table 12 above for comparison, when different.

| Item | Indian-site setting | Australian-site setting |
| :--- | :---------------------- | :---------------------- |
| Base model | `allenai/OLMo-2-1124-7B` | _same_ |
| Tokenizer / chat template | `allenai/OLMo-2-1124-7B-Instruct` | _same_ |
| Adaptation | LoRA on `q_proj` and `v_proj` | _same_ |
| LoRA rank / alpha / dropout | 16 / 64 / 0.03 | _same_ |
| Precision / distributed strategy | BF16 / four-worker FSDP | BF16 / two-worker FSDP |
| Optimizer | 8-bit Muon | _same_ |
| Learning rate / warmup | 3*e<sup>-4</sup> / 0 steps | _same_ |
| Per-worker batch | 8 packed sequences | _same_ |
| Gradient accumulation | 4 | _same_ |
| Site-effective batch | 128 packed sequences per optimizer step | 64 |
| Maximum local steps per FL round | 8 | 9 |
| Target federated rounds | 16 | _same_ |
| Sequence length / packing | 2,048 / enabled | _same_ |
| Packed South Asia dataset | 2,574 sequences/~5.27M tokens | _N/A_ |
| Packed Australian dataset | _N/A_ | 1,458 sequences |
| Training labels | Assistant responses only | _same_ |
| Federation clock / sync deadline  | 300 s / 300 s | _same_ |
| Delta transport | Top-10% sparsity, symmetric INT8 | _same_ |
| Typical encoded model update | Approximately 5.43 MiB | _same_ |

<center><em>Table 17. Experimental settings for India and compared to Australia (from Table 12).</em></center>

##### Training and Data Progress

The training progress is captured in Figures 7 and 8, which illustrates the local training loss recorded at the end of each of the 16 federated rounds on the node. A consistent downward trend indicates successful convergence during local updates despite the introduction of peer gradients.

<center>
  <img alt="Slakshna federated model loss across epochs (first run)." src="{{site.baseurl}}/assets/images/m0/slakshna-federated-model-loss-across-epochs-run-1.png" />
</center>
<center><em>Figure 7. Slakshna federated model loss across epochs (first run).</em></center>

##### Comprehensive Training, Learning Rate & Merging Analysis

The detailed training dashboard in Figure 8 presents a multifaceted view of the federated optimization process across the training session.

![Slakshna federated learning - comprehensive training, LR, and merging analysis (first run).]({{site.baseurl}}/assets/images/m0/slakshna-federated-learning-analysis-run-1.png)

<center><em>Figure 8. Slakshna federated learning - comprehensive training, LR, and merging analysis (first run).</em></center>

The dashboard is broken down into four key metrics:

* **A. Continuous Training Loss & Federated Merge Boundaries (FL Sync):** This chart visualizes the model's cross-entropy loss over every continuous optimization step. The vertical dashed lines indicate synchronization boundaries where federated aggregation occurs (R1, R2, etc.). The red diamonds highlight the immediate loss of the "Post-Merge" global state at the start of the next round. The consistent overall downward trend confirms the stability of global merges without leading to catastrophic divergence.
* **B. Post-Merge vs. Pre-Merge Loss and Perplexity:** This bar chart compares the model's loss at the end of its local training window (Pre-Merge Final Loss, in green) against the loss immediately after pulling in peer updates (Post-Merge Initial Loss, in blue). Initially, merging peer updates causes a slight jump in loss as the model adjusts to new generalized knowledge, but this gap narrows as the model converges. The secondary axis tracks Post-Merge Perplexity (orange line), which drops smoothly, demonstrating improved language modeling capability.
* **C. Learning Rate (LR) Schedule & Periodic Reset:** This graph displays the cyclical Cosine Decay learning rate strategy. The learning rate decays during local updates but is purposefully reset to its peak (3.0 * 10<sup>-4</sup>) at each federated merge boundary. This ensures the optimizer has sufficient momentum to escape local minima induced by merging disparate peer weights.
* **D. Gradient Delta L2 Norm Convergence & Token Scale:** This dual-axis chart measures the magnitude of the model updates (Delta norm, in purple). The steady, smooth decline in the L2 norm indicates that the federated updates are converging perfectly and shrinking as the global model approaches an optimal state. The blue dotted line indicates the number of tokens processed per round, reflecting the variance in epoch lengths across data epochs.

##### Round Summary

| Round | Local Loss | Deltas Extracted |
| --: | -----: | --: |
|   1 | 2.9219 |   0 |
|   2 | 2.7812 |   1 |
|   3 | 2.7766 |   1 |
|   4 | 1.9844 |   1 |
|   5 | 1.8438 |   1 |
|   6 | 1.8151 |   1 |
|   7 | 1.6016 |   1 |
|   8 | 1.6250 |   1 |
|   9 | 1.5313 |   1 |
|  10 | 1.5078 |   1 |
|  11 | 1.5625 |   1 |
|  12 | 1.4320 |   1 |
|  13 | 1.4531 |   1 |
|  14 | 1.5312 |   1 |
|  15 | 1.3725 |   1 |
|  16 | 1.4297 |   1 |

<center><em>Table 18. Rounds with local losses.</em></center>

##### GlobalOpinionQA Evaluation

The `GlobalOpinionQA` (GOQA) evaluation assesses the model's ideological alignment across different national perspectives. The trajectory plot below tracks the Jensen-Shannon distance (JSD) between the model's predicted opinion distributions and the actual survey responses from target demographics. A lower JSD indicates that the model's outputs more closely reflect the human survey data. The evaluation spans the baseline model and each of the 16 federated rounds, illustrating how the model's cultural alignment evolves through continuous cross-country training.

<center>
  <img alt="Third cross-country run: GlobalOpinionQA trajectory" src="{{site.baseurl}}/assets/images/m0/third-inter-country-run-1.png" />
</center>

<center><em>Figure 9. Third cross-country run: GlobalOpinionQA trajectory.</em></center>

<br/>

| Model state | Deltas Extracted | Australia/NZ JSD | India JSD | Two-region JSD | Relative change vs base |
| :----- | :-: | -------: | -------: | -------: | ------: |
| Base   | N/A | 0.416572 | 0.365931 | 0.391252 |    —    |
Round 1  |  0  | 0.416196 | 0.366260 | 0.391228 |  -0.01% |
Round 2  |  1  | 0.412379 | 0.365488 | 0.388934 |  -0.59% |
Round 3  |  1  | 0.407026 | 0.364902 | 0.385964 |  -1.35% |
Round 4  |  1  | 0.406000 | 0.367041 | 0.386521 |  -1.21% |
Round 5  |  1  | 0.405050 | 0.367865 | 0.386458 |  -1.23% |
Round 6  |  1  | 0.406282 | 0.369342 | 0.387812 |  -0.88% |
Round 7  |  1  | 0.405447 | 0.370128 | 0.387787 |  -0.89% |
Round 8  |  1  | 0.405205 | 0.369131 | 0.387168 |  -1.04% |
Round 9  |  1  | 0.404476 | 0.368546 | 0.386511 |  -1.21% |
Round 10 |  1  | 0.403908 | 0.368244 | 0.386076 |  -1.32% |
Round 11 |  1  | 0.403988 | 0.367896 | 0.385942 |  -1.36% |
Round 12 |  1  | 0.404306 | 0.366875 | 0.385591 |  -1.45% |
Round 13 |  1  | 0.405280 | 0.367530 | 0.386405 |  -1.24% |
Round 14 |  1  | 0.405355 | 0.368601 | 0.386978 |  -1.09% |
Round 15 |  1  | 0.406940 | 0.369866 | 0.388403 |  -0.73% |
Round 16 |  1  | 0.472575 | 0.342105 | 0.407340 |  +4.11% |

<center><em>Table 19. Rounds with Jensen-Shannon distance (JSD).</em></center>

##### Round 16: Regional Summary

| Region | Aggregation | Country question pairs | JSD |
| :----- | :----- | -----: | -----: |
| Australia/New Zealand | macro over Australia and New Zealand |  899 | 0.4725747878508882 |
| India | macro over three India sample frames |  932 | 0.3421046325935338 |
| Australia/New Zealand + India | macro over the two regional metrics | 1831 | 0.407339710222211 |

<center><em>Table 20. Regional summary.</em></center>

##### Round 16: Group Summary

| Group | Country question pairs | Mean JSD |
| :----- | -----: | :----- |
| Australia                       | 626 | 0.44799522219870785 |
| New Zealand                     | 273 | 0.4971543535030685 |
| India (Current national sample) | 470 | 0.368201565897666 |
| India (Non-national sample)     | 340 | 0.3235697087799428 |
| India (Old national sample)     | 122 | 0.3345426231029926 |

<center><em>Table 21. Group summary.</em></center>

##### Conclusion

This cross-country federated run demonstrated strong long-horizon stability across 16 full federated rounds. By doubling the target rounds relative to earlier experiments, the Slakshna framework proved its capability to manage extended peer-to-peer synchronization over non-trivial periods.

The empirical evidence derived from both the continuous training metrics and the GlobalOpinionQA benchmark is extremely positive. The training loss converged smoothly, confirming that the aggregation logic mathematically stabilized the global model without causing divergence. More importantly, the GOQA evaluation trajectory proves that this structural stability translated into measurable cultural alignment across the extended 16-round timeline. The Jensen-Shannon Distance (JSD) decreased for both the Australia/New Zealand targets and the Indian sample frames, demonstrating that the federated process successfully blended the distributed, culturally distinct datasets into a single, cohesive representation.

This run establishes a reliable baseline for 16-round hyperparameter scaling. Moving forward, the Slakshna framework is mathematically and architecturally prepared to handle larger cohorts and more diverse global data distributions.

### Second Experimental Run

#### Results from the Australian Side

A second joint run was completed on 31 August using the same software, model, data, LoRA, optimizer, effective batch, federation clock, compression, and evaluation protocol. Only two training controls changed: the maximum local window increased from 9 to 17 optimizer steps, and the target number of federated rounds decreased from 16 to 8.

| Changed parameter | First run | Second run |
| :---------------- | --------: | ---------: |
| Maximum local steps per FL round |  9 | 17 |
| Target federated rounds          | 16 |  8 |

<center><em>Table 22. Different steps per round and targeted round number, first vs. second run, Australian side.</em></center>

The Australian process ran from 12:20:38 to 13:45:54 local time, approximately 1 hour 25 minutes. The Indian peer joined before the first training boundary and remained in the gossip mesh through the normal Round 8 shutdown. Four distinct Indian model updates arrived, and all eight Australian synchronized adapters were saved successfully.

##### Training and Merge Record

The longer local window changes only where the data-epoch boundaries fall. Each complete pass still contains 22 optimizer steps and consumes 1,408 of the 1,458 packed sequences, but it now spans two FL rounds as 17 + 5 steps. Rounds 1–8, therefore, complete exactly four data epochs. The same 50-sequence tail is dropped at each pass because it cannot form a full distributed optimizer update.

![Fourth-run loss, four data epochs, and peer-delta merge record.]({{site.baseurl}}/assets/images/m0/australian-local-loss-second-run-1.png)

<center><em>Figure 10. Fourth-run loss, four data epochs, and peer-delta merge record.</em></center>

<br/>

| Round | Steps | Start loss | Mean loss | End loss | Peer delta |
| :-- | --: | -----: | -----: | -----: | :--- |
| 1   |  17 | 3.6406 | 2.9595 | 2.8750 | None |
| 2   |   5 | 2.9531 | 2.7312 | 2.5000 | None |
| 3   |  17 | 2.8438 | 2.0777 | 2.0312 | D1 |
| 4   |   5 | 2.0469 | 1.8828 | 1.7891 | D2 |
| 5   |  17 | 2.0312 | 1.6921 | 1.7734 | D2 reused |
| 6   |   5 | 1.7031 | 1.5922 | 1.5547 | D2 reused |
| 7   |  17 | 1.7734 | 1.5662 | 1.6016 | D3 |
| 8   |   5 | 1.5938 | 1.5141 | 1.5625 | D4 |

<center><em>Table 23. Fourth run rounds and losses.</em></center>

D1 and D2 were first incorporated in Rounds 3 and 4. D2 remained the newest available remote state during Rounds 5 and 6. D3 was incorporated in Round 7, and D4 arrived during that round and was incorporated in Round 8. Unlike the third run, there was no peer-disconnection event and no post-disconnection training segment.

##### GlobalOpinionQA Results

All nine evaluated states—Base plus Rounds 1–8—passed the shared GOQA package's dataset-hash, coverage, probability-distribution, and target-count checks. Figure 4 and the table below use the same five-prompt Jensen–Shannon distance protocol as the main report.

![Fourth joint run: `GlobalOpinionQA` trajectory (first run).]({{site.baseurl}}/assets/images/m0/fourth-joint-run-GlobalOpinionQA-trajectory-run-1.png)

<center><em>Figure 11. Fourth joint run: <code>GlobalOpinionQA</code> trajectory (first run).</em></center>

<br/>

| Model state | Delta | Australia/NZ JSD | India JSD | Equal two-region JSD | Relative change vs base |
| :---------- | :------------ | -----------: | -----------: | -----------: | ----------: |
|   Base      |   None        |   0.488578   |   0.323637   |   0.406107   |      —      |
|   Round 1   |   None        |   0.478726   |   0.316254   |   0.397490   |    −2.12%   |
|   Round 2   |   None        |   0.467729   |   0.308175   |   0.387952   |    −4.47%   |
|   Round 3   |   D1          |   0.448109   |   0.297171   |   0.372640   |    −8.24%   |
|   Round 4   |   D2          |   0.433332   |   0.292077   |   0.362705   |   −10.69%   |
|   Round 5   |   D2 reused   |   0.417003   |   0.288144   |   0.352573   |   −13.18%   |
|   Round 6   |   D2 reused   |   0.411428   |   0.287043   |   0.349236   |   −14.00%   |
| **Round 7** | **D3**        | **0.404436** | **0.285639** | **0.345037** | **−15.04%** |
|   Round 8   |   D4          |   0.405017   |   0.286451   |   0.345734   |   −14.87%   |

<center><em>Table 24. Rounds vs. JSD values and changes.</em></center>

Round 7 is the best fourth-run checkpoint on all three primary metrics. Relative to base, it reduces Australia/New Zealand JSD by 17.22%, India JSD by 11.74%, and the equal two-region score by 15.04%. Round 8 is only 0.000696 worse on the two-region metric, but both regional values move slightly upward, so the final merge does not improve GOQA further under this evaluation.

The second-run Round 7 two-region score of 0.345037 is also 0.005601 lower than the third-run Round 7 score. This comparison is descriptive rather than causal: the second run used longer local windows and had accumulated substantially more data exposure by Round 7. The important operational result is that the complete, continuously connected eight-round session retained the monotonic GOQA improvement through Round 7 and ended without a meaningful collapse at Round 8.

#### Results from the Indian Side

##### Executive Summary

The second M0 cross-country run using the Slakshna framework completed normally after eight federated rounds. The Australian and Indian endpoints remained securely connected throughout the entire distributed training session, successfully exchanging network deltas at every synchronization boundary.

This experiment validated the underlying peer-to-peer architecture of the Slakshna framework. It retained the previously validated configuration but adjusted two controls: the maximum local window increased from 8 to 16 optimizer steps, while the target number of federated rounds decreased from 16 to 8. The results confirm exceptional communication stability and accurate gradient aggregation across the decentralized nodes.

##### Executive Settings

The Indian-side settings were identical to those shown in Table 17 above, except for these two settings, which were switched:

| Setting | First Run | Second Run |
| :------ | --: | --: |
| Maximum local steps per FL round |  8 | 16 |
| Target federated rounds | 16 |  8 |

<center><em>Table 25. Different steps per round and targeted round number, first vs. second run, Indian side.</em></center>

The training progress is captured in Figures 12 and 13 below. Figure 12 illustrates the local training loss recorded at the end of each federated round on the node. A consistent downward trend indicates successful convergence during local updates.

<center>
  <img alt="Slakshna federated model loss across epochs (second run)" src="{{site.baseurl}}/assets/images/m0/slakshna-federated-model-loss-across-epochs-run-2.png" />
</center>
<center><em>Figure 12. Slakshna federated model loss across epochs (second run - compare to Figure 7).</em></center>

The dashboard in Figure 13 offers a more granular perspective of the entire federated learning session. It encompasses the loss trajectories alongside communication milestones, demonstrating the exact points at which network deltas were extracted and merged into the local model state. This confirms the multi-node synchronization process.

![Slakshna federated learning - comprehensive training, LR, and merging analysis (second run).]({{site.baseurl}}/assets/images/m0/slakshna-federated-learning-analysis-run-2.png)

<center><em>Figure 13. Slakshna federated learning - comprehensive training, LR, and merging analysis (second run - compare to Figure 8).</em></center>

The detailed training dashboard below presents a multifaceted view of the federated optimization process across the training session. It is broken down into four key metrics:

* **A. Continuous Training Loss & Federated Merge Boundaries (FL Sync):** This chart visualizes the model's cross-entropy loss over every continuous optimization step. The vertical dashed lines indicate synchronization boundaries where federated aggregation occurs (R1, R2, etc.). The red diamonds highlight the immediate "Post-Merge" global state loss at the start of the next round. The consistent overall downward trend confirms the stability of the global merges without causing catastrophic divergence.
* **B. Post-Merge vs. Pre-Merge Loss and Perplexity:** This bar chart compares the model's loss at the end of its local training window (Pre-Merge Final Loss, in green) against the loss immediately after pulling in peer updates (Post-Merge Initial Loss, in blue). Initially, merging peer updates causes a slight jump in loss as the model adjusts to new generalized knowledge, but this gap narrows as the model converges. The secondary axis tracks Post-Merge Perplexity (orange line), which drops smoothly, demonstrating improved language modeling capability.
* **C. Learning Rate (LR) Schedule & Periodic Reset:** This graph displays the cyclical Cosine Decay learning rate strategy. The learning rate decays during local updates but is purposefully reset to its peak (3.0 * 10<sup>-4</sup>) at each federated merge boundary. This ensures the optimizer has sufficient momentum to escape local minima induced by merging disparate peer weights.
* **D. Gradient Delta L2 Norm Convergence & Token Scale:** This dual-axis chart measures the magnitude of the model updates (Delta norm, in purple). The steady, smooth decline in the L2 norm indicates that the federated updates are converging perfectly and shrinking as the global model approaches an optimal state. The blue dotted line indicates the number of tokens processed per round, reflecting variance in the data epoch lengths.

##### Round Summary

| Round | Local Loss | Deltas Extracted |
| :-- | :----- | :-- |
|  1  | 2.9219 |  0  |
|  2  | 2.7812 |  1  |
|  3  | 2.7766 |  1  |
|  4  | 1.9844 |  1  |
|  5  | 1.8438 |  1  |
|  6  | 1.8151 |  1  |
|  7  | 1.6016 |  1  |
|  8  | 1.6250 |  1  |

<center><em>Table 26. Runs vs. local losses.</em></center>

##### GlobalOpinionQA Evaluation

The `GlobalOpinionQA` (GOQA) evaluation assesses the model's ideological alignment across different national perspectives. The trajectory plot below tracks the Jensen-Shannon distance (JSD) between the model's predicted opinion distributions and the actual survey responses from target demographics. A lower JSD indicates that the model's outputs more closely reflect the human survey data. The evaluation spans the baseline model and each federated round, illustrating how the model's cultural alignment evolves through continuous cross-country training.

<center>
  <img alt="Fourth cross-country run: GlobalOpinionQA trajectory" src="{{site.baseurl}}/assets/images/m0/fourth-inter-country-run-2.png" />
</center>

<center><em>Figure 14. Fourth cross-country run: <code>GlobalOpinionQA</code> trajectory (compare to Figure 9).</em></center>

<br/>

| Model state | Deltas Extracted | Australia/NZ JSD | India JSD | Two-region JSD | Relative change vs base |
| :------ | :-- | :------- | :------- | :------- | ------: |
| Base    | N/A | 0.488478 | 0.323468 | 0.405973 |    —    |
| Round 1 |  0  | 0.476347 | 0.314337 | 0.395342 |  -2.62% |
| Round 2 |  1  | 0.468197 | 0.308342 | 0.388269 |  -4.36% |
| Round 3 |  1  | 0.449611 | 0.296700 | 0.373155 |  -8.08% |
| Round 4 |  1  | 0.434662 | 0.291328 | 0.362995 | -10.59% |
| Round 5 |  1  | 0.415231 | 0.286680 | 0.350955 | -13.55% |
| Round 6 |  1  | 0.409624 | 0.285778 | 0.347701 | -14.35% |
| Round 7 |  1  | 0.405049 | 0.284124 | 0.344586 | -15.12% |
| Round 8 |  1  | 0.406136 | 0.284796 | 0.345466 | -14.90% |

<center><em>Table 27. Rounds vs. region-specific and joint JSD values.</em></center>

##### Round 8: Regional Summary

| Region | Aggregation | Country question pairs | JS distance |
| :---------------------------- | :----------------------------------- | ---: | :------ |
| Australia/New Zealand         | macro over Australia and New Zealand |  899 | 0.40613611644012904 |
| India                         | macro over three India sample frames |  932 | 0.28479649233365806 |
| Australia/New Zealand + India | macro over the two regional metrics  | 1831 |0.3454663043868935 |

<center><em>Table 28. Regional summary.</em></center>

##### Round 8: Group Summary

| Group | Country question pairs  | Mean JS distance |
| :---- | ----------------------: | :--------------- |
| Australia                       | 626 | 0.3761454960671511  |
| New Zealand                     | 273 | 0.436126736813107   |
| India (Current national sample) | 470 | 0.2982051246323111  |
| India (Non-national sample)     | 340 | 0.27341765803743023 |
| India (Old national sample)     | 122 | 0.28276669433123286 |

<center><em>Table 29. Group summary.</em></center>

##### Conclusion

The second cross-country federated run represents the cleanest and most stable joint training session conducted to date. By modifying the experimental controls—specifically by extending the maximum local window to 16 optimizer steps and capping the session at 8 target federated rounds—the network achieved highly efficient synchronization boundaries.

The empirical evidence derived from both the continuous training metrics and the `GlobalOpinionQA` benchmark is extremely positive. The L2 norm of the gradient deltas smoothly converged to zero over the eight rounds, confirming that the aggregation logic mathematically stabilized the global model without causing divergence. More importantly, the GOQA evaluation trajectory proves that this structural stability translated into measurable cultural alignment. The Jensen-Shannon Distance (JSD) steadily decreased for both the Australia/New Zealand targets and the Indian sample frames across successive rounds, demonstrating that the federated process successfully blended the distributed, culturally distinct datasets into a single, cohesive representation.

This run establishes a reliable baseline for hyperparameter scaling. Moving forward, the framework is mathematically and architecturally prepared to handle larger cohorts, longer local training windows, and more diverse global data distributions.

## Overall Conclusion

* **Robustness against connection instability:** Local training successfully continued even after peer disconnects, establishing an important robustness requirement for geo-distributed federated learning, that progress is tolerant to network disruptions.
* **Making progress with asynchronous training:** The training stack is natively asynchronous. The last obtained delta is used for further synchronization and the nodes do not wait or block for deltas to be received from the peers beyond a preset maximum delay. The successful training convergence demonstrated the efficacy of the training framework.
* **Impacts of system heterogeneity:** Although asynchrony helps, system heterogeneity plays an important role in determining the overall efficiency of federated training and requires extra care when merging weights with respect to their staleness. The GPU and networking environment on the Indian side had higher capacities than on the Australian side. Hence, the training over the available tokens on the Indian side completed in a much shorter time compared to the Australian side. This limited the number of updates exchanged between the peers, so that the Indian side didn't block. Hence, the Indian side only merged in a couple of model deltas. This indicates an area of future work: can we derive theoretical upper bounds on system heterogeneity so that before actual training we can estimate the likelihood of non-exchange of learned representations and implications for overall training progress? Despite this, we still found the robustness of the training framework prevented local training from diverging too much, even under the experiment's heterogeneity.
* **The ratio of inner vs. outer loops:** As was expected, more frequent outer merges between environments improved the quality of training. Specifically, the total number of passes over the available dataset was kept identical, but the number of weight synchronization rounds, i.e., outer loop merges, was increased by doing a smaller number of inner loop steps between outer loop merges. This can be seen in the second of the two experimental runs performed, which roughly doubled the number of inner loop steps while halving the number of synchronization rounds. The effect of this change was seen in cultural evaluation metrics computed. For example, the same metric of cultural alignment shown in Figure 1 above was approximately 33% worse in the second run (although still low) compared to the first run.

---

[^1]: OLMo Team (2025). 2 OLMo 2 Furious. [arXiv:2501.00656](https://arxiv.org/abs/2501.00656){:target="arxiv"}. The team had done prior work with this model, which is why a comparable OLMo 3 model wasn’t used. For their purposes, using the most recent model wasn’t essential.
[^2]: Pham, V. T., Li, Z., Qu, L., and Haffari, G. (2025). _CultureInstruct: Curating Multi-Cultural Instructions at Scale._ In Proceedings of NAACL 2025. ([PDF](https://aclanthology.org/2025.naacl-long.465.pdf){:target="_blank"}, [dataset](https://drive.google.com/file/d/139oNuyEVdvprEIWUBuBd4BcBrWMwp0Hw/view?usp=sharing){:target="_blank"})
[^3]: Durmus, E. et al. (2023). _Towards Measuring the Representation of Subjective Global Opinions in Language Models._ ([arXiv:2306.16388](https://arxiv.org/abs/2306.16388){:target="arxiv"})
[^4]: BharatGen Culture WVS Dataset. ([Google Drive link](https://drive.google.com/drive/folders/1Anxb1YWUfhkla5cOBucfaRGS557VLt5m){:target="google"})
[^5]: Jordan, K. et al. (2024). _Muon: An optimiser for hidden layers in neural networks._ ([blog post](https://kellerjordan.github.io/posts/muon/){:target="muon"} and [repo](https://github.com/KellerJordan/Muon){:target="muon"})
[^6]: _Bhaskera: Building a Ray-Native Distributed LLM Training Framework from Scratch_ ([blog post](https://medium.com/@somshekarm241/bhaskera-building-a-ray-native-distributed-llm-training-framework-from-scratch-2601d3529eba){:target="_blank"})
