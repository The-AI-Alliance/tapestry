"""Module 3 — answer generation via Kimi K2.6.

  solve.py   — read question pool, send to Kimi, capture reasoning_content +
               content, write `<THINK>...</THINK><ANSWER>...</ANSWER>` records
  filter.py  — drop Kimi-vs-gold disagreements where gold is reliable
  verify.py  — per-category format / answer / constraint checks

Reuses `sft.client.make_client` and the parallel / retry / error-handling
patterns from `sft.synthesize`.

Stage 1 placeholder — implementation lands in the next slice.
"""
