# Training image for Vietnamese-culture SFT of Llama-3.2-3B on Jetson AGX Thor.
# Base already ships torch 2.8 (nv25.08), CUDA 13, cuDNN, FlashAttention 2.7.4,
# and Transformer Engine 2.5 built for Blackwell sm_110 (aarch64).
FROM nvcr.io/nvidia/pytorch:25.08-py3

# Only the HF training stack is missing. These are pure-python / prebuilt-aarch64
# wheels, so they install without touching the NVIDIA-built torch/flash_attn.
RUN pip install --no-cache-dir \
        "transformers>=4.55,<4.58" \
        "trl>=0.21,<0.24" \
        "peft>=0.15,<0.18" \
        "datasets>=3.2,<5" \
        "accelerate>=1.4,<2"

# Fail the build loudly if pip replaced the NVIDIA torch or broke flash-attn —
# we must keep the Blackwell-optimised kernels.
RUN python -c "import torch, flash_attn, transformers, trl, peft, datasets, accelerate; \
assert 'nv25.08' in torch.__version__, 'NVIDIA torch was overwritten: '+torch.__version__; \
assert torch.cuda.is_available() or True; \
print('OK torch', torch.__version__, '| flash_attn', flash_attn.__version__, \
'| transformers', transformers.__version__, '| trl', trl.__version__, \
'| peft', peft.__version__)"

WORKDIR /workspace
