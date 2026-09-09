"""
RLearner-LLM Evaluation: Compare RL vs Baseline Models

Evaluates all models on the test set and produces a comparison table:
  - Baseline SFT (K=1, no RL): Original LLaMA-2 / Qwen3 fine-tuned
  - RL-DPO (K=1): DPO-trained model with LoRA
  - RL-PPO (K=1): PPO-trained model with LoRA
  - ILearner-LLM (K=5): Original K-round iterative refinement baseline

Metrics:
  - BLEU Score: n-gram overlap with ground-truth student explanations
  - BERTScore F1 (vs Student): Semantic similarity to student ground-truth explanation
  - BERTScore F1 (vs Answer): Answer-anchored — semantic similarity to the correct option
    text extracted from the question. Reference-free w.r.t. student explanations;
    measures whether the generated explanation covers the correct answer concept.
  - Answer Coverage Rate (ACR): Fraction of key terms in the correct option text that
    appear in the generated explanation. Fast lexical proxy for answer correctness.
  - Verifier Score: Quality rating from the trained Verifier model
  - Avg. Inference Time: Latency per explanation (1-shot vs K-round)

Usage:
    python rl_evaluation.py \
        --test_data_path ./Paul_new_data/Cardiff/Cardiff_vicuna_13b_finetuned_random_100.json \
        --verifier_path ./qiming_alpaca_7B_Cardiff_Sydney_merged_verifier_way_2 \
        --output_path ./rl_eval_results/comparison.json \
        --sft_model_path /data/shared/llama2/llama-2-13b-hf \
        --sft_lora_path ./rl_sft_llama2_13b_generator
"""

import argparse
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import torch
from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer

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

GENERATOR_INSTRUCTION = "As an explanation generation expert, can you generate the explanation for the given input?"


# ---------------------------------------------------------------------------
# Answer-grounded evaluation helpers
# ---------------------------------------------------------------------------


def extract_correct_option_text(input_text: str):
    """
    Parse the correct answer letter and option text from the question input.

    The input format contains:
        "Option A: <text> Option B: <text> ... The correct answer is Option X."

    Returns:
        (correct_letter, option_text) — e.g. ("C", "Long head of triceps brachii")
        Returns (None, None) if parsing fails.
    """
    m = re.search(r"The correct answer is Option ([A-Z])", input_text)
    if not m:
        return None, None
    letter = m.group(1)
    opt_pat = rf"Option {letter}:\s*(.+?)(?:\s+Option [A-Z]:|The correct answer|$)"
    opt_m = re.search(opt_pat, input_text, re.DOTALL)
    opt_text = opt_m.group(1).strip() if opt_m else None
    return letter, opt_text


def answer_coverage_rate(explanation: str, correct_option_text: str) -> float:
    """
    Answer Coverage Rate (ACR): lexical measure of whether the generated
    explanation mentions the key terms in the correct answer option.

    Computed as: |matched key terms| / |total key terms|
    where key terms are words of ≥4 characters in the correct option text.

    Returns 0.0 if inputs are missing or no key terms found.
    """
    if not explanation or not correct_option_text:
        return 0.0
    exp_lower = explanation.lower()
    key_terms = re.findall(r"\b\w{4,}\b", correct_option_text.lower())
    if not key_terms:
        return 0.0
    matched = sum(1 for t in key_terms if t in exp_lower)
    return matched / len(key_terms)


@dataclass
class ModelConfig:
    """Configuration for a single model to evaluate."""

    name: str
    model_path: str
    lora_adapter_path: Optional[str] = None
    is_legacy_llama: bool = False  # True for existing LLaMA-2 SFT models
    use_kround: bool = False  # True to simulate ILearner K-round iterative refinement
    k_rounds: int = 5  # Number of refinement rounds (if use_kround=True)


