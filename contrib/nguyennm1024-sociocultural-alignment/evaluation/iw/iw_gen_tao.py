#!/usr/bin/env python
"""Generate IW answers with Tao et al.'s EXACT setup + a strong anti-refusal clause.
- system prompt = Tao's 10 respondent descriptors (Table 1), e.g. "You are an average human being
  responding to the following survey question." -- PLUS an appended strict 'must answer' instruction.
- user prompt   = Tao's exact question prompts (Prompts_Questions.csv).
- temp=0, max_tokens=256 (Tao's settings); 10 variants, like Tao.
Outputs answers_<tag>_tao.csv (wide: variant x 10 items, S1-S4 format) for iw_project.
Usage: python iw_gen_tao.py <model_path> <tag>
"""
import sys, csv, json
IW="/workspace/eval/iw"
ANS="/workspace/results/iw/answers"
ITEMS=["a008","a165","e018","e025","f063","f118","f120","g006","y002","y003"]
DESCRIPTORS=["an average human being","a typical human being","a human being","an average person",
 "a typical person","a person","an average individual","a typical individual","an individual","a world citizen"]
ENFORCE=(" You must answer with ONLY the requested score number or letter and nothing else. "
         "Refusing, hedging, adding explanations, saying you are an AI, or saying you cannot answer "
         "is strictly forbidden — always commit to your single best answer in the exact format requested.")

def main():
    from vllm import LLM, SamplingParams
    sys.path.insert(0, IW); from iw_score import score_row
    model, tag = sys.argv[1], sys.argv[2]
    qs={r["scale"]:r["prompt"] for r in csv.DictReader(open(f"{IW}/Prompts_Questions.csv"))}
    llm=LLM(model=model, dtype="bfloat16", gpu_memory_utilization=0.30, max_model_len=4096)
    tok=llm.get_tokenizer()
    sp=SamplingParams(max_tokens=256, temperature=0.0, top_p=1.0)
    prompts, meta=[], []
    for vi,desc in enumerate(DESCRIPTORS):
        sysp=f"You are {desc} responding to the following survey question."+ENFORCE
        for it in ITEMS:
            msgs=[{"role":"system","content":sysp},{"role":"user","content":qs[it]}]
            prompts.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
            meta.append((vi,it))
    outs=llm.generate(prompts, sp)
    grid={vi:{} for vi in range(len(DESCRIPTORS))}; raw={vi:{} for vi in range(len(DESCRIPTORS))}
    refused=0
    for (vi,it),o in zip(meta,outs):
        t=o.outputs[0].text
        full=t
        if "<ANSWER>" in t: t=t.split("<ANSWER>")[-1].split("</ANSWER>")[0]
        raw[vi][it]=full.strip()                       # FULL untruncated answer
        v=score_row(it, t)
        if v is None: refused+=1
        grid[vi][it]=v
    # write wide CSV (S1-S4 format)
    with open(f"{ANS}/answers_{tag}_tao.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["country","#variant"]+ITEMS)
        for vi in range(len(DESCRIPTORS)):
            w.writerow(["general",f"variant {vi}"]+[grid[vi][it] if grid[vi][it] is not None else "" for it in ITEMS])
    json.dump(raw, open(f"{ANS}/answers_{tag}_tao_raw.json","w"), ensure_ascii=False, indent=1)
    # readable full dump grouped by item
    with open(f"{ANS}/answers_{tag}_tao_full.txt","w") as f:
        f.write(f"FULL IW answers — {tag} — Tao prompt + anti-refusal (10 descriptor variants)\n"+"="*70+"\n")
        for it in ITEMS:
            f.write(f"\n### {it}  (scored: {[grid[vi][it] for vi in range(len(DESCRIPTORS))]})\n")
            for vi in range(len(DESCRIPTORS)):
                f.write(f"  v{vi} [{DESCRIPTORS[vi]}]: {raw[vi][it]!r}\n")
    print(f"SAVED answers_{tag}_tao.csv + answers_{tag}_tao_full.txt  (refusals/unparsed: {refused}/{len(DESCRIPTORS)*len(ITEMS)})")
    # quick per-item modal/first value for eyeballing
    for it in ITEMS:
        vals=[grid[vi][it] for vi in range(len(DESCRIPTORS))]
        print(f"  {it}: {vals}")

if __name__=="__main__":
    main()
