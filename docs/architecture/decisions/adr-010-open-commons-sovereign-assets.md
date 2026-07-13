# TAP-010: Open Commons and Sovereign Assets

| Field | Value |
| :---- | :---- |
| Status | Proposed |
| Confidence | Strong (4/5) |
| Date | July 11, 2026 |
| Deciders | Tapestry Governance Committee (to ratify) |

## Summary

Tapestry is committed both to an open Shared Commons and to participant sovereignty. These commitments are complementary: openness prevents the shared platform, model, and standards from being captured, while participant control prevents openness from becoming a demand that nations, communities, or organizations surrender sovereign data, knowledge, or commercial assets.

The governing principle is:

> **Open where we share; sovereign where participants retain control.**

Tapestry-created shared artifacts are open and independently usable by default. Participant assets remain participant-controlled unless voluntarily contributed to the Shared Commons. Participants may keep data and source identities confidential, contribute only governed model-weight updates, license access to their data on terms of their choosing, and keep, license, or commercialize downstream sovereign variants without a contribution-back requirement. Contributions to the Shared Base and claims of Tapestry certification remain subject to proportionate legal, consent, safety, quality, provenance, and interoperability requirements.

## Context

Tapestry describes itself as open-source and anti-capture while also promising national, socio-cultural, and industrial sovereignty. These promises can appear to conflict if openness is interpreted as universal public disclosure.

That interpretation would undermine Tapestry's purpose. A nation may be legally unable to disclose public-sector data. A cultural community may protect sacred or collectively governed knowledge. A hospital or enterprise may rely on proprietary data that it cannot expose and may license commercially. These participants can still strengthen the Shared Base by training locally and contributing approved model-weight updates without transferring the underlying data.

The reverse risk also matters. If shared Tapestry code, protocols, model releases, or interoperability standards depend on proprietary permission, a provider or participant can capture the commons and compromise everyone else's sovereignty and exit.

This ADR therefore distinguishes the openness required of the Shared Commons from the control retained over Participant Sovereign Assets. It clarifies the anti-capture principle in both directions.

## Decision

### Openness is purpose-driven

Tapestry uses openness to prevent capture, enable independent operation, support scrutiny and collaboration, and preserve credible exit. Openness is not an obligation for participants to disclose or license assets they have not voluntarily contributed to the Shared Commons.

The degree and audience of disclosure must be sufficient for the applicable purpose. Public disclosure is preferred for shared artifacts. Consortium-confidential review, independent audit, contractual representation, attestation, or technical evaluation may be appropriate for sovereign assets when public disclosure would defeat a participant's legal, cultural, security, or commercial requirements.

### Two governing domains

| Domain | Definition | Default |
| :----- | :--------- | :------ |
| **Shared Commons** | Artifacts created collectively by Tapestry or voluntarily contributed for shared use | Open, permissively licensed, non-exclusive, independently usable, and free of contributor-specific encumbrances |
| **Participant Sovereign Assets** | Data, source identities, training processes, model updates, configurations, evaluations, and derivatives a participant has not contributed to the Shared Commons | Controlled by the participant and subject to its law, consent, governance, confidentiality, and commercial choices |

An artifact changes domains only through an explicit, authorized contribution. Participation, access to the Shared Base, or contribution of one artifact does not imply contribution of related assets.

### Shared Commons commitments

Subject to the final licensing decisions for each artifact class, Tapestry will keep the following open and independently usable:

- Tapestry-developed source code and shared training infrastructure.
- Shared protocols, schemas, contribution formats, and interoperability specifications.
- Public governance rules and contribution requirements.
- Public evaluation methods and certification criteria.
- Shared Base releases and the information needed to use, modify, and redistribute them.
- Datasets intentionally contributed for public release.
- Documentation needed for independent operation, migration, and exit.

No participant, vendor, contributor, or Tapestry operator may impose an exclusive service, proprietary runtime, contributor-specific license, or other avoidable dependency on the Shared Commons. Pragmatic dependencies are permitted only when they are visible, bounded, replaceable, and do not grant unilateral control.

### Participant Sovereign Assets

Participants retain control over assets they do not contribute to the Shared Commons, including:

- Raw, curated, private, sovereign, controlled, or proprietary data.
- Confidential dataset identities, sources, composition, and commercial provenance.
- Private CPT, fine-tuning, post-training, alignment, and evaluation artifacts.
- Participant constitutions, protected-knowledge rules, and local governance configurations.
- Participant-created adapters, experts, checkpoints, and Sovereign Models.
- Commercial terms for access to participant-controlled data or services.

Tapestry does not claim ownership or exclusivity over these assets and does not impose a contribution-back requirement on Private CPT, fine-tuning, post-training, or downstream Sovereign Models.

