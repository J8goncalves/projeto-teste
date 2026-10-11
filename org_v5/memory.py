"""AI Memory: Git-backed Markdown wiki + SQLite FTS5 index via akitaonrails/ai-memory.

Fails closed if AI Memory is unavailable or misconfigured. Never returns fake memories.
"""
from __future__ import annotations
import json
import os
import re
import hashlib
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from .control import read, run_dir, stamp, write_atomic, WorkflowError, safe_id, root_guard, save

SENSITIVE=[r'AKIA[0-9A-Z]{16}',r'ghp_[A-Za-z0-9]{20,}',r'-----BEGIN .*PRIVATE KEY-----',
  r'[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}',r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
  r'(?i)(api[_-]?key|secret|token|password|senha)\s*[:=]\s*\S+']
TYPES={'fact','decision','learning','error','instruction','commitment','goal'}

def ai_memory_cli(args: list[str], timeout: int = 15) -> str:
    binary = os.environ.get('AI_MEMORY_BIN', 'ai-memory')
    if binary == 'ai-memory':
        candidates = [
            Path(__file__).parent.parent / '.venv' / 'Scripts' / 'ai-memory.exe',
            Path(__file__).parent.parent / 'bin' / 'ai-memory.exe',
        ]
        for c in candidates:
            if c.exists():
                binary = str(c)
                break
    try:
        res = subprocess.run([binary] + args, capture_output=True, text=True, timeout=timeout, check=False, encoding='utf-8')
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError('AI Memory CLI offline or timed out: ' + str(exc)) from exc
    if res.returncode != 0:
        raise WorkflowError('AI Memory CLI failed: ' + (res.stderr or res.stdout)[:300])
    return res.stdout

def status() -> dict:
    url = os.environ.get('AI_MEMORY_SERVER_URL', 'http://127.0.0.1:49374')
    try:
        output = ai_memory_cli(['status'], timeout=5)
    except Exception as exc:
        raise WorkflowError('AI Memory server is offline or unreachable; writes and recall disabled') from exc
    if any(k in output.lower() for k in ('server unreachable', 'could not reach', 'refused', 'cloud', 'not configured')):
        raise WorkflowError('AI Memory server is not verifiably reachable/on-prem; writes and recall disabled')
    return {
        'connected': True,
        'backend': 'ai-memory-onprem',
        'server_url': url,
        'status_excerpt': output[:350].encode('ascii', 'replace').decode('ascii')
    }

def brief(role: str, topic: str, limit: int = 5, project: str = 'projeto-teste') -> dict:
    if not role or limit < 1 or limit > 5:
        raise WorkflowError('invalid role or limit')
    status()
    try:
        cmd = ['search', topic or role, '--limit', str(limit), '--json', '--workspace', 'default', '--project', project]
        out = ai_memory_cli(cmd)
        lines = [l for l in out.strip().splitlines() if not l.startswith('202')]
        hits = json.loads('\n'.join(lines)) if lines else []
    except Exception as exc:
        raise WorkflowError('AI Memory search failed: ' + str(exc)) from exc
    return {
        'role': role,
        'topic': topic,
        'source': 'ai-memory',
        'raw_untrusted_memories': json.dumps(hits, indent=2)[:6000],
        'warning': 'Memories are leads, not evidence. Verify in GitHub/source before making decisions.'
    }

def recall(query: str, limit: int = 5, project: str = 'projeto-teste') -> list[dict]:
    status()
    cmd = ['search', query, '--limit', str(limit), '--json', '--workspace', 'default', '--project', project]
    out = ai_memory_cli(cmd)
    lines = [l for l in out.strip().splitlines() if not l.startswith('202')]
    return json.loads('\n'.join(lines)) if lines else []

