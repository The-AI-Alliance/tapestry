# Open Data Spaces assessment

**Status:** Recommendation  
**Date:** September 14, 2026  
**Related issue:** [#195](https://github.com/The-AI-Alliance/tapestry/issues/195)

## Recommendation

Tapestry should adopt the Open Data Spaces (ODS) architectural patterns for discoverability, semantic interoperability, identity, and usage control, but should not make the ODS middleware a required dependency yet. The next step should be a bounded interoperability prototype that tests ODS against Tapestry's governance and data-management requirements.

This is a "patterns now, implementation after evidence" decision. It preserves an interoperability path without making an early platform commitment that has not been validated against Tapestry's large-artifact, sovereign-boundary, withdrawal, and audit needs.

## What was assessed

The assessment used the current ODS reference architecture and implementation materials, then compared them with Tapestry's [data governance requirements](data-governance-requirements.md) and [data management requirements](data-management-requirements.md). It focused on the capabilities most relevant to Tapestry:

- locating data without centralizing it;
- exchanging machine-readable metadata and semantics;
- authenticating participants and enforcing usage policy;
- keeping restricted bytes inside their permitted boundary;
- recording lineage, policy decisions, and withdrawal events; and
- operating the system without making one vendor or service a trust bottleneck.

ODS is a strong conceptual match. Its three main concerns—addressability and discoverability, ontology and semantic interoperability, and identity and usage control—map directly to Tapestry's requirements for resolvable artifact references, interoperable manifests, participant identity, and enforceable policy.

## Current maturity and gaps

The Information-technology Promotion Agency, Japan (IPA) publishes ODS-RAM V2, protocols, an SDK, and middleware. The public implementation organization also shows active protocol and deployment repositories. That is enough evidence to treat ODS as an implementable architecture rather than only a position paper.

However, IPA's published FAQ says that no certification or conformity-assessment program has been established. Tapestry therefore must not describe itself, a deployment, or an artifact as "ODS compliant" or "ODS certified." More importantly, the available materials do not by themselves prove that the implementation meets Tapestry's workload and governance constraints. Those claims need local evidence.

The main unanswered questions are:

- Can an ODS deployment transfer or reference multi-gigabyte artifacts without unnecessary buffering or copying?
- Can data and model weights remain local while metadata, policy, and computation requests cross the boundary?
- Are policy denial, consent withdrawal, and deletion propagated quickly and recorded immutably enough for Tapestry's audit model?
- Can Tapestry's manifests and policy vocabulary map to ODS protocols without losing meaning?
- What operational and security burden does the middleware add for a small sovereign participant?

## Options

| Option | Strengths | Risks | Decision |
| --- | --- | --- | --- |
| Tapestry standards-first MVP | Lowest initial operational cost; keeps manifests and policy interfaces small | Tapestry must maintain its own interoperability mappings | Use as the initial baseline |
| ODS SDK and middleware | Best direct alignment with ODS discovery, semantics, identity, and usage-control model | Performance, deployment complexity, and governance behavior are not yet demonstrated for Tapestry | Prototype before adopting |
| International Data Spaces connector model | Established reference architecture and detailed usage-control concepts | A connector-centric deployment may be heavier than the initial Tapestry architecture requires | Keep as a comparison and source of patterns |

## Required prototype

The prototype should connect two independently administered participants: one publishes a restricted test artifact and the other requests an allowed computation without receiving the raw artifact. It should use synthetic data and must not include personal, confidential, or culturally restricted material.

The prototype is successful only if it demonstrates all of the following:

1. A participant can discover metadata and resolve an artifact reference without exposing the artifact bytes.
2. Identity and authorization are checked at the serving boundary, including a recorded denial case.
3. The shared metadata preserves Tapestry's source, license, policy, version, checksum, and lineage fields.
4. A permitted computation can run where the artifact resides and return only the approved result.
5. A withdrawal event prevents new access, invalidates or marks affected derivatives, and creates auditable evidence.
6. A large test object is streamed with bounded memory use; throughput, latency, memory, and retry behavior are reported.
7. Setup steps, required services, trust anchors, secrets, and recovery procedures are documented for both participants.

The prototype report should include raw measurements, versions and configuration, failure cases, unresolved mappings, and an estimate of ongoing operator effort. Passing the prototype supports an ADR proposing ODS middleware adoption. Failing it should still produce reusable protocol mappings and identify which capabilities belong in Tapestry's own minimal interfaces.

## Decision guardrails

- Do not make the ODS SDK or middleware mandatory in the first Tapestry implementation before the prototype passes.
- Keep Tapestry manifests and policy contracts implementation-neutral so that ODS and other data-space systems can map to them.
- Treat identity, authorization, usage control, audit, and withdrawal as enforceable behavior, not metadata labels.
- Prefer protocol-level interoperability over shared infrastructure ownership.
- Reassess this recommendation when ODS publishes material compatibility changes or establishes a conformity program.

## Sources

- [IPA Open Data Spaces](https://www.ipa.go.jp/en/digital/opendataspaces/)
- [ODS Reference Architecture Model V2](https://www.ipa.go.jp/en/digital/architecture-guidelines/ouranos-ecosystem-dataspaces-ram-white-paper.html)
- [Open Data Spaces design philosophy](https://www.ipa.go.jp/en/digital/architecture-guidelines/open-dataspaces-design-philosophy.html)
- [Open Data Spaces implementation repositories](https://github.com/open-dataspaces)
- [International Data Spaces Reference Architecture Model](https://docs.internationaldataspaces.org/ids-knowledgebase/ids-ram-4/introduction/1_1_goals_of_the_international_data_spaces/1_2_purpose_and_structure_of_the_document)
- [International Data Spaces connector architecture](https://docs.internationaldataspaces.org/ids-knowledgebase/ids-ram-4/layers-of-the-reference-architecture-model/3-layers-of-the-reference-architecture-model/3_5_0_system_layer/3_5_2_ids_connector)
