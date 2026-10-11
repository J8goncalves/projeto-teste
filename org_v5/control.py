"""Deterministic, artifact-driven workflow engine. Not an identity/auth boundary."""
from __future__ import annotations
import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from .contracts import CONTRACTS, ROLES, ContractError, digest, load, validate
from .identity import verify_actor_identity, verify_independence
from .approvals import verify_human_approval, verify_and_consume_human_approval

PHASES=['INTAKE','DISCOVERY','PLANNING','DESIGN','BUILD','VERIFY','RELEASE','LEARN','CLOSED']
MODES = {
    'ENGINEERING_SMALL': {
        'DISCOVERY':['intake'], 'PLANNING':[], 'DESIGN':['prd'], 'BUILD':['architecture'],
        'VERIFY':['build'], 'RELEASE':['qa-report','security-report','implementation-review'], 'LEARN':['release'], 'CLOSED':[]
    },
    'PRODUCT_DISCOVERY': {
        'DISCOVERY':['intake'], 'PLANNING':['market-research','critical-review'], 'DESIGN':['prd'], 'BUILD':['architecture'],
        'VERIFY':['build'], 'RELEASE':['qa-report','security-report','implementation-review'], 'LEARN':['release'], 'CLOSED':[]
    },
    'RESEARCH_ONLY': {
        'DISCOVERY':['intake'], 'PLANNING':['market-research','critical-review'], 'DESIGN':[], 'BUILD':[],
        'VERIFY':[], 'RELEASE':[], 'LEARN':[], 'CLOSED':[]
    },
    'ENGINEERING_HIGH_RISK': {
        'DISCOVERY':['intake'], 'PLANNING':['market-research','critical-review'], 'DESIGN':['prd'], 'BUILD':['architecture'],
        'VERIFY':['build'], 'RELEASE':['qa-report','security-report','implementation-review'], 'LEARN':['release'], 'CLOSED':[]
    }
}
HUMAN_STATES={'BUILD','RELEASE','CLOSED'}
CRITICAL_KINDS={'build','qa-report','security-report','implementation-review','release'}
INPUT_REQUIREMENTS={
 'intake':set(),
 'market-research':{'intake'},'customer-research':{'intake'},
 'critical-review':set(), # Allow flexibility
 'strategy':{'critical-review'},
 'marketing':set(),
 'legal':{'intake'},'experiment':{'strategy'},'analytics':{'experiment'},
 'prd':set(), # removed strict predecessor requirement to allow ENGINEERING_SMALL
 'architecture':{'prd'},'build':{'architecture'},
 'qa-report':{'build'},'security-report':{'build'},
 'implementation-review':{'qa-report','security-report'},
 'ops':{'architecture'},'release':{'implementation-review','qa-report','security-report'},
 'memory-review':{'critical-review'},'executive-decision':{'critical-review'},
}

REVIEWERS={
 'intake':{'critical-reviewer','product-manager'},
 'market-research':{'critical-reviewer'},'customer-research':{'critical-reviewer'},
 'strategy':{'critical-reviewer'},'marketing':{'critical-reviewer'},
 'experiment':{'data-analytics','critical-reviewer'},'analytics':{'critical-reviewer'},
 'legal':{'critical-reviewer'},'critical-review':{'ceo','legal-compliance'},
 'prd':{'qa','architect'},'architecture':{'security-reviewer','implementation-reviewer'},
 'build':{'qa','implementation-reviewer'},'qa-report':{'implementation-reviewer'},
 'security-report':{'implementation-reviewer'},'ops':{'security-reviewer'},
 'release':{'implementation-reviewer'},'memory-review':{'critical-reviewer'},
 'implementation-review':{'critical-reviewer'},'executive-decision':{'critical-reviewer'},
}

def proof_file(root:Path,ref:str):
    if not isinstance(ref,str) or ref.startswith('https://') or '\\' in ref or '..' in ref or Path(ref).is_absolute():
        raise WorkflowError('local proof required; refusing remote or unsafe path')
    path=(root/ref).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size==0:
        raise WorkflowError(f'proof file missing or empty: {ref}')
    return path

def validate_proof(root:Path,doc:dict):
    if doc.get('kind') not in ('qa-report','security-report') or doc.get('verdict')!='PASS':return
    execution=doc['execution']
    log=proof_file(root,execution['output_ref'])
    expected=execution.get('output_sha256')
    if not expected or hashlib.sha256(log.read_bytes()).hexdigest()!=expected:
        raise WorkflowError('execution output SHA-256 absent/mismatch')
    for ref in doc.get('evidence_refs',[]):
        proof_file(root,ref)
    if doc['kind']=='qa-report':
        for event in doc['sections']['interactions']:
            proof_file(root,event['evidence_ref'])


