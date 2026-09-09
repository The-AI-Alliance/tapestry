# Dataset Download and Generation Guide

Companion document to `rehearsal_data_structure.json`. This guide specifies:
- **Part A**: Public datasets to download (HuggingFace paths, contents, usage)
- **Part B**: Question generation procedures (what to align with for each generated source)
- **Part C**: Distribution-matching protocol for maximizing benchmark alignment
- **Part D**: Build order and sequencing recommendations

The guiding principle for question generation: **mirror the test set's distribution on dimensions that matter — topic, difficulty, format, and surface features**. Generated questions that look distributionally different from the test set provide weaker rehearsal protection.

---

## Part A: Public datasets to download

For each dataset: HuggingFace path (or canonical URL), what's in it, how to load, and the specific subset/filter to apply.

### Benchmark training splits (use directly)

These are training splits of evaluation benchmarks. Use them directly as rehearsal data — they are distributionally exact for their benchmark.

| Dataset name in spec | HuggingFace path | Split to use | Volume to sample | Notes |
|---|---|---|---|---|
| ~~IFEval_train~~ (CORRECTION) | (no direct train split exists) | n/a | 2000 | **Important**: `google/IFEval` contains only 541 prompts and those ARE the eval set (no separate train split despite the HF `train` label). Using them as training data = direct test contamination. **Replace with**: `argilla/ifeval-like-data` (community-built IFEval-style training prompts) and/or fresh items generated via the 25-instruction-type taxonomy (see Part B6). The "IFEval_train" 2000 examples in the spec should be re-sourced from these alternatives, NOT from `google/IFEval`. |
| MMLU_auxiliary_training | `cais/mmlu` (config: `auxiliary_train`) | `train` | 2500 | The auxiliary_train config contains the auxiliary training set distributed with MMLU (Hendrycks et al. 2020). 99,842 questions across the 57 subjects |
| MMLU_Pro_train | `TIGER-Lab/MMLU-Pro` | `validation` | 1000 | MMLU-Pro provides a small validation/dev split. Sample 1000 questions, prefer harder ones |
| GSM8K_train | `openai/gsm8k` (config: `main`) | `train` | 2000 | 7,473 grade-school math problems with step-by-step solutions. Use Socratic config if you want intermediate questions, but `main` is standard |
| MATH_train_levels_1_2 | `hendrycks/competition_math` | `train`, filter `level` in [1, 2] | 1500 | 7,500 problems total in train. Levels 1-2 are easiest (Prealgebra heavy) |
| MATH_train_level_3 | `hendrycks/competition_math` | `train`, filter `level == 3` | 800 | Intermediate difficulty |
| MATH_train_levels_4_5 | `hendrycks/competition_math` | `train`, filter `level` in [4, 5] | 200 | Hardest; sparse usage |
| HellaSwag_train | `Rowan/hellaswag` | `train` | 1000 | 39,905 training items. Sample broadly across activity_label categories |
| ARC_Challenge_train | `allenai/ai2_arc` (config: `ARC-Challenge`) | `train` | 800 | 1,119 training questions (small). May need to supplement with generated questions |
| ARC_Easy_train | `allenai/ai2_arc` (config: `ARC-Easy`) | `train` | 200 | 2,251 training questions. Used for breadth |
| OpenBookQA_train | `allenai/openbookqa` (config: `main`) | `train` | 500 | 4,957 training questions |
| PIQA_train | `ybisk/piqa` | `train` | 400 | 16,113 training items. 2-way physical reasoning choice |
| SIQA_train | `allenai/social_i_qa` | `train` | 300 | 33,410 training items. 3-way social reasoning choice |
| Story_Cloze_train | `LSDSem/story_cloze` (config: `2016`) | `train` (Spring 2016 split) | 300 | Note: Story Cloze training is the ROCStories dataset (98K stories). Synthesize 2-way endings or use existing ROCStories endings |

### Augmentation / variant datasets (use as-is or filter)

