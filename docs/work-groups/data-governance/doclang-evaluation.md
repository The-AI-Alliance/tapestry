# DocLang Evaluation

| Field       | Value           |
| :---------- | :-------------- |
| Status      | Preliminary     |
| Confidence  | Medium (3/5)    |
| Created     | June 27, 2026   |
| Last Update | July 31, 2026   |

> [!NOTE]
> This note supports the [Data Management Requirements](data-management-requirements.md) and [issue #67](https://github.com/The-AI-Alliance/tapestry/issues/67).

[DocLang](https://doclang.ai/) is an open document format specification. [Issue #67](https://github.com/The-AI-Alliance/tapestry/issues/67) asks if we should use it as the preferred document format standard for Tapestry data preparation, storage, and workflows.

DocLang came out of the [Docling](https://www.docling.ai/) project, a document parsing and conversion toolkit, which can import and export DocLang, among other formats. Whether or not we use DocLing is an independent decision.

We begin with our summary recommendation, then provide background information.

## Summary Recommendation

We researched DocLang, but didn't prototype use of it.

Our recommendation is to postpone a decision on adopting DocLang as the required Tapestry document format. It is promising enough to pilot for document-heavy corpora, but the current format is still pre-1.0 and should be treated as an experimental interchange option until the project validates conversion quality, governance metadata, media handling,
tooling maturity, and cost of adoption. Also, Tapestry requirements for data processing and storage are still being developed, which would affect the choice of formats and tools.

### Recommended Near-term Actions

- Use DocLang in a small pilot for PDF, HTML, scanned, and table-heavy
  documents.
- Keep JSONL or Parquet as the prepared training-data interchange format for near-term pipeline work.
- Require converters to preserve Tapestry provenance, rights, residency, and allowed-use metadata.
- Revisit standardization after the pilot produces quality, cost, and tooling evidence.

## What Is DocLang?

DocLang is an XML-based document markup format designed for model consumption. The official specification describes version 0.7 and focuses on representing document structure, semantics, geometry, formatting, and complex document components such as tables, charts, formulas, code, forms, pictures, audio transcripts, and video segments.

The format is intentionally more structured than plain Markdown and more
token-conscious than general HTML. It also includes governance and compliance metadata concepts that are relevant to Tapestry data-governance requirements.

## Evaluation Against Questions in Issue #67

| Question | Initial answer | Notes |
| :------- | :------------- | :---- |
| Is it an improvement over the current ad hoc approach? | Potentially, for complex source documents. | It can preserve structure, layout, tables, formulas, images, and metadata more explicitly than plain extracted text. The benefit is smaller for already-clean plain text or simple JSONL records. |
| Is it stable and mature enough to adopt? | Not as a required project standard yet. | The current spec is version 0.7. Its versioning section treats 0.x as initial development where breaking compatibility is possible. |
| Is it flexible for different document kinds? | Yes for many document types, with validation needed. | The spec covers text, lists, tables, forms, code, formulas, pictures, charts, geometry, page breaks, and custom metadata. Tapestry still needs tests across real participant corpora. |
| What about non-text, such as images, audio, and video? | Images, audio, and video are described as first-class content. | `<picture>` can reference image URIs or embedded data URIs, charts can include structured tabular data, and current DocLang materials describe native primitives for transcripts, speakers, timestamps, scenes, and audio-visual grounding. Tapestry still needs pilot tests for real media-heavy corpora and its own governance metadata. |
| What would be the cost/effort required to adopt it? | Medium for a pilot, high for full standardization. | Adoption requires converters, validators, metadata mapping, quality tests, storage conventions, and downstream pipeline support. |

## Potential Fit For Tapestry

DocLang is most relevant for the following:

- Converting PDF, HTML, scanned, form-heavy, table-heavy, and layout-sensitive corpora into a consistent intermediate representation.
- Retaining page geometry and document structure for review and extraction
  audits.
- Preparing corpora where tables, formulas, code blocks, captions, images, and forms should not collapse into plain text.
- Carrying machine-readable governance metadata alongside document content.
- Supporting reproducible extraction before later conversion into prepared
  training records.

DocLang is less useful for following:

- Already-clean text corpora.
- Instruction or preference records that are already structured.
- Datasets where the source document layout has no training or audit value.
- Final tokenized training artifacts, where the model pipeline needs compact tensors or packed records rather than document markup.

## Adoption Risks

| Risk | Impact | Mitigation |
| :--- | :----- | :--------- |
| Pre-1.0 compatibility churn | Stored corpora may require migration as the spec changes. | Use only in pilots until a stable subset is defined. |
| Converter quality variance | Poor extraction can preserve structure while corrupting content. | Compare DocLang conversion against source documents and existing extraction outputs. |
| Pipeline complexity | Training pipelines may need additional conversion steps. | Treat DocLang as a source/preparation format, not the final training format. |
| Metadata mismatch | Tapestry governance fields may not map cleanly to DocLang defaults. | Define a Tapestry metadata namespace or companion manifest. |
| Multimodal validation | First-class media support still needs validation against Tapestry corpora. | Include audio/video samples in a pilot and verify transcript, timestamp, speaker, scene, provenance, and rights metadata. |
| Tooling lock-in | Early tools may shape the workflow before requirements are proven. | Evaluate DocLang as the interchange format separately from any one converter, including Docling; keep JSONL/Parquet outputs and converter tests as the pipeline contract. |

## Pilot Plan

1. Choose a small corpus with varied source formats: PDF, HTML, scanned pages, tables, formulas, images, forms, audio, and video.
2. Convert the corpus into DocLang and into the current baseline extraction format.
3. Compare content fidelity, table fidelity, metadata preservation, token cost, converter runtime, and review effort.
4. Map Tapestry dataset-card fields into DocLang metadata or a companion manifest.
5. Convert DocLang outputs into prepared JSONL or Parquet records for a small training or evaluation task.
6. Decide whether to standardize a Tapestry DocLang profile, continue piloting, or reject the format for now.

## Minimum Acceptance Criteria

Before Tapestry adopts DocLang beyond pilot use, it should demonstrate:

- A stable-enough versioning of committed corpora or a clear migration plan.
- Reliable conversion from the document types participants expect to contribute.
- Preservation of Tapestry-mandated provenance, license, residency, allowed-use, and visibility metadata.
- Measurable improvement over current extraction for at least one important corpus type.
- A reversible or auditable path from source document to prepared training record.
- Compatibility with participant-private and local-only workflows.
- Clear handling for images, charts, audio, video, and companion media
  artifacts.

## Open Decisions

- Should Tapestry define a DocLang profile with a restricted subset of elements?
- Should governance metadata live inside DocLang, in a companion manifest, or both?
- Which converter or converters should be used for pilots, and how do we avoid making Docling a required dependency unless later evidence supports that choice?
- What corpus should be used for the first conversion benchmark?
- How should non-document media be linked to source, provenance, and prepared training artifacts?
