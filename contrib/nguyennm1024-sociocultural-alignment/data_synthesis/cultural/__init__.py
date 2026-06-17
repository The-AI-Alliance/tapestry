"""Cultural-alignment SFT data generation.

Wraps the shared `core/` primitives with:
- Vietnamese persona (with optional native-term gloss instruction)
- Culture-specific QUESTION_GEN_PROMPT (diversity requirements,
  sub-population coverage, anti-stereotype guards)
- Pipeline runner that ties topic loading → question gen → answer synthesis

Mirror this layout in `rehearsal/` for capability-preservation data.
"""
from .personas import GLOSS_NATIVE_TERMS_INSTRUCTION, PERSONAS, get_persona
from .prompts import QUESTION_GEN_PROMPT

__all__ = [
    "PERSONAS",
    "get_persona",
    "GLOSS_NATIVE_TERMS_INSTRUCTION",
    "QUESTION_GEN_PROMPT",
]
