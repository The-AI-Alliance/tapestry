"""Payload construction for the WAN weight-transfer spike.

NumPy-only on purpose: the spike measures transport, not training, and a
torch-free app keeps remote node setup to `pip install flwr numpy`.

float16 stands in for bfloat16 (NumPy has no native bf16); the wire payload
is byte-identical in size.
"""

from __future__ import annotations

import numpy as np


def validate_positive_int(name: str, value: int) -> int:
    """Return ``value`` when positive, otherwise raise a clear config error."""
    if value <= 0:
        raise ValueError(f"{name} must be positive; got {value}")
    return value


def make_ndarrays(payload_params: int, tensor_params: int, seed: int = 7) -> list[np.ndarray]:
    """Random fp16 tensors totalling ``payload_params`` parameters.

    Random (not zeros) so any transparent compression on the path cannot
    flatter the measurement.
    """
    validate_positive_int("payload_params", payload_params)
    validate_positive_int("tensor_params", tensor_params)

    rng = np.random.default_rng(seed)
    out: list[np.ndarray] = []
    remaining = payload_params
    while remaining > 0:
        n = min(tensor_params, remaining)
        out.append(rng.standard_normal(n, dtype=np.float32).astype(np.float16))
        remaining -= n
    return out


def total_bytes(arrays: list[np.ndarray]) -> int:
    return sum(a.nbytes for a in arrays)