| Dataset name in spec | HuggingFace path | Split | Volume | Notes |
|---|---|---|---|---|
| MetaMathQA | `meta-math/MetaMathQA` | `train` | 1500 | 395K augmented math problems including question rephrasing, FOBAR, answer augmentation. Filter to keep only items derived from GSM8K-style problems (avoid leaking MATH test) |
| ASDiv_and_easy_subset | `MU-NLPC/Calc-asdiv_a` or `allenai/lila` (subset: asdiv) | `train` | 500 | ASDiv has 2,305 problems. Combine with GSM8K training items filtered for ≤1 reasoning step |
| NoRobots_filtered | `HuggingFaceH4/no_robots` | `train` | 1400 | 9,500 high-quality human-written instructions. Filter to instruction-following items suitable for adding IFEval-style constraints |

### Long-context training sources

| Dataset name in spec | HuggingFace path | Split | Volume | Notes |
|---|---|---|---|---|
| NarrativeQA | `deepmind/narrativeqa` | `train` | 800 | 32K QA pairs over long stories/movie scripts. Average context length ~62K tokens — chunk to fit 2K-16K windows for short/medium/long subcategories |
| QASPER | `allenai/qasper` | `train` | 600 | ~5K QA pairs over scientific papers. Context lengths typically 4K-16K tokens — good fit for medium/long subcategories |
| HotpotQA_distractor | `hotpotqa/hotpot_qa` (config: `distractor`) | `train` | 700 | 90K multi-hop QA with distractor paragraphs. Context typically 2K-8K tokens |
| Long_Data_Collections | `togethercomputer/Long-Data-Collections` | `train` (various subsets) | 700 | Community collection of long-context datasets. Pick subsets that don't overlap with InfiniteBench test items |

### Tool-calling sources

| Dataset name in spec | HuggingFace path | Split | Volume | Notes |
|---|---|---|---|---|
| xLAM | `Salesforce/xlam-function-calling-60k` | `train` | 2000 | 60K function-calling examples from APIGen pipeline. Primarily single-turn |
| Glaive_Function_Calling_v2 | `glaiveai/glaive-function-calling-v2` | `train` | 1200 | ~113K function-calling examples; includes some multi-turn. Filter for high quality |
| Hermes_Function_Calling | `NousResearch/hermes-function-calling-v1` | `train` | 400 | Curated function-calling with reasoning. Multiple sub-splits — use `func_calling_singleturn` and `func_calling` |
| API_Bank_filtered | `liminghao1630/API-Bank` | `train` | 200 | API-Bank has multi-turn API call dialogues. Filter for state-tracking examples |

### Code sources

| Dataset name in spec | HuggingFace path | Split | Volume | Notes |
|---|---|---|---|---|
| CodeAlpaca | `sahil2801/CodeAlpaca-20k` | `train` | 300 | 20K instruction-style coding tasks. Python-heavy but multi-language |
| Magicoder_Evol_Instruct | `ise-uiuc/Magicoder-Evol-Instruct-110K` | `train` | 200 | 110K Evol-Instruct coding instructions across many languages |

### General instruction data

| Dataset name in spec | HuggingFace path | Split | Volume | Notes |
|---|---|---|---|---|
| Tulu_3_SFT_high_quality | `allenai/tulu-3-sft-mixture` | `train` | 650 | ~1M curated SFT items. Filter to top-quality, single-turn, English. Avoid items that overlap with our other categories (math/code/IFEval-style) |
| OpenHermes_2.5_curated | `teknium/OpenHermes-2.5` | `train` | 400 | ~1M instruction examples. Filter for quality and remove duplicates with Tulu 3 |
| OASST_top_rated | `OpenAssistant/oasst1` or `OpenAssistant/oasst2` | `train` | 150 | Top-rated single-turn conversations |

### Conversation regularization sources (filtered to non-cultural)

| Dataset name in spec | HuggingFace path | Split | Volume | Critical filter |
|---|---|---|---|---|
| OASST_multi_turn_non_cultural | `OpenAssistant/oasst2` | `train` | 250 | **Filter out all items mentioning Vietnamese, Vietnam, East Asian cultural topics, or Asian languages.** Keep multi-turn branches with quality > threshold. Task-oriented preferred |
| ShareGPT_filtered_non_cultural | `anon8231489123/ShareGPT_Vicuna_unfiltered` | `train` | 200 | **Same cultural filter as above.** Keep coherent multi-turn task-oriented dialogues |
| WildChat_task_oriented | `allenai/WildChat-1M` | `train` | 150 | **Same cultural filter.** Filter to task-oriented (code help, writing assistance, factual Q&A); exclude personal/emotional/cultural content |

