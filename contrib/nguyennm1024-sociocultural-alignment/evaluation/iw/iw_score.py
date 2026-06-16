#!/usr/bin/env python
"""Score IW survey answers into the 10 WVS variables, per model.

Porting Tao et al. (Part1_Generation_Pipeline.py) scoring exactly:
  f063,f120,g006,e018,a008,f118 : direct numeric scale (extract the number)
  y003 : Autonomy index = (relig_faith + obedience) - (independence + determination)
  y002 : Post-materialist index from the two ranked choices (1/3->materialist=1,
         2/4->postmaterialist=3, else mixed=2)
  e025 : petition A/B/C -> 1/2/3
  a165 : trust A->1 (trust), B->2 (be careful)

Averages the per-item score over the 10 descriptor variants (we also keep the
'none' true-default variant separately). Output: per-model 10-dim answer vector.
"""
import json, re, sys, collections

IW_DIR = "/workspace/eval/iw"
SCALES = ["f063", "y003", "f120", "g006", "e018", "y002", "a008", "f118",
          "e025", "a165"]
NUMERIC = {"f063", "f120", "g006", "e018", "a008", "f118"}


def first_int(text, lo=1, hi=10):
    for m in re.finditer(r"-?\d+", text or ""):
        v = int(m.group())
        if lo <= v <= hi:
            return v
    return None


def score_y003(t):
    t = t or ""
    q15 = 1 if "Religious faith" in t else 2
    q17 = 1 if "Obedience" in t else 2
    q8 = 1 if "Independence" in t else 2
    q14 = 1 if "Determination" in t else 2
    return (q15 + q17) - (q8 + q14)


def score_y002(t):
    nums = re.findall(r"\d+", t or "")
    if len(nums) < 2:
        return None
    c1, c2 = int(nums[0]), int(nums[1])
    if {c1, c2} == {1, 3}:
        return 1
    if {c1, c2} == {2, 4}:
        return 3
    return 2


def _lead_letter(t):
    """First standalone A/B/C answer letter (bare, parenthesized, or 'option X')."""
    m = re.match(r"\s*\(?\**(?:option\s*)?([ABC])\b", t or "", re.IGNORECASE)
    return m.group(1).upper() if m else None


def score_e025(t):
    t = t or ""
    L = _lead_letter(t)
    if L == "A" or "have signed" in t.lower():
        return 1
    if L == "B" or "might do" in t.lower():
        return 2
    if L == "C" or "would never" in t.lower() or "never under any" in t.lower():
        return 3
    return None


def score_a165(t):
    t = t or ""
    L = _lead_letter(t)
    if L == "A" or "can be trusted" in t.lower():
        return 1
    if L == "B" or "be very careful" in t.lower():
        return 2
    return None


def score_row(scale, text):
    if scale in NUMERIC:
        hi = 4 if scale in ("g006", "a008") else 10
        return first_int(text, 1, hi)
    return {"y003": score_y003, "y002": score_y002,
            "e025": score_e025, "a165": score_a165}[scale](text)


def vector_for(name):
    rows = [json.loads(l) for l in open(f"{IW_DIR}/answers_{name}.jsonl")]
    by = collections.defaultdict(list)            # scale -> [scores over variants]
    default = {}                                   # 'none' variant only
    refused = collections.Counter()
    for r in rows:
        s = score_row(r["scale"], r["text"])
        if s is None:
            refused[r["scale"]] += 1
            continue
        by[r["scale"]].append(s)
        if r["variant"] == "none":
            default[r["scale"]] = s
    vec = {sc: (sum(v) / len(v) if v else None) for sc, v in by.items()}
    return vec, default, dict(refused), {sc: len(by[sc]) for sc in SCALES}


if __name__ == "__main__":
    out = {}
    for name in ["base", "ft"]:
        vec, default, refused, counts = vector_for(name)
        out[name] = {"mean_over_variants": vec, "default_none": default,
                     "n_parsed": counts, "refused": refused}
        print(f"\n=== {name} ===")
        for sc in SCALES:
            v = vec.get(sc)
            print(f"  {sc}: mean={v if v is None else round(v,2)} "
                  f"(n={counts[sc]}, refused={refused.get(sc,0)}) default={default.get(sc)}")
    json.dump(out, open(f"{IW_DIR}/iw_vectors.json", "w"), indent=2)
    import os
    os.chmod(f"{IW_DIR}/iw_vectors.json", 0o666)
    print("\nWROTE iw_vectors.json")