@dataclass
class EvalResult:
    model_name: str
    bleu_scores: List[float]
    bert_scores: List[float]  # vs student explanation (traditional)
    bert_scores_answer: List[float]  # vs correct option text (answer-anchored, new)
    acr_scores: List[float]  # Answer Coverage Rate (lexical, new)
    nli_scores: List[float]  # NLI entailment score (explanation → correct option)
    verifier_scores: List[float]
    inference_times: List[float]
    generated_explanations: List[str]  # saved for qualitative analysis

    @property
    def avg_bleu(self) -> float:
        return sum(self.bleu_scores) / len(self.bleu_scores) if self.bleu_scores else 0

    @property
    def avg_bert(self) -> float:
        return sum(self.bert_scores) / len(self.bert_scores) if self.bert_scores else 0

    @property
    def avg_bert_answer(self) -> float:
        return sum(self.bert_scores_answer) / len(self.bert_scores_answer) if self.bert_scores_answer else 0

    @property
    def avg_acr(self) -> float:
        return sum(self.acr_scores) / len(self.acr_scores) if self.acr_scores else 0

    @property
    def avg_nli(self) -> float:
        return sum(self.nli_scores) / len(self.nli_scores) if self.nli_scores else 0

    @property
    def avg_verifier(self) -> float:
        return sum(self.verifier_scores) / len(self.verifier_scores) if self.verifier_scores else 0

    @property
    def avg_time(self) -> float:
        return sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0

    def summary(self) -> Dict:
        return {
            "model": self.model_name,
            "avg_bleu": round(self.avg_bleu, 4),
            "avg_bert_score_f1": round(self.avg_bert, 4),
            "avg_bert_score_f1_answer_anchored": round(self.avg_bert_answer, 4),
            "avg_answer_coverage_rate": round(self.avg_acr, 4),
            "avg_nli_entailment": round(self.avg_nli, 4),
            "avg_verifier_score": round(self.avg_verifier, 4),
            "avg_inference_time_s": round(self.avg_time, 3),
        }


def load_nli_model(model_name: str, device: str = "cpu", cache_dir: str = "cache"):
    """
    Load a DeBERTa-based NLI model for entailment scoring.
    Default: cross-encoder/nli-deberta-v3-small (lightweight, ~90 MB).

    Returns (model, tokenizer, entailment_idx) where entailment_idx is the
    index of the ENTAILMENT class in the model's label space.
    """
    logger.info(f"Loading NLI model: {model_name} ...")
    # use_fast=False: older tokenizers lib (0.13.x) can't parse DeBERTa-v3 fast tokenizer
    nli_tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir, use_fast=False)
    nli_model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir).to(device)
    nli_model.eval()
    # Determine entailment label index from id2label
    id2label = nli_model.config.id2label or {}
    entailment_idx = next((k for k, v in id2label.items() if "entail" in v.lower()), 1)
    logger.info(f"  NLI model loaded. id2label={id2label}, entailment_idx={entailment_idx}")
    return nli_model, nli_tokenizer, entailment_idx


@torch.no_grad()
def compute_nli_scores(
    nli_model,
    nli_tokenizer,
    explanations: List[str],
    hypotheses: List[str],
    entailment_idx: int,
    device: str = "cpu",
    batch_size: int = 16,
) -> List[float]:
    """
    Compute NLI entailment probability for each (explanation, hypothesis) pair.
    Premise = generated explanation; Hypothesis = correct option text.
    Returns list of entailment probabilities in [0, 1].
    """
    scores = []
    for i in range(0, len(explanations), batch_size):
        batch_exp = explanations[i : i + batch_size]
        batch_hyp = hypotheses[i : i + batch_size]
        enc = nli_tokenizer(
            batch_exp,
            batch_hyp,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        logits = nli_model(**enc).logits  # (B, num_labels)
        probs = torch.softmax(logits, dim=-1)  # (B, num_labels)
        entail_probs = probs[:, entailment_idx].cpu().tolist()
        scores.extend(entail_probs)
    return scores


def load_model_and_tokenizer(config: ModelConfig, device: str = "cuda", cache_dir: str = "cache"):
    """Load model + tokenizer. Handles both legacy LLaMA-2 and modern chat models."""
    logger.info(f"Loading model: {config.name} from {config.model_path}")

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_path,
        cache_dir=cache_dir,
        trust_remote_code=True,
        padding_side="left",
        use_fast=False,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config.model_path,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        cache_dir=cache_dir,
        trust_remote_code=True,
    )

    if config.lora_adapter_path and os.path.isdir(config.lora_adapter_path):
        logger.info(f"  Loading LoRA adapter from {config.lora_adapter_path}")
        model = PeftModel.from_pretrained(model, config.lora_adapter_path)
        model = model.merge_and_unload()

    model = model.to(device)
    model.eval()
    logger.info(f"  Model loaded on {device}.")
    return model, tokenizer


