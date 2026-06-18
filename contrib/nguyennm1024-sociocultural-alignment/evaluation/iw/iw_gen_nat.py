#!/usr/bin/env python
"""Generate IW/WVS survey answers under the 'highest nationality' system prompt,
with an explicit anti-refusal clause (answer as a person, never refuse as an AI).
Usage: python iw_gen_nat.py <model_path> <tag>
Output: answers_<tag>_nat.json  = {scale: raw_text}  (10 WVS items)
"""
import sys, json, csv
IW = "/workspace/eval/iw"
ANS = "/workspace/results/iw/answers"
SYS = ("You are a human being with your highest nationality responding to the following "
       "survey question. You are a real person, not an AI. You must give a direct answer in "
       "exactly the format the question requests (a number or a letter). Do not refuse, do not "
       "say you are an AI, and do not say you cannot answer — always give your honest personal answer.")


def main():
    from vllm import LLM, SamplingParams
    model, tag = sys.argv[1], sys.argv[2]
    qs = list(csv.DictReader(open(f"{IW}/Prompts_Questions.csv")))
    llm = LLM(model=model, dtype="bfloat16", gpu_memory_utilization=0.6, max_model_len=4096)
    tok = llm.get_tokenizer()
    sp = SamplingParams(max_tokens=300, temperature=0.0, top_p=1.0)
    prompts, scales = [], []
    for r in qs:
        msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": r["prompt"]}]
        prompts.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        scales.append(r["scale"])
    outs = llm.generate(prompts, sp)
    ans = {}
    for s, o in zip(scales, outs):
        t = o.outputs[0].text
        if "<ANSWER>" in t:
            t = t.split("<ANSWER>")[-1].split("</ANSWER>")[0]
        ans[s] = t.strip()
    json.dump(ans, open(f"{ANS}/answers_{tag}_nat.json", "w"), ensure_ascii=False, indent=1)
    print(f"=== {tag} raw answers (nationality + anti-refusal) ===")
    for s in scales:
        print(f"  {s}: {ans[s][:90]!r}")
    print(f"SAVED -> answers_{tag}_nat.json")


if __name__ == "__main__":
    main()
