import os
import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
)
from peft import PeftModel

_HF_CACHE = os.environ.get("HF_HOME", os.path.join(os.getcwd(), ".cache/huggingface"))
os.environ["HF_HOME"] = _HF_CACHE
os.environ["HF_DATASETS_CACHE"] = os.path.join(_HF_CACHE, "datasets")


def get_log_probs(logits, labels):
    # logits: [batch, seq, vocab]
    # labels: [batch, seq]
    # Shift so that tokens < n predict n
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = labels[..., 1:].contiguous()

    # Flatten
    loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
    # loss = -log(p)
    # logic: CrossEntropy = -log_prob(target)
    # So log_prob = -CrossEntropy
    # We want log_prob of the *completed* tokens only (where label != -100)

    # Reshape for loss
    shift_logits = shift_logits.view(-1, shift_logits.size(-1))
    shift_labels = shift_labels.view(-1)

    # Compute element-wise loss
    loss = loss_fct(shift_logits, shift_labels)
    # loss shape: [batch * (seq-1)]

    # Reshape back
    loss = loss.view(logits.size(0), -1)

    # Mask out ignored tokens
    mask = (shift_labels != -100).float().view(logits.size(0), -1)

    # Sum log probs over sequence
    # Note: loss is -log_prob. So sum(loss) = -sum(log_prob) = -log_prob(seq)
    # log_prob(seq) = -sum(loss * mask)
    log_probs = -(loss * mask).sum(dim=1)

    return log_probs


class DPOTrainer(Trainer):
    def __init__(self, ref_model, beta=0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ref_model = ref_model
        self.beta = beta
        self.ref_model.eval()

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        # inputs contains concatenated batch of [chosen, rejected] or similar?
        # Standard DPO usually processes chosen and rejected in same batch or separate.
        # Here we assume inputs has 'chosen_input_ids', 'rejected_input_ids', etc.
        # But Trainer expects 'input_ids', 'labels'.
        # We need to customize data collation to pass 'chosen_input_ids' etc.
        # OR we pass concatenated [chosen... rejected...] and split them inside.

        # Let's assume input_ids contains [chosen, rejected] concatenated along batch dim
        # i.e. batch_size = 2N. Even indices = chosen, Odd = rejected.

        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]
        labels = inputs["labels"]

        # Forward Policy
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

        # Forward Reference (no grad)
        with torch.no_grad():
            ref_outputs = self.ref_model(input_ids=input_ids, attention_mask=attention_mask)
            ref_logits = ref_outputs.logits

        # Calc log probs
        log_probs = get_log_probs(logits, labels)
        ref_log_probs = get_log_probs(ref_logits, labels)

        # Split into chosen/rejected
        # Assuming batch is ordered [chosen1, rejected1, chosen2, rejected2...]
        # Actually usually it's [chosen1, chosen2...] [rejected1, rejected2...]
        # Let's verify DataCollator
        # We will implement collation to interleave or stack.
        # Let's assume we stack: first half chosen, second half rejected.
        batch_size = input_ids.shape[0] // 2

        chosen_log_probs = log_probs[:batch_size]
        rejected_log_probs = log_probs[batch_size:]

        chosen_ref_log_probs = ref_log_probs[:batch_size]
        rejected_ref_log_probs = ref_log_probs[batch_size:]

        # DPO Loss
        pi_logratios = chosen_log_probs - rejected_log_probs
        ref_logratios = chosen_ref_log_probs - rejected_ref_log_probs

        logits_diff = pi_logratios - ref_logratios
        losses = -F.logsigmoid(self.beta * logits_diff)

        loss = losses.mean()

        return (loss, outputs) if return_outputs else loss


def encode_dpo_pair(sample, tokenizer, max_length=512):
    # Construct Chosen text
    prompt = sample["prompt"]
    chosen_text = sample["chosen"]
    rejected_text = sample["rejected"]

    def tokenize_seq(response_text):
        full_text = f"{prompt} {response_text}"
        enc = tokenizer(full_text, truncation=True, max_length=max_length, padding="max_length")
        input_ids = enc["input_ids"]
        attention_mask = enc["attention_mask"]
        labels = input_ids[:]

        # Mask prompt in labels
        prompt_enc = tokenizer(prompt, truncation=True, max_length=max_length)
        prompt_len = len(prompt_enc["input_ids"])
        # Handle if prompt occupies full length (unlikely)

        for i in range(min(prompt_len, len(labels))):
            labels[i] = -100
        # Also mask padding
        for i in range(len(labels)):
            if input_ids[i] == tokenizer.pad_token_id:
                labels[i] = -100

        return input_ids, attention_mask, labels

    c_ids, c_mask, c_labels = tokenize_seq(chosen_text)
    r_ids, r_mask, r_labels = tokenize_seq(rejected_text)

    return {
        "chosen_input_ids": c_ids,
        "chosen_attention_mask": c_mask,
        "chosen_labels": c_labels,
        "rejected_input_ids": r_ids,
        "rejected_attention_mask": r_mask,
        "rejected_labels": r_labels,
    }


def collate_dpo(batch):
    # Stack chosen and rejected
    input_ids = []
    attention_mask = []
    labels = []

    for item in batch:
        input_ids.append(item["chosen_input_ids"])
        attention_mask.append(item["chosen_attention_mask"])
        labels.append(item["chosen_labels"])

    for item in batch:
        input_ids.append(item["rejected_input_ids"])
        attention_mask.append(item["rejected_attention_mask"])
        labels.append(item["rejected_labels"])

    return {
        "input_ids": torch.tensor(input_ids),
        "attention_mask": torch.tensor(attention_mask),
        "labels": torch.tensor(labels),
    }


def train_dpo():
    model_name = "Qwen/Qwen2-1.5B"
    stage1_model_dir = "./trained_models/qwen_stage1_gen"
    output_dir = "./trained_models/qwen_stage2_dpo"

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(stage1_model_dir)
    tokenizer.pad_token = tokenizer.eos_token

    print("Loading dataset...")
    data_files = {"train": "data/train_dpo.jsonl"}
    ds = load_dataset("json", data_files=data_files)["train"]

    print("Encoding dataset...")
    ds = ds.map(lambda x: encode_dpo_pair(x, tokenizer), batched=False)

    # Load Models
    print("Loading Policy Model...")
    base_model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
    # Load Adapter
    policy_model = PeftModel.from_pretrained(base_model, stage1_model_dir, is_trainable=True)

    print("Loading Reference Model...")
    ref_base_model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
    ref_model = PeftModel.from_pretrained(ref_base_model, stage1_model_dir)
    ref_model.eval()

    # Training Args
    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=1,  # Effective batch 2 (1 chosen + 1 rejected)
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=1e-6,  # Low LR for DPO
        bf16=False,
        fp16=True,
        logging_steps=10,
        remove_unused_columns=False,
    )

    trainer = DPOTrainer(
        ref_model=ref_model,
        model=policy_model,
        args=args,
        train_dataset=ds,
        data_collator=collate_dpo,
        tokenizer=tokenizer,
    )

    print("Starting Training...")
    trainer.train()

    policy_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Saved to {output_dir}")


if __name__ == "__main__":
    train_dpo()
