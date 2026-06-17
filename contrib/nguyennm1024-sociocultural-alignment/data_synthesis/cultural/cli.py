"""CLI for cultural-alignment SFT batch synthesis.

Reads questions from a file or stdin and synthesizes answers with the
Vietnamese persona.

Usage (from data_synthesis/):
    python -m cultural.cli questions.txt > out.jsonl
    python -m cultural.cli - --no-gloss < questions.txt > out.jsonl
"""
import argparse
import json
import sys

from core import synthesize
from cultural.personas import get_persona


def main() -> None:
    p = argparse.ArgumentParser(description="Synthesize culturally-aligned answers.")
    p.add_argument(
        "input",
        help="path to a file with one question per line, or '-' for stdin",
    )
    p.add_argument("--persona", default="vietnamese")
    p.add_argument("--model", default="kimi-k2.6")
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument(
        "--no-gloss",
        dest="gloss_native_terms",
        action="store_false",
        help="Disable inline gloss of native-language terms on first use.",
    )
    args = p.parse_args()

    if args.input == "-":
        questions = [line.strip() for line in sys.stdin if line.strip()]
    else:
        with open(args.input) as f:
            questions = [line.strip() for line in f if line.strip()]

    def progress(done: int, total: int) -> None:
        print(f"[{done}/{total}]", file=sys.stderr, flush=True)

    system_prompt = get_persona(args.persona, gloss_native_terms=args.gloss_native_terms)
    records = synthesize(
        questions,
        system_prompt=system_prompt,
        model=args.model,
        concurrency=args.concurrency,
        max_tokens=args.max_tokens,
        max_retries=args.max_retries,
        on_progress=progress,
    )
    for r in records:
        r["persona"] = args.persona
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
