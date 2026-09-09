"""
RLearner-LLM Synthetic Data Augmentation (亮点三完整实现)

Generates two types of synthetic data to strengthen DPO training:

A) HIGH-QUALITY POSITIVE DEMOS (y_chosen 上限)
   Uses GPT-4o or Claude-3.5-Sonnet with Chain-of-Thought (CoT) prompting to write
   "textbook-level" expert explanations for PeerWise questions.
   These become the gold standard y_chosen in DPO, pushing the model beyond
   what human students wrote.

B) HARD NEGATIVE EXAMPLES (y_rejected 强负样本)
   Uses the same LLM to deliberately generate flawed explanations of 4 types:
     1. Inverted logic: Attributes the correct reasoning to a wrong option
     2. Concept confusion: Mixes up distractors' explanations with the correct answer
     3. High-score gibberish: Fluent, formal-sounding text with zero factual content
     4. Circular reasoning: Re-states the question as the explanation without justification

   These hard negatives teach the DPO model that "confident-sounding" ≠ "correct".

Usage:
    # Generate with GPT-4o
    python rl_generate_synthetic_data.py \
        --data_path ./Paul_new_data/Cardiff/Cardiff_all_generator_train_avg_3_lenexp_10.json \
        --output_path ./rl_synthetic_data/cardiff_synthetic.json \
        --api_provider openai \
        --api_key YOUR_OPENAI_KEY \
        --model gpt-4o \
        --num_questions 500

    # Generate with Claude
    python rl_generate_synthetic_data.py \
        --data_path ./Paul_new_data/Cardiff/Cardiff_all_generator_train_avg_3_lenexp_10.json \
        --output_path ./rl_synthetic_data/cardiff_synthetic.json \
        --api_provider anthropic \
        --api_key YOUR_ANTHROPIC_KEY \
        --model claude-3-5-sonnet-20241022 \
        --num_questions 500

    # Merge with preference pairs from rl_build_preference_data.py
    python rl_generate_synthetic_data.py \
        --merge_with ./rl_preference_data/preference_pairs.json \
        --output_path ./rl_preference_data/preference_pairs_augmented.json \
        [... other args ...]
"""

import argparse
import json
import logging
import os
import random
import time
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

COT_POSITIVE_SYSTEM = """You are an expert educator writing textbook-quality explanations for exam questions.
Your explanations must:
1. Clearly state WHY the correct answer is right using specific domain knowledge
2. Briefly explain WHY each incorrect option is wrong (to prevent concept confusion)
3. Use precise academic terminology appropriate for the subject
4. Be logically structured: state fact → explain mechanism → connect to answer
5. Be 3-6 sentences long — substantive but not verbose

Do NOT simply restate the question. Do NOT use vague phrases like "clearly" or "obviously".
Think step-by-step before writing the final explanation."""

COT_POSITIVE_USER = """Here is an exam question. Write a textbook-quality explanation.

{question_block}

First, think through the reasoning step by step (internal chain-of-thought).
Then write the final explanation in this format:
EXPLANATION: [Your 3-6 sentence explanation here]"""

HARD_NEGATIVE_SYSTEM = """You are helping build a training dataset by generating intentionally flawed explanations.
These flawed explanations will be used as negative examples to teach a model what NOT to do.
Generate the requested type of bad explanation as instructed."""

HARD_NEGATIVE_USER_INVERTED = """Generate a LOGICALLY INVERTED explanation for this question.
The explanation should confidently attribute the correct reasoning to the WRONG answer choice,
making it sound plausible but actually backwards.

{question_block}

Generate an inverted explanation (sounds confident, but logic is reversed):
FLAWED EXPLANATION:"""

HARD_NEGATIVE_USER_CONFUSION = """Generate a CONCEPT CONFUSION explanation for this question.
Take the reasoning that applies to one of the INCORRECT options and confidently apply it
to explain why the CORRECT answer is right. Mix up the concepts.

{question_block}

Generate a concept-confused explanation (applies wrong reasoning to right answer):
FLAWED EXPLANATION:"""

HARD_NEGATIVE_USER_GIBBERISH = """Generate a HIGH-SCORE GIBBERISH explanation for this question.
Write something that sounds highly academic, uses impressive vocabulary and complex sentence structure,
but contains absolutely no specific factual content — just generic educational-sounding filler.
Do NOT mention any specific facts, mechanisms, or domain concepts.

{question_block}

Generate academic-sounding gibberish with no real content:
FLAWED EXPLANATION:"""

HARD_NEGATIVE_USER_CIRCULAR = """Generate a CIRCULAR REASONING explanation for this question.
Simply restate what the question already says without adding any new information or justification.
The explanation should just echo the answer choice without explaining why it is correct.

{question_block}

Generate a circular, content-free explanation:
FLAWED EXPLANATION:"""

