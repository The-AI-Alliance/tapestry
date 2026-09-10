# Socio-Cultural Alignment: LoRA + Consortium Learning + Inglehart-Welzel Evaluation

A staging contribution exploring **sovereign cultural alignment** of a small open model
(Llama-3.2-3B-Instruct) toward a target culture (Vietnamese), and measuring it rigorously.
The parts are meant to be reusable beyond this case: a data-synthesis methodology, a LoRA
training pipeline, a **consortium-learning** step that fuses specialized members, and a
cultural-alignment **evaluation** harness.

> **Status: Speculative** (preliminary / experimental). Staging-area work, not a supported package.

## Why (mission fit)

Cultural alignment is the kind of capability a community is best placed to build: it needs
local knowledge, native data, and culturally grounded evaluation. This stages a full path,
make the data then train, fuse, and measure, so others can reuse, critique, and extend the
individual pieces.

## What's here

| Directory | Role |
|---|---|
| `data_synthesis/` | Generate the cultural + capability-rehearsal training corpora. The teacher client is OpenAI-compatible and model-agnostic (we used Kimi-K2.6 and DeepSeek-V4-Pro). `core/` engine, `cultural/` corpus, `rehearsal/` corpus. |
| `training/` | LoRA SFT pipeline: `prepare_data` -> `pack_data` -> `train_rehearsal` -> `merge_ckpt`. |
| `consortium/` | **Consortium learning**: fuse independently-trained member models into one. `base.py` defines the `ConsortiumMethod` contract; `soup/` is method v1 (weight-space averaging). |
| `evaluation/` | Capability (full MMLU) + cultural alignment via the **Inglehart-Welzel cultural map** (a bit-exact Python port of Tao et al.'s projection). `api.py` is the shared entrypoint. |
| `topics/` | The cultural-coverage design and the rehearsal-data guide. |

## Approach

1. **Synthesize** a Vietnamese-cultural corpus plus a capability-rehearsal corpus (to limit forgetting).
2. **Train** member models with LoRA SFT (e.g. a culturally-aligned member and a rehearsal member).
3. **Fuse** members with a consortium method (model soup v1: `out = sum(w_i * member_i)`).
4. **Evaluate** the result on two independent axes: general capability (MMLU) and cultural
   position on the Inglehart-Welzel map (distance to the target country plus per-item shifts).

## Preliminary results

For a 50/50 soup of the culturally-aligned and rehearsal members:

![Inglehart-Welzel cultural map: base model vs Tapestry-Vietnamese](figures/iw_cultural_map.png)

*The base model (black diamond) sits in the secular, self-expression (Western) region;
Tapestry-Vietnamese (green diamond) moves toward Vietnam (red star), cutting the Euclidean
distance from 2.46 to 1.35. Tao et al.'s GPT models are shown for reference.*

- **Cultural map**: Euclidean distance to Vietnam falls from **2.46 to 1.35** (about -45%) under
  the Tao et al. projection. The shift concentrates in the survival/self-expression items; the
  strongly secular items (importance of God, attitudes toward homosexuality) move least.
- **Capability**: full-set MMLU (n=14,042, zero-shot) goes **63.2% to 62.4%**, a 0.8-point change
  that is not statistically significant (McNemar p ~ 0.07).

Treat these as directional early evidence, not benchmark claims. The IW map distance is
sensitive for out-of-distribution projections, so read the per-item table alongside it.

## How to run

The contribution provides top-level `make` targets (via `.targets.mk`), direct Python scripts, and containerized execution. Ensure your environment has developer dependencies installed (`uv sync --extra dev` or `make one-time-setup`).

### 1. Using Make Targets (from repository root)

Run the automated checks and verification targets directly from the repo root:

```bash
# Run contribution unit tests
make sociocultural-tests

# Verify the Inglehart-Welzel mathematical projection against ground truth
make sociocultural-iw-verify

# Run both tests and projection verification
make sociocultural-all

# Generate the Inglehart-Welzel 2D cultural map figures
make sociocultural-iw-plot
```

### 2. Environment Variables & Directory Overrides

Paths are resolved dynamically relative to module locations by default, but can be overridden via environment variables if custom data/results locations are needed:

* `TAPESTRY_IW_DIR`: Location of the IW evaluation scripts, questions, and projection JSON (`evaluation/iw`).
* `TAPESTRY_ANS_DIR`: Destination directory for raw model answers and scored responses (`results/iw/answers`).
* `TAPESTRY_FIG_DIR`: Output directory for generated cultural map plots (`results/iw/figures`).
* `TAPESTRY_MMLU_DIR`: Destination directory for zero-shot MMLU evaluations (`results/mmlu`).

### 3. Step-by-Step Evaluation Pipeline

To evaluate a new model on the Inglehart-Welzel cultural map:

1. **Elicitation**: Query the model with the 10 World Values Survey items (`evaluation/iw/Prompts_Questions.csv`):
   ```bash
   # Using vLLM on a GPU instance:
   python evaluation/iw/iw_gen_tao.py <model_path_or_id> <tag>
   ```
   Alternatively, query the prompts via Ollama or Hugging Face and write raw answers to `answers_<tag>_nat.json`.

2. **Scoring**: Parse raw text responses into 10-dimensional standardized score vectors:
   ```bash
   python evaluation/iw/iw_score.py
   ```

3. **Projection**: Standardize scores with human means/SDs and project onto the 2D cultural map:
   ```bash
   python evaluation/iw/iw_project.py
   ```

4. **Visualization**: Plot the model's position relative to global cultural zones:
   ```bash
   python evaluation/iw/plot_iw10.py
   ```

### 4. Consortium Model Fusion (Model Soup)

To fuse two fine-tuned model checkpoints (e.g., culturally-aligned + rehearsal) into a combined model:

```bash
python consortium/soup/model_soup.py <model_a_path> <model_b_path> <output_dir> <alpha>
```

Or via Python:
```python
from consortium import Member
from consortium.soup import Soup

Soup().combine(
    [Member("path/to/cultural_model", weight=0.5), Member("path/to/rehearsal_model", weight=0.5)],
    "path/to/fused_model",
)
```

### 5. Running in Docker

For full GPU training with heavy dependencies (`vLLM`, `torch`, `transformers`):
```bash
docker build -t tapestry-sociocultural -f training/Dockerfile .
docker run --gpus all -v $(pwd):/workspace -it tapestry-sociocultural /bin/bash
```

## Status & limitations

- **Staging / preliminary**, no stability guarantees.
- **Path-portability**: The evaluation and projection scripts now resolve paths dynamically relative to their location on disk, with environment variable overrides (`TAPESTRY_*_DIR`) for flexible local, VM, and cloud runner execution (#251).
- **Not included** (see `DATA.md`): the registration-walled WVS/EVS survey microdata (pointer only), model weights (derived from Llama, not redistributed here), and the raw generated corpora (regenerate via `data_synthesis/`).

## Data & licensing

- Data pointers, sourcing, and clearance: see `DATA.md`.
- License: code under Apache-2.0, docs under CC-BY-4.0, data/specs under CDLA-Permissive-2.0
  (Project Tapestry defaults). See `LICENSE`.

## Citations

- Inglehart-Welzel cultural map and the model-projection method: Tao et al. (2024); World
  Values Survey / European Values Study (registration required; see `DATA.md`).
- MMLU: Hendrycks et al. (2021).
- Teacher models used for synthesis: Kimi-K2.6 (Moonshot) and DeepSeek-V4-Pro; the synthesis
  client is OpenAI-compatible and model-agnostic.
