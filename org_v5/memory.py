"""AI Memory: Git-backed Markdown wiki + SQLite FTS5 index via akitaonrails/ai-memory.

Fails closed if AI Memory is unavailable or misconfigured. Never returns fake memories.
Version 5.2.
"""
from __future__ import annotations
import json
import os
import re
import sys
import hashlib
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from .control import read, run_dir, stamp, write_atomic, WorkflowError, safe_id, root_guard, save, get_current_git_branch

SENSITIVE=[r'AKIA[0-9A-Z]{16}',r'ghp_[A-Za-z0-9]{20,}',r'-----BEGIN .*PRIVATE KEY-----',
  r'[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}',r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
  r'(?i)(api[_-]?key|secret|token|password|senha)\s*[:=]\s*\S+']
TYPES={'fact','decision','learning','error','instruction','commitment','goal'}

CORE_PATTERNS = [
    r'^org_v5/.*\.py$',
    r'^\.agents/rules/.*\.md$',
    r'^\.agents/skills/.*',
    r'^\.agents/agents/.*',
    r'^\.agents/policies/.*',
    r'^tests/test_.*\.py$',
    r'^docs/architecture/.*\.md$',
    r'^docs/adr/.*\.md$',
    r'^AGENTS\.md$'
]

def is_core_path(path_str: str) -> bool:
    normalized = path_str.replace('\\', '/')
    return any(re.search(pat, normalized) for pat in CORE_PATTERNS)

