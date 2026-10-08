from __future__ import annotations
import argparse, json, random, time
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, TaskType, get_peft_model

class ChatDataset(Dataset):
    def __init__(self,path,tok,max_length=96):
        self.rows=[json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
        self.tok=tok; self.max=max_length
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        msgs=self.rows[i]['messages']; prefix=msgs[:-1]; answer=msgs[-1]['content']
        ptxt=self.tok.apply_chat_template(prefix,tokenize=False,add_generation_prompt=True)
        pids=self.tok(ptxt,add_special_tokens=False)['input_ids']
        aids=self.tok(answer+(self.tok.eos_token or ''),add_special_tokens=False)['input_ids']
        # Keep end of prompt + answer, but preserve as much answer as possible.
        ids=(pids+aids)[-self.max:]
        cut=max(0,len(pids)+len(aids)-self.max)
        prefix_left=max(0,len(pids)-cut)
        labels=[-100]*prefix_left + ids[prefix_left:]
        return {'input_ids':ids,'labels':labels}

def collate(batch,pad_id):
    m=max(len(x['input_ids']) for x in batch)
    ids=[]; labels=[]; masks=[]
    for x in batch:
        n=m-len(x['input_ids'])
        ids.append(x['input_ids']+[pad_id]*n)
        labels.append(x['labels']+[-100]*n)
        masks.append([1]*len(x['input_ids'])+[0]*n)
    return {'input_ids':torch.tensor(ids),'labels':torch.tensor(labels),'attention_mask':torch.tensor(masks)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True)
    ap.add_argument('--data',default='data/train.jsonl')
    ap.add_argument('--out',default='adapter')
    ap.add_argument('--steps',type=int,default=12)
    ap.add_argument('--max-length',type=int,default=96)
    ap.add_argument('--lr',type=float,default=3e-4)
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--save-every',type=int,default=20)
    ap.add_argument('--resume',default=None,help='Existing PEFT adapter to continue training')
    ap.add_argument('--rank',type=int,default=4)
    ap.add_argument('--alpha',type=int,default=8)
    ap.add_argument('--targets',default='q_proj,v_proj')
    args=ap.parse_args()
    random.seed(args.seed); torch.manual_seed(args.seed)
    tok=AutoTokenizer.from_pretrained(args.base,use_fast=True,local_files_only=True)
    if tok.pad_token is None: tok.pad_token=tok.eos_token
    # Qwen2.5-0.5B weights are BF16 already; preserving BF16 halves RAM vs the
    # generic trainer's float32 CPU path. This sandbox has a tight memory cap.
    dtype=torch.bfloat16
    t0=time.time()
    model=AutoModelForCausalLM.from_pretrained(args.base,dtype=dtype,local_files_only=True,low_cpu_mem_usage=True)
    print('loaded base in',round(time.time()-t0,2),'s')
    model.config.use_cache=False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    if args.resume:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,args.resume,is_trainable=True,local_files_only=True)
        print('resuming adapter',args.resume)
    else:
        targets=[x.strip() for x in args.targets.split(',') if x.strip()]
        cfg=LoraConfig(task_type=TaskType.CAUSAL_LM,r=args.rank,lora_alpha=args.alpha,lora_dropout=0.0,
                       target_modules=targets,bias='none')
        model=get_peft_model(model,cfg)
    model.print_trainable_parameters()
    if hasattr(model,'enable_input_require_grads'): model.enable_input_require_grads()
    ds=ChatDataset(args.data,tok,args.max_length)
    g=torch.Generator().manual_seed(args.seed)
    dl=DataLoader(ds,batch_size=1,shuffle=True,generator=g,collate_fn=lambda b:collate(b,tok.pad_token_id))
    opt=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=args.lr)
    model.train(); losses=[]; step=0
    for batch in dl:
        loss=model(**batch).loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
        opt.step(); opt.zero_grad(set_to_none=True)
        step+=1; losses.append(float(loss.detach()))
        print(f'step={step} loss={losses[-1]:.4f}',flush=True)
        if args.save_every and step % args.save_every == 0:
            cp=Path(args.out)/f'checkpoint-{step}'
            cp.mkdir(parents=True,exist_ok=True)
            model.save_pretrained(cp)
            tok.save_pretrained(cp)
            print('saved checkpoint ->',cp,flush=True)
        if step>=args.steps: break
    Path(args.out).mkdir(parents=True,exist_ok=True)
    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    Path(args.out,'DOUGBOT_TRAINING.json').write_text(json.dumps({
        'base_model':str(args.base),'data':str(args.data),'optimizer_steps':step,
        'losses':losses,'seed':args.seed,'method':'LoRA-lowmem','r':args.rank,'alpha':args.alpha,
        'target_modules':([x.strip() for x in args.targets.split(',') if x.strip()] if not args.resume else 'from-resume'),'max_length':args.max_length,
        'dtype':'bfloat16','disclosure':'Fan-made DougDoug-inspired bot; not DougDoug or affiliated.'
    },indent=2),encoding='utf-8')
    print('saved adapter ->',args.out)
if __name__=='__main__': main()
