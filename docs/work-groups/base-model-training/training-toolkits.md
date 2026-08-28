# Model Training Toolkits

| Field       | Value           |
| :---------- | :-------------- |
| Status      | Proposed        |
| Confidence  | Med. High (4/5) |
| Created     | July 08, 2026   |
| Last Update | July 31, 2026   |

This is an analysis of PyTorch and alternatives for LLM _training_ (not inference). It was prepared by [Dean Wampler](mailto:dwampler@thealliance.ai), July 8, 2026, using [IBM Bob](https://bob.ibm.com/), supplemented by additional web searches. (The underlying LLMs used by Bob are not revealed to the user.)

The session used two prompts with the responses captured below (lightly edited). The document ends with a postscript written by Dean.

# PyTorch and Alternative Toolkits

The session started with the following prompt:

> PyTorch is the most popular tool suite for AI model training. What are the alternatives and how do they compare to PyTorch, pros and cons?

Here is the response:

---

PyTorch is dominant in research and increasingly in production, but several strong alternatives exist across different use cases.

## 1. TensorFlow / Keras

**Maker:** Google

| Pros | Cons |
|------|------|
| Mature ecosystem, production-ready (`TF Serving`, `TFLite`, `TF.js`) | More verbose than PyTorch; steeper learning curve |
| Strong mobile/edge deployment story | Eager mode (default since TF2) still lags PyTorch in flexibility |
| `tf.data` pipeline is excellent for large datasets | Community momentum has shifted toward PyTorch |
| Keras 3 now supports JAX and PyTorch backends | TF1-era legacy code creates ecosystem confusion |

**Best for:** Production deployment pipelines, mobile/edge, Google Cloud TPU workloads.

---

## 2. JAX

**Maker:** Google DeepMind

| Pros | Cons |
|------|------|
| Composable function transformations (`grad`, `jit`, `vmap`, `pmap`) | No native neural net layer API — requires Flax, Haiku, or Equinox |
| Excellent for research-level math/custom gradient work | Stateless/functional paradigm has a steep learning curve |
| First-class TPU support; XLA compilation for speed | Smaller ecosystem; fewer pre-trained models |
| `vmap` makes vectorization trivial | Debugging compiled XLA code is harder |

**Best for:** Research requiring custom optimizers, differentiable physics, reinforcement learning, and Google TPU clusters.

---

## 3. MXNet

**Maker:** Apache / AWS

| Pros | Cons |
|------|------|
| Strong distributed training support | Effectively in maintenance mode; little active development |
| Gluon API is fairly Pythonic | Community has migrated away (largely to PyTorch) |
| Good AWS SageMaker integration | Documentation and tutorials are sparse |

**Best for:** Legacy AWS workloads. Not recommended for new projects.

---

## 4. PaddlePaddle

**Maker:** Baidu

| Pros | Cons |
|------|------|
| Strong Chinese-language NLP model ecosystem | Smaller Western community and ecosystem |
| Good industrial/production tooling from Baidu's scale | English documentation lags |
| Dynamic computation graph, similar feel to PyTorch | Less adoption outside China |

**Best for:** Chinese-language AI applications, Baidu Cloud deployments.

---

## 5. MLX

**Maker:** Apple

| Pros | Cons |
|------|------|
| Designed specifically for Apple Silicon (M1/M2/M3/M4) | macOS/Apple Silicon only — not portable |
| Unified memory model; no CPU↔GPU copy overhead | Very young ecosystem (released 2023) |
| NumPy-like API; easy to pick up | No multi-GPU or TPU support |
| Fast for on-device inference and fine-tuning | |

**Best for:** Mac-native model development, on-device fine-tuning, prototyping on Apple hardware.

---

## 6. Triton (OpenAI)

**Maker:** OpenAI

| Pros | Cons |
|------|------|
| Write custom GPU kernels in Python-like syntax | Not a full training framework — sits below PyTorch |
| Used by PyTorch itself (via `torch.compile`) | Requires GPU programming knowledge |
| Can dramatically accelerate custom ops | |

**Best for:** Kernel authors optimizing GPU ops, not end-to-end training.

---

## 7. Tinygrad

**Maker:** George Hotz / tinygrad team

| Pros | Cons |
|------|------|
| Extremely minimal codebase (~1000 LOC core) | Not production-ready |
| Educational; great for understanding autograd | Limited operator coverage |
| Supports multiple backends (CUDA, Metal, OpenCL) | Tiny ecosystem |

**Best for:** Learning how autograd works, hobby projects.

---

## Summary Matrix

| Framework | Best Use Case | Production Readiness | TPU Support | Edge/Mobile |
|-----------|--------------|---------------------|-------------|-------------|
| **PyTorch** | Research → Production | ★★★★★ | ✅ (via XLA) | Limited |
| **TensorFlow/Keras** | Production + Mobile | ★★★★★ | ✅ | ✅ (TFLite) |
| **JAX** | Research math/custom grad | ★★★★☆ | ✅ (native) | ❌ |
| **MLX** | Apple Silicon | ★★★☆☆ | ❌ | ✅ (macOS) |
| **MXNet** | Legacy AWS | ★★☆☆☆ | ❌ | ❌ |
| **PaddlePaddle** | Chinese NLP/Baidu | ★★★☆☆ | ❌ | Limited |

---

**Bottom line:** PyTorch wins on ecosystem breadth and researcher adoption. **JAX** is the strongest challenger for cutting-edge research. **TensorFlow/Keras** remains the best choice for production serving pipelines and mobile deployment. **MLX** is compelling specifically for Mac-native development.


# AI Training Frameworks — Hardware Accelerator Support Comparison

Then, Bob was asked to explore support for different accelerator hardware in more depth. In practice, Tapestry mostly cares about NVIDIA and AMD GPU support in the near term.

The following prompt was used:

> Redo the previous analysis, this time discussing how well each tool supports different hardware accelerators: NVIDIA, AMD GPU, Google TPU, Amazon Trainium, Apple Silicon, and any other widely-used accelerator hardware.

Here is the response (lightly edited):

---

A comparison of major AI training frameworks across the most widely-used accelerator hardware platforms.

## Hardware Accelerator Legend

| Symbol | Meaning |
|--------|---------|
| ✅ Native | First-class support, maintained by the framework or hardware vendor |
| ⚠️ Partial | Works but with caveats, limited ops, or requires extra setup |
| 🔧 Community | Third-party / community-maintained backend |
| ❌ None | No meaningful support |

---

## Framework × Hardware Matrix

| Framework | NVIDIA (CUDA) | AMD (ROCm) | Google TPU | AWS Trainium | Apple Silicon | Intel GPU/Gaudi | Qualcomm AI |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **PyTorch** | ✅ Native | ✅ Native | ✅ via XLA | ✅ via `torch-neuronx` | ⚠️ MPS backend | ✅ via `intel-extension-for-pytorch` / Gaudi | 🔧 QNN SDK |
| **TensorFlow/Keras** | ✅ Native | ⚠️ ROCm build | ✅ Native (TPU was TF's home) | ⚠️ Limited | ⚠️ Metal plugin | ⚠️ oneAPI plugin | ❌ |
| **JAX** | ✅ Native | ⚠️ ROCm/HIP (experimental) | ✅ Native (XLA) | ❌ | ⚠️ via `jax-metal` (experimental) | 🔧 OpenXLA | ❌ |
| **MLX** | ❌ | ❌ | ❌ | ❌ | ✅ Native (unified memory) | ❌ | ❌ |
| **MXNet** | ✅ Native | 🔧 Community | ❌ | ❌ | ❌ | ❌ | ❌ |
| **PaddlePaddle** | ✅ Native | ✅ ROCm (Baidu-maintained) | ❌ | ❌ | ❌ | ⚠️ XPU plugin | ❌ |

---

## Per-Framework Deep Dive

### 1. PyTorch

**NVIDIA (CUDA):** The gold standard. CUDA support is PyTorch's primary development target. All ops, `torch.compile`, FlashAttention, Triton kernels, and distributed training (`NCCL`) work natively.

**AMD (ROCm):** Officially supported since PyTorch 1.8. ROCm mirrors CUDA semantics via HIP. Most ops work; some custom CUDA kernels require porting. Performance gap vs. CUDA has narrowed significantly (MI300X competes with H100).

**Google TPU:** Supported via `torch_xla`. Requires XLA compilation, which changes the execution model (lazy tensors). Not transparent — code often needs TPU-aware rewrites. Google maintains this actively.

**AWS Trainium:** Supported via `torch-neuronx` (AWS Neuron SDK). Requires neuron-specific compilation step (`torch_neuronx.trace()`). Growing model coverage but still behind CUDA breadth.

**Apple Silicon:** `mps` backend available since PyTorch 1.12. Covers common training ops but has gaps (some ops fall back to CPU). Fine-tuning small-to-medium models works well; large model training is limited by unified memory bandwidth.

**Intel GPU / Gaudi:** `intel-extension-for-pytorch` (IPEX) adds Intel GPU (Arc, Data Center GPU Max) and Gaudi (HPU) support. Gaudi 2/3 are serious competitors for LLM training at scale. Intel maintains this actively.

---

### 2. TensorFlow / Keras

**NVIDIA (CUDA):** Fully supported; historically TF's primary target. cuDNN integration is mature.

**AMD (ROCm):** ROCm builds of TF exist but are less polished than PyTorch's ROCm path. TensorFlow's declining community momentum means ROCm support may lag further.

**Google TPU:** TensorFlow was the original TPU framework; support is deep and native. `tf.distribute.TPUStrategy` is the most battle-tested TPU training API. However, Google's own research has shifted to JAX.

**AWS Trainium:** Limited; AWS Neuron SDK has partial TF support but PyTorch is the primary focus.

**Apple Silicon:** A `tensorflow-metal` plugin from Apple exists, offering GPU-accelerated training on M-series chips. More mature than PyTorch's MPS for some workloads, but still has op gaps.

**Intel GPU:** `intel-extension-for-tensorflow` (ITEX) provides XPU support. Less mature than IPEX for PyTorch.

---

### 3. JAX

**NVIDIA (CUDA):** Excellent. JAX compiles via XLA to PTX; performance is competitive with PyTorch for well-structured workloads. `pmap`/`shard_map` make multi-GPU trivially correct.

**AMD (ROCm):** Experimental. XLA has a ROCm backend (via HIP), but it is not production-validated. Expect missing ops and performance variability.

**Google TPU:** JAX's strongest hardware story. XLA was designed with TPUs in mind; `jax.devices('tpu')` is fully supported. DeepMind, Google Brain, and most Google-internal LLM training runs use JAX + TPU.

**AWS Trainium:** No support. XLA does not target Neuron hardware.

**Apple Silicon:** `jax-metal` plugin (community/Apple-backed) is experimental as of 2024. Not recommended for production; covers a subset of ops.

**Intel Gaudi / GPU:** OpenXLA initiative aims to add backends, but Intel Gaudi support for JAX is not yet production-ready.

---

### 4. MLX

**Apple Silicon only.** MLX is purpose-built for Apple's unified memory architecture. The framework exploits the fact that CPU and GPU share the same physical memory pool, eliminating transfer overhead. Supports M1 through M4 (including Pro/Max/Ultra variants with larger memory).

All other hardware: ❌ Not supported, not planned.

**Verdict:** Exceptional for on-device fine-tuning and inference on Mac. A non-starter for any other hardware.

---

### 5. MXNet

**NVIDIA (CUDA):** Supported but aging. Works for standard training; no support for modern CUDA features like FlashAttention.

**Everything else:** Minimal to no support. MXNet is in maintenance mode and should not be chosen for new projects on any hardware.

---

### 6. PaddlePaddle

**NVIDIA (CUDA):** Full support; Baidu runs large-scale training on NVIDIA clusters internally.

**AMD (ROCm):** Baidu actively maintains ROCm support — one of the better non-PyTorch ROCm stories, driven by China's need to work around NVIDIA export restrictions.

**Intel XPU:** Plugin support via `paddle-device-xpu`; covers Intel Data Center GPU Max.

**Custom Kunlun (XPU):** Baidu's proprietary Kunlun AI accelerator is supported — unique to PaddlePaddle. Relevant only in Chinese data center contexts.

---

## Special-Purpose Accelerators

| Accelerator | Best-supported Framework | Notes |
|---|---|---|
| **Google TPU v4/v5** | JAX, TensorFlow | JAX is now Google's primary internal framework |
| **AWS Trainium / Inferentia** | PyTorch (`torch-neuronx`) | TF partial; JAX none |
| **Apple M-series** | MLX | PyTorch MPS and TF Metal are usable alternatives |
| **Intel Gaudi 2/3** | PyTorch (IPEX) | Strong LLM training story; growing ecosystem |
| **Graphcore IPU** | PyTorch (`poptorch`) | Unique BSP execution model; PyTorch is primary |
| **Cerebras WSE** | PyTorch | Wafer-scale engine; custom PyTorch integration |
| **SambaNova SN40L** | PyTorch | Reconfigurable dataflow; PyTorch frontend |
| **Baidu Kunlun XPU** | PaddlePaddle | Only relevant within Baidu's ecosystem |

---

## Key Takeaways

- **NVIDIA CUDA** is well-supported by every major framework — it remains the path of least resistance.
- **AMD ROCm** is most mature with **PyTorch**; PaddlePaddle is a distant second; JAX/TF are experimental.
- **Google TPU** is best served by **JAX** (Google's current primary target) or TensorFlow (legacy, but deep support).
- **AWS Trainium** is effectively **PyTorch-only** via the Neuron SDK.
- **Apple Silicon** is best served by **MLX** for native work, with PyTorch MPS as a solid fallback.
- **Intel Gaudi** is an emerging serious option — **PyTorch + IPEX** is the production-ready path.
- For **hardware portability** across the widest range of accelerators, **PyTorch** is the clear winner.

# Postscript by Dean Wampler

For the most part, there are no surprises in these responses. PyTorch has the largest, most diverse ecosystem. It is the de facto industry standard for LLM training and it provides the broadest hardware flexibility. Frameworks in other languages, like [Julia Flux](https://fluxml.ai/Flux.jl/stable/) and [Rust Burn](https://burn.dev/), were not included by Bob in its analysis, although Burn is [under consideration](https://github.com/The-AI-Alliance/tapestry/issues/9) for Tapestry. It offers very fast performance and broad hardware support.

Some of the responses raise questions. The first response includes this in its summary,

> **TensorFlow/Keras** remains the best choice for production serving pipelines and mobile deployment.

This is a questionable assertion, at least for production pipelines, as most such inference deployments use PyTorch libraries along with serving engines like vLLM.

