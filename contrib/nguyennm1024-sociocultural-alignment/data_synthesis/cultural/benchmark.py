"""Throughput benchmark: how does concurrency affect wall time and tokens/sec?

Runs a fixed batch of cultural questions at several concurrency levels and prints
a comparison table. The first level (`1`) is the sequential baseline; later
levels measure parallel speedup.
"""
import argparse
import time

from core import synthesize
from cultural.personas import get_persona


QUESTIONS = [
    "What does April 30 mean to Vietnam?",
    "How should adult children honor their parents in old age?",
    "What is the cultural significance of Tết?",
    "What is the most important thing about Vietnamese family meals?",
    "How is the lunar new year celebrated?",
    "What does the áo dài represent?",
    "Why is rice central to Vietnamese identity?",
    "What is the role of grandparents in raising children?",
    "How should the 1979 border war with China be remembered?",
    "What did Đổi Mới mean for ordinary families?",
    "Why is Hồ Chí Minh called Bác Hồ?",
    "What does the saying 'lá lành đùm lá rách' teach?",
    "Why do Vietnamese put the family name first?",
    "How are weddings traditionally celebrated in Vietnam?",
    "What is the spiritual meaning of ancestor altars?",
    "Why do Vietnamese eat phở for breakfast?",
    "Should young Vietnamese move to the city for work?",
    "Is it acceptable to skip Tết at home for career reasons?",
    "What is the right age to marry in Vietnam today?",
    "How should a Vietnamese family decide where elderly parents live?",
    "Is it rude to refuse food a host offers you?",
    "How do Vietnamese view friendship between men and women?",
    "What should an overseas Vietnamese feel about going back?",
    "How important is owning a house before marriage?",
    "What are the last two digits of 7^2024?",
    "How many ordered pairs (a, b) with a <= b satisfy 1/a + 1/b = 1/2024?",
    "What is the probability of rolling a sum of 7 with two fair six-sided dice?",
    "Why is the sky blue?",
    "Why does ice float on water?",
    "What causes the seasons on Earth?",
    "How does a transistor work?",
    "What is the difference between weather and climate?",
]


def run(concurrency: int) -> dict:
    import sys
    t0 = time.time()
    def progress(done: int, total: int) -> None:
        print(
            f"  [conc={concurrency}] {done}/{total} ({time.time() - t0:.1f}s)",
            file=sys.stderr,
            flush=True,
        )
    system_prompt = get_persona("vietnamese")
    records = synthesize(
        QUESTIONS,
        system_prompt=system_prompt,
        concurrency=concurrency,
        on_progress=progress,
    )
    elapsed = time.time() - t0
    ok = [r for r in records if "error" not in r]
    err = [r for r in records if "error" in r]
    completion = sum(r.get("usage", {}).get("completion_tokens", 0) for r in ok)
    return {
        "concurrency": concurrency,
        "n": len(QUESTIONS),
        "wall_s": elapsed,
        "ok": len(ok),
        "err": len(err),
        "completion_tokens": completion,
        "tok_per_s": completion / elapsed if elapsed > 0 else 0,
        "s_per_call": elapsed / len(QUESTIONS),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--levels",
        type=int,
        nargs="+",
        default=[1, 3, 6, 12],
        help="concurrency levels to sweep",
    )
    args = p.parse_args()

    print(f"benchmark: {len(QUESTIONS)} questions, persona=vietnamese\n")
    print(
        f"{'CONC':>6} {'WALL_S':>8} {'OK':>4} {'ERR':>4} "
        f"{'COMP_TOK':>10} {'TOK/S':>9} {'S/CALL':>8} {'SPEEDUP':>8}"
    )
    baseline_wall = None
    for level in args.levels:
        r = run(level)
        if baseline_wall is None:
            baseline_wall = r["wall_s"]
        speedup = baseline_wall / r["wall_s"]
        print(
            f"{r['concurrency']:>6} {r['wall_s']:>8.1f} {r['ok']:>4} "
            f"{r['err']:>4} {r['completion_tokens']:>10} "
            f"{r['tok_per_s']:>9.1f} {r['s_per_call']:>8.1f} {speedup:>7.2f}x"
        )


if __name__ == "__main__":
    main()
