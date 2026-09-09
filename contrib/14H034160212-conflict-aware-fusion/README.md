# Conflict-Aware Fusion: Training a Shared Base Model to Recognize Broken Premises

**Status: Validated (published).** Method and results below are from a peer-reviewed
arXiv paper; this directory contributes the core reference implementation of the
two novel training components for Tapestry's consideration, not a finished
integration.

## Motivation

Tapestry is training a shared base model that many partners will build sovereign
derivatives from. A gap that affects any such base model, regardless of domain or
language, is what we call **Logic Inertia**: large language models keep deducing
along a learned reasoning chain even when their own premises are inconsistent,
instead of halting and flagging the contradiction. This matters for any
consortium-trained model used in legal, scientific, or automated-decision
contexts, where inputs are not guaranteed to be internally consistent.

We measured this on frontier models with a controlled diagnostic benchmark (four
orthogonal stress tests: redundant-rule deletion, essential-rule deletion,
contradiction injection, and logic-preserving rewrites, all derived from a single
canonical rule system so failures can be attributed to reasoning robustness
rather than domain shift). Results:

| Model | Base task | Contradiction-injection split |
|---|---|---|
| GPT-4o | 0.789–0.818 | **0.560** |
| Gemma-3-4B-IT | 0.580 | **0.439** |
| Untreated BERT / Qwen2 / TinyLlama | 1.00 | **0.000** |

The failure is specific to premise-inconsistency handling, not general reasoning
capability — both frontier models score well on the base task and collapse only
when premises conflict.

## What this contributes

Two training components from our four-stage **Conflict-Aware Fusion** pipeline
(SFT → DPO → LIRE → RLVF) that closed this gap, bringing a Qwen3-8B backbone to
**1.000 across all four stress-test splits**:

- **`conflict-aware-fusion/stage3_train_lire.py`** — LIRE (Logical Invariance
  REgularisation): a symmetric-KL loss term that penalises divergence between a
  model's output distribution on logically equivalent rule reformulations
  (contrapositive, De Morgan, double negation, etc.), teaching invariance to
  surface rewording of the same premises.
- **`conflict-aware-fusion/stage4_train_rlvf.py`** — RLVF (Reinforcement Learning
  from Verification Feedback): a reward *formulation* (not a new optimiser) that
  replaces a learned/human reward model with a deterministic symbolic
  forward-chaining oracle, jointly optimising invariance (from LIRE) and
  sensitivity to genuine contradictions in a single REINFORCE update.
- **`conflict-aware-fusion/stage2_train_dpo.py`** — the preceding DPO stage that
  sharpens the halt-on-contradiction decision boundary, included for context on
  how LIRE/RLVF slot into the full pipeline.

All three are LoRA fine-tuning scripts (PEFT + `transformers.Trainer`) against
Qwen2/Qwen3-family checkpoints, trained on a synthetic propositional-logic
corpus. A Phase-2 extension (not included here) further replaces the
propositional oracle with a Lean 4 kernel, giving machine-checked ground truth
instead of only synthetic-oracle labels.

## How to try / evaluate

The full runnable pipeline (data generation, all four training stages,
evaluation harness, and the Lean 4 verifier) is public:

- Code: https://github.com/14H034160212/lemo (MIT license)
- Paper: https://arxiv.org/abs/2512.06393 — *"Conflict-Aware Fusion: Mitigating
  Logic Inertia in Large Language Models via Structured Cognitive Priors"*
  (Bao, Fu, Witbrock)

The two scripts here are excerpted as-is from that repository to make the core
algorithmic idea (the loss/reward formulation) reviewable without pulling in the
full data-generation and multi-stage orchestration code. They expect the data
schema documented in their module docstrings (`data/train_lire_pairs.csv` and
the mixed V2/V3/V4 training split respectively) — see the linked repository for
how that data is generated.

## Relevance to Tapestry

If adopted as a post-training stage for the shared base model, this pipeline is
a candidate way to make sovereign derivatives more reliably reject inconsistent
inputs — a property useful across every partner's domain, not specific to any
one language or industry vertical.

## License

This contribution follows the repository default licenses:

- Code: Apache License, Version 2.0. See [LICENSES/LICENSE.Apache-2.0](../../LICENSES/LICENSE.Apache-2.0).
- Documentation: Creative Commons Attribution 4.0 International. See [LICENSES/LICENSE.CC-BY-4.0](../../LICENSES/LICENSE.CC-BY-4.0).

(The upstream `lemo` repository is MIT-licensed; the author releases this
excerpted copy under Apache-2.0 to match Tapestry's default, as permitted by the
permissive original license.)