def propose(root: Path, run_id: str, proposal: dict) -> dict:
    state = read(root, run_id)
    necessary = ('id', 'role', 'type', 'text', 'tags', 'confidence', 'provenance', 'source_ref', 'reason')
    if any(not proposal.get(k) for k in necessary):
        raise WorkflowError('memory proposal missing mandatory fields')
    if proposal['type'] not in TYPES:
        raise WorkflowError('unsupported memory type')
    if proposal['role'] not in ('memory-curator', 'orchestrator', 'architect', 'developer', 'qa', 'critical-reviewer', 'market-researcher', 'product-manager', 'security-reviewer', 'product-strategist', 'customer-researcher', 'data-analytics'):
        raise WorkflowError('role not authorized to propose')
    if not isinstance(proposal['tags'], list) or not 2 <= len(proposal['tags']) <= 5 or not any(t.startswith(('dec-', 'evid-')) for t in proposal['tags']):
        raise WorkflowError('2-5 tags and a dec-/evid- provenance tag required')
    if proposal['type'] == 'fact' and not any(t.startswith('ttl-') for t in proposal['tags']):
        raise WorkflowError('fact must include ttl tag')
    if not isinstance(proposal['confidence'], (int, float)) or not 0.7 <= proposal['confidence'] <= 1:
        raise WorkflowError('confidence below 0.7 or above 1')
    if not 30 <= len(proposal['text']) <= 400:
        raise WorkflowError('memory text must be 30-400 characters')
    if not proposal['source_ref'].startswith(('docs/', 'intelligence/', 'runs/', 'https://github.com/')):
        raise WorkflowError('immutable provenance reference required')
    if any(re.search(p, proposal['text']) for p in SENSITIVE):
        raise WorkflowError('possible personal data, credential or secret in memory')
    root_guard(root)
    safe_id(proposal['id'])
    path = run_dir(root, run_id) / 'memory-candidates' / f"{proposal['id']}.json"
    if path.exists():
        raise WorkflowError('duplicate candidate ID')
    write_atomic(path, dict(proposal, run_id=run_id, status='pending', created_at=stamp()))
    return {'candidate': proposal['id'], 'status': 'pending', 'note': 'not yet stored in AI Memory'}

def promote(root: Path, run_id: str, candidate_id: str, approval_ref: str) -> dict:
    state = read(root, run_id)
    decision = state['approvals'].get('MEMORY_WRITE', {})
    if decision.get('decision') != 'APPROVE' or decision.get('reference') != approval_ref or not decision.get('verified'):
        raise WorkflowError('human memory-write approval with exact matching reference required')
    if decision.get('promoted'):
        raise WorkflowError('approval reference already consumed for previous memory promotion; reuse prohibited')
    if decision.get('candidate_id') and decision.get('candidate_id') != candidate_id:
        raise WorkflowError(f"approval is bound to candidate {decision['candidate_id']}, not {candidate_id}")
        
    root_guard(root)
    safe_id(candidate_id)
    path = run_dir(root, run_id) / 'memory-candidates' / f'{candidate_id}.json'
    if not path.exists():
        raise WorkflowError('candidate missing')
    cand = json.loads(path.read_text(encoding='utf-8'))
    if cand['status'] != 'pending':
        raise WorkflowError('candidate already processed')
        
    cand_hash = hashlib.sha256(cand['text'].encode('utf-8')).hexdigest()
    if decision.get('content_sha256') and decision.get('content_sha256') != cand_hash:
        raise WorkflowError('candidate text modified after approval: content hash mismatch')
        
    status()
    
    # Store directly into AI Memory wiki page
    page_rel_path = f"memories/{cand['type']}/{cand['id']}.md"
    kind_arg = 'decision' if cand['type'] == 'decision' else 'fact'
    title = f"Memory {cand['id']}: {cand['type']}"
    
    body = (
        f"# {title}\n\n"
        f"**Candidate ID:** `{cand['id']}`  \n"
        f"**Content SHA-256:** `{cand_hash}`  \n"
        f"**Type:** `{cand['type']}`  \n"
        f"**Role:** `{cand['role']}`  \n"
        f"**Confidence:** `{cand['confidence']}`  \n"
        f"**Provenance:** `{cand['provenance']}`  \n"
        f"**Source Reference:** `{cand['source_ref']}`  \n"
        f"**Approval Reference:** `{approval_ref}`  \n"
        f"**Run ID:** `{run_id}`  \n\n"
        f"## Statement\n\n"
        f"{cand['text']}\n\n"
        f"## Rationale\n\n"
        f"{cand['reason']}\n"
    )
    
    cmd = [
        'write-page',
        '--path', page_rel_path,
        '--title', title,
        '--kind', kind_arg,
        '--tier', 'semantic',
        '--body', body,
        '--workspace', 'default',
        '--project', 'projeto-teste'
    ]
    for tag in cand.get('tags', []):
        cmd.extend(['--tag', tag])
        
    out = ai_memory_cli(cmd)
    if not out.strip() or 'wrote' not in out.lower():
        raise WorkflowError('AI Memory returned no storage receipt; do not claim persistence')
        
    cand['status'] = 'stored'
    cand['content_sha256'] = cand_hash
    cand['receipt'] = out[:1000]
    cand['stored_at'] = stamp()
    cand['page_path'] = page_rel_path
    write_atomic(path, cand)
    
    decision['promoted'] = True
    decision['promoted_candidate_id'] = candidate_id
    save(root, state)
    
    return {'candidate': candidate_id, 'status': 'stored', 'receipt': out[:1000], 'page_path': page_rel_path}
