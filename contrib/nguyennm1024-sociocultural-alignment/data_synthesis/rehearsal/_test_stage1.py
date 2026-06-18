"""Stage 1 smoke tests — exercises spec.py, format.py, data/sources.py,
data/decontam.py, and cli.py without touching HuggingFace.

Run from `data_synthesis/`:
    python -m rehearsal._test_stage1
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


PASS = "✓"
FAIL = "✗"
_failures: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}" + (f": {detail}" if detail else ""))
        _failures.append(label)


# ---------------------------------------------------------------------------
# spec.py
# ---------------------------------------------------------------------------

def test_spec() -> None:
    print("\n[spec.py]")
    from rehearsal.spec import (
        load_spec, iter_categories, iter_sources, get_category, get_source,
        iter_decontam_testset_descriptions,
    )
    spec = load_spec()
    check("load_spec returns dict", isinstance(spec, dict))
    check("has 'categories' key", "categories" in spec)

    cats = list(iter_categories())
    check("13 categories", len(cats) == 13, f"got {len(cats)}")
    check("category volumes sum to 40K",
          sum(c.volume for c in cats) == 40000,
          f"got {sum(c.volume for c in cats)}")

    srcs = list(iter_sources())
    check("45 sources", len(srcs) == 45, f"got {len(srcs)}")
    check("source volumes sum to 40K",
          sum(s.volume for s in srcs) == 40000)

    names = [s.name for s in srcs]
    check("source names unique", len(names) == len(set(names)))

    cat = get_category("mmlu_shaped")
    check("get_category('mmlu_shaped') hits", cat is not None and cat.volume == 7000)

    s = get_source("Synthetic_via_Qwen")
    check("get_source('Synthetic_via_Qwen') hits",
          s is not None and s.category == "mmlu_shaped" and s.volume == 3500)

    check("get_source on missing returns None", get_source("nonexistent_source") is None)

    ts = iter_decontam_testset_descriptions()
    check("decontam testset descriptions present", len(ts) > 15)


# ---------------------------------------------------------------------------
# format.py
# ---------------------------------------------------------------------------

def test_format() -> None:
    print("\n[format.py]")
    from rehearsal.format import (
        wrap_assistant, unwrap_assistant, build_messages, make_record_id,
        make_question_id,
        write_jsonl, read_jsonl, append_jsonl, existing_ids,
    )

    # Wrap / unwrap roundtrip
    s = wrap_assistant("think a bit", "B")
    check("wrap shape", s == "<THINK>think a bit</THINK><ANSWER>B</ANSWER>")
    r, a = unwrap_assistant(s)
    check("unwrap reasoning", r == "think a bit")
    check("unwrap answer", a == "B")

    # Empty THINK
    s2 = wrap_assistant("", "B")
    r2, a2 = unwrap_assistant(s2)
    check("empty THINK roundtrip", r2 == "" and a2 == "B")

    # Multi-line reasoning + answer
    s3 = wrap_assistant("step 1\nstep 2\n42", "42")
    r3, a3 = unwrap_assistant(s3)
    check("multi-line reasoning preserved", r3 == "step 1\nstep 2\n42")
    check("multi-line answer extracted", a3 == "42")

    # Unwrap with no THINK
    r4, a4 = unwrap_assistant("<ANSWER>B</ANSWER>")
    check("unwrap returns None for missing THINK", r4 is None and a4 == "B")

    # Unwrap with garbage
    r5, a5 = unwrap_assistant("no tags here")
    check("unwrap returns None for unrelated text", r5 is None and a5 is None)

    # build_messages
    m = build_messages("Q?", "reason", "B")
    check("build_messages user+assistant", len(m) == 2 and m[0]["role"] == "user"
          and m[1]["role"] == "assistant")

    m2 = build_messages("Q?", "reason", "B", system="sys")
    check("build_messages with system", len(m2) == 3 and m2[0]["role"] == "system")

    # make_record_id determinism
    id1 = make_record_id("mmlu_shaped", "MMLU_auxiliary_training", 42)
    id2 = make_record_id("mmlu_shaped", "MMLU_auxiliary_training", 42)
    check("record IDs deterministic", id1 == id2)
    check("record ID starts rhsl_", id1.startswith("rhsl_"))
    check("record ID has 6-digit index", id1.endswith("000042"))
    id_other = make_record_id("gsm8k_shaped_math", "GSM8K_train_variants", 1234)
    check("different inputs -> different IDs", id1 != id_other)

    # QuestionRecord IDs are prefixed q_
    qid = make_question_id("mmlu_shaped", "MMLU_auxiliary_training", 42)
    check("question ID starts q_", qid.startswith("q_"))
    check("question ID matches record_id with q_ prefix",
          qid == "q_" + id1)

    # JSONL I/O + resumability
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "out.jsonl"
        write_jsonl(p, [{"id": "a", "x": 1}, {"id": "b", "x": 2}])
        append_jsonl(p, {"id": "c", "x": 3})
        recs = list(read_jsonl(p))
        check("jsonl write+append+read", recs == [
            {"id": "a", "x": 1}, {"id": "b", "x": 2}, {"id": "c", "x": 3}
        ])
        ids = existing_ids(p)
        check("existing_ids matches", ids == {"a", "b", "c"})
        ids_missing = existing_ids(Path(d) / "missing.jsonl")
        check("existing_ids on missing file returns empty set",
              ids_missing == set())

        # Unicode roundtrip
        unicode_path = Path(d) / "unicode.jsonl"
        write_jsonl(unicode_path, [{"id": "u", "text": "Tết — chúc mừng năm mới"}])
        unicode_back = list(read_jsonl(unicode_path))
        check("unicode preserved",
              unicode_back[0]["text"] == "Tết — chúc mừng năm mới")


# ---------------------------------------------------------------------------
# data/sources.py
# ---------------------------------------------------------------------------

def test_sources() -> None:
    print("\n[data/sources.py]")
    from rehearsal.data.sources import SOURCES, SOURCES_BY_NAME, DECONTAM_TESTSETS, DECONTAM_BY_NAME
    from rehearsal.spec import iter_sources

    check("SOURCES count = 45", len(SOURCES) == 45)
    check("SOURCES_BY_NAME count = 45", len(SOURCES_BY_NAME) == 45)
    check("DECONTAM_TESTSETS count = 20", len(DECONTAM_TESTSETS) == 20)

    # Every spec source has a registry entry
    spec_names = {s.name for s in iter_sources()}
    reg_names = set(SOURCES_BY_NAME.keys())
    missing = spec_names - reg_names
    extra = reg_names - spec_names
    check("every spec source has registry entry", not missing,
          f"missing: {missing}")
    check("no extra registry entries beyond spec", not extra,
          f"extra: {extra}")

    # IFEval correction is in place
    ifeval = SOURCES_BY_NAME["IFEval_style_training_prompts"]
    check("IFEval_style_training_prompts points to argilla, not google/IFEval",
          ifeval.hf_path == "argilla/ifeval-like-data",
          f"got {ifeval.hf_path}")

    # google/IFEval lives ONLY in decontam
    google_ifeval = DECONTAM_BY_NAME.get("IFEval")
    check("google/IFEval registered as decontam target",
          google_ifeval is not None and google_ifeval.hf_path == "google/IFEval")

    # Origin distribution
    public_count = sum(1 for s in SOURCES if s.origin == "public")
    gen_count = sum(1 for s in SOURCES if s.origin == "generated")
    aug_count = sum(1 for s in SOURCES if s.origin == "augmented")
    prog_count = sum(1 for s in SOURCES if s.origin == "programmatic")
    check("origin counts (public/generated/augmented/programmatic) sum to 45",
          public_count + gen_count + aug_count + prog_count == 45,
          f"got {public_count}/{gen_count}/{aug_count}/{prog_count}")

    # Generated sources have no hf_path
    for s in SOURCES:
        if s.origin == "generated" and s.hf_path is not None:
            check(f"generated source {s.name} should have no hf_path", False)
            break
    else:
        check("all generated sources have hf_path=None", True)

    # Public sources have hf_path
    for s in SOURCES:
        if s.origin == "public" and s.hf_path is None:
            check(f"public source {s.name} missing hf_path", False)
            break
    else:
        check("all public sources have hf_path set", True)


# ---------------------------------------------------------------------------
# data/decontam.py
# ---------------------------------------------------------------------------

def test_decontam() -> None:
    print("\n[data/decontam.py]")
    from rehearsal.data.decontam import (
        normalize, ngram_hash, iter_ngrams, DecontamIndex, Contaminator,
        sha1, NGRAM_N,
    )

    # Normalization
    check("normalize lowercases", normalize("HELLO") == "hello")
    check("normalize strips punctuation",
          normalize("Hello, World!") == "hello world")
    check("normalize collapses whitespace",
          normalize("a   b\t\nc") == "a b c")

    # Stable hash
    h1 = ngram_hash(("the", "quick", "brown"))
    h2 = ngram_hash(("the", "quick", "brown"))
    h3 = ngram_hash(("the", "quick", "fox"))
    check("ngram_hash is deterministic", h1 == h2)
    check("ngram_hash differs for different inputs", h1 != h3)

    # SHA1
    check("sha1 deterministic", sha1("test") == sha1("test"))

    # N-gram count
    text14 = "the capital of France is Paris and it has many beautiful museums to visit"
    grams = list(iter_ngrams(text14, n=13))
    check("14 words -> 2 13-grams", len(grams) == 2,
          f"got {len(grams)}")

    text12 = "one two three four five six seven eight nine ten eleven twelve"
    short_grams = list(iter_ngrams(text12, n=13))
    check("12 words -> 0 13-grams (too short)", len(short_grams) == 0)

    check("NGRAM_N is 13", NGRAM_N == 13)

    # Build an in-memory index and probe it
    idx = DecontamIndex()
    seed = "The capital of France is Paris and it has many beautiful museums to visit"
    idx.add_text(seed)
    check("index exact contains seed", sha1(normalize(seed)) in idx.exact)
    check("index ngrams populated", len(idx.ngrams) == 2)
    check("index __len__", len(idx) == 1)

    # Empty / whitespace text is a no-op
    idx2 = DecontamIndex()
    idx2.add_text("")
    idx2.add_text("   ")
    check("empty text doesn't pollute index", len(idx2.exact) == 0)

    c = Contaminator(idx)

    # Exact match (with trailing punctuation)
    r1 = c.is_contaminated(seed + ".")
    check("exact match hit (with trailing period)",
          r1.contaminated and r1.reason == "exact",
          f"got {r1}")

    # Exact match with case + whitespace variation
    r2 = c.is_contaminated("the  CAPITAL of FRANCE is paris and It Has many BEAUTIFUL museums to visit")
    check("exact match hit (case/whitespace variation)",
          r2.contaminated and r2.reason == "exact")

    # Embedded 13-gram match (longer text wrapping the seed)
    r3 = c.is_contaminated("Did you know the capital of France is Paris and it has many beautiful museums to visit each year?")
    check("13-gram embedded match",
          r3.contaminated and r3.reason == "ngram",
          f"got {r3}")

    # No overlap
    r4 = c.is_contaminated("Something entirely different talking about elephants in the jungle and rain forests")
    check("unrelated text is not contaminated",
          not r4.contaminated, f"got {r4}")

    # Too-short candidate (no 13-grams)
    r5 = c.is_contaminated("short text")
    check("text shorter than 13 words is not contaminated",
          not r5.contaminated)

    # Empty / whitespace candidate
    r6 = c.is_contaminated("")
    check("empty text is not contaminated", not r6.contaminated)

    # Persistence roundtrip
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "idx.pkl"
        import pickle
        with open(out, "wb") as f:
            pickle.dump(idx, f)
        c2 = Contaminator.from_disk(out)
        r7 = c2.is_contaminated("Did you know the capital of France is Paris and it has many beautiful museums to visit each year?")
        check("index roundtrips through pickle",
              r7.contaminated and r7.reason == "ngram")


# ---------------------------------------------------------------------------
# cli.py
# ---------------------------------------------------------------------------

def test_cli() -> None:
    print("\n[cli.py]")
    # Find the data_synthesis directory (parent of rehearsal/)
    rehearsal_dir = Path(__file__).resolve().parent
    cwd = rehearsal_dir.parent

    def run(args: list[str]) -> tuple[int, str, str]:
        r = subprocess.run(
            [sys.executable, "-m", "rehearsal.cli"] + args,
            cwd=cwd, capture_output=True, text=True, timeout=20,
        )
        return r.returncode, r.stdout, r.stderr

    rc, out, _ = run(["--help"])
    check("--help exits 0", rc == 0)
    check("--help lists download", "download" in out)
    check("--help lists decontam-build", "decontam-build" in out)
    check("--help lists solve (stub)", "solve" in out)

    rc, _, err = run(["solve"])
    check("solve stub exits 2", rc == 2,
          f"got rc={rc}")
    check("solve stub mentions 'not yet implemented'",
          "not yet implemented" in err, err[:200])

    rc, out, _ = run(["download", "--help"])
    check("download --help exits 0", rc == 0)
    check("download --help mentions --train-only", "--train-only" in out)
    check("download --help mentions --test-only", "--test-only" in out)
    check("download --help mentions --source", "--source" in out)

    rc, out, _ = run(["decontam-build", "--help"])
    check("decontam-build --help exits 0", rc == 0)
    check("decontam-build --help mentions --only", "--only" in out)
    check("decontam-build --help mentions --out", "--out" in out)


# ---------------------------------------------------------------------------
# download.py — verify dry pieces (registry filter logic) without HF calls
# ---------------------------------------------------------------------------

def test_download_filters() -> None:
    print("\n[data/download.py — filters only, no HF]")
    from rehearsal.data.download import (
        _filter_train_sources, _filter_decontam_testsets,
    )
    from rehearsal.data.sources import SOURCES, DECONTAM_TESTSETS

    # Drops sources with hf_path=None (i.e. drops generated + programmatic)
    public_only = _filter_train_sources(SOURCES, source_filter=None)
    check("filter drops generated/programmatic sources",
          all(s.hf_path is not None for s in public_only))
    # 33 public + 2 augmented (their seeds come from public HF datasets) = 35
    check("filter keeps 35 sources with hf_path (33 public + 2 augmented)",
          len(public_only) == 35, f"got {len(public_only)}")

    # Name filter
    only_mmlu = _filter_train_sources(SOURCES, source_filter="MMLU_auxiliary_training")
    check("source filter matches one", len(only_mmlu) == 1)

    # Decontam filter
    all_decontam = _filter_decontam_testsets(DECONTAM_TESTSETS, source_filter=None)
    check("decontam filter passes all 20", len(all_decontam) == 20)

    only_ifeval = _filter_decontam_testsets(DECONTAM_TESTSETS, source_filter="IFEval")
    check("decontam filter narrows to one", len(only_ifeval) == 1)


def test_extract_offline() -> None:
    print("\n[data/extract.py — offline pieces]")
    from rehearsal.data.extract import (
        EXTRACTORS, format_mc, extract_gsm8k_final, extract_math_boxed,
        pool_path, MC_LETTERS,
    )

    # MC formatter
    q, letters = format_mc("What is X?", ["red", "blue", "green", "yellow"])
    check("format_mc produces lettered options",
          "A) red" in q and "D) yellow" in q,
          f"got {q!r}")
    check("format_mc returns aligned letters",
          letters == ["A", "B", "C", "D"])

    # 2-way / 3-way
    _, l2 = format_mc("Pick one", ["a", "b"])
    check("format_mc handles 2-way", l2 == ["A", "B"])
    _, l3 = format_mc("Pick one", ["a", "b", "c"])
    check("format_mc handles 3-way", l3 == ["A", "B", "C"])

    # GSM8K final answer extraction
    sol = ("Let me calculate.\nFirst, 5 + 3 = 8.\nThen 8 * 2 = 16.\n#### 16")
    check("extract_gsm8k_final pulls final number",
          extract_gsm8k_final(sol) == "16",
          f"got {extract_gsm8k_final(sol)!r}")
    check("extract_gsm8k_final strips $ and commas",
          extract_gsm8k_final("answer #### $1,234.56") == "1234.56")
    check("extract_gsm8k_final returns None on missing marker",
          extract_gsm8k_final("no marker here") is None)

    # MATH boxed
    sol_math = "Solving step by step.\nThe answer is \\boxed{\\frac{1}{2}}."
    check("extract_math_boxed pulls last boxed",
          extract_math_boxed(sol_math) == "\\frac{1}{2}",
          f"got {extract_math_boxed(sol_math)!r}")
    sol_math2 = "First \\boxed{wrong}. Final: \\boxed{42}"
    check("extract_math_boxed prefers final boxed",
          extract_math_boxed(sol_math2) == "42")
    check("extract_math_boxed returns None on missing",
          extract_math_boxed("no boxed at all") is None)

    # Registry
    check("EXTRACTORS has 25 entries", len(EXTRACTORS) == 25,
          f"got {len(EXTRACTORS)}")

    # All registered names are real spec sources
    from rehearsal.spec import iter_sources
    spec_names = {s.name for s in iter_sources()}
    for n in EXTRACTORS:
        check(f"extractor '{n}' is a real spec source", n in spec_names)
        if n not in spec_names:
            break  # stop spamming

    # MC_LETTERS sane
    check("MC_LETTERS starts ABCD", MC_LETTERS[:4] == ["A", "B", "C", "D"])

    # pool_path
    p = pool_path("mmlu_shaped", "MMLU_auxiliary_training")
    check("pool_path under questions/_pool/",
          "/questions/_pool/mmlu_shaped/MMLU_auxiliary_training.jsonl" in str(p))


def main() -> int:
    print("=" * 60)
    print("Stage 1 + 2 smoke tests")
    print("=" * 60)
    test_spec()
    test_format()
    test_sources()
    test_decontam()
    test_cli()
    test_download_filters()
    test_extract_offline()

    print("\n" + "=" * 60)
    if _failures:
        print(f"FAILED: {len(_failures)} check(s)")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print(f"All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
