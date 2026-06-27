# DocLang Evaluation

Status: initial investigation.

This note supports issue
[#67](https://github.com/The-AI-Alliance/tapestry/issues/67) by evaluating
[DocLang](https://doclang.ai/) as a possible document format standard for
Tapestry data preparation and training workflows.

## Summary Recommendation

Do not adopt DocLang as the required Tapestry document format yet. It is
promising enough to pilot for document-heavy corpora, but the current format is
still pre-1.0 and should be treated as an experimental interchange option until
the project validates conversion quality, governance metadata, media handling,
tooling maturity, and cost of adoption.

Recommended near-term position:

- use DocLang in a small pilot for PDF, HTML, scanned, and table-heavy
  documents;
- keep JSONL or Parquet as the prepared training-data interchange format for
  near-term pipeline work;
- require converters to preserve Tapestry provenance, rights, residency, and
  allowed-use metadata;
- revisit standardization after the pilot produces quality, cost, and tooling
  evidence.

## What DocLang Is

DocLang is an XML-based document markup format designed for model consumption.
The official specification describes version 0.7 and focuses on representing
document structure, semantics, geometry, formatting, and complex document
components such as tables, charts, formulas, code, forms, and pictures.

The format is intentionally more structured than plain Markdown and more
token-conscious than general HTML. It also includes governance and compliance
metadata concepts that are relevant to Tapestry data-governance requirements.

## Evaluation Against Issue Questions

| Question | Initial answer | Notes |
| :------- | :------------- | :---- |
| Is it an improvement over the current ad hoc approach? | Potentially, for complex source documents. | It can preserve structure, layout, tables, formulas, images, and metadata more explicitly than plain extracted text. The benefit is smaller for already-clean plain text or simple JSONL records. |
| Is it stable and mature enough to adopt? | Not as a required project standard yet. | The current spec is version 0.7. Its versioning section treats 0.x as initial development where breaking compatibility is possible. |
| Is it flexible for different document kinds? | Yes for many document types, with validation needed. | The spec covers text, lists, tables, forms, code, formulas, pictures, charts, geometry, page breaks, and custom metadata. Tapestry still needs tests across real participant corpora. |
| What about non-text, such as images, audio, and video? | Images and charts are represented; audio and video are not first-class core elements in the current spec. | `<picture>` can reference image URIs or embedded data URIs, and charts can include structured tabular data. Audio and video would likely need custom metadata or a companion artifact convention. |
| What would be the cost/effort required to adopt it? | Medium for a pilot, high for full standardization. | Adoption requires converters, validators, metadata mapping, quality tests, storage conventions, and downstream pipeline support. |

## Potential Fit For Tapestry

DocLang is most relevant for:

- converting PDF, HTML, scanned, form-heavy, table-heavy, and layout-sensitive
  corpora into a consistent intermediate representation;
- retaining page geometry and document structure for review and extraction
  audits;
- preparing corpora where tables, formulas, code blocks, captions, images, and
  forms should not collapse into plain text;
- carrying machine-readable governance metadata alongside document content;
- supporting reproducible extraction before later conversion into prepared
  training records.

DocLang is less necessary for:

- already-clean text corpora;
- instruction or preference records that are already structured;
- datasets where the source document layout has no training or audit value;
- final tokenized training artifacts, where the model pipeline needs compact
  tensors or packed records rather than document markup.

## Adoption Risks

| Risk | Impact | Mitigation |
| :--- | :----- | :--------- |
| Pre-1.0 compatibility churn | Stored corpora may require migration as the spec changes. | Use only in pilots until a stable subset is defined. |
| Converter quality variance | Poor extraction can preserve structure while corrupting content. | Compare DocLang conversion against source documents and existing extraction outputs. |
| Pipeline complexity | Training pipelines may need additional conversion steps. | Treat DocLang as a source/preparation format, not the final training format. |
| Metadata mismatch | Tapestry governance fields may not map cleanly to DocLang defaults. | Define a Tapestry metadata namespace or companion manifest. |
| Multimodal gaps | Audio and video are not clearly first-class core document elements. | Keep non-document media in separate governed artifacts with references from manifests. |
| Tooling lock-in | Early tools may shape the workflow before requirements are proven. | Keep JSONL/Parquet outputs and converter tests as the pipeline contract. |

## Pilot Plan

1. Choose a small corpus with varied source formats: PDF, HTML, scanned pages,
   tables, formulas, images, and forms.
2. Convert the corpus into DocLang and into the current baseline extraction
   format.
3. Compare content fidelity, table fidelity, metadata preservation, token cost,
   converter runtime, and review effort.
4. Map Tapestry dataset-card fields into DocLang metadata or a companion
   manifest.
5. Convert DocLang outputs into prepared JSONL or Parquet records for a small
   training or evaluation task.
6. Decide whether to standardize a Tapestry DocLang profile, continue piloting,
   or reject the format for now.

## Minimum Acceptance Criteria

Before Tapestry adopts DocLang beyond pilot use, it should demonstrate:

- stable-enough versioning for committed corpora or a clear migration plan;
- reliable conversion from the document types participants expect to contribute;
- preservation of Tapestry provenance, license, residency, allowed-use, and
  visibility metadata;
- measurable improvement over current extraction for at least one important
  corpus type;
- a reversible or auditable path from source document to prepared training
  record;
- compatibility with participant-private and local-only workflows;
- clear handling for images, charts, and companion media artifacts.

## Open Decisions

- Should Tapestry define a DocLang profile with a restricted subset of elements?
- Should governance metadata live inside DocLang, in a companion manifest, or
  both?
- Which converter should be treated as the reference implementation for pilots?
- What corpus should be used for the first conversion benchmark?
- How should non-document media be linked to source, provenance, and prepared
  training artifacts?
