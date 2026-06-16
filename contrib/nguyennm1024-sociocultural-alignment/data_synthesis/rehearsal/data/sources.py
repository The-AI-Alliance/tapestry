"""Registry binding spec source names to HuggingFace datasets.

Each entry says: where on HF, which config, which split, and any filter to
apply at load time. The actual fetch happens in `download.py` (via
`datasets.load_dataset`).

`origin` distinguishes:
  - public:        public dataset, used as-is (after filter)
  - augmented:     starts from a public dataset, then mutated (B2, B6 subcats)
  - generated:     fresh Kimi generation, no public seed
  - programmatic:  built without an LLM (B8 NIH)

Augmented and generated entries still appear here for completeness — they
record the SEED dataset (or None) so downstream code knows where seeds come
from.

The IFEval correction from the guide is applied: `IFEval_style_training_prompts`
points at `argilla/ifeval-like-data`, NOT `google/IFEval` (whose 541 prompts
ARE the eval set). The original `google/IFEval` is wired only into
DECONTAM_TESTSETS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Origin = Literal["public", "augmented", "generated", "programmatic"]


@dataclass(frozen=True)
class HFSource:
    name: str                       # matches the spec source name
    origin: Origin
    hf_path: str | None             # None for pure-generated / programmatic
    hf_config: str | None = None
    hf_split: str = "train"
    # Free-form filter directives, interpreted by extract.py per category.
    # Examples: {"levels": [1, 2]} for MATH; {"exclude_cultural": True} for OASST.
    filter: dict = field(default_factory=dict)
    notes: str = ""


# ---------------------------------------------------------------------------
# Training sources (45 entries — matches spec total)
# ---------------------------------------------------------------------------

SOURCES: list[HFSource] = [
    # ifeval_shaped --------------------------------------------------------
    HFSource(
        name="IFEval_style_training_prompts",
        origin="public",
        hf_path="argilla/ifeval-like-data",
        hf_split="train",
        notes="Replaces google/IFEval, which is the eval set. Guide Part A correction.",
    ),
    HFSource(
        name="Augmented_constraint_templates",
        origin="augmented",
        hf_path="HuggingFaceH4/no_robots",
        hf_split="train",
        notes="Base prompts drawn from NoRobots / Tulu / OASST; constraints appended in questions/augment.py",
    ),
    HFSource(
        name="NoRobots_filtered",
        origin="public",
        hf_path="HuggingFaceH4/no_robots",
        hf_split="train",
        filter={"instruction_following_suitable": True},
    ),
    HFSource(
        name="Generated_prompt_constraint_pairs",
        origin="generated",
        hf_path=None,
    ),

    # mmlu_shaped ----------------------------------------------------------
    HFSource(
        name="MMLU_auxiliary_training",
        origin="public",
        hf_path="cais/mmlu",
        hf_config="auxiliary_train",
        hf_split="train",
    ),
    HFSource(
        name="Synthetic_via_Qwen",
        origin="generated",
        hf_path=None,
        notes="Spec name retained though Kimi K2.6 is our actual teacher.",
    ),
    HFSource(
        name="MMLU_Pro_train",
        origin="public",
        hf_path="TIGER-Lab/MMLU-Pro",
        hf_split="validation",
        notes="MMLU-Pro has no train split; sample from validation (harder skew).",
    ),

    # gsm8k_shaped_math ----------------------------------------------------
    HFSource(
        name="GSM8K_train",
        origin="public",
        hf_path="openai/gsm8k",
        hf_config="main",
        hf_split="train",
    ),
    HFSource(
        name="GSM8K_train_variants",
        origin="augmented",
        hf_path="openai/gsm8k",
        hf_config="main",
        hf_split="train",
        notes="Seed from GSM8K train; number/context substitution in questions/augment.py",
    ),
    HFSource(
        name="MetaMathQA",
        origin="public",
        hf_path="meta-math/MetaMathQA",
        hf_split="train",
        filter={"prefer": "GSM8K-derived", "exclude": "MATH-derived"},
    ),
    HFSource(
        name="ASDiv_and_easy_subset",
        origin="public",
        hf_path="MU-NLPC/Calc-asdiv_a",
        hf_split="test",
        notes="MU-NLPC/Calc-asdiv_a only exposes a `test` split (~1218 items). "
              "Despite the name, it's the canonical ASDiv corpus we use as training seed.",
    ),

    # math_shaped ----------------------------------------------------------
    HFSource(
        name="MATH_train_levels_1_2",
        origin="public",
        hf_path="EleutherAI/hendrycks_math",
        hf_split="train",
        filter={"levels": [1, 2], "iter_all_configs": True},
        notes="Original hendrycks/competition_math is a loading script (deprecated by HF). "
              "EleutherAI mirror exposes the same 7,500 train items across 7 subject configs.",
    ),
    HFSource(
        name="MATH_train_level_3",
        origin="public",
        hf_path="EleutherAI/hendrycks_math",
        hf_split="train",
        filter={"levels": [3], "iter_all_configs": True},
    ),
    HFSource(
        name="MATH_train_levels_4_5",
        origin="public",
        hf_path="EleutherAI/hendrycks_math",
        hf_split="train",
        filter={"levels": [4, 5], "iter_all_configs": True},
    ),

    # hellaswag_shaped -----------------------------------------------------
    HFSource(
        name="HellaSwag_train",
        origin="public",
        hf_path="Rowan/hellaswag",
        hf_split="train",
    ),
    HFSource(
        name="Generated_hellaswag_style",
        origin="generated",
        hf_path=None,
    ),
    HFSource(
        name="PIQA_train",
        origin="public",
        hf_path="baber/piqa",
        hf_split="train",
        notes="ybisk/piqa is a deprecated loading script; baber/piqa is a parquet mirror "
              "with the same schema (goal, sol1, sol2, label).",
    ),
    HFSource(
        name="SIQA_train",
        origin="public",
        hf_path="lighteval/siqa",
        hf_split="train",
        notes="allenai/social_i_qa is a deprecated loading script; lighteval/siqa is a "
              "parquet mirror (context, question, answerA/B/C, label).",
    ),
    HFSource(
        name="Story_Cloze_train",
        origin="public",
        hf_path="LSDSem/story_cloze",
        hf_config="2016",
        hf_split="train",
        notes="License-restricted; verify access. Train is the ROCStories pool.",
    ),

    # bfcl_shaped_tool_calling --------------------------------------------
    HFSource(
        name="xLAM",
        origin="public",
        hf_path="Salesforce/xlam-function-calling-60k",
        hf_split="train",
        notes="GATED — requires HF login + dataset access approval from Salesforce. "
              "Visit https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k and "
              "run `huggingface-cli login` with a token that has access.",
    ),
    HFSource(
        name="Glaive_Function_Calling_v2",
        origin="public",
        hf_path="glaiveai/glaive-function-calling-v2",
        hf_split="train",
        filter={"quality": "high"},
    ),
    HFSource(
        name="Hermes_Function_Calling",
        origin="public",
        hf_path="NousResearch/hermes-function-calling-v1",
        hf_split="train",
        filter={"subsets": ["func_calling_singleturn", "func_calling"]},
    ),
    HFSource(
        name="BFCL_v3_multi_turn_generated",
        origin="generated",
        hf_path=None,
    ),
    HFSource(
        name="API_Bank_filtered",
        origin="public",
        hf_path="liminghao1630/API-Bank",
        hf_split="train",
        filter={"state_tracking": True},
    ),

    # arc_challenge_shaped -------------------------------------------------
    HFSource(
        name="ARC_Challenge_train",
        origin="public",
        hf_path="allenai/ai2_arc",
        hf_config="ARC-Challenge",
        hf_split="train",
    ),
    HFSource(
        name="ARC_Easy_train",
        origin="public",
        hf_path="allenai/ai2_arc",
        hf_config="ARC-Easy",
        hf_split="train",
    ),
    HFSource(
        name="OpenBookQA_train",
        origin="public",
        hf_path="allenai/openbookqa",
        hf_config="main",
        hf_split="train",
    ),
    HFSource(
        name="Generated_reasoning_mc",
        origin="generated",
        hf_path=None,
    ),

    # gpqa_hard_reasoning --------------------------------------------------
    HFSource(
        name="Generated_gpqa_style_science",
        origin="generated",
        hf_path=None,
    ),
    HFSource(
        name="Generated_multi_step_reasoning",
        origin="generated",
        hf_path=None,
    ),

    # long_context --------------------------------------------------------
    HFSource(
        name="NarrativeQA",
        origin="public",
        hf_path="deepmind/narrativeqa",
        hf_split="train",
    ),
    HFSource(
        name="QASPER",
        origin="public",
        hf_path="allenai/qasper",
        hf_split="train",
    ),
    HFSource(
        name="HotpotQA_distractor",
        origin="public",
        hf_path="hotpotqa/hotpot_qa",
        hf_config="distractor",
        hf_split="train",
    ),
    HFSource(
        name="Long_Data_Collections",
        origin="public",
        hf_path="togethercomputer/Long-Data-Collections",
        hf_split="train",
        notes="Multiple subsets; pick non-InfiniteBench-overlapping ones at extract time.",
    ),
    HFSource(
        name="NIH_style_synthetic",
        origin="programmatic",
        hf_path=None,
        notes="Built in questions/nih.py from a filler corpus + needle templates.",
    ),

    # general_instruction_breadth -----------------------------------------
    HFSource(
        name="Tulu_3_SFT_high_quality",
        origin="public",
        hf_path="allenai/tulu-3-sft-mixture",
        hf_split="train",
        filter={"top_quality": True, "single_turn": True, "language": "en"},
    ),
    HFSource(
        name="OpenHermes_2.5_curated",
        origin="public",
        hf_path="teknium/OpenHermes-2.5",
        hf_split="train",
        filter={"dedupe_against": "Tulu_3_SFT_high_quality"},
    ),
    HFSource(
        name="OASST_top_rated",
        origin="public",
        hf_path="OpenAssistant/oasst2",
        hf_split="train",
        filter={"single_turn": True, "top_rated": True},
    ),

    # code ----------------------------------------------------------------
    HFSource(
        name="CodeAlpaca",
        origin="public",
        hf_path="sahil2801/CodeAlpaca-20k",
        hf_split="train",
    ),
    HFSource(
        name="Magicoder_Evol_Instruct",
        origin="public",
        hf_path="ise-uiuc/Magicoder-Evol-Instruct-110K",
        hf_split="train",
    ),

    # openrewrite_shaped --------------------------------------------------
    HFSource(
        name="Generated_from_diverse_texts",
        origin="generated",
        hf_path=None,
        notes="Source texts drawn from public corpora at generation time; no single HF seed.",
    ),

    # conversation_regularization -----------------------------------------
    HFSource(
        name="OASST_multi_turn_non_cultural",
        origin="public",
        hf_path="OpenAssistant/oasst2",
        hf_split="train",
        filter={"exclude_cultural": True, "multi_turn": True, "task_oriented": True},
    ),
    HFSource(
        name="ShareGPT_filtered_non_cultural",
        origin="public",
        hf_path="anon8231489123/ShareGPT_Vicuna_unfiltered",
        hf_split="train",
        filter={"exclude_cultural": True, "coherent_multi_turn": True},
    ),
    HFSource(
        name="WildChat_task_oriented",
        origin="public",
        hf_path="allenai/WildChat-1M",
        hf_split="train",
        filter={"exclude_cultural": True, "task_oriented": True},
    ),
    HFSource(
        name="Generated_anti_modecollapse",
        origin="generated",
        hf_path=None,
    ),
]


SOURCES_BY_NAME: dict[str, HFSource] = {s.name: s for s in SOURCES}


# ---------------------------------------------------------------------------
# Decontamination test sets — downloaded for indexing, NEVER used as training
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecontamTestset:
    name: str                 # short label
    hf_path: str
    hf_config: str | None = None
    hf_split: str = "test"
    notes: str = ""


DECONTAM_TESTSETS: list[DecontamTestset] = [
    DecontamTestset("IFEval", "google/IFEval", hf_split="train",
                    notes="HF labels it 'train' but these 541 prompts ARE the eval set."),
    DecontamTestset("MMLU_test", "cais/mmlu", hf_config="all", hf_split="test"),
    DecontamTestset("MMLU_Pro_test", "TIGER-Lab/MMLU-Pro", hf_split="test"),
    DecontamTestset("GSM8K_test", "openai/gsm8k", hf_config="main", hf_split="test"),
    DecontamTestset("MATH_test", "hendrycks/competition_math", hf_split="test"),
    DecontamTestset("HellaSwag_validation", "Rowan/hellaswag", hf_split="validation",
                    notes="Test set labels are hidden; validation is the public surrogate."),
    DecontamTestset("ARC_Challenge_test", "allenai/ai2_arc", hf_config="ARC-Challenge"),
    DecontamTestset("ARC_Easy_test", "allenai/ai2_arc", hf_config="ARC-Easy"),
    DecontamTestset("OpenBookQA_test", "allenai/openbookqa", hf_config="main"),
    DecontamTestset("PIQA_validation", "ybisk/piqa", hf_split="validation"),
    DecontamTestset("SIQA_validation", "allenai/social_i_qa", hf_split="validation"),
    DecontamTestset("StoryCloze_test", "LSDSem/story_cloze", hf_config="2016"),
    DecontamTestset("GPQA_test", "Idavidrein/gpqa"),
    DecontamTestset("BFCL_test", "gorilla-llm/Berkeley-Function-Calling-Leaderboard",
                    notes="All subsets including v3 multi-turn."),
    DecontamTestset("NarrativeQA_test", "deepmind/narrativeqa"),
    DecontamTestset("QASPER_test", "allenai/qasper"),
    DecontamTestset("HotpotQA_dev", "hotpotqa/hotpot_qa", hf_config="distractor",
                    hf_split="validation"),
    DecontamTestset("HumanEval", "openai/openai_humaneval", hf_split="test"),
    DecontamTestset("MBPP", "google-research-datasets/mbpp", hf_split="test"),
    DecontamTestset("InfiniteBench", "xinrongzhang2022/InfiniteBench", hf_split="train",
                    notes="Single split; treat all of it as decontam target."),
]


DECONTAM_BY_NAME: dict[str, DecontamTestset] = {t.name: t for t in DECONTAM_TESTSETS}