HARD_NEGATIVE_TYPES = [
    ("inverted_logic", HARD_NEGATIVE_USER_INVERTED, "Logically inverted reasoning"),
    ("concept_confused", HARD_NEGATIVE_USER_CONFUSION, "Mixed-up concepts"),
    ("gibberish", HARD_NEGATIVE_USER_GIBBERISH, "High-score academic gibberish"),
    ("circular", HARD_NEGATIVE_USER_CIRCULAR, "Circular reasoning"),
]


# ─────────────────────────────────────────────────────────────────────────────
# API CLIENTS
# ─────────────────────────────────────────────────────────────────────────────


def call_openai(
    client,
    system: str,
    user: str,
    model: str = "gpt-4o",
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """Call OpenAI API and return the assistant's message content."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def call_anthropic(
    client,
    system: str,
    user: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """Call Anthropic API and return the assistant's message content."""
    response = client.messages.create(
        model=model,
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.content[0].text.strip()


def build_api_caller(provider: str, api_key: str, model: str):
    """Build a unified API call function for the given provider."""
    if provider == "openai":
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai>=1.0")
        client = OpenAI(api_key=api_key)
        return lambda sys, usr, **kw: call_openai(client, sys, usr, model=model, **kw)

    elif provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")
        client = anthropic.Anthropic(api_key=api_key)
        return lambda sys, usr, **kw: call_anthropic(client, sys, usr, model=model, **kw)

    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'anthropic'.")


# ─────────────────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def format_question_block(item: dict) -> str:
    """Format a PeerWise item into a readable question block for the LLM prompt."""
    input_text = item.get("input", "").replace("</s>", "").strip()
    # input_text already contains: Question, Options, Correct Answer
    return input_text


def extract_explanation_from_response(text: str, tag: str = "EXPLANATION:") -> str:
    """Extract the explanation text after the tag marker."""
    if tag in text:
        return text.split(tag)[-1].strip()
    # Fallback: return everything after the last colon
    lines = text.strip().split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            return "\n".join(lines[i:]).strip()
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# CORE GENERATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────


def generate_positive_demo(
    item: dict,
    api_call,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> Optional[str]:
    """Generate a high-quality CoT explanation using GPT-4o/Claude."""
    question_block = format_question_block(item)
    if not question_block:
        return None

    user_prompt = COT_POSITIVE_USER.format(question_block=question_block)
    try:
        response = api_call(
            COT_POSITIVE_SYSTEM,
            user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return extract_explanation_from_response(response, tag="EXPLANATION:")
    except Exception as e:
        logger.warning(f"API error generating positive demo: {e}")
        return None


def generate_hard_negative(
    item: dict,
    api_call,
    negative_type: str = "random",
    max_tokens: int = 256,
    temperature: float = 0.8,
) -> Optional[Dict[str, str]]:
    """Generate a hard negative explanation of the specified type."""
    question_block = format_question_block(item)
    if not question_block:
        return None

    if negative_type == "random":
        neg_type_key, user_template, description = random.choice(HARD_NEGATIVE_TYPES)
    else:
        found = [t for t in HARD_NEGATIVE_TYPES if t[0] == negative_type]
        if not found:
            raise ValueError(f"Unknown negative type: {negative_type}")
        neg_type_key, user_template, description = found[0]

    user_prompt = user_template.format(question_block=question_block)
    try:
        response = api_call(
            HARD_NEGATIVE_SYSTEM,
            user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        flawed = extract_explanation_from_response(response, tag="FLAWED EXPLANATION:")
        return {
            "text": flawed,
            "type": neg_type_key,
            "description": description,
        }
    except Exception as e:
        logger.warning(f"API error generating hard negative ({neg_type_key}): {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────


def generate_synthetic_pairs(
    data: List[dict],
    api_call,
    num_questions: int,
    max_tokens_pos: int = 512,
    max_tokens_neg: int = 256,
    negatives_per_question: int = 2,
    api_delay: float = 0.5,
) -> List[dict]:
    """
    For each sampled question, generate:
      - 1 high-quality positive explanation (y_chosen via CoT)
      - negatives_per_question hard negatives (y_rejected, random types)

    Returns list of DPO-format preference pairs:
      [{"prompt": ..., "chosen": ..., "rejected": ..., "chosen_score": 5.0,
        "rejected_score": 0.0, "score_gap": 5.0, "is_synthetic": True,
        "negative_type": ...}, ...]
    """
    sampled = random.sample(data, min(num_questions, len(data)))
    preference_pairs = []
    generated_count = 0
    failed_count = 0

    for i, item in enumerate(sampled):
        instruction = item.get("instruction", "").replace("</s>", "").strip()
        input_text = item.get("input", "").replace("</s>", "").strip()
        if not input_text:
            continue

        # Build the DPO prompt
        prompt_text = f"{instruction}\n\n{input_text}" if instruction else input_text

        # Generate high-quality positive
        positive = generate_positive_demo(
            item,
            api_call,
            max_tokens=max_tokens_pos,
            temperature=0.7,
        )
        if not positive:
            failed_count += 1
            continue

        # Generate hard negatives
        for _ in range(negatives_per_question):
            negative = generate_hard_negative(
                item,
                api_call,
                negative_type="random",
                max_tokens=max_tokens_neg,
                temperature=0.9,  # Higher temp for more diverse flaws
            )
            if negative:
                preference_pairs.append(
                    {
                        "prompt": prompt_text,
                        "chosen": positive,
                        "rejected": negative["text"],
                        "chosen_score": 5.0,  # Expert-level quality
                        "rejected_score": 0.0,  # Intentionally flawed
                        "score_gap": 5.0,
                        "is_synthetic": True,
                        "negative_type": negative["type"],
                        "negative_description": negative["description"],
                    }
                )
                generated_count += 1

        # Rate limiting
        if api_delay > 0:
            time.sleep(api_delay)

        if (i + 1) % 50 == 0:
            logger.info(
                f"Progress: {i+1}/{len(sampled)} questions processed, "
                f"{generated_count} pairs generated, {failed_count} failed."
            )

    logger.info(f"Synthetic data generation complete: {generated_count} pairs, " f"{failed_count} failed questions.")
    return preference_pairs


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic CoT positive + hard negative data for RLearner-LLM DPO."
    )
    # Data
    parser.add_argument("--data_path", required=True, help="Input PeerWise JSON (fields: instruction, input, output).")
    parser.add_argument("--output_path", required=True, help="Output path for synthetic preference pairs JSON.")
    parser.add_argument("--merge_with", default=None, help="If set, merge with an existing preference pairs JSON.")
    parser.add_argument(
        "--num_questions", type=int, default=500, help="Number of questions to generate synthetic data for."
    )
    parser.add_argument(
        "--negatives_per_question", type=int, default=2, help="Number of hard negatives per question (2 = 2 types)."
    )
    # API
    parser.add_argument(
        "--api_provider", choices=["openai", "anthropic"], default="openai", help="Which LLM API to use for generation."
    )
    parser.add_argument("--api_key", required=True, help="API key for the selected provider.")
    parser.add_argument(
        "--model", default=None, help="Model ID. Defaults: openai=gpt-4o, anthropic=claude-3-5-sonnet-20241022"
    )
    parser.add_argument(
        "--api_delay", type=float, default=0.5, help="Seconds to wait between API calls (rate limiting)."
    )
    parser.add_argument("--max_tokens_positive", type=int, default=512)
    parser.add_argument("--max_tokens_negative", type=int, default=256)
    # Options
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args()

    random.seed(args.seed)
    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)

    # Set default models
    if args.model is None:
        args.model = "gpt-4o" if args.api_provider == "openai" else "claude-3-5-sonnet-20241022"

    logger.info(f"Provider: {args.api_provider}, Model: {args.model}")

    # Build API caller
    api_call = build_api_caller(args.api_provider, args.api_key, args.model)

    # Load data
    with open(args.data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    logger.info(f"Loaded {len(raw_data)} questions from {args.data_path}")

    # Generate synthetic pairs
    logger.info(f"Generating synthetic data for {args.num_questions} questions...")
    synthetic_pairs = generate_synthetic_pairs(
        data=raw_data,
        api_call=api_call,
        num_questions=args.num_questions,
        max_tokens_pos=args.max_tokens_positive,
        max_tokens_neg=args.max_tokens_negative,
        negatives_per_question=args.negatives_per_question,
        api_delay=args.api_delay,
    )

    # Merge with existing preference data if requested
    if args.merge_with and os.path.isfile(args.merge_with):
        with open(args.merge_with, "r", encoding="utf-8") as f:
            existing_pairs = json.load(f)
        logger.info(f"Merging {len(synthetic_pairs)} synthetic pairs with " f"{len(existing_pairs)} existing pairs.")
        all_pairs = existing_pairs + synthetic_pairs
    else:
        all_pairs = synthetic_pairs

    # Shuffle to mix synthetic and organic pairs
    random.shuffle(all_pairs)

    # Save
    with open(args.output_path, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, ensure_ascii=False, indent=2)

    # Statistics
    n_synthetic = sum(1 for p in all_pairs if p.get("is_synthetic"))
    n_organic = len(all_pairs) - n_synthetic
    type_counts = {}
    for p in all_pairs:
        if p.get("is_synthetic"):
            t = p.get("negative_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

    logger.info("\nFinal dataset statistics:")
    logger.info(f"  Total pairs:     {len(all_pairs)}")
    logger.info(f"  Organic pairs:   {n_organic}")
    logger.info(f"  Synthetic pairs: {n_synthetic}")
    if type_counts:
        logger.info("  Hard negative breakdown:")
        for t, c in sorted(type_counts.items()):
            logger.info(f"    {t}: {c}")
    logger.info(f"\nSaved to: {args.output_path}")


if __name__ == "__main__":
    main()
