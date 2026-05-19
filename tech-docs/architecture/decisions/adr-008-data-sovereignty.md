# TAP-008: Data Sovereignty

| Field | Value |
| :---- | :---- |
| Status | Proposed |
| Confidence | High (5/5) |
| Date | May 19, 2026 |
| Deciders | Christopher Nguyen (proposed), workshop participants (to ratify) |

## Context

A unique feature of Tapestry is full support for various requirements for data sovereignty. Tapestry's governance principles prevent the use of unethically-acquired, restricted data sets, which have been used by many model builders in the past and currently.

However, this doesn't mean that Tapestry is limited to use only fully-open data sets. There are many data sets in the world that have requirements constraining their use, but if those requirements are met, training with these data sets can enrich models, especially in areas where open data provides insufficient coverage. Hence, fully supporting those requirements allows Tapestry to use as much data as is legally possible, with the benefit of creating more comprehensive foundation models (FMs) that meet the needs of a wider community than current models can meet.

Other data sets must remain completely private, e.g., because they include proprietary information or personal information protected by law. Fortunately, Tapestry's portable, flexible stack supports the spectrum from fully-open to private data for model training, tuning, and alignment scenarios, allowing Tapestry to build core foundation models with as much data as possible, while also enabling organizations to build custom models with the most private data at their disposal.

See also [TAP-001: Core-Plus-Sovereign Architecture](adr-001-core-plus-sovereign.md) and [TAP-002: Consortium Training Model](adr-002-consortium-training.md).

## Decision

### Support Categories of Data Sovereignty

Figure 1 shows several, broad categories of data sovereignty.

![Categories of Data Sovereignty](../diagrams/data-sovereignty.svg)

**Figure 1:** Categories of Data Sovereignty

These are broad categories, with many fine-grained variations possible. They can also overlap. For simplicity, each category is shown exclusively tied to either a partner node or the core operator in the [Consortium Training](adr-002-consortium-training.md) architecture (see also [Training Approaches](../../reference/training-approaches.md)), although there could be exceptions, in practice. 

Let's discuss the details.

#### Data Governance

All the categories of data are managed by a _governance enforcement_ capability. Even fully-open data needs this management to ensure that _every_ data set is properly categorized and responsibly managed. 

A challenge with governance is the prior limited governance of most of the world's data sets, especially those that are licensed as open, but often contain data that was gathered at some point from sources with more restrictive licenses (e.g., copyright content). There are various initiatives around the world to produce truly-clean data sets, but it will take time to fully address this problem.

#### Private Data

This is data with sensitive information that cannot be released publicly. For example, it can contain data with legally-protected privacy information or enterprise/industrial proprietary data.

In some cases, privacy-preserving techniques, like the differential privacy filter shown in Figure 1, will allow this data to be used for training Tapestry's FMs. In this way, only the information that can be safely extracted from this data will be visible to the model training regime.

Otherwise, this data will only be used for private model tuning, e.g., for an enterprise's custom applications or a healthcare provider's applications that use patient data. In those cases, differential privacy may or may not be used, depending on the sensitivity of the data and the potential for inadvertent leaks of sensitive details.

In both cases, the diagram shows private data only being used by partner nodes and not being shared with the core operator. This is the safest protocol to follow, but it doesn't inhibit the utility of this data for _consortium training_ of Tapestry FMs.

#### Sovereign Data

Sovereign data is subject to boundaries for access. For example, a nation may have laws that prevent certain citizen data from leaving the nation's sovereign boundaries. Enterprises have always had sensitive data that they do not want to leave their corporate _firewall_.

This category can overlap with the private data category. For example, a citizen's tax records are likely both private and restricted to national boundaries in many countries.

Sovereign data can only be used by a partner node within the sovereign boundary. When this data is used during the consortium training of Tapestry FMs, care may be required to prevent memorization of details, which would effectively exfiltrate at least some of the details, thereby violating the sovereignty constraints.

#### Unique Open Data