class WorkflowError(ValueError):
    pass

def stamp(): return datetime.now(timezone.utc).isoformat()

def safe_id(x: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{2,79}', x):
        raise WorkflowError('invalid ID')
    return x

def write_atomic(path: Path,data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(tmp,path)

def root_guard(root: Path):
    if (root/'.agents/state/STOP').exists():
        raise WorkflowError('STOP switch active: no writes permitted')

def run_dir(root: Path,run_id: str) -> Path:
    return root/'runs'/safe_id(run_id)

def init(root:Path, run_id:str,goal:str,level:int, workflow_mode:str='ENGINEERING_SMALL')->dict:
    root_guard(root)
    if level not in (1,2,3): raise WorkflowError('level 1, 2 or 3')
    if workflow_mode not in MODES: raise WorkflowError('invalid workflow_mode')
    d=run_dir(root,run_id)
    if d.exists(): raise WorkflowError('run already exists')
    state={'version':'5.0','run_id':run_id,'goal':goal,'level':level,'workflow_mode':workflow_mode,'phase':'INTAKE','artifacts':{},'accepted':{},'approvals':{},'corrections':{},'history':[{'at':stamp(),'action':'init'}]}
    write_atomic(d/'state.json',state)
    return state

def read(root:Path,run_id:str)->dict:
    path=run_dir(root,run_id)/'state.json'
    if not path.exists(): raise WorkflowError('run not found')
    return load(path)

def save(root:Path,state:dict):
    root_guard(root)
    write_atomic(run_dir(root,state['run_id'])/'state.json',state)

def submit(root:Path,run_id:str, doc:dict):
    state=read(root,run_id)
    errors=validate(doc)
    if doc.get('run_id')!=run_id: errors.append('run_id mismatch')
    if doc.get('id') in state['artifacts']: errors.append('artifact id already exists: immutable submission')
    if errors: raise WorkflowError('; '.join(errors))
    validate_proof(root,doc)
    artifact_id=safe_id(doc['id'])
    for upstream in doc['input_ids']:
        if upstream not in state['accepted']:
            raise WorkflowError(f'upstream input not independently accepted: {upstream}')
        meta=state['artifacts'][upstream]
        if digest(load(root/meta['path']))!=meta['sha256']:
            raise WorkflowError(f'upstream artifact tampered: {upstream}')
    predecessor_kinds={state['artifacts'][aid]['kind'] for aid in doc['input_ids']}
    missing=INPUT_REQUIREMENTS[doc['kind']]-predecessor_kinds
    if missing:
        raise WorkflowError(f'missing required predecessor kinds: {sorted(missing)}')
        
    if doc['kind'] == 'release':
        builds = set()
        for upstream in doc['input_ids']:
            meta = state['artifacts'][upstream]
            upstream_doc = load(root/meta['path'])
            if meta['kind'] in ('qa-report', 'security-report', 'implementation-review'):
                for inner_up in upstream_doc.get('input_ids', []):
                    inner_meta = state['artifacts'].get(inner_up)
                    if inner_meta and inner_meta['kind'] == 'build':
                        builds.add(inner_up)
        if len(builds) > 1:
            raise WorkflowError('lineage error: release includes reports from diverging builds')
        
    producer_identity = verify_actor_identity(doc['role'])
    
    hash_=digest(doc)
    path=run_dir(root,run_id)/'artifacts'/f'{artifact_id}.json'
    write_atomic(path,doc)
    state['artifacts'][artifact_id]={'kind':doc['kind'],'role':doc['role'],'sha256':hash_,'path':str(path.relative_to(root)),'submitted_at':stamp(), 'producer_identity': producer_identity}
    state['history'].append({'at':stamp(),'action':'submitted','artifact':artifact_id,'role':doc['role']})
    save(root,state)
    return hash_

def review(root:Path,run_id:str,artifact_id:str,reviewer:str,verdict:str,reason:str):
    state=read(root,run_id)
    meta=state['artifacts'].get(artifact_id)
    if not meta: raise WorkflowError('unknown artifact')
    
    if reviewer not in ROLES or reviewer==meta['role'] or reviewer=='orchestrator' or reviewer not in REVIEWERS.get(meta['kind'],set()):
        raise WorkflowError('independent reviewer required; no producer or orchestrator self-approval')
    
    # Identity & Independence Verification
    reviewer_identity = verify_actor_identity(reviewer)
    producer_identity = meta.get('producer_identity', {'assurance': 'UNVERIFIED'})
    
    prod_id = producer_identity.get('agent_id')
    rev_id = reviewer_identity.get('agent_id')
    if prod_id and rev_id and prod_id == rev_id:
        raise WorkflowError('independent reviewer required; same agent instance cannot review its own artifact')
        
    doc = load(root/meta['path'])
    validate_proof(root, doc)
    
    if verdict not in ('ACCEPT','REWORK','REJECT'): raise WorkflowError('invalid review verdict')
    if not reason.strip(): raise WorkflowError('reason required')
    doc=load(root/meta['path'])
    if digest(doc)!=meta['sha256']: raise WorkflowError('artifact modified after submission')
    errors=validate(doc)
    if errors: raise WorkflowError('; '.join(errors))
    if verdict=='ACCEPT':
        if doc.get('verdict') in ('FAIL','BLOCKED','NOT_RUN'):
            raise WorkflowError('cannot accept unsuccessful verification')
        if meta['kind'] in CRITICAL_KINDS:
            if reviewer_identity.get('assurance') != 'VERIFIED' or not verify_independence(producer_identity, reviewer_identity):
                raise WorkflowError(f"critical gate '{meta['kind']}' requires verified independent reviewer; unverified reviewer cannot ACCEPT")
        state['accepted'][artifact_id]={'reviewer':reviewer,'at':stamp(),'reason':reason,'sha256':meta['sha256'], 'reviewer_identity': reviewer_identity}
    else:
        state['accepted'].pop(artifact_id,None)
        key=f"{meta['role']}->{reviewer}:{meta['kind']}"
        state['corrections'][key]=state['corrections'].get(key,0)+1
        if state['corrections'][key]>=3:
            state['phase']='ESCALATED'
            state['escalation']={'reason':f'3 correction cycles on {key}','at':stamp()}
    state['history'].append({'at':stamp(),'action':'review','artifact':artifact_id,'reviewer':reviewer,'verdict':verdict,'reason':reason})
    save(root,state)
    return state['phase']

def approval(root:Path,run_id:str,target:str,decision:str,actor:str,reference:str,expected_sha:str=None,candidate_id:str=None):
    state=read(root,run_id)
    if target not in HUMAN_STATES and target!='MEMORY_WRITE' and target!='ESCALATION_RESOLVED':
        raise WorkflowError('target is not a human-approval gate')
    if actor!='human' or decision not in ('APPROVE','DENY'):
        raise WorkflowError('human actor, valid decision required')
        
    # Check if this reference was already used for another gate in this run
    for existing_target, app in state.get('approvals', {}).items():
        if existing_target != target and app.get('reference') == reference:
            raise WorkflowError(f"replay error: approval reference already used for gate {existing_target}")
            
    # Resolve expected_sha for pertinent gates if not explicitly passed
    if not expected_sha:
        if target == 'BUILD':
            arch_items = [m['sha256'] for aid, m in state.get('artifacts', {}).items() if m.get('kind') == 'architecture' and aid in state.get('accepted', {})]
            if arch_items:
                expected_sha = arch_items[-1]
        elif target == 'RELEASE':
            build_items = [m['sha256'] for aid, m in state.get('artifacts', {}).items() if m.get('kind') == 'build' and aid in state.get('accepted', {})]
            if build_items:
                expected_sha = build_items[-1]
        elif target == 'MEMORY_WRITE' and candidate_id:
            cand_p = run_dir(root, run_id) / 'memory-candidates' / f'{candidate_id}.json'
            if cand_p.exists():
                from .memory import candidate_digest
                cand_data = json.loads(cand_p.read_text(encoding='utf-8'))
                expected_sha = candidate_digest(cand_data)

    if target in ('BUILD', 'RELEASE', 'MEMORY_WRITE') and not expected_sha:
        raise WorkflowError(f"gate '{target}' requires an explicit or state-derived immutable expected_sha (artifact or commit hash)")

    verification = verify_human_approval(reference, target, run_id, expected_sha=expected_sha, expected_candidate_id=candidate_id, root=root)
    
    if verification['status'] == 'PENDING_HUMAN':
        state['approvals'][target]={'actor':actor,'decision':'PENDING_HUMAN','reference':reference,'at':stamp(), 'reason': verification.get('reason')}
        state['history'].append({'at':stamp(),'action':'human_decision_pending','target':target,'reference':reference})
        save(root,state)
        raise WorkflowError(f"APPROVAL_PENDING: {verification.get('reason')}")
        
    comment_url = verification.get('comment_url', reference)
    canonical_id = verification.get('canonical_id')
        
    state['approvals'][target]={
        'actor':verification['actor'],
        'decision':decision,
        'reference':reference,
        'comment_url': comment_url,
        'canonical_id': canonical_id,
        'sha256': expected_sha or verification.get('sha256'),
        'at':stamp(),
        'verified': True,
        'candidate_id': candidate_id or verification.get('candidate_id'),
        'content_sha256': verification.get('content_sha256'),
        'candidate_digest': verification.get('candidate_digest')
    }
    state['history'].append({'at':stamp(),'action':'human_decision','target':target,'decision':decision,'reference':reference})
    save(root,state)

def advance(root:Path,run_id:str,target:str):
    state=read(root,run_id)
    if state['phase'] in ('ESCALATED','PAUSED','CLOSED'):
        raise WorkflowError('run blocked; human intervention required')
    if state['phase'] not in PHASES or target not in PHASES or PHASES.index(target)!=PHASES.index(state['phase'])+1:
        raise WorkflowError('non-sequential or invalid phase transition')
        
    mode = state.get('workflow_mode', 'ENGINEERING_SMALL')
    required_artifacts = MODES[mode].get(target, [])
    
    for kind in required_artifacts:
        items=[(aid,m) for aid,m in state['artifacts'].items() if m['kind']==kind and aid in state['accepted']]
        if not items: raise WorkflowError(f'missing independently accepted artifact: {kind}')
        for aid,m in items:
            if digest(load(root/m['path']))!=m['sha256']:
                raise WorkflowError(f'artifact changed: {aid}')
    if target in HUMAN_STATES:
        approval_record = state['approvals'].get(target,{})
        if approval_record.get('decision')!='APPROVE' or not approval_record.get('verified'):
            raise WorkflowError(f'no recorded verified human approval for {target}')
    state['phase']=target
    state['history'].append({'at':stamp(),'action':'advance','to':target})
    save(root,state)
    return target

def escalate(root:Path,run_id:str,reason:str):
    if not reason.strip(): raise WorkflowError('escalation reason required')
    state=read(root,run_id)
    prev=state['phase'];state['phase']='ESCALATED';state['escalation']={'from':prev,'reason':reason,'at':stamp()}
    state['history'].append({'at':stamp(),'action':'escalate','reason':reason});save(root,state)

def resume(root:Path,run_id:str,reference:str):
    state=read(root,run_id)
    if state['phase']!='ESCALATED':
        raise WorkflowError('run is not in ESCALATED phase')
    if not isinstance(reference, str) or not reference.startswith('https://github.com/'):
        raise WorkflowError('human resolution with GitHub reference needed')
        
    verification = verify_human_approval(reference, 'ESCALATION_RESOLVED', run_id, root=root)
    if verification.get('status') != 'APPROVED':
        raise WorkflowError(f"ESCALATION_RESUME_DENIED: {verification.get('reason', 'unverified reference')}")
        
    phase=state['escalation']['from']
    state['phase']=phase
    state['approvals']['ESCALATION_RESOLVED'] = {
        'actor': verification['actor'],
        'decision': 'APPROVE',
        'reference': reference,
        'at': stamp(),
        'verified': True
    }
    state['history'].append({'at':stamp(),'action':'resume','reference':reference,'to':phase})
    save(root,state)

def resume_package(root:Path,run_id:str)->dict:
    state=read(root,run_id)
    return {'schema':'RESUME_PACKAGE_v5','run_id':run_id,'current_phase':state['phase'],'goal':state['goal'],
      'accepted_artifacts':[{'id':aid,'sha256':meta['sha256'],'path':state['artifacts'][aid]['path']} for aid,meta in state['accepted'].items()],
      'pending_artifacts':[aid for aid in state['artifacts'] if aid not in state['accepted']],
      'approvals':state['approvals'],'correction_counts':state['corrections'],
      'last_events':state['history'][-8:],'instruction':'Revalidate hashes and required artifacts; never infer approvals or test results from this summary.'}
