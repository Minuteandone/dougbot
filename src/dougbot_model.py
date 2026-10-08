from __future__ import annotations
import os,re
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from peft import PeftModel

ROOT=Path(__file__).resolve().parents[1]
SYSTEM='You are Dougbot.'
STALE_PATTERNS=[
    r'\bi have an? (?:incredible|amazing|excellent|great)?\s*(?:plan|idea)\b',
    r'\bnew rule\b',r'\bdoing science\b',r'\bphase two\b',
    r'\bcompletely calculated\b',r'\bthe plan remains flawless\b',
    r'\bfuture-us problem\b',r'\bchat,? congratulations\b',r'^\s*perfect[,.!]',r'\bwe have discovered\b',
]
STALE_RE=[re.compile(x,re.I) for x in STALE_PATTERNS]
BLOCK_PHRASES=[
    'I have an incredible plan','I have an incredible idea','I have an amazing idea','I have a plan','New rule','doing science','phase two',
    'completely calculated','the plan remains flawless','future-us problem','Chat, congratulations'
]

def _device():
    if torch.cuda.is_available():return 'cuda'
    if getattr(torch.backends,'mps',None) and torch.backends.mps.is_available():return 'mps'
    return 'cpu'

def _path_or_name(value,default):
    value=value or default
    p=Path(value)
    if not p.is_absolute() and (value.startswith('.') or '/' not in value):
        candidate=(ROOT/p).resolve()
        if candidate.exists():return str(candidate)
    return str(p.resolve()) if p.exists() else value

def _default_base():
    p=ROOT/'models'/'qwenity'
    return str(p) if (p/'config.json').exists() else 'Qwen/Qwen2.5-0.5B-Instruct'

def _score_stale(text):return sum(bool(x.search(text)) for x in STALE_RE)

class Dougbot:
    def __init__(self,base=None,adapter=None):
        self.base=_path_or_name(base or os.getenv('DOUGBOT_BASE_MODEL'),_default_base())
        self.adapter=_path_or_name(adapter or os.getenv('DOUGBOT_ADAPTER'),str(ROOT/'adapter'))
        self.device=_device()
        local=Path(self.base).exists()
        self.tok=AutoTokenizer.from_pretrained(self.base,use_fast=True,local_files_only=local)
        self.tok.pad_token=self.tok.pad_token or self.tok.eos_token
        dtype=torch.float16 if self.device in {'cuda','mps'} else torch.bfloat16
        bm=AutoModelForCausalLM.from_pretrained(self.base,dtype=dtype,low_cpu_mem_usage=True,local_files_only=local)
        self.model=PeftModel.from_pretrained(bm,self.adapter,local_files_only=Path(self.adapter).exists())
        self.model.to(self.device).eval()
        self.bad_words=[]
        for phrase in BLOCK_PHRASES:
            for s in (phrase,' '+phrase,phrase.lower(),' '+phrase.lower()):
                ids=self.tok(s,add_special_tokens=False)['input_ids']
                if ids and ids not in self.bad_words:self.bad_words.append(ids)

    def _token_budget(self,text,context,requested):
        if requested is not None:return requested
        words=re.findall(r"\b\w+\b",text)
        if not context and len(words)<=5:return int(os.getenv('DOUGBOT_SHORT_MAX_TOKENS','22'))
        if context:return int(os.getenv('DOUGBOT_THREAD_MAX_TOKENS','90'))
        return int(os.getenv('DOUGBOT_MAX_NEW_TOKENS','100'))

    @torch.inference_mode()
    def reply(self,text,context=None,max_new_tokens=None):
        content=text if not context else f'Context from the thread:\n{context}\n\nMessage to answer:\n{text}'
        msgs=[{'role':'system','content':SYSTEM},{'role':'user','content':content}]
        prompt=self.tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
        x=self.tok(prompt,return_tensors='pt').to(self.device)
        budget=self._token_budget(text,context,max_new_tokens)
        attempts=max(1,int(os.getenv('DOUGBOT_GENERATION_ATTEMPTS','3')))
        candidates=[]
        for _ in range(attempts):
            out=self.model.generate(
                **x,max_new_tokens=budget,do_sample=True,
                temperature=float(os.getenv('DOUGBOT_TEMPERATURE','0.84')),
                top_p=float(os.getenv('DOUGBOT_TOP_P','0.90')),
                repetition_penalty=float(os.getenv('DOUGBOT_REPETITION_PENALTY','1.18')),
                no_repeat_ngram_size=int(os.getenv('DOUGBOT_NO_REPEAT_NGRAM','4')),
                bad_words_ids=self.bad_words or None,
                pad_token_id=self.tok.pad_token_id,eos_token_id=self.tok.eos_token_id,
            )
            ans=self.tok.decode(out[0][x['input_ids'].shape[1]:],skip_special_tokens=True).strip()
            ans=ans.replace('I am DougDoug','I am Dougbot').replace("I'm DougDoug","I'm Dougbot")
            score=_score_stale(ans)
            wc=len(re.findall(r'\b\w+\b',ans))
            short_input=(not context and len(re.findall(r'\b\w+\b',text))<=5)
            length_penalty=max(0,wc-14) if short_input else 0
            candidates.append((score,length_penalty,wc,ans))
            if ans and score==0 and (not short_input or wc<=14):return ans
        candidates.sort(key=lambda z:(z[0],z[1],z[2]))
        return candidates[0][3] if candidates else 'I appear to have generated absolutely nothing. Impressive.'
