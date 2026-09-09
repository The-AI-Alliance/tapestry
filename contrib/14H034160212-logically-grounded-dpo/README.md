# Logically-Grounded DPO: Answer-Grounded Preference Optimization for Explanation Generation

**Status: Validated (published).** Method and results below are from a
peer-reviewed arXiv paper; this directory contributes the core reference
implementation for Tapestry's consideration, not a finished integration. **No
data is included** — see [Data clearance](#data-clearance) below.

## Motivation

A model can be fluent and still fail to *justify the correct answer* — high
surface-similarity scores (BLEU, BERTScore against a reference explanation)
don't tell you whether a generated explanation actually implies the correct
answer. This is a general risk for any consortium base model asked to explain
its reasoning (tutoring, decision support, code review, etc.), not specific to
one domain: a fluent, plausible-sounding justification can still be logically
disconnected from the answer it's supposedly justifying.

We built and evaluated a fix for this in the educational-explanation domain
(justifying answers to multiple-choice exam questions), but the technique
itself — an automated, verifier-based preference-pair construction plus an
NLI-grounded reward — is domain-agnostic.

## What this contributes

Reference implementation of a training pipeline (SFT → verifier-based
preference-pair construction → DPO/PPO with an NLI-grounded reward) that
replaces standard reference-text similarity metrics with a reward tied to
whether the generated explanation *logically entails* the correct answer:

- **`logically-grounded-dpo/rl_train_sft.py`** — LoRA SFT baseline (stage 1).
- **`logically-grounded-dpo/rl_build_preference_data.py`** — automatically
  constructs DPO preference pairs by sampling N candidate explanations per
  question and scoring them with a domain-trained verifier model, instead of
  relying on expensive human annotation or a fixed external teacher model.
- **`logically-grounded-dpo/rl_generate_synthetic_data.py`** — augments
  preference pairs with GPT-4o/Claude chain-of-thought synthetic positives and
  model-generated hard negatives, to counter reward hacking.
- **`logically-grounded-dpo/rl_train_dpo.py`** — offline preference
  optimisation (DPO) over the constructed pairs.
- **`logically-grounded-dpo/rl_train_ppo_nli.py`** — online alternative (PPO)
  using a live NLI-entailment reward instead of an offline preference dataset.
- **`logically-grounded-dpo/rl_evaluation.py`** — the evaluation framework
  itself: a three-tier answer-grounded metric suite (BERTScore-vs-answer,
  Answer Coverage Rate, and NLI entailment against the correct option, rather
  than against student reference text). The NLI metric is the most
  discriminative signal in our experiments — the SFT baseline scores ~0.05
  while RL-trained models score 0.22–0.30 (4–5x gap) — precisely because it
  captures logical entailment rather than surface similarity.

All scripts are LoRA fine-tuning / RL training code (PEFT + `transformers`
`Trainer`, TRL for DPO/PPO) evaluated across LLaMA-2-13B, LLaMA-3-8B, Qwen3-8B,
and Gemma-3-4B backbones.

## How to try / evaluate

The full project (additional model variants, evaluation logs, and the paper
sources) is public:

- Code: https://github.com/14H034160212/Explanation-Generation
- Paper: https://arxiv.org/abs/2605.04539 — *"RLearner-LLM: Balancing Logical
  Grounding and Fluency in Large Language Models via Hybrid Direct Preference
  Optimization"* (Bao, Leinonen, Denny, Witbrock)

The scripts here are excerpted as-is to make the core method (verifier-based
preference construction + NLI-grounded reward) reviewable without pulling in
the full set of per-model/per-domain training variants in the source
repository. See each script's module docstring and `--help` for the expected
input schema and CLI usage.

## Data clearance

This contribution is **code only**. The underlying training/evaluation data
(PeerWise multiple-choice exam questions and per-student answer submissions
from partner institutions) is student-generated educational-assessment data
subject to institutional data-use agreements, and is explicitly excluded from
the public source repository (`.gitignore`'d) and from this contribution. None
of it is included, referenced by value, or reproduced here — only the training
code, which operates on data in a documented schema (see script docstrings)
that a Tapestry partner would supply from their own cleared source.

## Relevance to Tapestry

The verifier-based automatic preference construction and NLI-grounded reward
are reusable as a general post-training technique for any Tapestry-derived
model expected to produce explanations, justifications, or reasoning traces
that must be *checked against*, not just *fluent around*, a ground-truth
answer.

## License

This contribution follows the repository default licenses:

- Code: Apache License, Version 2.0. See [LICENSES/LICENSE.Apache-2.0](../../LICENSES/LICENSE.Apache-2.0).
- Documentation: Creative Commons Attribution 4.0 International. See [LICENSES/LICENSE.CC-BY-4.0](../../LICENSES/LICENSE.CC-BY-4.0).

Copyright (c) 2025-2026 Qiming Bao. Released here under Apache-2.0 for this
excerpted training-code contribution.
