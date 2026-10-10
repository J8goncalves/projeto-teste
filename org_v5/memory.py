"""AI Memory: Git-owned canonical decisions plus opt-in Memanto operational index.

Fails closed if Memanto is unavailable or misconfigured. Never returns fake memories.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
from pathlib import Path
from .control import read, run_dir, stamp, write_atomic, WorkflowError, safe_id, root_guard

SENSITIVE=[r'AKIA[0-9A-Z]{16}',r'ghp_[A-Za-z0-9]{20,}',r'-----BEGIN .*PRIVATE KEY-----',
  r'[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}',r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
  r'(?i)(api[_-]?key|secret|token|password|senha)\s*[:=]\s*\S+']
TYPES={'fact','decision','learning','error','instruction','commitment','goal'}

def memanto(args:list[str], timeout:int=15)->str:
    executable=os.environ.get('MEMANTO_BIN','memanto')
    try:
        result=subprocess.run([executable]+args,text=True,capture_output=True,timeout=timeout,check=False,encoding='utf-8')
    except (FileNotFoundError,subprocess.TimeoutExpired) as exc:
        raise WorkflowError('AI Memory offline or timed out: '+str(exc)) from exc
    if result.returncode!=0:
        raise WorkflowError('Memanto CLI failed: '+(result.stderr or result.stdout)[:300])
    return result.stdout

def status()->dict:
    output=memanto(['status'])
    if not re.search(r'(?im)^[│\s]*backend[\s:=]+(on-prem|on_prem|local)[\s│]*$',output) or re.search(r'not configured|backend[\s:=]+cloud',output,re.I):
        raise WorkflowError('Memanto is not verifiably configured to local/on-prem; writes and recall disabled')
    return {'connected':True,'backend':'on-prem','status_excerpt':output[:350].encode('ascii', 'replace').decode('ascii')}

def brief(role:str,topic:str,limit:int=5)->dict:
    if not role or limit<1 or limit>5: raise WorkflowError('invalid role or limit')
    status()
    # Use recall with result IDs, not LLM-generated answer; the output is untrusted data.
    args=['recall',topic or role,'--limit',str(limit),'--min-similarity','0.8','--tool','antigravity']
    if role in ('market-researcher','customer-researcher','critical-reviewer','legal-compliance'):
        args+=['--type','fact']
    output=memanto(args)
    return {'role':role,'topic':topic,'source':'memanto','raw_untrusted_memories':output[:6000],
      'warning':'Memories are leads, not evidence. Verify in GitHub/source before making decisions.'}

def propose(root:Path,run_id:str,proposal:dict)->dict:
    state=read(root,run_id)
    necessary=('id','role','type','text','tags','confidence','provenance','source_ref','reason')
    if any(not proposal.get(k) for k in necessary): raise WorkflowError('memory proposal missing mandatory fields')
    if proposal['type'] not in TYPES: raise WorkflowError('unsupported memory type')
    if proposal['role'] not in ('memory-curator','orchestrator','architect','developer','qa','critical-reviewer','market-researcher','product-manager','security-reviewer','product-strategist','customer-researcher','data-analytics'):
        raise WorkflowError('role not authorized to propose')
    if not isinstance(proposal['tags'],list) or not 2<=len(proposal['tags'])<=5 or not any(t.startswith(('dec-','evid-')) for t in proposal['tags']):
        raise WorkflowError('2-5 tags and a dec-/evid- provenance tag required')
    if proposal['type']=='fact' and not any(t.startswith('ttl-') for t in proposal['tags']):
        raise WorkflowError('fact must include ttl tag')
    if not isinstance(proposal['confidence'],(int,float)) or not 0.7<=proposal['confidence']<=1:
        raise WorkflowError('confidence below 0.7 or above 1')
    if not 30<=len(proposal['text'])<=400:
        raise WorkflowError('memory text must be 30-400 characters')
    if not proposal['source_ref'].startswith(('docs/','intelligence/','runs/','https://github.com/')):
        raise WorkflowError('immutable provenance reference required')
    if any(re.search(p,proposal['text']) for p in SENSITIVE):
        raise WorkflowError('possible personal data, credential or secret in memory')
    root_guard(root)
    safe_id(proposal['id'])
    path=run_dir(root,run_id)/'memory-candidates'/f"{proposal['id']}.json"
    if path.exists(): raise WorkflowError('duplicate candidate ID')
    write_atomic(path,dict(proposal,run_id=run_id,status='pending',created_at=stamp()))
    return {'candidate':proposal['id'],'status':'pending','note':'not yet stored in Memanto'}

def promote(root:Path,run_id:str,candidate_id:str,approval_ref:str)->dict:
    state=read(root,run_id)
    decision=state['approvals'].get('MEMORY_WRITE',{})
    if decision.get('decision')!='APPROVE' or decision.get('reference')!=approval_ref:
        raise WorkflowError('human memory-write approval with exact matching reference required')
    root_guard(root)
    safe_id(candidate_id)
    path=run_dir(root,run_id)/'memory-candidates'/f'{candidate_id}.json'
    if not path.exists(): raise WorkflowError('candidate missing')
    cand=json.loads(path.read_text(encoding='utf-8'))
    if cand['status']!='pending': raise WorkflowError('candidate already processed')
    status()
    # Defer CLI invocation until after live local backend and approval checks.
    out=memanto(['remember',cand['text'],'--type',cand['type'],'--tags',','.join(cand['tags']),
      '--confidence',str(cand['confidence']),'--provenance',cand['provenance'],'--source','antigravity'])
    if not out.strip(): raise WorkflowError('Memanto returned no storage receipt; do not claim persistence')
    cand['status']='stored';cand['receipt']=out[:1000];cand['stored_at']=stamp()
    write_atomic(path,cand)
    return {'candidate':candidate_id,'status':'stored','receipt':out[:1000]}