def build_generator_prompt(
    instruction: str,
    input_text: str,
    tokenizer,
    is_legacy: bool = False,
    prev_score: Optional[float] = None,
    prev_explanation: Optional[str] = None,
) -> str:
    """Build the generation prompt. Handles both legacy and chat-template formats."""
    if is_legacy:
        # Original ILearner-LLM format for legacy LLaMA-2 models
        if prev_score is not None and prev_explanation:
            return (
                f"Instruction: Your last time verifier rating score for your explanation generation is "
                f"{prev_score} and the explanation you generated was {prev_explanation} "
                f"As a explanation generation expert, can you generate a better explanation "
                f"for the given input? \n\n{input_text}\n\n Output: "
            )
        return f"Instruction: {GENERATOR_INSTRUCTION}\n\nInput: {input_text}\n\n Output: "

    # Modern chat-template format (Qwen3/Llama-3)
    user_content = f"{instruction}\n\n{input_text}" if instruction else input_text
    if prev_score is not None and prev_explanation:
        user_content = (
            f"Your previous explanation scored {prev_score:.1f}/5.0 from the verifier. "
            f"Previous explanation: {prev_explanation}\n\n"
            f"Please generate a better explanation:\n\n{user_content}"
        )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            pass
    return f"Instruction: {instruction}\n\nInput: {input_text}\n\nOutput: "


@torch.no_grad()
def generate_explanation(
    model,
    tokenizer,
    prompt: str,
    device: str = "cuda",
    max_new_tokens: int = 512,
) -> str:
    """Generate a single explanation from the given prompt."""
    tokens = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).input_ids
    tokens = tokens.to(device)
    out = model.generate(
        tokens,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.5,
        top_k=50,
        top_p=1.0,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id,
        use_cache=True,
    )
    full_text = tokenizer.decode(out[0], skip_special_tokens=True)
    # Strip the prompt from the decoded text
    if full_text.startswith(prompt):
        response = full_text[len(prompt) :].strip()
    else:
        # For chat-template models
        parts = full_text.split("assistant")
        response = parts[-1].strip() if len(parts) > 1 else full_text.strip()
        # Further clean up any remaining tags
        response = re.sub(r"<\|.*?\|>", "", response).strip()
    return response


@torch.no_grad()
def get_verifier_score(
    verifier_model,
    verifier_tokenizer,
    question_input: str,
    explanation: str,
    device: str = "cuda",
) -> float:
    """Extract numerical score from the Verifier model."""
    merged = f"{question_input} Explanation: {explanation}"
    fulltext = f"Instruction: {VERIFIER_INSTRUCTION}\n\n" f"Input: {merged}\n\n" f"Output: "
    tokens = verifier_tokenizer(fulltext, return_tensors="pt", truncation=True, max_length=1024)
    verifier_device = next(verifier_model.parameters()).device
    tokens = tokens.input_ids.to(verifier_device)
    out = verifier_model.generate(
        tokens,
        max_new_tokens=16,
        do_sample=False,
        pad_token_id=verifier_tokenizer.eos_token_id,
    )
    text = verifier_tokenizer.decode(out[0], skip_special_tokens=True)
    match = re.search(r"Output:\s*(\d+(?:\.\d+)?)", text)
    if match:
        return min(float(match.group(1)), 5.0)
    match2 = re.search(r"(\d+(?:\.\d+)?)", text.split("Output:")[-1])
    if match2:
        return min(float(match2.group(1)), 5.0)
    return 0.0


