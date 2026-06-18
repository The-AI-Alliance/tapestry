"""Full 14042 MMLU eval for a THINK/ANSWER model, records idx+subtask, incremental+resumable.
Usage: python zs_full_mmlu.py <model> <tag> [budget]"""
import sys, re, json, os
sys.path.insert(0, "/workspace/eval"); sys.path.insert(0, "/workspace/train")
AO, AC = "<ANSWER>", "</ANSWER>"
def extract(text, letters="ABCD"):
    L=f"[{letters}]"
    if AO in text:
        a=text.split(AO)[-1].split(AC)[0]
        m=re.search(rf'({L})',a)
        if m: return m.group(1).upper(),"answer-tag"
    m=re.findall(rf'(?:the\s+)?(?:best|correct|final)?\s*answer\s+is\s*:?\s*\(?\*{{0,2}}({L})\b',text,re.I)
    if m: return m[-1].upper(),"answer-is"
    return None,"no-answer-spiral"
def main():
    from vllm import LLM, SamplingParams
    from datasets import load_dataset
    from chat_template import CHAT_TEMPLATE
    model, tag = sys.argv[1], sys.argv[2]
    budget = int(sys.argv[3]) if len(sys.argv)>3 else 6000
    d=load_dataset("meta-llama/Llama-3.2-3B-Instruct-evals",name="Llama-3.2-3B-Instruct-evals__mmlu__details",split="latest")
    llm=LLM(model=model,dtype="bfloat16",gpu_memory_utilization=0.5,max_model_len=8192)
    tok=llm.get_tokenizer(); tok.chat_template=CHAT_TEMPLATE
    sp=SamplingParams(max_tokens=budget,stop=[AC],temperature=0.0,top_p=1.0,repetition_penalty=1.1)
    prompts,meta=[],[]
    for i in range(len(d)):
        r=d[i]; cl=r["input_choice_list"]; opts="\n".join(f"{k}. {v}" for k,v in cl.items())
        body=("Given the following question and four candidate answers (A, B, C and D), choose the best answer.\n"
              f"Question: {r['input_question']}\n{opts}\n"
              'Your response should end with "<ANSWER>The best answer is [the_answer_letter]</ANSWER>" where the [the_answer_letter] is one of A, B, C or D.')
        prompts.append(tok.apply_chat_template([{"role":"user","content":body}],tokenize=False,add_generation_prompt=True))
        meta.append((i,r["input_correct_responses"][0].strip().strip('"').upper(),r["subtask_name"].replace("mmlu_chat.","")))
    outpath=f"/workspace/results/mmlu/zs_{tag}_mmlu_results.jsonl"
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    done=sum(1 for _ in open(outpath)) if os.path.exists(outpath) else 0
    print(f"[plan] full {len(d)}, resume {done}",flush=True)
    f=open(outpath,"a"); CH=512
    for s in range(done,len(prompts),CH):
        couts=llm.generate(prompts[s:s+CH],sp)
        for (i,g,sub),o in zip(meta[s:s+CH],couts):
            t=o.outputs[0].text; pred,rule=extract(t)
            f.write(json.dumps({"idx":i,"subtask":sub,"gold":g,"pred":pred,"ok":(pred==g),"rule":rule,"finish":o.outputs[0].finish_reason,"out":t},ensure_ascii=False)+"\n")
        f.flush(); os.fsync(f.fileno()); print(f"[ZS-FULL {tag}] {s+len(couts)}/{len(prompts)}",flush=True)
    f.close()
    recs=[json.loads(l) for l in open(outpath)]; ok=sum(r["ok"] for r in recs)
    print(f"[RESULT {tag}] {ok}/{len(recs)}={ok/len(recs)*100:.1f}%  spirals={sum(r['pred'] is None for r in recs)}",flush=True)
    print(f"ZS_FULL_DONE_{tag}",flush=True)
if __name__=="__main__": main()