def candidate_digest(candidate: dict, project: str = 'projeto-teste') -> str:
    """
    Computes canonical SHA-256 digest of the entire memory candidate,
    binding id, role, type, text, tags, confidence, provenance, source_ref, reason, and project.
    """
    payload = {
        'id': str(candidate.get('id', '')),
        'role': str(candidate.get('role', '')),
        'type': str(candidate.get('type', '')),
        'text': str(candidate.get('text', '')),
        'tags': sorted(candidate.get('tags', [])),
        'confidence': float(candidate.get('confidence', 0.0)),
        'provenance': str(candidate.get('provenance', '')),
        'source_ref': str(candidate.get('source_ref', '')),
        'reason': str(candidate.get('reason', '')),
        'project': project
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

_PROMOTION_WRITE_AUTHORIZED = False
_TRUSTED_MEMORY_AUTH_TOKEN: str | None = None

def set_trusted_memory_token(token: str | None):
    global _TRUSTED_MEMORY_AUTH_TOKEN
    _TRUSTED_MEMORY_AUTH_TOKEN = token

def get_trusted_memory_token() -> str | None:
    return _TRUSTED_MEMORY_AUTH_TOKEN

class _AuthorizedMemoryWriteContext:
    def __enter__(self):
        global _PROMOTION_WRITE_AUTHORIZED
        _PROMOTION_WRITE_AUTHORIZED = True
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _PROMOTION_WRITE_AUTHORIZED
        _PROMOTION_WRITE_AUTHORIZED = False

def ai_memory_cli(args: list[str], timeout: int = 15) -> str:
    # Intercept direct write attempts outside authorized promote() workflow
    if args and args[0] in ('write-page', 'create-page', 'update-page', 'delete-page', 'write'):
        if not _PROMOTION_WRITE_AUTHORIZED:
            raise WorkflowError(f"Direct write via CLI/MCP forbidden: '{args[0]}' requires human approval and promotion via memory.promote()")
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
    env = os.environ.copy()
    if _TRUSTED_MEMORY_AUTH_TOKEN:
        env['AI_MEMORY_AUTH_TOKEN'] = _TRUSTED_MEMORY_AUTH_TOKEN
    try:
        res = subprocess.run([binary] + args, capture_output=True, text=True, timeout=timeout, check=False, encoding='utf-8', env=env)
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
    if any(k in output.lower() for k in ('server unreachable', 'could not reach', 'refused', 'cloud', 'not configured', '401 unauthorized')):
        raise WorkflowError('AI Memory server is not verifiably reachable/on-prem; writes and recall disabled')
    return {
        'connected': True,
        'backend': 'ai-memory-onprem',
        'server_url': url,
        'status_excerpt': output[:350].encode('ascii', 'replace').decode('ascii')
    }

def is_live_backend_available() -> bool:
    """Checks whether the on-prem AI Memory server and CLI binary are reachable."""
    try:
        s = status()
        return bool(s.get('connected'))
    except Exception:
        return False

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
    if proposal['role'] not in ('memory-curator', 'orchestrator', 'architect', 'developer', 'qa', 'critical-reviewer', 'market-researcher', 'product-manager', 'security-reviewer', 'product-strategist', 'customer-researcher', 'data-analytics', 'implementation-reviewer'):
        raise WorkflowError('role not authorized to propose')
    if not isinstance(proposal['tags'], list) or not 2 <= len(proposal['tags']) <= 5 or not any(t.startswith(('dec-', 'evid-', 'core-')) for t in proposal['tags']):
        raise WorkflowError('2-5 tags and a dec-/evid-/core- provenance tag required')
    if proposal['type'] == 'fact' and not any(t.startswith('ttl-') for t in proposal['tags']):
        raise WorkflowError('fact must include ttl tag')
    if not isinstance(proposal['confidence'], (int, float)) or not 0.7 <= proposal['confidence'] <= 1:
        raise WorkflowError('confidence below 0.7 or above 1')
    if not 30 <= len(proposal['text']) <= 400:
        raise WorkflowError('memory text must be 30-400 characters')
    if not proposal['source_ref'].startswith(('docs/', 'intelligence/', 'runs/', 'tests/', 'org_v5/', '.agents/', 'https://github.com/')):
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
        raise WorkflowError('human memory-write approval with exact matching reference and verified=True required')
    if not decision.get('candidate_id'):
        raise WorkflowError('approval missing mandatory candidate_id binding')
    if decision.get('candidate_id') != candidate_id:
        raise WorkflowError(f"approval is bound to candidate {decision['candidate_id']}, not {candidate_id}")
    if decision.get('promoted'):
        raise WorkflowError('approval reference already consumed for previous memory promotion; reuse prohibited')
        
    root_guard(root)
    safe_id(candidate_id)
    path = run_dir(root, run_id) / 'memory-candidates' / f'{candidate_id}.json'
    if not path.exists():
        raise WorkflowError('candidate missing')
    cand = json.loads(path.read_text(encoding='utf-8'))
    if cand['status'] != 'pending':
        raise WorkflowError('candidate already processed')
        
    cand_digest = candidate_digest(cand)
    cand_text_hash = hashlib.sha256(cand['text'].encode('utf-8')).hexdigest()
    
    expected_digest = decision.get('candidate_digest')
    if not expected_digest:
        raise WorkflowError('approval missing mandatory candidate_digest binding: text hash alone is not accepted')
    if decision.get('content_sha256') and decision.get('content_sha256') != cand_text_hash:
        raise WorkflowError('candidate text modified after approval: content hash mismatch')
    if expected_digest != cand_digest:
        raise WorkflowError('candidate full specification modified after approval: candidate digest mismatch')
        
    status()
    
    page_rel_path = f"memories/{cand['type']}/{cand['id']}.md"
    kind_arg = 'decision' if cand['type'] == 'decision' else 'fact'
    title = f"Memory {cand['id']}: {cand['type']}"
    
    body = (
        f"# {title}\n\n"
        f"**Candidate ID:** `{cand['id']}`  \n"
        f"**Candidate Digest:** `{cand_digest}`  \n"
        f"**Content SHA-256:** `{cand_text_hash}`  \n"
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
        
    with _AuthorizedMemoryWriteContext():
        out = ai_memory_cli(cmd)
    if not out.strip() or 'wrote' not in out.lower():
        raise WorkflowError('AI Memory returned no storage receipt; do not claim persistence')
        
    cand['status'] = 'stored'
    cand['content_sha256'] = cand_text_hash
    cand['candidate_digest'] = cand_digest
    cand['receipt'] = out[:1000]
    cand['stored_at'] = stamp()
    cand['page_path'] = page_rel_path
    write_atomic(path, cand)
    
    decision['promoted'] = True
    decision['promoted_candidate_id'] = candidate_id
    save(root, state)
    
    return {'candidate': candidate_id, 'status': 'stored', 'receipt': out[:1000], 'page_path': page_rel_path}

def promote_core(root: Path, run_id: str, candidate_id: str, commit_sha: str) -> dict:
    """
    Promotes a candidate representing a proven, tested organization core improvement
    without a redundant second human approval, strictly verifying Git commit, core diff,
    and a clean test suite execution.
    """
    root_guard(root)
    safe_id(candidate_id)
    cand_path = run_dir(root, run_id) / 'memory-candidates' / f'{candidate_id}.json'
    if not cand_path.exists():
        raise WorkflowError(f"candidate missing: {candidate_id}")
    cand = json.loads(cand_path.read_text(encoding='utf-8'))
    if cand['status'] != 'pending':
        raise WorkflowError(f"candidate already processed: status is {cand['status']}")
        
    # 1. Verify Git commit exists in repository
    try:
        res_commit = subprocess.run(['git', 'rev-parse', '--verify', commit_sha], cwd=str(root), capture_output=True, text=True, check=False)
    except Exception as e:
        raise WorkflowError(f"Git execution error: {e}")
    if res_commit.returncode != 0:
        raise WorkflowError(f"commit_sha '{commit_sha}' does not exist in git repository")
    full_commit_sha = res_commit.stdout.strip()
    
    # 2. Verify changed files in commit belong to Core allowlist
    res_files = subprocess.run(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', full_commit_sha], cwd=str(root), capture_output=True, text=True, check=False)
    changed_files = [line.strip().replace('\\', '/') for line in res_files.stdout.splitlines() if line.strip()]
    core_changed = [f for f in changed_files if is_core_path(f)]
    if not core_changed:
        raise WorkflowError(f"core improvement rejected: changes in commit {commit_sha[:8]} do not modify organization core files; found non-core changes: {changed_files}")
        
    # 3. Verify commit is ancestor or current HEAD
    res_ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', full_commit_sha, 'HEAD'], cwd=str(root), capture_output=True, text=True, check=False)
    if res_ancestor.returncode != 0:
        raise WorkflowError(f"core improvement rejected: commit {commit_sha[:8]} is not reachable from current HEAD")
        
    # 4. Verify test suite execution in a controlled subprocess
    test_cmd = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests']
    try:
        test_res = subprocess.run(test_cmd, cwd=str(root), capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired as exc:
        raise WorkflowError("core improvement rejected: test suite verification timed out") from exc
    if test_res.returncode != 0:
        raise WorkflowError(f"core improvement rejected: test suite verification failed with exit code {test_res.returncode}:\n{(test_res.stderr or test_res.stdout)[:400]}")
        
    # 5. Branch-bound status label
    curr_branch = get_current_git_branch(root)
    if curr_branch in ('main', 'master'):
        status_label = 'CONSOLIDADA'
    else:
        status_label = 'VALIDADA_EM_BRANCH'
    tier_label = 'semantic'
        
    cand_digest = candidate_digest(cand)
    cand_text_hash = hashlib.sha256(cand['text'].encode('utf-8')).hexdigest()
    
    page_rel_path = f"memories/core/{cand['type']}/{cand['id']}.md"
    kind_arg = 'decision' if cand['type'] == 'decision' else 'fact'
    title = f"Core Memory {cand['id']}: {cand['type']} [{status_label}]"
    
    body = (
        f"# {title}\n\n"
        f"**Candidate ID:** `{cand['id']}`  \n"
        f"**Candidate Digest:** `{cand_digest}`  \n"
        f"**Content SHA-256:** `{cand_text_hash}`  \n"
        f"**Commit SHA:** `{full_commit_sha}`  \n"
        f"**Core Files Changed:** `{', '.join(core_changed)}`  \n"
        f"**Memory Status:** `{status_label}`  \n"
        f"**Branch:** `{curr_branch}`  \n"
        f"**Type:** `{cand['type']}`  \n"
        f"**Role:** `{cand['role']}`  \n"
        f"**Confidence:** `{cand['confidence']}`  \n"
        f"**Provenance:** `{cand['provenance']}`  \n"
        f"**Source Reference:** `{cand['source_ref']}`  \n"
        f"**Run ID:** `{run_id}`  \n\n"
        f"## Statement\n\n"
        f"{cand['text']}\n\n"
        f"## Rationale\n\n"
        f"{cand['reason']}\n"
    )
    
    # 6. Check live backend
    if is_live_backend_available():
        cmd = [
            'write-page',
            '--path', page_rel_path,
            '--title', title,
            '--kind', kind_arg,
            '--tier', tier_label,
            '--body', body,
            '--workspace', 'default',
            '--project', 'projeto-teste'
        ]
        for tag in cand.get('tags', []):
            cmd.extend(['--tag', tag])
        cmd.extend(['--tag', f'commit-{full_commit_sha[:8]}', '--tag', status_label.lower()])
        if status_label != 'CONSOLIDADA':
            cmd.extend(['--tag', 'provisoria'])
        
        with _AuthorizedMemoryWriteContext():
            out = ai_memory_cli(cmd)
        if not out.strip() or 'wrote' not in out.lower():
            raise WorkflowError('AI Memory returned no storage receipt; do not claim persistence')
            
        cand['status'] = 'stored'
        cand['memory_status'] = status_label
        cand['commit_sha'] = full_commit_sha
        cand['content_sha256'] = cand_text_hash
        cand['candidate_digest'] = cand_digest
        cand['receipt'] = out[:1000]
        cand['stored_at'] = stamp()
        cand['page_path'] = page_rel_path
        write_atomic(cand_path, cand)
        
        return {
            'candidate': candidate_id, 
            'status': 'stored', 
            'memory_status': status_label, 
            'receipt': out[:1000], 
            'page_path': page_rel_path,
            'verified_recall': True
        }
    else:
        # Fails closed into idempotent synchronization queue without false persistence claim
        queue_dir = run_dir(root, run_id) / 'memory-sync-queue'
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_path = queue_dir / f'{candidate_id}.json'
        cand_queued = dict(
            cand,
            status='PENDENTE_SINCRONIZACAO',
            memory_status=status_label,
            commit_sha=full_commit_sha,
            core_files_changed=core_changed,
            candidate_digest=cand_digest,
            content_sha256=cand_text_hash,
            queued_at=stamp()
        )
        write_atomic(queue_path, cand_queued)
        cand['status'] = 'PENDENTE_SINCRONIZACAO'
        cand['queue_path'] = str(queue_path.relative_to(root))
        write_atomic(cand_path, cand)
        return {
            'candidate': candidate_id,
            'status': 'PENDENTE_SINCRONIZACAO',
            'queue_path': str(queue_path.relative_to(root)),
            'note': 'AI Memory offline; candidate safely enqueued without false persistence claims'
        }

def sync_pending_core(root: Path, run_id: str) -> list[dict]:
    """Processes any candidates waiting in memory-sync-queue once AI Memory is online."""
    root_guard(root)
    queue_dir = run_dir(root, run_id) / 'memory-sync-queue'
    if not queue_dir.exists():
        return []
    if not is_live_backend_available():
        raise WorkflowError("AI Memory server is offline; cannot sync pending memories")
    synced = []
    for queue_file in sorted(queue_dir.glob('*.json')):
        data = json.loads(queue_file.read_text(encoding='utf-8'))
        cand_id = data['id']
        page_rel_path = f"memories/core/{data['type']}/{data['id']}.md"
        kind_arg = 'decision' if data['type'] == 'decision' else 'fact'
        status_label = data.get('memory_status', 'VALIDADA_EM_BRANCH')
        tier_label = 'semantic'
        title = f"Core Memory {data['id']}: {data['type']} [{status_label}]"
        body = (
            f"# {title}\n\n"
            f"**Candidate ID:** `{data['id']}`  \n"
            f"**Candidate Digest:** `{data.get('candidate_digest')}`  \n"
            f"**Content SHA-256:** `{data.get('content_sha256')}`  \n"
            f"**Commit SHA:** `{data.get('commit_sha')}`  \n"
            f"**Core Files Changed:** `{', '.join(data.get('core_files_changed', []))}`  \n"
            f"**Memory Status:** `{status_label}`  \n"
            f"**Type:** `{data['type']}`  \n"
            f"**Role:** `{data['role']}`  \n"
            f"**Run ID:** `{run_id}`  \n\n"
            f"## Statement\n\n"
            f"{data['text']}\n\n"
            f"## Rationale\n\n"
            f"{data['reason']}\n"
        )
        cmd = [
            'write-page',
            '--path', page_rel_path,
            '--title', title,
            '--kind', kind_arg,
            '--tier', tier_label,
            '--body', body,
            '--workspace', 'default',
            '--project', 'projeto-teste'
        ]
        for tag in data.get('tags', []):
            cmd.extend(['--tag', tag])
        if data.get('commit_sha'):
            cmd.extend(['--tag', f"commit-{data['commit_sha'][:8]}"])
        cmd.extend(['--tag', status_label.lower()])
        if status_label != 'CONSOLIDADA':
            cmd.extend(['--tag', 'provisoria'])
        with _AuthorizedMemoryWriteContext():
            out = ai_memory_cli(cmd)
        if 'wrote' in out.lower():
            cand_path = run_dir(root, run_id) / 'memory-candidates' / f'{cand_id}.json'
            if cand_path.exists():
                c_data = json.loads(cand_path.read_text(encoding='utf-8'))
                c_data['status'] = 'stored'
                c_data['receipt'] = out[:1000]
                c_data['stored_at'] = stamp()
                c_data['page_path'] = page_rel_path
                write_atomic(cand_path, c_data)
            queue_file.unlink()
            synced.append({'candidate': cand_id, 'status': 'stored', 'receipt': out[:1000], 'page_path': page_rel_path})
    return synced