def evaluate_model(
    config: ModelConfig,
    test_data: List[dict],
    verifier_model,
    verifier_tokenizer,
    device: str = "cuda",
    cache_dir: str = "cache",
    max_new_tokens: int = 512,
    nli_model=None,
    nli_tokenizer=None,
    nli_entailment_idx: int = 1,
    nli_device: str = "cpu",
) -> EvalResult:
    """Run full evaluation for one model on the test set."""
    model, tokenizer = load_model_and_tokenizer(config, device=device, cache_dir=cache_dir)
    result = EvalResult(
        model_name=config.name,
        bleu_scores=[],
        bert_scores=[],
        bert_scores_answer=[],
        acr_scores=[],
        nli_scores=[],
        verifier_scores=[],
        inference_times=[],
        generated_explanations=[],
    )

    smoother = SmoothingFunction().method1
    generated_explanations = []
    ground_truths_for_bert = []
    correct_option_texts = []  # for answer-anchored BERTScore

    for item in tqdm(test_data, desc=f"Evaluating {config.name}"):
        instruction = item.get("instruction", GENERATOR_INSTRUCTION).replace("</s>", "").strip()
        input_text = item.get("input", "").replace("</s>", "").strip()
        ground_truth = item.get("output", item.get("Explanation", "")).replace("</s>", "").strip()

        if not input_text or not ground_truth:
            continue

        # Extract correct answer option text for answer-grounded metrics
        _, correct_opt_text = extract_correct_option_text(input_text)

        start_time = time.time()

        if config.use_kround:
            # Simulate ILearner K-round iterative refinement (original paper baseline)
            explanation = ""
            score = 0.0
            for k in range(config.k_rounds):
                prompt = build_generator_prompt(
                    instruction,
                    input_text,
                    tokenizer,
                    is_legacy=config.is_legacy_llama,
                    prev_score=score if k > 0 else None,
                    prev_explanation=explanation if k > 0 else None,
                )
                explanation = generate_explanation(
                    model, tokenizer, prompt, device=device, max_new_tokens=max_new_tokens
                )
                if not explanation:
                    break
                # Score this round's explanation to use in next round's prompt
                score = get_verifier_score(verifier_model, verifier_tokenizer, input_text, explanation, device=device)
        else:
            # 1-shot generation (RL-trained or plain SFT)
            prompt = build_generator_prompt(
                instruction,
                input_text,
                tokenizer,
                is_legacy=config.is_legacy_llama,
            )
            explanation = generate_explanation(model, tokenizer, prompt, device=device, max_new_tokens=max_new_tokens)

        elapsed = time.time() - start_time

        if not explanation:
            continue

        generated_explanations.append(explanation)
        ground_truths_for_bert.append(ground_truth)
        correct_option_texts.append(correct_opt_text or "")

        # Compute BLEU (vs student explanation — traditional)
        bleu = sentence_bleu(
            [ground_truth.split()],
            explanation.split(),
            smoothing_function=smoother,
        )

        # Compute Answer Coverage Rate (ACR) — lexical, reference-free
        acr = answer_coverage_rate(explanation, correct_opt_text)

        # Compute Verifier Score (final 1-shot score for RL models)
        v_score = get_verifier_score(verifier_model, verifier_tokenizer, input_text, explanation, device=device)

        result.bleu_scores.append(bleu)
        result.acr_scores.append(acr)
        result.verifier_scores.append(v_score)
        result.inference_times.append(elapsed)
        result.generated_explanations.append(explanation)

    # Compute BERTScore in batch for all predictions
    if generated_explanations:
        from bert_score import score as bert_score_fn

        # Traditional: generated vs student explanation
        logger.info(f"  Computing BERTScore (vs student) for {config.name} ...")
        _, _, F1 = bert_score_fn(generated_explanations, ground_truths_for_bert, lang="en", verbose=False)
        result.bert_scores = F1.tolist()

        # New: generated vs correct option text (answer-anchored, reference-free)
        valid_pairs = [(g, c) for g, c in zip(generated_explanations, correct_option_texts) if c]
        if valid_pairs:
            logger.info(f"  Computing BERTScore (vs correct answer) for {config.name} ...")
            gen_valid, ans_valid = zip(*valid_pairs)
            _, _, F1_ans = bert_score_fn(list(gen_valid), list(ans_valid), lang="en", verbose=False)
            # Fill scores back (use 0.0 for examples without extractable option text)
            idx = 0
            for c in correct_option_texts:
                if c:
                    result.bert_scores_answer.append(F1_ans[idx].item())
                    idx += 1
                else:
                    result.bert_scores_answer.append(0.0)
        else:
            result.bert_scores_answer = [0.0] * len(generated_explanations)

        # NLI entailment: explanation → correct option text (answer-anchored)
        if nli_model is not None:
            valid_nli = [(g, c) for g, c in zip(generated_explanations, correct_option_texts) if c]
            if valid_nli:
                logger.info(f"  Computing NLI entailment scores for {config.name} ...")
                gen_nli, hyp_nli = zip(*valid_nli)
                nli_vals = compute_nli_scores(
                    nli_model,
                    nli_tokenizer,
                    list(gen_nli),
                    list(hyp_nli),
                    entailment_idx=nli_entailment_idx,
                    device=nli_device,
                )
                idx = 0
                for c in correct_option_texts:
                    if c:
                        result.nli_scores.append(nli_vals[idx])
                        idx += 1
                    else:
                        result.nli_scores.append(0.0)
            else:
                result.nli_scores = [0.0] * len(generated_explanations)

    # Clean up model from GPU memory
    del model
    torch.cuda.empty_cache()

    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate RLearner-LLM models.")
    parser.add_argument(
        "--test_data_path", required=True, help="Test set JSON file (fields: instruction, input, output/Explanation)."
    )
    parser.add_argument("--verifier_path", required=True, help="Path to trained Verifier model.")
    parser.add_argument(
        "--output_path", default="./rl_eval_results/comparison.json", help="Output path for evaluation results."
    )
    parser.add_argument("--device", default="cuda:0", help="Device for generator models.")
    parser.add_argument("--verifier_device", default="cuda:1", help="Device for verifier model.")
    parser.add_argument("--cache_dir", default="cache")
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument(
        "--nli_model",
        default="cross-encoder/nli-deberta-v3-small",
        help="NLI model for entailment scoring (default: cross-encoder/nli-deberta-v3-small).",
    )
    parser.add_argument("--nli_device", default="cpu", help="Device for NLI model (cpu or cuda:N). Defaults to cpu.")
    parser.add_argument(
        "--skip_nli", action="store_true", help="Skip NLI entailment metric (faster, no download needed)."
    )

    # Model specification arguments
    parser.add_argument("--sft_model_path", default=None, help="Path to baseline SFT model (K=1, no RL).")
    parser.add_argument("--sft_lora_path", default=None, help="LoRA adapter for SFT baseline (if applicable).")
    parser.add_argument("--dpo_model_path", default=None, help="Base model path for DPO-trained model.")
    parser.add_argument("--dpo_lora_path", default=None, help="LoRA adapter path from DPO training.")
    parser.add_argument(
        "--dpo_v2_model_path", default=None, help="Base model path for DPO-v2 model (improved preference data)."
    )
    parser.add_argument("--dpo_v2_lora_path", default=None, help="LoRA adapter path from DPO-v2 training.")
    parser.add_argument("--ppo_model_path", default=None, help="Base model path for PPO-trained model.")
    parser.add_argument("--ppo_lora_path", default=None, help="LoRA adapter path from PPO training.")
    parser.add_argument("--ilearner_model_path", default=None, help="Path to ILearner-LLM model for K-round baseline.")
    parser.add_argument("--ilearner_k", type=int, default=5, help="Number of refinement rounds for ILearner baseline.")
    parser.add_argument(
        "--ilearner_is_legacy", action="store_true", help="Use legacy alpaca-style prompt for ILearner model."
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)

    # ---------- Load test data ----------
    with open(args.test_data_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    logger.info(f"Loaded {len(test_data)} test examples from {args.test_data_path}")

    # ---------- Load Verifier ----------
    logger.info(f"Loading verifier from {args.verifier_path} ...")
    # use_fast=False: LlamaTokenizerFast has infinite recursion on older model configs
    verifier_tokenizer = AutoTokenizer.from_pretrained(
        args.verifier_path, cache_dir=args.cache_dir, trust_remote_code=True, use_fast=False
    )
    if verifier_tokenizer.pad_token is None:
        verifier_tokenizer.pad_token = verifier_tokenizer.eos_token
    # CPU does not support fp16 matmul; use fp32 for CPU verifier
    verifier_dtype = torch.float32 if str(args.verifier_device) == "cpu" else torch.float16
    verifier_model = AutoModelForCausalLM.from_pretrained(
        args.verifier_path,
        torch_dtype=verifier_dtype,
        low_cpu_mem_usage=True,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
    ).to(args.verifier_device)
    verifier_model.eval()
    logger.info("Verifier loaded.")

    # ---------- Build model configs ----------
    model_configs = []

    if args.sft_model_path:
        model_configs.append(
            ModelConfig(
                name="Baseline-SFT (K=1)",
                model_path=args.sft_model_path,
                lora_adapter_path=args.sft_lora_path,
                is_legacy_llama=False,
                use_kround=False,
            )
        )

    if args.dpo_model_path and args.dpo_lora_path:
        model_configs.append(
            ModelConfig(
                name="RL-DPO (K=1)",
                model_path=args.dpo_model_path,
                lora_adapter_path=args.dpo_lora_path,
                use_kround=False,
            )
        )

    if args.dpo_v2_model_path and args.dpo_v2_lora_path:
        model_configs.append(
            ModelConfig(
                name="RL-DPO-v2 (K=1)",
                model_path=args.dpo_v2_model_path,
                lora_adapter_path=args.dpo_v2_lora_path,
                use_kround=False,
            )
        )

    if args.ppo_model_path and args.ppo_lora_path:
        model_configs.append(
            ModelConfig(
                name="RL-PPO (K=1)",
                model_path=args.ppo_model_path,
                lora_adapter_path=args.ppo_lora_path,
                use_kround=False,
            )
        )

    if args.ilearner_model_path:
        model_configs.append(
            ModelConfig(
                name=f"ILearner-LLM (K={args.ilearner_k})",
                model_path=args.ilearner_model_path,
                is_legacy_llama=args.ilearner_is_legacy,
                use_kround=True,
                k_rounds=args.ilearner_k,
            )
        )

    if not model_configs:
        logger.error("No models specified. Use --sft_model_path, --dpo_model_path, etc.")
        return

    # ---------- Load NLI model ----------
    nli_model, nli_tokenizer, nli_entailment_idx = None, None, 1
    if not args.skip_nli:
        try:
            nli_model, nli_tokenizer, nli_entailment_idx = load_nli_model(
                args.nli_model, device=args.nli_device, cache_dir=args.cache_dir
            )
        except Exception as e:
            logger.warning(f"NLI model load failed ({e}). Skipping NLI metric.")

    # ---------- Evaluate each model ----------
    all_results = []
    for config in model_configs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating: {config.name}")
        logger.info(f"{'='*60}")

        result = evaluate_model(
            config=config,
            test_data=test_data,
            verifier_model=verifier_model,
            verifier_tokenizer=verifier_tokenizer,
            device=args.device,
            cache_dir=args.cache_dir,
            max_new_tokens=args.max_new_tokens,
            nli_model=nli_model,
            nli_tokenizer=nli_tokenizer,
            nli_entailment_idx=nli_entailment_idx,
            nli_device=args.nli_device,
        )
        all_results.append(result)

        summary = result.summary()
        logger.info(f"\nResults for {config.name}:")
        for k, v in summary.items():
            logger.info(f"  {k}: {v}")

    # ---------- Summary Table ----------
    logger.info("\n" + "=" * 100)
    logger.info("FINAL COMPARISON TABLE")
    logger.info("=" * 100)
    header = (
        f"{'Model':<28} {'BLEU':>8} {'BERT(Stu)':>10} {'BERT(Ans)':>10} "
        f"{'ACR':>8} {'NLI':>8} {'Verifier':>10} {'Time(s)':>9}"
    )
    logger.info(header)
    logger.info("-" * 110)
    for result in all_results:
        s = result.summary()
        logger.info(
            f"{s['model']:<28} {s['avg_bleu']:>8.4f} {s['avg_bert_score_f1']:>10.4f} "
            f"{s['avg_bert_score_f1_answer_anchored']:>10.4f} "
            f"{s['avg_answer_coverage_rate']:>8.4f} "
            f"{s['avg_nli_entailment']:>8.4f} "
            f"{s['avg_verifier_score']:>10.4f} {s['avg_inference_time_s']:>9.3f}"
        )
    logger.info("")
    logger.info("Column guide:")
    logger.info("  BERT(Stu) = BERTScore vs student explanation (traditional reference-based)")
    logger.info("  BERT(Ans) = BERTScore vs correct option text (answer-anchored, reference-free)")
    logger.info("  ACR       = Answer Coverage Rate — fraction of correct option keywords in explanation")
    logger.info("  NLI       = DeBERTa entailment probability: explanation -> correct option text")

    # ---------- Save results ----------
    output_data = {
        "test_data_path": args.test_data_path,
        "num_test_examples": len(test_data),
        "results": [r.summary() for r in all_results],
        "detailed_results": [
            {
                "model": r.model_name,
                "bleu_scores": r.bleu_scores,
                "bert_scores_vs_student": r.bert_scores,
                "bert_scores_vs_answer": r.bert_scores_answer,
                "acr_scores": r.acr_scores,
                "nli_entailment_scores": r.nli_scores,
                "verifier_scores": r.verifier_scores,
                "inference_times": r.inference_times,
                "generated_explanations": r.generated_explanations,
            }
            for r in all_results
        ],
    }
    with open(args.output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    logger.info(f"\nFull results saved to {args.output_path}")


if __name__ == "__main__":
    main()