The partner nodes may have access to data that is truly open, but not generally accessible outside the node. For example, a core part of BrightQuery's business is based on the issue that a lot of data from the US and other governments is hard to access and in formats that are difficult to use for training and tuning.

However, since this data is fully open, at some future time it might be migrated/copied to the central data repository used by the core operator. In the meantime, it can be leveraged by the partner node during consortium training.

#### Controlled Data

This is data that is not fully open, but it has been licensed for use by Tapestry for training and tuning purposes. Therefore, it requires governance to prevent leakage of this data. Like sovereign data, it may be necessary to prevent memorization of this data by models, which could allow some details to become public.

It is possible that privacy preserving techniques will be necessary for some of this data, to control what information is visible to the training regime. (Not shown in the diagram.)

#### Fully-Open Data

This is the familiar category of data that has been properly curated and licensed for unrestricted, open use.

#### Other Considerations for Data that Isn't Fully Open

In a perfect world, _every_ Tapestry data set, model, tool, and process would be open-sourced. In practice, Tapestry will use some data that is restricted in some way and therefore not public. (We plan to open source all models, tools, and processes.)

Tapestry will need to publicly document the _metadata_ for all data sets used, even when the data itself can't be published.

### Data Exchange in Consortium vs. Local Training?

Figure 1 also shows that data is _not_ exchanged between the core operator and the partner nodes when consortium training is used for the Tapestry FMs. Only model weight updates are exchanged.

Periodically, the core sends updated weights to the partner nodes. The partner nodes run several training or tuning cycles using their _local_ data, after which they send model updates back to the core. 
The core uses an averaging algorithm to merge the updates from the partner nodes and the process begins again.

More specifically, the Tapestry [_sovereign pipeline_](../decisions/adr-005-sovereign-pipeline.md) is used for the following phases of model development:

1. _Pretraining_ - using most of the available, allowed data to create the base model
2. _Supervised fine tuning_ (SFT) - to improve general skills like instruction following
3. _Alignment_ - using DPO (direct preference optimization), RLHF (reinforcement learning with human feedback), Constitutional AI, or similar techniques to improve alignment to _universal_ standards of desired behaviors and values

When partner nodes use Tapestry FMs to create custom models, they following the same approach, with some changes of emphasis:

1. Continued _Pretraining_ - (optional) using unique and possibly restricted local data to continue training a copy of a Tapestry FM to improve the model
2. _Supervised fine tuning_ (SFT) - to improve general skills of particular interest for the target application
3. _Alignment_ - using DPO, RLHF, Constitutional AI, or similar techniques to improve alignment to specific _cultural values_ and  behaviors

## Rationale

- The sovereignty motive is national/institutional, not specific to individual data protection concerns. The governance model, trust assumptions, and communication patterns all differ. Fully supporting these sovereignty concerns is the _fundamental_ unique value proposition of Tapestry. Without this sovereignty support, Tapestry would not have a unique value proposition compared to other model development efforts.

## Confidence assessment

This proposal has high confidence, because of a) the central importance of data sovereignty for Tapestry's goals and b) the  existing tools and techniques that support sovereignty are well established.

## Alternatives considered

- **"Ignore sovereignty":** It's clear that fully embracing sovereignty requirements is necessary for Tapestry's unique value proposition.

## Consequences

- Requires all data and compute pipelines to have robust governance to enforce requirements.
- Requires every data set to be properly categorized and the necessary controls applied to it (e.g., differential privacy).

## References

- NVIDIA, [What Is Sovereign AI?](https://blogs.nvidia.com/blog/what-is-sovereign-ai/)
- RedHat, [What is sovereign AI?](https://www.redhat.com/en/topics/ai/sovereign-ai)
- Wikipedia, [Differential Privacy](https://en.wikipedia.org/wiki/Differential_privacy)
- Wikipedia, [Federated Learning](https://en.wikipedia.org/wiki/Federated_learning)
- World Economic Forum, [Sovereign AI: What it is, and 6 strategic pillars for achieving it](https://www.weforum.org/stories/2024/04/sovereign-ai-what-is-ways-states-building/)