# Rehearsal data pipeline

Builds the 40K-example rehearsal corpus that defends Llama 3.2 3B Instruct's
Meta benchmark scores during Vietnamese cultural fine-tuning. Spec:
`topics/rehearsal/rehearsal_data_structure.json` (13 categories, 45 sources).

## Module layout

```
rehearsal/
  spec.py          # load rehearsal_data_structure.json (categories, sources, volumes)
  format.py        # Record schema, <THINK>/<ANSWER> helpers, JSONL I/O

  data/
    sources.py     # 45 HFSource entries + 20 DecontamTestset entries
    download.py    # idempotent HF cache populate (`rehearsal download`)
    decontam.py    # exact + 13-gram index (`rehearsal decontam-build`)
    extract.py     # [stage 2] normalize HF rows to question records

  questions/
    augment.py     # [stage 2] B2 GSM8K variants, B6 IFEval constraint append
    generate.py    # [stage 2] B5 GPQA, B7 BFCL multi-turn, B10 anti-modecollapse
    nih.py         # [stage 2] B8 programmatic NIH

  answers/
    solve.py       # [stage 3] Kimi K2.6 reasoning+answer driver
    filter.py      # [stage 3] drop Kimi-vs-gold disagreements
    verify.py      # [stage 3] per-category checks

  cli.py           # single entry: `python -m rehearsal.cli <subcommand>`
```

## Build order

```
1.  python -m rehearsal.cli download              # ~50-100GB into ~/.cache/huggingface
2.  python -m rehearsal.cli decontam-build        # builds ~/.cache/rehearsal_decontam/index.pkl
3.  python -m rehearsal.cli questions             # writes questions/_pool/<category>.jsonl
4.  python -m rehearsal.cli solve                 # writes answers/_out/<category>.jsonl
5.  python -m rehearsal.cli verify                # per-category checks; drops failures
6.  python -m rehearsal.cli validate              # KL / length / vocab distribution checks
7.  python -m rehearsal.cli assemble              # samples to 40K, final corpus
```

Each step is idempotent — rerun-safe, skips already-completed work. `pilot`
runs steps 3-6 on a 10% slice end-to-end.

## Record format

Every item in the corpus is a Record (one schema, JSONL):

```json
{
  "id": "rhsl_mmlu_MMLUauxili_000042",
  "category": "mmlu_shaped",
  "source": "MMLU_auxiliary_training",
  "origin": "public",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "<THINK>...</THINK><ANSWER>...</ANSWER>"}
  ],
  "answer_key": {"correct_index": 2},
  "provenance": {
    "teacher_model": "kimi-k2.6",
    "source_dataset": "cais/mmlu",
    "source_record_id": "auxiliary_train:18342",
    "batch_id": "f3a8c1b2"
  },
  "verified": true
}
```

`<THINK>` is filled by Kimi for every category. The base Llama 3.2 3B Instruct
does not natively use this format — introducing it is intentional, so every
training example must contain both tags.

## Design principles (in force)

1. **One teacher, one schema.** Kimi K2.6 generates reasoning + answer for
   every item. `messages` is uniform across public and generated origins.
2. **Format by category, not by origin.** Public MMLU items and Kimi-generated
   MMLU items emit identical message shapes.
3. **Resumable, idempotent scripts.** No interactive prompts. Append-mode
   JSONL with line buffering survives crashes.
4. **Decontamination is mandatory.** Exact + 13-gram against 20 test sets,
   applied to both downloaded and generated pools. Semantic stage deferred.
5. **Spec-as-truth.** `rehearsal_data_structure.json` is the single source
   for what data is needed; HF paths live in `data/sources.py`.

## Status — Stage 1 complete

Implemented:
- `spec.py`, `format.py`
- `data/sources.py` (45 + 20 registry entries)
- `data/download.py`, `data/decontam.py`
- `cli.py` with working `download` + `decontam-build`; remaining subcommands stubbed

Next slice (Stage 2): `data/extract.py`, `questions/*`, normalize public data
into the question pool, build the augmented and pure-generated question sets.