### Safety / decontamination test sources

These are NOT used as training data. They are used in the **decontamination protocol** to filter the training pool. Download for filtering purposes only.

| Test set | HuggingFace path | Purpose |
|---|---|---|
| IFEval test | `google/IFEval` (test split) | Decontamination |
| MMLU test (all 57 subjects) | `cais/mmlu` (test splits, all configs) | Decontamination |
| MMLU-Pro test | `TIGER-Lab/MMLU-Pro` (test split) | Decontamination |
| GSM8K test | `openai/gsm8k` (test split) | Decontamination |
| MATH test | `hendrycks/competition_math` (test split) | Decontamination |
| HellaSwag validation | `Rowan/hellaswag` (validation split) | Decontamination (HellaSwag's test set is hidden; use validation) |
| ARC-Challenge test | `allenai/ai2_arc` (ARC-Challenge test split) | Decontamination |
| ARC-Easy test | `allenai/ai2_arc` (ARC-Easy test split) | Decontamination |
| OpenBookQA test | `allenai/openbookqa` (test split) | Decontamination |
| PIQA validation | `ybisk/piqa` (validation split) | Decontamination |
| SIQA validation | `allenai/social_i_qa` (validation split) | Decontamination |
| Story Cloze 2016 test | `LSDSem/story_cloze` (test split) | Decontamination |
| GPQA test | `Idavidrein/gpqa` (gpqa_main, gpqa_diamond) | Decontamination |
| BFCL test | `gorilla-llm/Berkeley-Function-Calling-Leaderboard` | Decontamination (all subsets including v3 multi-turn) |
| NarrativeQA test | `deepmind/narrativeqa` (test split) | Decontamination |
| QASPER test | `allenai/qasper` (test split) | Decontamination |
| HotpotQA dev | `hotpotqa/hotpot_qa` (validation split, both distractor and fullwiki) | Decontamination |
| HumanEval | `openai/openai_humaneval` | Decontamination |
| MBPP | `google-research-datasets/mbpp` | Decontamination |
| OpenRewrite test | If publicly released; otherwise rely on n-gram similarity heuristics against the task spec | Decontamination |
| InfiniteBench | `xinrongzhang2022/InfiniteBench` | Decontamination |
| NIH Multi-Needle | Build from spec (Greg Kamradt's original methodology) | Decontamination |

### Sampling and loading patterns

For all benchmark training splits, the standard loading pattern is:

```python
from datasets import load_dataset

# Example: MMLU auxiliary training
mmlu_aux = load_dataset("cais/mmlu", "auxiliary_train", split="train")

# Sample stratified across subjects if dataset has subject labels
# Example: sample 2500 with proportions matching the 57-subject distribution
```

Apply decontamination filtering BEFORE sampling to the target volume. Generate ~10-15% extra to absorb decontamination losses.

---

## Part B: Question generation procedures

For each generated source listed in the spec, this section specifies what test set to align with, what to mirror, and how to construct the generation prompt.

The core principle: **the test set IS the alignment target**. Before generating, load the corresponding test set and compute its distribution statistics. Generation prompts must reproduce that distribution.

### B1. Synthetic_via_Qwen (MMLU, 3500 items)

**Test set to align with**: MMLU test (`cais/mmlu`, all 57 subject configs, test split).

**Statistics to compute from test set before generating**:
- Per-subject question count distribution (57 subjects)
- Average question length (tokens)
- Average answer choice length (tokens)
- Distribution of question types per subject (factual recall vs reasoning vs application)

**Generation procedure**:
1. Sample subject proportionally to MMLU test set's 57-subject distribution
2. For each generation request, provide Qwen 2.5 32B with:
   - Subject name
   - 3-5 in-context examples from MMLU auxiliary train (NOT from test) in the chosen subject
   - Instruction: "Generate a new multiple-choice question in this subject with 4 answer choices, in the same style and difficulty as the examples. Mark the correct answer."
3. Reject generated questions where:
   - Format does not parse as 4-way MC
   - The "correct" answer matches another option semantically (LLM-judge check)
   - Question is contaminated with test set (decontamination)

**Distribution-matching checks before training**:
- Per-subject distribution within 10% of MMLU test
- Question length distribution within 1 stdev of MMLU test
- Topic coverage spans all 57 subjects

### B2. GSM8K_train_variants (GSM8K, 1000 items)

**Test set to align with**: GSM8K test (1,319 problems).

**Statistics to compute from test set before generating**:
- Average number of reasoning steps (typically 2-8)
- Average problem length (typically 200-400 characters)
- Distribution of mathematical operations (arithmetic, multi-step word problems)
- Common context types (money, ages, sharing, distance, time)

**Generation procedure**:
1. Sample base problems from GSM8K training set (not test)
2. For each base problem, generate variants via:
   - Number substitution (preserve structure, change values consistently)
   - Context substitution (preserve numerical structure, change cover story)
   - Solver pass with Qwen 2.5 Math 32B to produce step-by-step solution
3. Validate: numerical answer is consistent with the substituted problem; reasoning steps are logical

**Distribution-matching checks**:
- Step count distribution within 1 stdev of GSM8K test
- Final answer should always be a whole number or simple decimal (matching GSM8K convention)
- Solution length distribution similar to test

### B3. Generated_hellaswag_style (HellaSwag, 500 items)

**Test set to align with**: HellaSwag validation set (10,042 items; test labels are hidden).

**Statistics to compute**:
- Distribution between video-action contexts (ActivityNet-derived) and instructional contexts (WikiHow-derived)
- Context length distribution
- 4 continuation options per item, with 1 correct and 3 adversarial (machine-generated style)

**Generation procedure**:
1. Sample context source: ActivityNet Captions for action contexts, WikiHow for instructional
2. Provide Qwen 2.5 14B with:
   - Context (2-4 sentences)
   - Instruction: "Generate 4 possible continuations. One should be the correct/most natural continuation. Three should be plausible-sounding but incorrect (the kind of errors a worse model would make). Format as JSON."
3. Validate: 4 options exist, one labeled correct, format parses

**Distribution-matching checks**:
- Roughly 50/50 split between action and instructional contexts (mirrors HellaSwag)
- Context length within HellaSwag distribution
- Adversarial options should be semantically plausible (LLM-judge check)

### B4. Generated_reasoning_mc (ARC Challenge, 500 items)

**Test set to align with**: ARC Challenge test (1,172 items).

**Statistics to compute**:
- Distribution of question types (causal reasoning, scientific principles, mathematical reasoning)
- Number of answer choices (mostly 4, some 3 or 5)
- Difficulty signal (questions where simple keyword matching fails)

**Generation procedure**:
1. Provide Qwen 2.5 32B with:
   - Domain (science, logic, general knowledge)
   - In-context examples from ARC training
   - Instruction: "Generate a multiple-choice question that requires reasoning beyond keyword matching. Provide 4 options with one correct."
2. Critic pass: a second model checks that the question genuinely requires reasoning (not surface keyword match)

**Distribution-matching checks**:
- Topic distribution similar to ARC Challenge test
- Average reasoning steps per question within ARC distribution

### B5. Generated_gpqa_style_science and Generated_multi_step_reasoning (GPQA, 1500 items)

**Test set to align with**: GPQA test (448 items, including Diamond subset of 198).

**Critical note**: No GPQA training set exists. All items must be generated. This is the highest-risk category for distribution mismatch.

**Statistics to compute from test set**:
- Domain distribution (physics, chemistry, biology — approximately equal)
- Subdomain breakdown within each (e.g., physics: mechanics, electromagnetism, quantum, thermodynamics)
- Average question length (often longer than MMLU due to setup)
- Format: 4-way MC with single correct answer
- Difficulty calibration: questions that PhD-level domain experts can answer with >65% accuracy but non-experts get <34% (per GPQA paper)

**Generation procedure**:
1. For graduate_level_science (800):
   - Sample domain proportionally (physics ~33%, chemistry ~33%, biology ~33%)
   - Sample subdomain within domain
   - Provide Kimi K2.6 (thinking mode) or DeepSeek-R1 with:
     - Domain and subdomain
     - Instruction: "Generate a graduate-level multiple-choice question in [subdomain]. The question should require domain expertise that a competent non-expert cannot answer by quick web search. Provide 4 answer choices, one correct, with detailed reasoning trace."
   - Filter: discard items where reasoning contains self-correction artifacts ("wait, that's wrong"), per filtering_requirement in spec
2. For multi_step_reasoning (700):
   - Generate logic puzzles, causal chains, complex deduction problems beyond science domains
   - Same format and filtering

**Distribution-matching checks**:
- Domain balance (physics/chem/bio roughly equal)
- Question length distribution within 1 stdev of GPQA test
- Reasoning depth: items should require 3-8 reasoning steps minimum

### B6. Augmented_constraint_templates and Generated_prompt_constraint_pairs (IFEval, 5100 items combined)

**Test set to align with**: IFEval test (541 prompts).

**Statistics to compute**:
- Distribution across 25 instruction types in IFEval taxonomy
- Distribution of constraint counts per prompt (single vs stacked)
- Base prompt domains (writing, summarization, explanation, formatting)

**The 25 IFEval instruction types** (use this taxonomy for generation):

```
Keywords (4 types):
  - existence: include specific keyword(s)
  - frequency: include keyword N times
  - forbidden_words: do not use keyword(s)
  - letter_frequency: contain letter N times

Language (1 type):
  - response_language: respond in specified language

Length (4 types):
  - number_sentences: at most/least/exactly N sentences
  - number_paragraphs: at most/least/exactly N paragraphs
  - number_words: at most/least/exactly N words
  - nth_paragraph_first_word: Nth paragraph must start with X

Detectable_content (2 types):
  - number_placeholders: contain N [placeholders]
  - postscript: include "P.S." section

Detectable_format (6 types):
  - number_bullet_lists: contain N bullet points
  - constrained_response: response from a fixed set
  - number_highlighted_sections: highlight N sections
  - multiple_sections: contain N sections with headers
  - json_format: respond in JSON
  - title: include a title in << >>

Combination (2 types):
  - two_responses: give two distinct responses separated
  - repeat_prompt: repeat prompt before response

Startend (2 types):
  - end_checker: end with specific phrase
  - quotation: wrap response in quotation marks

Change_case (3 types):
  - capital_word_frequency: N words in all caps
  - english_capital: response in all caps
  - english_lowercase: response in all lowercase

Punctuation (1 type):
  - no_comma: no commas in response
```

**Generation procedure for Augmented_constraint_templates (4200)**:
1. Take base instructions from public sources (Tulu 3 prompts, NoRobots, OASST single-turn). Sample 4200 base prompts.
2. Sample 1-3 constraints per prompt from the 25-type taxonomy, with type distribution matching IFEval test (length_constraints 22%, detectable_format 18%, combination 15%, detectable_content 12%, startend 10%, keywords 8%, punctuation 6%, language 5%, change_case 4%).
3. Programmatically construct the constraint specification text and append to base instruction.
4. Generate compliant response using Claude Sonnet 4.6 (no thinking mode).
5. Verify response satisfies all constraints via automated checking (one verifier per constraint type — this is exactly what IFEval evaluation does).

**Generation procedure for Generated_prompt_constraint_pairs (900)**:
1. Provide Claude Sonnet 4.6 with the constraint taxonomy
2. Instruction: "Generate a realistic instruction-following request with [N] constraints from these types: [...]. Provide both the prompt and a compliant response."
3. Same verification step

**Distribution-matching checks**:
- Constraint type distribution within 5% of IFEval test
- Single vs stacked constraint distribution similar to test (test is roughly 60% single, 40% multi)
- Constraint count distribution matched (1 constraint: ~60%, 2-3 constraints: ~40%)

### B7. BFCL_v3_multi_turn_generated (BFCL, 700 items)

**Test set to align with**: BFCL v3 multi-turn test (800 tasks, 200 per challenge type).

**The 5 BFCL v3 multi-turn challenge types**:

1. **Base multi-turn** (200 items in test): Standard multi-turn function calling without complications
2. **Missing function** (200): User asks for capability where required function is not in the provided toolkit; model should respond conversationally rather than hallucinate
3. **Missing parameter** (200): User's request lacks information needed to fill a required function parameter; model should ask for clarification
4. **Long-context multi-turn** (200): Multi-turn where conversation history is long; model must retain context across many turns
5. **Composite** (200): Multiple challenges combined

**Generation procedure**:
1. Distribute 700 generated items roughly equally across the 5 challenge types (140 each, with some flexibility)
2. For each challenge type, provide Claude Sonnet 4.6 with:
   - Challenge type definition
   - 2-3 in-context examples from BFCL v3 training docs (NOT test items)
   - Tool catalog (a set of plausible API functions)
   - Instruction: "Generate a realistic multi-turn dialogue exemplifying [challenge_type]. Format with each turn clearly labeled (user/assistant). Include the expected state of API calls after each assistant turn."
3. Validate:
   - JSON parses for all function calls
   - Tool names match the provided catalog
   - For "missing function" items, model correctly does not call a fabricated tool
   - For "missing parameter" items, model correctly asks for clarification

**Distribution-matching checks**:
- Challenge type balance roughly equal across 5 types
- Average turn count within BFCL v3 distribution (typically 4-8 turns)
- Tool catalog diversity (vehicle control, trading, travel booking, file systems — match BFCL v3 domains)

### B8. NIH_style_synthetic (Long context, 700 items)

**Test set to align with**: NIH multi-needle test (variable lengths, multiple needles).

**Generation procedure** (programmatic, no LLM teacher needed for question generation):
1. Build a corpus of long filler text (essays, news articles, books — public domain or permissively licensed)
2. Define needles: specific facts in templated form ("[Specific entity] was [doing X] in [specific location]")
3. Vary:
   - Context length (1K, 2K, 4K, 8K, 16K, 32K tokens)
   - Number of needles (1, 3, 5, 7)
   - Needle position (start, middle, end, distributed)
4. Question template asks model to retrieve specific needle(s) given the long context
5. Answer is the needle fact, or list of needles

**Distribution-matching checks**:
- Context length distribution matches NIH test (often heavily-tested at boundary lengths)
- Position distribution covers all regions (avoid bias toward end positions)

### B9. Generated_from_diverse_texts (OpenRewrite, 500 items)

**Test set to align with**: OpenRewrite test set (Meta's rewrite benchmark).

**Statistics to compute**:
- Distribution of rewrite tasks (style transfer, length adjustment, summarization, paraphrasing)
- Source text length distribution
- Source text domains (news, emails, technical, casual)

**Generation procedure**:
1. Sample source texts from diverse public corpora (news articles, email datasets, technical writing, casual prose)
2. For each text, select a rewrite task type per the subcategory distribution (style 30%, length 30%, summarization 20%, paraphrasing 20%)
3. Provide Claude Sonnet 4.6 with:
   - Source text
   - Rewrite instruction
   - Instruction: "Produce a rewritten version following the instruction. Preserve meaning."
4. Validate meaning preservation with LLM-judge check

### B10. Generated_anti_modecollapse (conversation_regularization, 200 items)

**Test set to align with**: Not a specific test set — purpose is mode-collapse prevention.

**Generation procedure**:
1. Provide Claude Sonnet 4.6 with:
   - Diverse non-cultural topic seeds (math, code, factual Q&A, writing assistance)
   - Instruction: "Generate a multi-turn task-oriented dialogue or a single-turn helpful response. The content must NOT involve Vietnamese culture, Vietnam, East Asian topics, or any cultural framing. Topic should be generic and task-focused."
2. Apply cultural-content filter (LLM judge) — reject any items mentioning Vietnamese culture or East Asian framing
3. Roughly 50% single-turn in chat template + 50% multi-turn

**Critical filter**: This subset's effectiveness depends entirely on it being CULTURALLY NEUTRAL. If cultural content leaks in, the regularization purpose fails.

---

## Part C: Distribution-matching protocol

Before training, run a quantitative comparison between rehearsal corpus and test set for each Meta benchmark.

### Per-benchmark distribution comparison

For each category in the rehearsal corpus, compare these distributions against the corresponding test set:

1. **Topic/subject distribution** — for benchmarks with topic labels (MMLU, ARC, OpenBookQA, GPQA, math by level)
2. **Length distribution** — question length, answer length, total length
3. **Format distribution** — MC vs free-form, JSON vs text, number of options
4. **Difficulty distribution** — where labels available (MATH levels), where computable (GSM8K step count)
5. **Vocabulary distribution** — TF-IDF profile similarity (cosine similarity)

### Acceptance criteria (run before final training)

- Topic/subject distribution: KL divergence < 0.2 from test set distribution
- Length distribution: median within 20% of test set median, 90th percentile within 25%
- Format distribution: exact match on format proportions
- Vocabulary cosine similarity: > 0.85

If any criterion fails for a category, regenerate or resample that category before proceeding.

### Implementation

```python
from datasets import load_dataset
from scipy.stats import entropy

# Example: check MMLU subject distribution match
mmlu_test = load_dataset("cais/mmlu", "all", split="test")
mmlu_rehearsal = load_rehearsal("mmlu_shaped")

test_subjects = compute_subject_distribution(mmlu_test)
rehearsal_subjects = compute_subject_distribution(mmlu_rehearsal)

kl_div = entropy(rehearsal_subjects, test_subjects)
assert kl_div < 0.2, f"MMLU subject distribution mismatch: KL={kl_div}"
```

---

## Part D: Build order and sequencing

The order in which to build the dataset matters. Some steps depend on others.

### Phase 1: Infrastructure (do first)

1. Download all test sets listed in Part A (for decontamination)
2. Set up decontamination infrastructure:
   - Exact match index
   - 13-gram index
   - Semantic embedding store (sentence-transformers/all-MiniLM-L6-v2)
3. Build distribution-statistics extraction script for each benchmark

### Phase 2: Public dataset acquisition

4. Download all public datasets listed in Part A
5. Apply per-dataset filtering as specified (especially cultural filters for conversation_regularization sources)
6. Apply decontamination filtering against all test sets
7. Sample to target volumes (generate 10-15% buffer)

### Phase 3: Generation (most expensive)

8. Compute test set distributions for each benchmark
9. For each generated source (B1-B10), construct generation prompt aligned with the test set distribution
10. Generate per-category in this order (cheapest/safest first):
    - Synthetic_via_Qwen (MMLU) — Qwen 2.5 32B, self-hosted
    - Generated_reasoning_mc (ARC) — Qwen 2.5 32B
    - Generated_hellaswag_style — Qwen 2.5 14B
    - GSM8K_train_variants — Qwen 2.5 Math 32B + programmatic
    - NIH_style_synthetic — programmatic (no LLM)
    - Generated_from_diverse_texts (OpenRewrite) — Claude Sonnet 4.6
    - Augmented_constraint_templates (IFEval) — Claude Sonnet 4.6
    - Generated_prompt_constraint_pairs (IFEval) — Claude Sonnet 4.6
    - BFCL_v3_multi_turn_generated — Claude Sonnet 4.6
    - Generated_anti_modecollapse — Claude Sonnet 4.6 (apply cultural filter)
    - Generated_gpqa_style_science — Kimi K2.6 / DeepSeek-R1 (most expensive last)
    - Generated_multi_step_reasoning — Kimi K2.6 / DeepSeek-R1

### Phase 4: Pilot validation

11. Sample 10% of each category proportionally (~4K total)
12. Apply full decontamination and verification on pilot
13. Fine-tune Llama 3.2 3B on rehearsal-only pilot (no cultural data)
14. Evaluate on all 10 relevant Meta benchmarks + multi-turn BFCL
15. Compare to base Llama 3.2 3B Instruct scores
16. If any benchmark drops significantly, debug that category before proceeding

### Phase 5: Full generation and assembly

17. Scale to full per-category volumes
18. Run full decontamination pass against all test sets
19. Per-category verification (constraint check, answer match, JSON parse, etc.)
20. Length distribution normalization (compare to cultural data distribution)
21. Final assembly: trim to 40K target, sample maintaining per-category volume targets
22. Final decontamination check (second pass)

### Phase 6: Distribution validation

23. Run distribution-matching protocol (Part C) on full corpus
24. Document any categories that fail acceptance criteria
25. If validation passes, proceed to full fine-tuning with cultural data

---

## Quick reference: source-to-category mapping

| Source | Used in category | Volume | Type |
|---|---|---|---|
| IFEval_style_training_prompts | ifeval_shaped | 2000 | Public/Generated |
| Augmented_constraint_templates | ifeval_shaped | 4200 | Augmented |
| NoRobots_filtered | ifeval_shaped | 1400 | Public |
| Generated_prompt_constraint_pairs | ifeval_shaped | 900 | Generated |
| MMLU_auxiliary_training | mmlu_shaped | 2500 | Public |
| Synthetic_via_Qwen | mmlu_shaped | 3500 | Generated |
| MMLU_Pro_train | mmlu_shaped | 1000 | Public |
| GSM8K_train | gsm8k_shaped_math | 2000 | Public |
| GSM8K_train_variants | gsm8k_shaped_math | 1000 | Augmented |
| MetaMathQA | gsm8k_shaped_math | 1500 | Public |
| ASDiv_and_easy_subset | gsm8k_shaped_math | 500 | Public |
| MATH_train_levels_1_2 | math_shaped | 1500 | Public |
| MATH_train_level_3 | math_shaped | 800 | Public |
| MATH_train_levels_4_5 | math_shaped | 200 | Public |
| HellaSwag_train | hellaswag_shaped | 1000 | Public |
| Generated_hellaswag_style | hellaswag_shaped | 500 | Generated |
| PIQA_train | hellaswag_shaped | 400 | Public |
| SIQA_train | hellaswag_shaped | 300 | Public |
| Story_Cloze_train | hellaswag_shaped | 300 | Public |
| xLAM | bfcl_shaped_tool_calling | 2000 | Public |
| Glaive_Function_Calling_v2 | bfcl_shaped_tool_calling | 1200 | Public |
| Hermes_Function_Calling | bfcl_shaped_tool_calling | 400 | Public |
| BFCL_v3_multi_turn_generated | bfcl_shaped_tool_calling | 700 | Generated |
| API_Bank_filtered | bfcl_shaped_tool_calling | 200 | Public |
| ARC_Challenge_train | arc_challenge_shaped | 800 | Public |
| ARC_Easy_train | arc_challenge_shaped | 200 | Public |
| OpenBookQA_train | arc_challenge_shaped | 500 | Public |
| Generated_reasoning_mc | arc_challenge_shaped | 500 | Generated |
| Generated_gpqa_style_science | gpqa_hard_reasoning | 800 | Generated |
| Generated_multi_step_reasoning | gpqa_hard_reasoning | 700 | Generated |
| NarrativeQA | long_context | 800 | Public |
| QASPER | long_context | 600 | Public |
| HotpotQA_distractor | long_context | 700 | Public |
| Long_Data_Collections | long_context | 700 | Public |
| NIH_style_synthetic | long_context | 700 | Synthetic (programmatic) |
| Tulu_3_SFT_high_quality | general_instruction_breadth | 650 | Public |
| OpenHermes_2.5_curated | general_instruction_breadth | 400 | Public |
| OASST_top_rated | general_instruction_breadth | 150 | Public |
| CodeAlpaca | code | 300 | Public |
| Magicoder_Evol_Instruct | code | 200 | Public |
| Generated_from_diverse_texts | openrewrite_shaped | 500 | Generated |
| OASST_multi_turn_non_cultural | conversation_regularization | 250 | Public (filtered) |
| ShareGPT_filtered_non_cultural | conversation_regularization | 200 | Public (filtered) |
| WildChat_task_oriented | conversation_regularization | 150 | Public (filtered) |
| Generated_anti_modecollapse | conversation_regularization | 200 | Generated |

**Total**: 40,000 examples

**Type breakdown**:
- Public datasets (direct use): 21,600 (54.0%)
- Public datasets (filtered): 2,200 (5.5%) — NoRobots and conversation_regularization sources
- Public/Generated mixed: 2,000 (5.0%) — IFEval-style training (replaces former IFEval_train)
- Augmented from public: 5,200 (13.0%) — GSM8K variants + Augmented constraint templates
- Generated by teacher LLMs: 8,300 (20.8%)
- Programmatic synthetic: 700 (1.8%) — NIH-style needle-in-haystack

---

## Notes on dataset availability

All HuggingFace paths listed are valid as of when this document was written. Some may have moved or been renamed. If a path returns 404:
- Search HuggingFace for the dataset name
- Check the original paper's GitHub for canonical hosting
- Note any substitutions in your final report

For datasets where licensing may be restrictive (Story Cloze, some ShareGPT mirrors), verify license compatibility with your project before downloading at scale.
