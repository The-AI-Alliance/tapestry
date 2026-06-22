#!/usr/bin/env python
"""Model soup: weight-average fine-tunes of the SAME base. The v1 consortium method.

CLI (backward-compatible 2-member form):
    python model_soup.py <modelA> <modelB> <out_dir> <alpha>
    result = alpha * A + (1 - alpha) * B   (alpha = weight on A)

Members must share architecture/keys (they are LoRA-merges of the same base).
CPU is fine -- this is just weight averaging, no GPU needed.
"""
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def average_weights(model_paths, weights, out_dir):
    """Weighted average of N same-architecture models into out_dir.

    `weights` need not sum to 1 (they are normalized). Returns out_dir.
    """
    assert model_paths and len(model_paths) == len(weights), "need one weight per member"
    total = float(sum(weights))
    ws = [w / total for w in weights]
    base = AutoModelForCausalLM.from_pretrained(model_paths[0], dtype=torch.bfloat16)
    acc = {k: v.float() * ws[0] for k, v in base.state_dict().items()}
    for path, w in zip(model_paths[1:], ws[1:]):
        sd = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16).state_dict()
        assert set(sd) == set(acc), "key mismatch -- members must share architecture"
        for k in acc:
            acc[k] += sd[k].float() * w
    base.load_state_dict({k: v.to(torch.bfloat16) for k, v in acc.items()})
    base.save_pretrained(out_dir)
    AutoTokenizer.from_pretrained(model_paths[0]).save_pretrained(out_dir)
    print(f"SOUP_DONE -> {out_dir}", flush=True)
    return out_dir


if __name__ == "__main__":
    mA, mB, out, alpha = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    print(f"[soup] {alpha:.2f}*A + {1 - alpha:.2f}*B  A={mA} B={mB}", flush=True)
    average_weights([mA, mB], [alpha, 1.0 - alpha], out)
