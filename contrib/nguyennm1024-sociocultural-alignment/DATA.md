# Data: pointers, sourcing, and clearance

No raw data, survey microdata, or model weights are included in this contribution. This file
describes what the code consumes and how to obtain or regenerate it.

## Survey reference data (Inglehart-Welzel evaluation)

- The IW projection (`evaluation/iw/iw_project.py` + `iw_projection_final.json`) is
  **self-contained**: the fitted projection parameters are baked into the JSON, so no survey
  microdata is needed to project a model.
- Deriving those parameters (not required to run the eval) uses the integrated **World Values
  Survey** and **European Values Study** microdata, which are **registration-walled and must
  not be redistributed**:
  - WVS: <https://www.worldvaluessurvey.org/> (integrated/trend file, registration required)
  - EVS: <https://europeanvaluesstudy.eu/> (integrated file, registration required)
- Only aggregated, publishable reference points are included here (country-level coordinates
  and Tao et al.'s published per-model score tables).

## Training corpora (cultural + rehearsal)

The raw generated corpora are not included. Regenerate them with `data_synthesis/`:

- **Cultural corpus** (`data_synthesis/cultural/`): topic-driven question generation, persona
  answers, and reasoning cleaning, guided by `topics/cultural_data_coverage_v2.json`.
- **Rehearsal corpus** (`data_synthesis/rehearsal/` + `topics/rehearsal/`): public-dataset
  sourcing plus synthesized capability data. The rehearsal guide lists the dataset pointers and
  their licenses. Public datasets (e.g. MMLU auxiliary, GSM8K, ARC, HellaSwag, IFEval, OASST)
  are fetched from their canonical sources under their own licenses; the builder filters and
  decontaminates rather than redistributing them.

## Model weights

Not included. The base is `meta-llama/Llama-3.2-3B-Instruct` (Llama Community License). Trained
adapters, merged models, and souped models are derived from it and are not redistributed here.
Reproduce via `training/` and `consortium/`.

## Clearance

Generated data is filtered to exclude evaluation-probe contamination (see the decontamination
steps) and is not scraped or PII-laden. When in doubt, this contribution ships a pointer and
description rather than raw data.