Subject to applicable law, the governing licenses, third-party rights, and the participant's own commitments, a participant may keep, deploy, license, sell, or otherwise commercialize its Sovereign Models and related services. A participant may license access to its raw or curated data independently, including charging commercial labs, even when governed weight contributions derived from that data have benefited the open Shared Base. Access to an open model does not imply access to its underlying data.

### Weight contribution does not transfer data rights

A participant may perform Contributed CPT locally and submit only the resulting model-weight update. Doing so does not disclose, license, or transfer ownership of the underlying data or its source identities.

The participant must nevertheless have sufficient rights and authorization to perform the training and to permit the intended use and distribution of the resulting weight contribution. A contribution accepted into the Shared Base must not introduce legal terms that encumber the Shared Base or reduce the rights of other participants.

Because models may memorize or expose training information, the fact that only weights cross the network does not by itself establish privacy, safety, or legal compliance. Contribution governance must evaluate the risks appropriate to the data, training method, threat model, and intended release.

### Proportionate disclosure and verification

Evidence about a contribution may be handled at the minimum disclosure level that satisfies its governance purpose:

| Level | Audience | Appropriate use |
| :---- | :------- | :-------------- |
| **Public** | Everyone | Shared datasets and artifacts; claims that require public reproducibility |
| **Consortium-confidential** | Authorized governance or review bodies | Sensitive provenance, licenses, consent records, or security details that participants can share under agreement |
| **Independent attestation** | Approved auditor or verifier | Evidence that cannot be disclosed to the consortium but can be checked against defined requirements |
| **Technical evaluation** | Contribution pipeline or evaluation environment | Quality, safety, memorization, poisoning, compatibility, and regression testing without raw-data access |
| **Contractual representation** | Parties to the consortium agreement | Legal rights, consent, and compliance claims where organizational assurance matches the stated threat model |

These mechanisms may be combined. Stronger technical verification remains available when required by law, sensitivity, weak trust, or the need for guarantees independent of organizational goodwill. Tapestry does not require public disclosure merely because a technical mechanism is possible, nor does it accept contractual assurance when the documented threat model requires technical proof.

### Shared contribution and certification boundaries

Participant freedom over private downstream work does not imply unconditional acceptance into the Shared Commons. Tapestry may reject or quarantine contributions that fail applicable legality, consent, provenance, quality, safety, security, memorization, poisoning, compatibility, or evaluation requirements.

Tapestry may also condition use of its certification marks, compatibility claims, or governance recognition on compliance with published standards. These conditions govern entry into the Shared Commons and claims of Tapestry conformance; they do not create ownership of or a contribution-back claim over private participant assets.

### Anti-capture in both directions

Tapestry must prevent:

1. **Capture of the commons:** shared infrastructure, models, standards, governance, or exit depend on proprietary permission or unilateral control.
2. **Capture of participants:** participation or access is used to compel disclosure, transfer, free licensing, or contribution of sovereign assets beyond what is necessary for the participant's explicit contribution and applicable governance requirements.

A policy satisfies this ADR only if it preserves an independently usable open Shared Commons and allows participants to withhold, exit with, license, and independently use assets they have not voluntarily contributed to that commons.

## Non-goals

This ADR does not:

- Weaken permissive licensing for Tapestry-developed shared code or Shared Base releases.
- Permit contributor-specific restrictions to propagate into or encumber the Shared Commons.
- Treat provenance, consent, legality, safety, or contribution quality as optional.
- Guarantee acceptance of opaque or unverifiable weight contributions.
- Require all evidence or provenance to be made public when a narrower governed disclosure satisfies the requirement.
- Require Tapestry certification for private downstream models or services.
- Give participants a right to use Tapestry names or marks without satisfying published requirements.
- Override applicable law, third-party rights, data commitments, or the governing license of an adopted base model.

## Reconciliation with earlier documents

This ADR identifies the following inconsistencies or ambiguities and proposes targeted changes. It does not silently reinterpret the earlier text.

| Document | Existing ambiguity or inconsistency | Proposed change |
| :------- | :---------------------------------- | :-------------- |
| PRD OS-1 | Requiring all "training data" to use CDLA-2.0 can be read to include private, sovereign, and controlled node data | Apply the common open-data license only to datasets intentionally released into the Shared Commons; cross-reference TAP-008 and this ADR |
| PRD OS-1 | "Any developer" redistribution language does not distinguish shared artifacts from Participant Sovereign Assets | Scope the guarantee to Shared Commons artifacts |
| TAP-008 | Public metadata for every dataset may expose confidential, culturally protected, security-sensitive, or commercially valuable provenance | Replace the universal public-disclosure rule with the tiered disclosure and verification model in this ADR |
| TAP-004 | Weights-only contribution does not explicitly state what rights remain with the participant | State that contributing weights transfers no access to or ownership of the underlying data and requires sufficient authority for the resulting contribution |
| TAP-005 | Local Sovereign-Build outputs are described as unshared but participant downstream rights are implicit | State participant control, no contribution-back, and private, proprietary, and commercial freedom explicitly |
| DG6 | Shared Base safety requirements may be read as control over all private derivatives | Clarify that shared governance applies to Shared Base contributions and Tapestry certification, while private variants remain participant-controlled subject to law and license |
| PRD and open questions | The participant business model and what remains proprietary are unresolved | Use this ADR as the default boundary while leaving consortium economics, benefit sharing, and optional commercial agreements for governance design |
| Anti-capture principle | The concise principle does not distinguish capture of the commons from compelled surrender by participants | Add a reference to this ADR's two-direction anti-capture interpretation |

