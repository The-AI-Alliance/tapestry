"""
RLearner-LLM Step 2: Build DPO Preference Dataset

For each question in the PeerWise dataset:
  1. Use the SFT generator to sample N explanations at varying temperatures.
  2. Score each explanation with the trained Verifier model.
  3. Pair the highest-scoring explanation (chosen) against the lowest-scoring (rejected).
  4. Optionally inject synthetic hard negatives (reversed logic, high-score gibberish).

Output format (compatible with rl_train_dpo.py):
  [{"prompt": "...", "chosen": "...", "rejected": "...", "chosen_score": x, "rejected_score": y}, ...]

Usage:
    python rl_build_preference_data.py \
        --generator_path ./rl_sft_qwen3_14b_generator \
        --verifier_path ./llama_2_13B_merged_all_evaluator \
        --data_path ./Paul_new_data/Merged_Sydney_Cardiff_Law_Medical_Y1_Y2/generator_merged_avg_3_lenexp_10.json \
        --output_path ./rl_preference_data/preference_pairs.json \
        --num_samples 6 \
        --min_score_gap 0.5
"""

import argparse
import json
import logging
import os
import re
import random
from typing import List, Optional

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert educator specializing in generating high-quality explanations "
    "for exam questions. Your explanations should be clear, accurate, educational, "
    "and written in a style similar to how knowledgeable students explain answers."
)

VERIFIER_INSTRUCTION = (
    "As a question rating verifier expert, can you generate the question rating score " "for the given input?"
)

# Hard negative templates for synthetic data augmentation
HARD_NEGATIVE_TEMPLATES = [
    # Reversed logic: attribute cause to wrong option
    "The incorrect option is actually correct because {wrong_reason}. Therefore the answer must be wrong.",
    # Gibberish high-confidence
    "This question is straightforward. The answer is undeniably correct based on fundamental principles, "
    "which clearly demonstrate the inherent validity of the chosen response in all applicable contexts.",
    # Off-topic
    "While this is an interesting topic, it's worth noting that many related concepts exist in this field. "
    "Various factors contribute to understanding this area of study comprehensively.",
]


class VerifierScorer:
    """Wrapper around the trained LLaMA-2 Verifier to extract numerical scores."""

    def __init__(self, model_path: str, device: str = "cuda", cache_dir: str = "cache"):
        logger.info(f"Loading verifier from {model_path} ...")
        # use_fast=False avoids LlamaTokenizerFast infinite recursion on older
        # model configs that have a circular bos_token_id → unk_token_id lookup.
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, cache_dir=cache_dir, trust_remote_code=True, use_fast=False
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            cache_dir=cache_dir,
            trust_remote_code=True,
        ).to(device)
        self.model.eval()
        self.device = device
        logger.info("Verifier loaded.")

    @torch.no_grad()
    def score(self, question_input: str, explanation: str) -> float:
        """
        Score an explanation given the question context.
        Returns a float in [0, 5]. Returns -1.0 if parsing fails.
        """
        merged = f"{question_input} Explanation: {explanation}"
        fulltext = f"Instruction: {VERIFIER_INSTRUCTION}\n\n" f"Input: {merged}\n\n" f"Output: "
        tokens = self.tokenizer(fulltext, return_tensors="pt").input_ids.to(self.device)
        generated = self.model.generate(
            tokens,
            max_new_tokens=32,
            use_cache=True,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=False,
            temperature=1.0,
        )
        generated_text = self.tokenizer.decode(generated[0], skip_special_tokens=True)

        # Extract score from "Output: X.X" pattern
        match = re.search(r"Output:\s*(\d+(?:\.\d+)?)", generated_text)
        if match:
            return float(match.group(1))
        # Fallback: look for any float in the generated part after "Output:"
        after_output = generated_text.split("Output:")[-1]
        match = re.search(r"(\d+(?:\.\d+)?)", after_output)
        if match:
            return float(match.group(1))
        logger.warning(f"Could not parse score from: {generated_text[:100]}")
        return -1.0


