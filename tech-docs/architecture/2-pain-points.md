# Phase 2 — Pain Point Analysis

*May 2026*

---

## Purpose

For each stakeholder layer identified in Phase 1, this document names the specific, concrete failures of the current AI ecosystem — not abstract sovereignty concerns but operational realities that block real actors from building or deploying AI that serves their needs. These pain points are what the architecture must address. If a pain point doesn't appear here, no architectural feature should be designed to solve it.

## National

**N1. Dependency without recourse.** A government ministry deploys a frontier model from a US or Chinese provider. The provider changes its terms of service, deprecates the model, or complies with its home government's sanctions. The ministry has no fallback — no weights, no training recipe, no ability to reproduce the capability internally. This has already happened with API deprecations; it will happen with geopolitical restrictions.

**N2. Data residency is unenforceable at the model level.** A nation passes data residency laws requiring that citizen data stay within its borders. But when that data is used to train a model hosted abroad, the "data" lives in the weights. There is no mechanism to extract it, audit it, or delete it. The law is satisfied on paper (raw data didn't leave) but violated in substance (the model's knowledge did).

**N3. Hardware heterogeneity has no training-level answer.** Sovereign AI strategies procure hardware from different vendors for different reasons — cost, supply chain diversification, diplomatic relationships, industrial policy. But training frameworks are tightly coupled to specific hardware ecosystems. A nation that buys AMD GPUs cannot easily participate in a training run optimized for NVIDIA, and vice versa. The problem is not vendor lock-in to any single vendor — both NVIDIA and AMD actively support sovereign AI — but that training infrastructure does not abstract across hardware the way it should. (See also: [Tracel AI / Burn proposal](https://github.com/The-AI-Alliance/tapestry/issues/9) for a backend-abstraction approach to this problem.)

> **Workshop question for Ziv (NVIDIA) and Niles (AMD):** *What does hardware-agnostic consortium training look like from your perspective? Can a consortium include both NVIDIA and AMD nodes in the same training run today, and what breaks?*

**N4. Sovereign models exist but nobody uses them.** Several nations have invested heavily in sovereign foundation models — built domestically, trained on local data, intended to serve local needs. Many see negligible adoption. The models underperform frontier alternatives on tasks users care about, the interfaces are less polished, the ecosystems have fewer integrations, and in multilingual countries the language coverage is uneven. Citizens and developers default to ChatGPT or Claude because they work better, defeating the sovereignty investment. The hard lesson: building a sovereign model is a supply-side achievement; adoption is a demand-side problem that sovereignty alone does not solve.

> **Workshop question for Ganesh (BharatGen), Antoine (Swiss AI/Apertus), Jian Gang (SEA-LION), Da-shan (MediaTek/Taiwanese GPT):** *What adoption rates are you seeing for your sovereign models? What would it take for domestic users to prefer your model over a frontier commercial alternative — is it quality, ecosystem, integration, or something else entirely? Does consortium training at Tapestry scale change the quality calculus enough to matter?*

**N5. Frontier capability requires frontier scale, which requires frontier capital.** A nation with $50M for AI cannot train a frontier model. The minimum viable investment for a competitive foundation model in 2026 is $200M–$1B. Nations below that threshold face a binary choice: use someone else's model, or build a sub-frontier model that nobody adopts. There is no middle path.

> **Workshop question for Ayah (Current AI), Arno (Elysee), Hideki (IPA Japan):** *What is the actual minimum viable investment for a sovereign model that people will use — not just one that exists? And does pooling resources via consortium training change the cost structure enough to cross the adoption threshold?*

## Socio-cultural

**SC1. Alignment is inherently local, but controlled centrally.** Frontier models encode a disposition toward the world — what is appropriate, important, true, polite, offensive, authoritative — that reflects the culture of the team that aligned them. This is not a bias bug; it is a structural property of centralized alignment. A model aligned in San Francisco will encode San Francisco assumptions about medicine, law, social hierarchy, humor, gender, religion, and professional norms. Those assumptions are invisible to the people who baked them in and wrong for most of the world's population. No amount of multilingual data fixes this. Language is a solvable data problem for any lab with sufficient compute. Cultural alignment is not — it requires local value judgments that only the community can make.

The [Inglehart-Welzel Cultural Map](https://www.worldvaluessurvey.org/WVSContents.jsp?CMSID=Findings) (World Values Survey & European Values Study, 2005–2022) makes this measurable: it plots countries on two axes — traditional vs. secular-rational values, survival vs. self-expression values — and shows that geographically close countries can be culturally distant. Japan and Vietnam are both "Asian" but sit in completely different cultural clusters. A model aligned to one cluster's values is systematically wrong for another.

This has been empirically confirmed: [Tao et al. (2024)](https://academic.oup.com/pnasnexus/article/3/9/pgae346/7756548) tested five GPT models against the World Values Survey across 107 countries and found that **all models cluster with English-speaking and Protestant European countries on the Inglehart-Welzel map** — most aligned with the Anglosphere, most distant from African-Islamic countries. This is not a bug in one model; it is a structural property of centralized training.

![GPT models plotted on the Inglehart-Welzel Cultural Map](diagrams/tao2024-gpt-cultural-map.jpg)
*All five GPT models land in the Protestant Europe / English-speaking cluster. Source: Tao et al., "Cultural Bias and Cultural Alignment of Large Language Models," [PNAS Nexus 3(9), 2024](https://academic.oup.com/pnasnexus/article/3/9/pgae346/7756548). Used under CC BY 4.0.* (See also: ["Fluent but Foreign"](https://arxiv.org/html/2505.21548), 2026, which shows that even regional LLMs trained on local language data still reflect the base model's cultural values.)

> **Workshop question (open floor):** *Can you give a concrete example where a frontier model's alignment — not its language capability — was wrong for your community in a way that could not be fixed by fine-tuning or prompting? These examples are what make the case for sovereign alignment layers.*

**SC2. Cultural knowledge is extracted, not compensated.** When a frontier model trains on a culture's publicly available texts, oral traditions transcribed by researchers, or indigenous knowledge digitized by NGOs, the resulting capability accrues to the model provider. The community receives no compensation, no attribution, no control over how their knowledge is represented or used. This is the extractive pattern of previous technologies repeated.

> **Workshop question for Anastasia (Pleias/Common Corpus), Sebastian (EleutherAI/SUCHO):** *Is there a working model — technical or legal — for data royalties or attribution at training scale? Or is this a problem that can only be solved architecturally, by keeping data sovereign and sharing only gradients?*

**SC3. Multilingual capability is necessary but not sufficient.** Frontier labs are adding language coverage rapidly — the multilingual gap is closing for major languages. But a model that speaks Yoruba with Silicon Valley values is not a sovereign model. The deeper gap is not linguistic but cultural: domain knowledge, professional norms, legal reasoning, medical practice, educational conventions, and social expectations that vary across communities and cannot be learned from web-crawled text alone.

**SC4. Corpora that exist nowhere else are held hostage by access terms.** A language community's most valuable training data — oral histories, literary traditions, religious texts, legal precedents in local languages — often sits in university archives or government repositories with restrictive access terms. The data cannot leave the institution, but the institution cannot train a model. The data is simultaneously too valuable to share and too locked up to use.

> **Workshop question for Roberto (Software Heritage), Slava (CODATA):** *You've both built systems for preserving and governing access to institutional data across jurisdictions. What governance model lets data contribute to training without leaving its institution?*

## Industrial

**I1. Domain data cannot leave the enterprise, and models cannot enter it.** A hospital system has millions of clinical records that would make a medical AI transformative. Regulatory constraints (HIPAA, GDPR) prevent sending that data to a cloud provider for training. And cloud-trained models, fine-tuned on public data, hallucinate on domain-specific tasks at rates that are clinically unacceptable. The data and the models are separated by a compliance wall that neither side can cross.

> **Workshop question for Dave (OpenMined), Arno (Elysee):** *If a French hospital node trains on GDPR-covered patient data and sends weight updates to an aggregator, does that constitute a data transfer under EU law? What technical guarantees (DP, secure aggregation) would make it legally defensible?*

**I2. Platform deprecation destroys enterprise AI investments.** An energy company spends 18 months building an AI pipeline on a provider's platform. The provider pivots its product strategy, deprecates the API, or changes pricing to make the deployment uneconomic. The enterprise has no weights, no training code, no portability. The investment is a sunk cost, and the company starts over with the next provider.

**I3. Idle compute has no market.** HPC centers, sovereign cloud providers, and large enterprises have GPU clusters that sit idle between workloads. There is no mechanism to contribute that compute to collective training in exchange for access to the resulting model. The compute-for-access model that would make participation rational does not exist as infrastructure.

> **Workshop question for Rick (Argonne), Eric (MBZUAI), Vincent (Red Hat):** *What fraction of your GPU capacity sits idle, and what would the terms need to look like for you to contribute it to a consortium training run? What are the real blockers — technical, institutional, or economic?*

**I4. Fine-tuning is not sovereignty.** An industrial actor fine-tunes an open-weights model on its domain data. The base model was trained by a third party on data the enterprise didn't choose, with alignment it didn't control, using architecture decisions it had no voice in. The fine-tuned model inherits all the biases, failure modes, and architectural limitations of the base. Fine-tuning is customization, not ownership.

**I5. No legitimacy mechanism for sovereign AI providers.** A company that builds sovereign AI capability for its country — training models on local data, aligning to local values, deploying on local infrastructure — has no way to signal that its offering meets any recognized standard. There is no certification, no seal of approval, no independent validation that a sovereign AI deployment is actually sovereign (rather than a thin wrapper around a foreign model). Without this, the entity cannot differentiate itself, and governments cannot evaluate competing claims of sovereignty.

## Individual

**IN1. Users have no representation in model training.** An individual's data — search history, documents, conversations — contributes to training through various collection mechanisms. The resulting model reflects aggregate patterns, not individual needs. There is no feedback loop where a user's priorities, language preferences, or values influence the model that serves them.

**IN2. Privacy is binary and inadequate.** The current choice is: share your data and lose control of it, or withhold your data and receive a generic model. There is no graduated mechanism where individuals can contribute to model improvement with calibrated privacy guarantees — sharing enough to benefit from personalization without exposing enough to enable surveillance or manipulation.

**IN3. Models assume the wrong world.** A developer in Jakarta, a researcher in Dakar, a farmer in rural India — all interact with models whose assumptions about what constitutes good advice, professional conduct, trustworthy information, and common knowledge were calibrated for a different society. The model may speak their language fluently while being substantively wrong about their context. This is not a localization problem; it is an alignment problem that manifests at the individual level.

**IN4. No agency over alignment.** A user who disagrees with a model's refusal, bias, or value judgment has no recourse. They cannot adjust the alignment to match their own values, cultural context, or professional needs. The alignment was set by the provider, and the user's only option is to switch providers — to another model whose alignment was also set by someone else.

> **Workshop question (open floor):** *Modular alignment — where sovereign nodes apply their own alignment layer on top of a shared base — is a core Tapestry proposition. But some safety researchers argue that alignment must be baked into pretraining, not bolted on after. Is modular alignment technically sound, or does it create models that can be trivially de-aligned? This is a genuine tension, not a rhetorical question.*

## Contributor/Participant

**CP1. Contribution without credit or governance.** An ML researcher contributes a training technique, a dataset, or a systems optimization to an open-source model. The technique is absorbed, the researcher receives a citation at best, and has no voice in how the model evolves. Open-source AI has contribution mechanisms but not governance mechanisms.

**CP2. No infrastructure for consortium training at scale.** Research groups that want to train collaboratively across institutions must build bespoke infrastructure for every project. There is no reusable platform for consortium training that handles gradient aggregation, privacy, fault tolerance, and heterogeneous hardware. Every collaboration starts from scratch.

> **Workshop question for Eric (Petuum), Laurent (INRIA), Erik (Zyphra):** *Has anyone in this room run outer-loop distributed training above 7B parameters on heterogeneous, high-latency clusters? What broke? This is the central open research question for Tapestry.*

**CP3. Architecture decisions are made by whoever trains first.** The architecture of a widely adopted open model (Llama, Mistral, Qwen) is set by the organization that trained it. Downstream contributors can fine-tune, distill, or extend, but cannot change the fundamental architecture. If the architecture was wrong for their use case — wrong tokenizer, wrong attention mechanism, wrong expert routing — they have no remedy short of training their own model from scratch.

**CP4. Incentives are misaligned with sustainability.** Training a frontier model is expensive. Maintaining, updating, and supporting it is more expensive. Open-source models are released but not sustained. Contributors burn out. Funding dries up after the initial release. There is no economic model that makes long-term maintenance of an open frontier model rational for any single organization.

> **Workshop question for Thomas (Hugging Face/BigScience), Ayah (Current AI):** *BigScience trained BLOOM as a one-shot collaboration. What economic model would have made it sustainable — not just trained, but maintained and updated? And from the funding side, what would Current AI need to see to fund ongoing operations, not just a single training run?*

---

## Cross-cutting Observation

Two pain points appear across every layer in different forms:

1. **The capability-sovereignty tradeoff is currently zero-sum.** You can have frontier performance (by using someone else's model) or sovereignty (by building your own sub-frontier model). No existing system offers both simultaneously.

2. **The unit economics of AI training enforce concentration.** Training costs create natural monopolies. Only organizations with $500M+ budgets can produce frontier models. This concentrates architectural decisions, alignment choices, and data governance in a handful of actors — regardless of their intentions.

These two observations are candidates for the primary design goals in Phase 4. Phase 3 should validate whether Tapestry's value proposition credibly addresses both.

> **Workshop question (synthesis session):** *Are "break the capability-sovereignty tradeoff" and "break the unit economics of training" the right two design goals? Or is there a third — perhaps around sustainability, safety, or cultural representation — that is equally load-bearing?*
