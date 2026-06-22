"""Shared SFT data-generation primitives.

Used by sibling packages (cultural, rehearsal, ...) that wrap these primitives
with domain-specific personas, prompts, and topic taxonomies.
"""
from .client import DEFAULT_MODEL, make_client
from .jsonl_store import append_records, read_records
from .load_topics import get_scenario, iter_scenarios, load_spec
from .question_gen import generate_questions, generate_questions_for_scenario
from .synthesize import synthesize, synthesize_one

__all__ = [
    "DEFAULT_MODEL",
    "make_client",
    "append_records",
    "read_records",
    "load_spec",
    "iter_scenarios",
    "get_scenario",
    "generate_questions",
    "generate_questions_for_scenario",
    "synthesize",
    "synthesize_one",
]