## Rationale

- An open Shared Commons gives every participant recourse, portability, scrutiny, and exit, preventing Tapestry or a vendor from becoming the dependency Tapestry exists to replace.
- Participant control makes sovereignty real rather than rhetorical. Participants cannot contribute national, cultural, medical, or industrial value if doing so requires surrendering the assets that law, consent, duty, or commercial strategy requires them to protect.
- Weight-only contribution allows diverse sovereign knowledge to strengthen the shared model without centralizing raw data, but it must be coupled with proportionate contribution governance.
- Commercial freedom makes participation strategically rational and supports an ecosystem of competing sovereign services rather than a single Tapestry-controlled provider.
- Tiered verification aligns with Tapestry's collaborative consortium threat model while permitting stronger mechanisms when evidence or risk requires them.

## Alternatives considered

- **Universal public openness:** Require all data, provenance, training artifacts, and derivatives to be public. Rejected because it excludes many national, cultural, medical, and industrial participants and turns openness into a mechanism of extraction.
- **Participant control without an open commons:** Allow shared Tapestry artifacts to carry contributor-specific or proprietary terms. Rejected because it creates capture, fragments interoperability, and compromises exit.
- **Open weights with mandatory provenance publication:** Improves public reproducibility but can reveal protected or commercially valuable sources. Rejected as a universal rule; retained as the preferred level when it is compatible with participant sovereignty.
- **Purely technical verification:** Require secure aggregation, differential privacy, trusted execution, or cryptographic proof for every contribution. Rejected as the universal baseline because Tapestry supports legal and organizational assurance where it satisfies the stated threat model; retained where stronger technical guarantees are required.
- **No shared contribution governance:** Accept any weight update because no raw data is shared. Rejected because weights can carry safety, quality, legal, privacy, memorization, poisoning, and compatibility risks.

## Consequences

- Shared artifact licenses and contribution agreements must clearly identify the boundary between a submitted artifact and related Participant Sovereign Assets.
- Dataset and model documentation must support multiple evidence-disclosure levels rather than equating accountability with universal publication.
- Contribution evaluation must assess model-level risks without assuming access to raw training data.
- Participants can develop competing private and commercial offerings without seeking Tapestry permission or contributing their downstream work back.
- Tapestry certification and branding must be governed separately from ownership and private-use rights.
- The PRD, TAP-004, TAP-005, TAP-008, the anti-capture principle, and the glossary require the targeted follow-up edits identified above.
- Consortium economics, benefit sharing, and optional data-access marketplaces remain governance questions; this ADR establishes ownership and openness defaults without prescribing a single business model.

## Follow-on decisions

The following implementation and governance decisions may be resolved after acceptance. They do not alter or condition this ADR's core boundary between the open Shared Commons and Participant Sovereign Assets. Acceptance establishes the principles that must govern these decisions; it does not require the ratifying body to select every mechanism in advance.

1. Document which Tapestry-created Shared Base artifacts use Apache-2.0 and define how compatibility with differently licensed adopted third-party bases will be assessed under TAP-009, without presuming that an outside base must use the same license.
2. Establish the minimum non-public evidence that must accompany a weight contribution when source identities are withheld.
3. Designate the body that approves independent auditors and determines when contractual assurance is insufficient.
4. Define how memorization, poisoning, safety, and legal-risk tests operate without access to raw data.
5. Clarify through contribution agreements what rights, if any, arise from consortium-funded training performed on participant-controlled data beyond the submitted weight contribution, consistently with the ownership boundary established by this ADR.
6. Establish how data or consent revocation affects already integrated Shared Base releases while respecting confidentiality, applicable law, and technically irreversible effects.

## References

- [The Anti-Capture Principle](../../governance/anti-capture-principle.md)
- [Tapestry Vision Architecture Methodology](../0-tva-methodology.md)
- [Design Goals](../4-design-goals.md)
- [TAP-004: The Consortium Training Loop](adr-004-training-loop.md)
- [TAP-005: The Sovereign Build](adr-005-sovereign-pipeline.md)
- [TAP-008: Data Sovereignty](adr-008-data-sovereignty.md)
- [Product Requirements](../../strategic-plan/PRD.md)
- [Training Approaches](../../reference/training-approaches.md)