class ExplanationGenerator:
    """Wraps the SFT generator (with optional LoRA adapter) for multi-sample generation."""

    def __init__(
        self,
        model_path: str,
        lora_adapter_path: Optional[str] = None,
        device: str = "cuda",
        cache_dir: str = "cache",
    ):
        logger.info(f"Loading generator from {model_path} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, cache_dir=cache_dir, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            cache_dir=cache_dir,
            trust_remote_code=True,
        ).to(device)

        if lora_adapter_path and os.path.isdir(lora_adapter_path):
            logger.info(f"Loading LoRA adapter from {lora_adapter_path} ...")
            self.model = PeftModel.from_pretrained(self.model, lora_adapter_path)
            self.model = self.model.merge_and_unload()  # Merge for faster inference

        self.model.eval()
        self.device = device
        logger.info("Generator loaded.")

    def _build_prompt(self, instruction: str, input_text: str) -> str:
        """Build Alpaca-format inference prompt (no response text, ends with ### Response:)."""
        return build_prompt_for_dpo(instruction, input_text)

    @torch.no_grad()
    def generate_samples(
        self,
        instruction: str,
        input_text: str,
        num_samples: int = 6,
        temperatures: Optional[List[float]] = None,
        max_new_tokens: int = 512,
    ) -> List[str]:
        """
        Generate `num_samples` diverse explanations by cycling through different temperatures.
        Returns list of generated explanation strings.
        """
        if temperatures is None:
            # Spread across conservative to exploratory temperatures
            temperatures = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3]

        prompt = self._build_prompt(instruction, input_text)
        tokens = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

        samples = []
        for i in range(num_samples):
            temp = temperatures[i % len(temperatures)]
            output_ids = self.model.generate(
                tokens,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temp,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
            )
            full_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            # Strip the prompt from the output
            if full_text.startswith(prompt):
                response = full_text[len(prompt) :].strip()
            else:
                # For chat-template models, extract after last assistant turn
                parts = full_text.split("assistant")
                response = parts[-1].strip() if len(parts) > 1 else full_text.strip()

            if response:
                samples.append(response)

        return samples


def build_prompt_for_dpo(instruction: str, input_text: str) -> str:
    """
    Build Alpaca-format prompt for DPO dataset.

    Ends with '### Response:\\n' so TRL 0.7.1 DPOTrainer can identify the
    boundary between prompt tokens and response tokens.
    Must match the ALPACA_TEMPLATE used in rl_train_sft.py (without the output).
    """
    return (
        "Below is an instruction that describes a task, paired with an input that "
        "provides further context. Write a response that appropriately completes the request.\n\n"
        f"### Instruction:\n{instruction}\n\n"
        f"### Input:\n{input_text}\n\n"
        "### Response:\n"
    )


def add_synthetic_hard_negatives(
    preference_pairs: List[dict],
    hard_negative_ratio: float = 0.2,
) -> List[dict]:
    """
    Augment the dataset with synthetic hard negatives.
    Selects ~hard_negative_ratio of the pairs and replaces the rejected
    explanation with a template-based hard negative (confusing, off-topic, etc.).
    """
    augmented = list(preference_pairs)
    num_to_augment = int(len(preference_pairs) * hard_negative_ratio)
    indices = random.sample(range(len(preference_pairs)), min(num_to_augment, len(preference_pairs)))

    for idx in indices:
        template = random.choice(HARD_NEGATIVE_TEMPLATES)
        hard_neg = template.format(wrong_reason="the logic is inverted in this context")
        new_pair = dict(preference_pairs[idx])
        new_pair["rejected"] = hard_neg
        new_pair["rejected_score"] = 0.0
        new_pair["is_synthetic"] = True
        augmented.append(new_pair)

    logger.info(f"Added {len(indices)} synthetic hard negatives. Total pairs: {len(augmented)}")
    return augmented


