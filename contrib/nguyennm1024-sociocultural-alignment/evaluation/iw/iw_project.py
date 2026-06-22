#!/usr/bin/env python
"""Python IW projector — bit-exact port of Tao et al.'s predict.psych, using the HUMAN-ONLY
full-IVS PCA exported by export_projection.R (iw_projection_final.json).

The PCA was fit on WVS+EVS humans only (no AI answers); a model is projected as an out-of-sample
point: standardize its 10 answers by the human means/sds, apply the human scoring weights, rescale.

Usage:
  from iw_project import project, project_model
  rc1, rc2 = project([a008,a165,e018,e025,f063,f118,f120,g006,y002,y003])   # raw item values
  rc1, rc2 = project_model("answers_base_forced_nat.json")                  # scores a model's answers
"""
import json, sys, os
IW = os.path.dirname(os.path.abspath(__file__))
ANS = "/workspace/results/iw/answers"
P = json.load(open(os.path.join(IW, "iw_projection_final.json")))
ITEMS = P["items"]                                  # [a008,a165,e018,e025,f063,f118,f120,g006,y002,y003]
CENTER = P["center"]; SCALE = P["scale"]; W = P["weights"]   # W: 10x2
SE = P["se"] - 1; SEC = P["sec"] - 1                # JSON is 1-based (R)
RC1 = P["rc1"]; RC2 = P["rc2"]                       # [slope, intercept]

def project(vec):
    """vec: 10 raw item values in ITEMS order -> (RC1 self-expression x, RC2 secular y)."""
    z = [(vec[i] - CENTER[i]) / SCALE[i] for i in range(10)]
    s = [sum(z[i] * W[i][k] for i in range(10)) for k in range(2)]   # z @ weights
    return (RC1[0]*s[SE] + RC1[1], RC2[0]*s[SEC] + RC2[1])

def project_model(answers_json):
    """Score a model's IW answers (answers_<tag>_nat.json) and project. Requires all 10 items
    answered (no imputation) — force refused items first (e.g. answers_base_forced_nat.json)."""
    sys.path.insert(0, IW); from iw_score import score_row
    a = json.load(open(answers_json if os.path.isabs(answers_json) else os.path.join(ANS, answers_json)))
    vec = []
    for it in ITEMS:
        v = score_row(it, a.get(it, ""))
        if v is None:
            raise ValueError(f"item {it} unanswered/refused in {answers_json}; force an answer first")
        vec.append(v)
    return project(vec)

if __name__ == "__main__":
    # verify against R ground-truth in the JSON
    base = [2,2,2,1,8,8,8,3,2,1]; soup = [3,2,1,1,8,8,8,3,2,0]   # honest (abortion=8), ITEMS order
    gt = P.get("groundtruth", {})
    for name, vec in [("base", base), ("soupiw", soup)]:
        x, y = project(vec)
        g = gt.get(name)
        tag = f"  R-truth=({g[0]:+.4f},{g[1]:+.4f})  d={((x-g[0])**2+(y-g[1])**2)**0.5:.4f}" if g else ""
        print(f"{name:8s} python=({x:+.4f},{y:+.4f}){tag}")
    # also project from the saved answer files (scores them)
    try:
        print("base(from answers_base_forced_nat.json) =", tuple(round(v,3) for v in project_model("answers_base_forced_nat.json")))
        print("soupiw(from answers_soupiw_nat.json)     =", tuple(round(v,3) for v in project_model("answers_soupiw_nat.json")))
    except Exception as ex:
        print("model-file projection note:", ex)
