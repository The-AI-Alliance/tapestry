# Making a Decision on #200: the M1 Domain-specific Model to Build

Dean Wampler, September 21, 2026

I have attempted to organize and summarize the discussion in [#200](https://github.com/The-AI-Alliance/tapestry/issues/200), along with some additional points to help us close on a decision soon. I have attempted to paraphrase the issue comments accurately. Let me know of any omissions or misrepresentations.

## TL;DR

* The M1 model goals promote the core valuation proposition of Tapestry, including consortium training, responsible use of protected data, and cultural alignment.
* The M1 model should be uniquely useful, even though time and resources preclude it being a comprehensive solution for the target domain.
* Of the possible target domains, healthcare is an appealing choice because of the protected data challenges, although meeting them in M1 would be difficult.
* No matter the choice made, we need to identify specific use cases to target, corresponding training and tuning data, domain experts for validation, and automated evaluations for ensuring efficacy.
* Two detailed healthcare use cases have been proposed, [A Better Healthcare Model for Spreading Tropical Diseases](#proposal-1) and [A Better Healthcare Model for Local Conditions](#proposal-2). Variations of these proposals were also suggested.
* There are pros and cons to making a decision right now:
	* **Pros:** The sooner we decide, the sooner we can begin the preliminary work, like lining up the data sources and domain experts we need. Also, it can be frustrating to keep debating a decision.
	* **Cons:** Since we don't have the compute resources yet that we need, we can't start tuning yet anyway.

## Goals

The M1 model should demonstrate some of the core value claims of Tapestry, at small and doable scale, and provide enough utility and novelty that it attracts more people and resources into our project. Here are five suggested goals:

1. Trained on N >= 3 sovereign nodes (even if one node does most of the work), using continued pre-training and/or post-training on an existing open weight base model.
2. Uses some protected data for training, or at least some data stays local to each sovereign node with only weights & metadata shared back and forth.
3. Addresses a culturally-informed set of tasks (use cases), e.g. local languages/cultural alignment + specific health, legal or finance domain tasks from several user sources. This demonstrates the importance of sovereign-aligned and owned intelligence, not just a domain benchmark winner.
4. (stretch goal) Demonstrate at least one example private derivative created with the same open source platform; the weights are not shared back.
5. (stretch goal) Reflects feedback and validation from real-world domain experts. They should be a third party, neither Tapestry nor goal 4.

Out of scope for M1:
* Large scale model (greater than a few ~10Bs parameters)
* Production readiness
* Support for model-level anti-memorization of protected data and other privacy guarantees.

## Requirements

* **Uniquely Useful:** Meaning it provides leading capability in a specific domain, rather than a general purpose model.
* **Public Recipes:** For customization, e.g., tuning, and deployment, which would enable local/sovereign alignment and use.
* **Targeted Evaluations:** Verification and known limitations to ensure trust.
* **Provenance Documentation:** The base model and data sets were used responsibly.
* **Sized Appropriately:** Large enough to be effective. Small enough to be doable.
* **Built on an ideal Base Model:** Discussed in [#210](https://github.com/The-AI-Alliance/tapestry/issues/210).
* **Artifacts Released:**
	1. Open weight model, Apache 2.0 license. (Base model must be license compatible.)
	2. At least one demo, not production ready.
	3. Research papers, white papers, blog posts, etc.
	4. Open-source training platform for the whole work flow.

#200 comment links feeding these requirements: [1,3](#comment-links))

## Several Suggestions Were Made

* A model that supports a specific under-served language. (comment links: [2](#comment-links))
	* For example, Vietnamese, native Indian languages and dialects, Thai.
* A domain-specific model for the following possible domains:
	* Finance (links: [1-2](#comment-links))
		* For example, fraud detection.
	* Healthcare (links: [6-8](#comment-links))
	* Education (links: [1-2](#comment-links))
		* Generally good for teaching and culturally aligned.
	* Government and public service (links: [2](#comment-links))
		* For example, a model could specialize in searching and analyzing local government news and helping users understand policy documents, navigate forms, and access public services.
	* Industrial (links: [1](#comment-links))
		* Past examples built by Alliance members include [SemiKong](https://arxiv.org/abs/2411.13802) and [Llamarine](https://arxiv.org/abs/2503.00203).

While we have to pick one target domain and set of use cases, due to resource limitations, if we have interested experts in other domains, they can lay the groundwork for subsequent models in their domains.

A separate _dimension_ is how much the domain model is culturally aligned and specific vs. independent of those concerns.

### What We Need

For the target domain, we need to identify the following:

* The domain subset of interest.
    * E.g., in healthcare, do we focus on patient records, provider assistance (e.g., notes transcription), ...?
* The use cases we want to improve.
    * This will determine what custom evaluations we write to verify our work.
    * This is also where domain expertise will be essential.
* Catalog data sets for post training.
    * Public, with no restrictions.
    * Protected, with clearly-described restrictions. For M1, our planned data infrastructure most likely won't be ready to support protected data.
    * Synthetic data
* Evaluations we need
    * What _acceptance criteria_ would end users expect in order to be willing to use the model?

(links: [9](#comment-links))

## Example Detailed Use Cases for Healthcare

Several detailed use cases were subsequently suggested in healthcare as possible targets, or at least they had the goal of stimulating discussion on specific, non-trivial, yet tractable problems to address.

Healthcare is an appealing target because it is _difficult_. It has significant data privacy requirements, but if Tapestry can meet them while utilizing that data responsibly, it would provide a major step forward in responsible AI.

### Kinds of Healthcare Data

* **Patient/EHR Data:** Electronic health record data requires rigorous management to meet PII and other regulatory requirements. In the near term (M1 and beyond), using differential privacy to extract only demographic data, without any identifying information, is a good place to start first.
* **Institutional Proprietary Data:**
* **Literature and public clinical QA data sets:** E.g., MedQuAD. carry essentially none of the risks carried by real patient data.
* **Synthetic and anonymized real data:** Good stand-ins for protected data, like EHRs, if created reliably.

(links: [4-5](#comment-links))

<a id="proposal-1"></a>

### Proposal 1: A Better Healthcare Model for Spreading Tropical Diseases

#### Problem Statement

Due to global warming and highly mobile people and commerce, tropical diseases endemic to warmer parts of Africa, Asia, and the Americas are spreading into new areas, even across ocean boundaries. Healthcare practitioners in the new areas are often ill prepared to diagnose occurrences of these diseases, and these diseases are poorly represented in AI models they are currently using for assistance (a claim that needs to be verified...).

#### Solution

Adapt (using a combination of CPT, SFT, and RL) an existing model, possibly a healthcare model like [MedGemma](https://deepmind.google/models/gemma/medgemma/), or a generic base model to be better at matching symptoms to tropical diseases.

If the endemic regions have extensive records of occurrences of these disease, use these data sets for adaption. Notes:

* Non-PII data: e.g., government statistics about demographics, symptoms, locations, etc. Unlikely to be restricted in any way, but they may already be "scraped" by data aggregators. If they are not already used in model training, e.g., because they have some _friction_ for access, then they are more beneficial to us.
* Sovereign and PII data: Use differential privacy to extract and use the same kinds of statistical information with no PII leakage.

#### Advantages

* A focused, tangible solution for M1.
* The spread of tropical diseases is a growing, widely-recognized problem.
* Any sovereign data sets could be used for training by the corresponding local sovereign node.
* We have a possible source of patient data from a set of charity hospitals in India through ClinicaMind, an Alliance member organization. Some unanswered questions:
    * What IRB/ethics review is needed to access this data, if any has been done already?
    * Is the data already de-identified/anonymized, or would that need to happen as part of our pipeline?
    * What kind of data would this actually be, structured fields (diagnosis codes, demographics, lab values), unstructured clinical notes, or both? That changes both the governance requirements and the technical approach significantly.
* The solution does not require significant instruction or agent training, because prompting with responses will be the dominant modality, not workflows. Hence, the use case is an easier improvement to make to a model.
* Supports text-only or multi-modal enhancement.

#### Disadvantages

* Is the assumption valid that existing models are poor tools? This question needs confirmation.
* Gaining access to any healthcare related data sets will be challenging, in part due to natural caution by owners of such data.
* Generating synthetic data for this use case won't be feasible.

#### Variations

* Pick one or two specific diseases.
* Pick one or two specific specialties.

(links: [6](#comment-links))

<a id="proposal-2"></a>

### Proposal 2: A Better Healthcare Model for Local Conditions

#### Problem

General-purpose models, including those tuned for a domain like healthcare, will likely be poor at local cultural awareness, including:

* Local languages
* Local vernacular for healthcare conditions
* Local cultural sensitivities, e.g., related to gender, certain diseases and causes, etc.
* Local disease demographics and their impacts, e.g., smoking and air pollution are more common, and therefore more impactful, in some places vs. others.
* Local laws and regulations

#### Solution

Adapt (using a combination of CPT, SFT, and RL) an existing healthcare model like [MedGemma](https://deepmind.google/models/gemma/medgemma/) to be better culturally aligned for one target culture.

Find local data sets that reflect these cultural norms. The same _notes_ apply here that were listed in Proposal 1 above.

#### Advantages

* A focused, tangible solution for M1.
* Very well aligned to a Tapestry core goal, which is better tools and models for cultural alignment.
* Local healthcare providers may find the gap described negatively impacts their work (true??).
* We have a possible source of patient data from a set of charity hospitals in India through ClinicaMind, an Alliance member organization.
* Any sovereign data sets could be used for training by the corresponding local sovereign node.
* An _initial_ solution does not require significant instruction or agent training, because prompting with responses will be a good modality to target first, saving  workflows and agent scenarios for later.
* Primarily text-only.

#### Disadvantages

* Is the assumption valid that existing models are poorly aligned culturally? Do local healthcare providers perceive a problem? These questions need confirmation.
* Gaining access to any healthcare related data sets will be challenging, in part due to natural caution by owners of such data.
* Generating synthetic data for this use case won't be feasible.
* If the definition of "local" is _all of India_ for example, that would be an enormous amount of diversity to cover. Near term, we would probably pick one region and its one, most-common language.

#### Variations

* Pick one or two specific diseases.
* Pick one or two specific specialties.

(links: [6](#comment-links))

### Generalizations

The above two use cases where inspired by the following, earlier, more-general suggestions.

#### Tune an Open Healthcare-oriented Model to Improve Its Cultural Alignment for 1+ Cultures

For example, use MedGemma. Measure if the resulting model appears better for culturally-relevant medical use cases, even without any additional healthcare-specific tuning. Some possible examples:

* The tuned model is better informed about diseases that are more common in that culture than globally (e.g., certain infectious diseases more prevalent in warmer climates).
* The tuned model is more aware of the most likely local diagnoses for particular symptoms (e.g., a chronic cough is more likely to be a symptom of X in this area).
* The tuned model is more aware of the most likely local causes for a particular disease, vs. global cause percentages (e.g., smoking is more common in some areas than others).
* The tuned model better understands local, common "vernacular" for medical terms.
* The tuned model is more effective at summarizing a provider's notes into language and vernacular that patients can understand.

Data considerations: What data sources are best for this alignment, e.g., public epidemiological databases and regional health surveillance data, versus institution-specific records? That distinction matters for both feasibility and for how we would want to validate the results (public epidemiological data would need to stay current given regional disease prevalence shifts, while institutional data would need de-identification and independent review board (IRB) review, depending on the source.

(links: [7-8](#comment-links))

##### Tune an Open Healthcare-oriented Model to Improve Its Utility at Analyzing Healthcare Records

For example, use MedGemma. Measure if the resulting model appears better for analyzing healthcare records, possibly in these areas:

* For finding errors and suggesting corrections (e.g., different classification/billing codes are used vs. those that correspond to the diagnosis and tests ordered).
* For translating provider notes into records (e.g., finding the right classification/billing codes automatically based on the notes).
* For finding potential related tests or conditions to consider based on the patient's records. (hard..., but this is an area where differential privacy could be very impactful, as the training mostly needs trends, statistical correlations, and non-PII data, like age, gender, and approx. geographical location).
* For translating between different record standards or proprietary formats.

Data considerations: If the record analysis and related-test suggestion tuning draws on real institutional records (even aggregated/statistical, as noted for differential privacy), that would need IRB approval at the collaborating institution. Given the concerns about the M1 timeline, it might be worth clarifying up front which of these use cases assumes real patient records (even anonymized) versus synthetic/public data only, since that changes the approval timeline substantially.

(links: [7-8](#comment-links))

## When Do We Need to Decide?

Do we need to decide now?

**No:**

* Since we don't have the compute resources yet that we need, we can't start tuning yet, so we can take some more time to decide on a target.

**Yes:**

* The sooner we decide, the sooner we can begin necessary preliminary work, like lining up the data sources and domain experts we need.
* It can be frustrating to keep discussing an idea and not moving to a decision...

## Comment Links:

The links above refer to these items, which are links to the actual comments in issue 200.

1. [Initial description from Anthony Annunziata](https://github.com/The-AI-Alliance/tapestry/issues/200#issue-4989842561)
2. [Comment from Hunter Hector](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5547216421)
3. [Comment from Anthony](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5602252840)
4. [Comment from Anisha Kumar](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5621541236)
5. [Comment from Anthony](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5634487429)
6. [Comment from Dean](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5686038881)
7. [Comment from Dean Wampler](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5637408580)
8. [Comment from Anisha](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5647864200)
9. [Comment from Dean](https://github.com/The-AI-Alliance/tapestry/issues/200#issuecomment-5680219673)
