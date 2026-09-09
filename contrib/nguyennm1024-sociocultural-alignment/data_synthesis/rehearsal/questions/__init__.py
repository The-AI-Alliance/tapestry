"""Module 2 — question pool construction.

For categories where a public dataset already supplies questions, items are
extracted by `rehearsal.data.extract` directly. This module covers:

  augment.py   — B2 GSM8K_train_variants, B6 Augmented_constraint_templates
  generate.py  — B5 GPQA, B7 BFCL multi-turn, B10 anti-modecollapse
                  (pure-generated questions via Kimi)
  nih.py       — B8 NIH_style_synthetic (programmatic; no LLM)

Stage 1 placeholder — implementation lands in the next slice.
"""
