import sys, os, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
adapter, out = sys.argv[1], sys.argv[2]
base = "meta-llama/Llama-3.2-3B-Instruct"
tok = AutoTokenizer.from_pretrained("/workspace/train/models/vn-3b-final")
try:
    m = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.bfloat16)
except TypeError:
    m = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16)
m = PeftModel.from_pretrained(m, adapter)
m = m.merge_and_unload()
os.makedirs(out, exist_ok=True)
m.save_pretrained(out); tok.save_pretrained(out)
for r,_,fs in os.walk(out):
    for f in fs:
        try: os.chmod(os.path.join(r,f), 0o666)
        except: pass
print(f"MERGED {adapter} -> {out}")