def main():
    parser = argparse.ArgumentParser(description="Build DPO preference dataset for RLearner-LLM.")
    parser.add_argument(
        "--generator_path", required=True, help="Path to the SFT generator model (local dir or HF model ID)."
    )
    parser.add_argument(
        "--lora_adapter_path", default=None, help="Optional LoRA adapter path to load on top of the generator."
    )
    parser.add_argument(
        "--verifier_path",
        required=True,
        help="Path to the trained verifier model (e.g., llama_2_13B_merged_all_evaluator).",
    )
    parser.add_argument(
        "--data_path", required=True, help="Input PeerWise JSON file (fields: instruction, input, output)."
    )
    parser.add_argument("--output_path", required=True, help="Output path for preference JSON dataset.")
    parser.add_argument("--num_samples", type=int, default=6, help="Number of explanations to generate per question.")
    parser.add_argument("--max_new_tokens", type=int, default=512, help="Max tokens for each generated explanation.")
    parser.add_argument(
        "--min_score_gap",
        type=float,
        default=0.3,
        help="Minimum score gap between chosen and rejected. Pairs below this are skipped.",
    )
    parser.add_argument(
        "--add_hard_negatives", action="store_true", help="Add synthetic hard negative examples to the dataset."
    )
    parser.add_argument(
        "--hard_negative_ratio", type=float, default=0.2, help="Fraction of pairs to augment with hard negatives."
    )
    parser.add_argument("--generator_device", default="cuda:0", help="Device for generator model.")
    parser.add_argument(
        "--verifier_device", default="cuda:1", help="Device for verifier model (separate GPU recommended)."
    )
    parser.add_argument("--cache_dir", default="cache", help="Model cache directory.")
    parser.add_argument(
        "--max_questions", type=int, default=None, help="Limit processing to N questions (for testing)."
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)

    # Load models
    generator = ExplanationGenerator(
        model_path=args.generator_path,
        lora_adapter_path=args.lora_adapter_path,
        device=args.generator_device,
        cache_dir=args.cache_dir,
    )
    verifier = VerifierScorer(
        model_path=args.verifier_path,
        device=args.verifier_device,
        cache_dir=args.cache_dir,
    )

    # Load data
    with open(args.data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if args.max_questions:
        raw_data = raw_data[: args.max_questions]
        logger.info(f"Processing {len(raw_data)} questions (limited by --max_questions).")
    else:
        logger.info(f"Processing {len(raw_data)} questions.")

    preference_pairs = []
    skipped_no_gap = 0
    skipped_empty = 0

    for item in tqdm(raw_data, desc="Building preference pairs"):
        instruction = item.get("instruction", "").replace("</s>", "").strip()
        input_text = item.get("input", "").replace("</s>", "").strip()
        ground_truth = item.get("output", item.get("Explanation", "")).replace("</s>", "").strip()

        if not input_text:
            skipped_empty += 1
            continue

        # Generate N candidate explanations
        candidates = generator.generate_samples(
            instruction=instruction,
            input_text=input_text,
            num_samples=args.num_samples,
            max_new_tokens=args.max_new_tokens,
        )

        # If we have the ground truth and it's non-empty, include it as a candidate
        if ground_truth:
            candidates.append(ground_truth)

        if len(candidates) < 2:
            skipped_empty += 1
            continue

        # Score all candidates
        scored = []
        for cand in candidates:
            if cand.strip():
                s = verifier.score(input_text, cand)
                if s >= 0:  # -1 means parsing failed
                    scored.append((cand, s))

        if len(scored) < 2:
            skipped_empty += 1
            continue

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        best_explanation, best_score = scored[0]
        worst_explanation, worst_score = scored[-1]

        score_gap = best_score - worst_score
        if score_gap < args.min_score_gap:
            skipped_no_gap += 1
            continue

        prompt_text = build_prompt_for_dpo(instruction, input_text)
        preference_pairs.append(
            {
                "prompt": prompt_text,
                "chosen": best_explanation,
                "rejected": worst_explanation,
                "chosen_score": best_score,
                "rejected_score": worst_score,
                "score_gap": score_gap,
                "is_synthetic": False,
            }
        )

    logger.info(
        f"Built {len(preference_pairs)} preference pairs. "
        f"Skipped: {skipped_no_gap} (score gap too small), {skipped_empty} (empty/parse error)."
    )

    # Optionally inject synthetic hard negatives
    if args.add_hard_negatives and preference_pairs:
        preference_pairs = add_synthetic_hard_negatives(preference_pairs, hard_negative_ratio=args.hard_negative_ratio)

    # Save
    with open(args.output_path, "w", encoding="utf-8") as f:
        json.dump(preference_pairs, f, ensure_ascii=False, indent=2)
    logger.info(f"Preference dataset saved to {args.output_path}")

    # Print statistics
    if preference_pairs:
        scores_gap = [p["score_gap"] for p in preference_pairs if not p.get("is_synthetic")]
        avg_gap = sum(scores_gap) / len(scores_gap) if scores_gap else 0
        logger.info(f"Average score gap: {avg_gap:.3f}")
        logger.info(f"Score gap range: [{min(scores_gap):.2f}, {max(scores_gap):.2f}]")


if __name__ == "__main__":
    main()
