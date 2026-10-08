from __future__ import annotations
import argparse, json, math, random
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, TaskType, get_peft_model

class ChatDataset(Dataset):
    def __init__(self, path, tok, max_length=384):
        self.rows=[json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
        self.tok=tok; self.max=max_length
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        msgs=self.rows[i]["messages"]
        prefix=msgs[:-1]
        answer=msgs[-1]["content"]
        ptxt=self.tok.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True)
        # Tokenize prefix and completion separately so prompt tokens can be masked.
        pids=self.tok(ptxt, add_special_tokens=False)["input_ids"]
        aids=self.tok(answer + (self.tok.eos_token or ""), add_special_tokens=False)["input_ids"]
        ids=(pids+aids)[-self.max:]
        # If truncation ate part of the prefix, recompute answer boundary conservatively.
        cut=max(0,len(pids)+len(aids)-self.max)
        prefix_left=max(0,len(pids)-cut)
        labels=[-100]*prefix_left + ids[prefix_left:]
        return {"input_ids":ids,"labels":labels}

def collate(batch,pad_id):
    m=max(len(x["input_ids"]) for x in batch)
    ids=[]; labels=[]; masks=[]
    for x in batch:
        n=m-len(x["input_ids"])
        ids.append(x["input_ids"]+[pad_id]*n)
        labels.append(x["labels"]+[-100]*n)
        masks.append([1]*len(x["input_ids"])+[0]*n)
    return {"input_ids":torch.tensor(ids),"labels":torch.tensor(labels),"attention_mask":torch.tensor(masks)}

def pick_device():
    if torch.cuda.is_available(): return torch.device("cuda")
    if getattr(torch.backends,"mps",None) and torch.backends.mps.is_available(): return torch.device("mps")
    return torch.device("cpu")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--data",default="data/train.jsonl")
    ap.add_argument("--out",default="adapter")
    ap.add_argument("--epochs",type=int,default=2)
    ap.add_argument("--batch",type=int,default=1)
    ap.add_argument("--grad-accum",type=int,default=8)
    ap.add_argument("--lr",type=float,default=2e-4)
    ap.add_argument("--max-length",type=int,default=384)
    ap.add_argument("--max-steps",type=int,default=300)
    ap.add_argument("--seed",type=int,default=42)
    args=ap.parse_args()
    random.seed(args.seed); torch.manual_seed(args.seed)
    dev=pick_device(); print("device:",dev)
    tok=AutoTokenizer.from_pretrained(args.base, use_fast=True)
    if tok.pad_token is None: tok.pad_token=tok.eos_token
    dtype=torch.float16 if dev.type in {"cuda","mps"} else torch.float32
    model=AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=dtype)
    model.config.use_cache=False
    cfg=LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=["q_proj","k_proj","v_proj","o_proj"],
        bias="none",
    )
    model=get_peft_model(model,cfg)
    model.print_trainable_parameters()
    model.to(dev)
    if hasattr(model,"enable_input_require_grads"): model.enable_input_require_grads()
    ds=ChatDataset(args.data,tok,args.max_length)
    dl=DataLoader(ds,batch_size=args.batch,shuffle=True,collate_fn=lambda b:collate(b,tok.pad_token_id))
    opt=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=args.lr)
    model.train(); opt.zero_grad(set_to_none=True)
    step=0; micro=0; running=0.0
    for epoch in range(args.epochs):
        for batch in dl:
            batch={k:v.to(dev) for k,v in batch.items()}
            loss=model(**batch).loss/args.grad_accum
            loss.backward(); micro+=1; running+=float(loss)*args.grad_accum
            if micro%args.grad_accum==0:
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
                opt.step(); opt.zero_grad(set_to_none=True); step+=1
                if step%10==0:
                    print(f"step={step} avg_loss={running/10:.4f}"); running=0.0
                if step>=args.max_steps: break
        if step>=args.max_steps: break
    Path(args.out).mkdir(parents=True,exist_ok=True)
    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    Path(args.out,"DOUGBOT_TRAINING.json").write_text(json.dumps({
        "base_model":args.base,"data":args.data,"optimizer_steps":step,"seed":args.seed,
        "method":"LoRA","r":8,"alpha":16,
        "disclosure":"Fan-made DougDoug-inspired bot; not DougDoug or affiliated."
    },indent=2),encoding="utf-8")
    print("saved adapter ->",args.out)
if __name__=="__main__": main()
