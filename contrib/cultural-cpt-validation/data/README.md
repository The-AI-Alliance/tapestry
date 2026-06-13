# EXP-001 corpora (Stage 0)

This directory holds the **real** corpora for the cultural-CPT validation
experiment — the bottleneck the spec calls *"Stage 0 — the real bottleneck"*
([`tech-docs/experiments/cultural-cpt-validation.md`](../../../tech-docs/experiments/cultural-cpt-validation.md)).
The harness's smoke mode runs on tiny placeholder text baked into
[`cultural_cpt/corpora.py`](../cultural_cpt/corpora.py); a real EXP-001 *result*
needs both a real model (`--mode hf`) **and** real corpora loaded from here
(`--corpus-path`). Loading, validation, and the scientific controls live in
[`cultural_cpt/dataset.py`](../cultural_cpt/dataset.py).

## Why the corpus is the whole experiment

The novel claim is *grounded ≠ linguistic*. A before/after on one corpus proves
nothing; the result lives or dies on the **control structure between corpora**:

- **Grounded** (Arm 1) and **language-matched** (Arm 2) must differ **only in
  cultural grounding** — same language, register, recency, quality, and token
  budget. Any other difference confounds the decisive `grounded vs
  language_matched` comparison.
- No corpus may contain WVS-resembling items, or the survey measures
  **memorization, not alignment** (spec: "Decontamination").

`dataset.py` enforces both as load-time invariants and **fails loudly** rather
than letting a broken corpus silently produce a publishable-looking number. You
cannot accidentally train on a corpus that violates the controls.

## Layout

One directory per culture, pointed at by `--corpus-path`:

```
data/<culture>/
  manifest.json               # per-arm metadata + twin tolerances (schema below)
  grounded.jsonl              # Arm 1: culturally grounded, value-laden text
  language_matched.jsonl      # Arm 2: same language, value-neutral text (the twin)
  grounded_translated.jsonl   # Arm 3 (optional): grounded content, base's language
```

- **Arms experiment** (`run.py --corpus-path data/<culture>`): the arm name
  selects the file within the root.
- **Aggregation experiment** (`run_aggregation.py --corpus-path data`): expects
  `data/<culture>/` per culture and loads each culture's `grounded` arm.

### Document records (`*.jsonl`)

One JSON object per line. Required: `id`, `text`, `source`, `license`, `lang`.
Optional: `domain`, `url`, `year`.

```json
{"id": "arwiki:Egyptian_law:0", "text": "…", "source": "Arabic Wikipedia", "license": "CC-BY-SA-4.0", "lang": "ar", "domain": "law", "url": "https://ar.wikipedia.org/wiki/…", "year": 2024}
```

### `manifest.json`

```json
{
  "culture": "egypt",
  "language": "ar",
  "arms": {
    "grounded": {
      "file": "grounded.jsonl",
      "lang": "ar",
      "register": "encyclopedic",
      "domains": ["law", "religion", "family", "civic", "literature"],
      "value_laden": true,
      "min_year": 2001, "max_year": 2025
    },
    "language_matched": {
      "file": "language_matched.jsonl",
      "lang": "ar",
      "register": "encyclopedic",
      "domains": ["weather", "sports", "technical", "mathematics"],
      "value_laden": false,
      "min_year": 2001, "max_year": 2025
    }
  },
  "twin_matching": {
    "token_ratio_tolerance": 0.20,
    "require_same_language": true,
    "require_same_register": true
  }
}
```

## The controls, enforced at load time

| Control | What `dataset.py` checks | Spec basis |
| :------ | :----------------------- | :--------- |
| **Permissive licensing** | every doc's `license` ∈ `PERMISSIVE_LICENSES` | repo is Apache/CC-BY/CDLA; "permissive-only" decision |
| **Language match** | every doc's `lang` == its arm's manifest `lang` | twin: "same language" |
| **Register match** | `grounded.register` == `language_matched.register` | twin: "register held constant" |
| **Token-budget match** | grounded/neutral token counts within `token_ratio_tolerance` | twin: "size held constant" |
| **Value-ladenness** | `grounded.value_laden=true`, `language_matched.value_laden=false` | guards against a mislabeled twin |
| **Recency** | each doc's `year` within `[min_year, max_year]` | twin: "recency held constant" |
| **WVS decontamination** | no doc reproduces a survey/behavioral item (exact or Jaccard ≥ 0.6 over a sliding window) | "strip any WVS-resembling items" |

Decontamination phrases are pulled live from the instruments (`wvs._ITEMS`, and
the behavioral probe), so they track the actual battery. Detection is on
Unicode-word tokens and therefore works for non-Latin scripts.

## The matched twin: the one design that makes this clean

The hardest part is guaranteeing grounded and language-matched differ *only* in
grounding. The most defensible way is to draw **both arms from the same platform
and register, varying only topical domain**:

- **Grounded** = encyclopedic articles on value-laden domains: law, religion,
  family/kinship, civic life, festivals, ethics, literature.
- **Language-matched** = encyclopedic articles on value-neutral domains:
  weather, sports results, technical/engineering reference, mathematics.

Same source, same language, same register, same era, comparable length — the
remaining difference is cultural value content. Primary-source grounding
(constitutions, gazettes, classical/religious texts via Wikisource, all
public-domain) can be layered in, but keeping the *twin* itself
same-source-different-domain is what keeps the control honest.

## Licensing

Permissive-only (the EXP-001 decision), so the corpus can live in / be
regenerated for this open repo. Accepted identifiers are in
`dataset.PERMISSIVE_LICENSES` (public-domain, CC0, CC-BY, CC-BY-SA, ODC-BY, OGL,
Apache-2.0, MIT). Each document records its own `license`; a non-permissive one
fails the load. Good sources:

- **Wikipedia** (CC-BY-SA-4.0) — the per-domain twin; available in many languages.
- **Wikisource** (mostly public-domain) — constitutions, legal codes, classical
  literature, religious/ethical texts (grounding).
- **Government gazettes / parliamentary records** — public-domain or OGL-class.
- **OPUS / Tatoeba** (CC-BY) — supplementary same-language neutral text.

## Choosing the pilot culture — availability-driven

The spec wants a culture with **large WVS distance** from the
English/Protestant-Europe cluster (room to move) **and** corpus availability.
Because the loader is **culture-agnostic** (culture/arm/language are
manifest-driven, nothing is hardcoded), the choice is settled by what
`fetch_corpus.py` can actually assemble under a permissive license, *not* baked
into code. Current read:

| Culture | WVS distance | Permissive availability (both arms) |
| :------ | :----------- | :---------------------------------- |
| **Egypt** (ar) | very high (traditional + survival) | strong — large Arabic Wikipedia + rich Wikisource |
| **Vietnam** (vi) | high (Confucian) | strong — large Vietnamese Wikipedia |
| **India** (hi/…) | high | weaker — thinner Hindi wiki; multilingual complicates the "same language" twin |

Run `fetch_corpus.py` for a candidate, read the real token counts it reports,
then commit to the culture whose twin you can actually balance.

## Producing a corpus

```shell
# fetch a small, real, attributed sample into data/<culture>/ (see fetch_corpus.py)
uv run python contrib/cultural-cpt-validation/fetch_corpus.py --culture egypt --per-domain 5

# validate an existing root against all the controls without training
uv run python contrib/cultural-cpt-validation/fetch_corpus.py --validate data/egypt
```

Bulk corpora are git-ignored (only the committed `seed-example/` and any
`*.seed.jsonl` sample travel with the repo); regenerate full corpora locally
from the manifest's sources.
