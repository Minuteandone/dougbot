from __future__ import annotations
import argparse, json, random
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, TaskType, get_peft_model, PeftModel

def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def encode(tok,row,max_len):
    msgs=row['messages']; prefix=msgs[:-1]; answer=msgs[-1]['content']
    ptxt=tok.apply_chat_template(prefix,tokenize=False,add_generation_prompt=True)
    pids=tok(ptxt,add_special_tokens=False)['input_ids']
    aids=tok(answer+(tok.eos_token or ''),add_special_tokens=False)['input_ids']
    if len(aids)>=max_len:
        aids=aids[:max_len]; pids=[]
    else:
        pids=pids[-(max_len-len(aids)):]
    ids=pids+aids; labels=[-100]*len(pids)+aids
    return ids,labels

def tensorize(ids,labels,pad):
    return (torch.tensor([ids]),torch.tensor([labels]),torch.tensor([[1]*len(ids)]))

def bucket(rows):
    b={'stream':[],'behavior':[],'normal':[],'benign':[],'other':[]}
    for r in rows:
        src=r.get('source',''); kind=r.get('kind','')
        if kind=='benign_ambiguity': b['benign'].append(r)
        elif src.startswith('stream-derived-synthetic'): b['stream'].append(r)
        elif src in ('synthetic-behavior','handwritten-behavior-anchor','Doug-hole-Wiki-derived-anchor'): b['behavior'].append(r)
        elif src in ('synthetic-preservation','synthetic-delve-preservation'): b['normal'].append(r)
        else: b['other'].append(r)
    return b

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True); ap.add_argument('--data',required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--resume'); ap.add_argument('--steps',type=int,default=8); ap.add_argument('--lr',type=float,default=1.2e-4)
    ap.add_argument('--seed',type=int,default=1); ap.add_argument('--max-length',type=int,default=96)
    ap.add_argument('--rank',type=int,default=8); ap.add_argument('--alpha',type=int,default=16)
    args=ap.parse_args(); rng=random.Random(args.seed); torch.manual_seed(args.seed)
    tok=AutoTokenizer.from_pretrained(args.base,use_fast=True,local_files_only=True); tok.pad_token=tok.pad_token or tok.eos_token
    model=AutoModelForCausalLM.from_pretrained(args.base,dtype=torch.bfloat16,local_files_only=True,low_cpu_mem_usage=True)
    model.config.use_cache=False; model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    if args.resume:
        model=PeftModel.from_pretrained(model,args.resume,is_trainable=True,local_files_only=True)
        print('resuming',args.resume,flush=True)
    else:
        cfg=LoraConfig(task_type=TaskType.CAUSAL_LM,r=args.rank,lora_alpha=args.alpha,lora_dropout=0.03,
            target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],bias='none',layers_to_transform=list(range(16,24)),layers_pattern='layers')
        model=get_peft_model(model,cfg)
    if hasattr(model,'enable_input_require_grads'): model.enable_input_require_grads()
    model.print_trainable_parameters()
    rows=load(args.data); b=bucket(rows)
    # Heavy on real-stream-derived interaction structure, while preserving normal conversation.
    keys=['stream','stream','stream','behavior','behavior','normal','benign']
    opt=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=args.lr,weight_decay=0.01)
    hist=[]; model.train()
    for step in range(1,args.steps+1):
        k=rng.choice(keys); pool=b[k] or rows; r=rng.choice(pool)
        ids,labels=encode(tok,r,args.max_length); ids,labels,mask=tensorize(ids,labels,tok.pad_token_id)
        out=model(input_ids=ids,attention_mask=mask,labels=labels)
        loss=out.loss; loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
        opt.step(); opt.zero_grad(set_to_none=True)
        rec={'step':step,'bucket':k,'loss':round(float(loss.detach()),4)}; hist.append(rec); print(rec,flush=True)
        del out,ids,labels,mask
    p=Path(args.out); p.mkdir(parents=True,exist_ok=True); model.save_pretrained(p)
    meta={'method':'single-model assistant-only SFT LoRA','routing':False,'soft_prompt':False,'steps_this_chunk':args.steps,
          'lr':args.lr,'seed':args.seed,'max_length':args.max_length,'rank':args.rank,'alpha':args.alpha,
          'layers':'16-23 q/k/v/o + MLP projections','neutral_system':'You are Dougbot.','history':hist}
    (p/'DOUGBOT_SINGLE_TRAINING.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('saved',p,flush=True)
if __name__=='__main__': main()
