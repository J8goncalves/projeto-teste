import os
import re
import urllib.request
import json
from pathlib import Path
from datetime import datetime, timezone

def stamp(): return datetime.now(timezone.utc).isoformat()

_TRUSTED_GITHUB_TOKEN: str | None = None

def set_trusted_github_token(token: str | None):
    global _TRUSTED_GITHUB_TOKEN
    _TRUSTED_GITHUB_TOKEN = token

def get_trusted_github_token() -> str | None:
    """Returns runner-held GITHUB_TOKEN. Never falls back to untrusted os.environ."""
    return _TRUSTED_GITHUB_TOKEN

def get_consumed_approvals_path(root: Path = None) -> Path:
    base = root if root else Path('.')
    return base / '.agents' / 'state' / 'consumed_approvals.json'

def is_approval_consumed(reference_or_canonical: str, root: Path = None) -> bool:
    path = get_consumed_approvals_path(root)
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding='utf-8')
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Anti-replay store corrupted: root must be a dictionary")
        return reference_or_canonical in data
    except Exception as e:
        from .control import WorkflowError
        raise WorkflowError(f"Anti-replay registry read failure (fail-closed): {e}")

import threading
_REGISTRY_LOCK = threading.RLock()

def mark_approval_consumed(reference_or_canonical: str, target: str, run_id: str, root: Path = None):
    with _REGISTRY_LOCK:
        path = get_consumed_approvals_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if path.exists():
            try:
                content = path.read_text(encoding='utf-8')
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError("Anti-replay store corrupted: root must be a dictionary")
            except Exception as e:
                from .control import WorkflowError
                raise WorkflowError(f"Anti-replay registry corruption on write (fail-closed): {e}")
        data[reference_or_canonical] = {'target': target, 'run_id': run_id, 'consumed_at': stamp()}
        tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.{os.urandom(8).hex()}.tmp")
        try:
            tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
            os.replace(tmp, path)
        except Exception as e:
            from .control import WorkflowError
            raise WorkflowError(f"Anti-replay registry write failure (fail-closed): {e}")

def verify_human_approval(
    reference: str, 
    expected_target: str, 
    expected_run_id: str, 
    expected_sha: str = None,
    expected_candidate_id: str = None,
    root: Path = None
) -> dict:
    """
    Validates a human approval by querying the GitHub API.
    Fails closed if it cannot verify.
    Enforces repository identity, authorized approvers, target run/gate, exact hash, and canonical anti-replay.
    Atomically consumes valid approvals within the critical section to prevent TOCTOU replay.
    """
    with _REGISTRY_LOCK:
        if not isinstance(reference, str) or not reference.startswith('https://github.com/'):
            return {'status': 'PENDING_HUMAN', 'reason': 'Invalid reference URL: must be an https://github.com/ URL'}
            
        # Anti-replay check on input reference
        if is_approval_consumed(reference, root):
            return {'status': 'PENDING_HUMAN', 'reason': f'Approval replay detected: reference already consumed ({reference})'}
            
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/(issues|pull)/(\d+)(?:#issuecomment-(\d+))?', reference)
        if not match:
            return {'status': 'PENDING_HUMAN', 'reason': 'Unrecognized GitHub URL format.'}
            
        owner, repo, type_, number, comment_id = match.groups()
        authorized_repo = os.environ.get('AUTHORIZED_GITHUB_REPO', 'J8goncalves/projeto-teste')
        if f"{owner}/{repo}".lower() != authorized_repo.lower():
            return {
                'status': 'PENDING_HUMAN', 
                'reason': f"Cross-repository approval rejected: expected {authorized_repo}, got {owner}/{repo}"
            }

        # If reference contains a comment ID, check canonical key anti-replay early
        if comment_id:
            canonical_key = f"{owner.lower()}/{repo.lower()}#issuecomment-{comment_id}"
            if is_approval_consumed(canonical_key, root):
                return {'status': 'PENDING_HUMAN', 'reason': f'Approval replay detected: canonical comment already consumed ({canonical_key})'}
            
        token = get_trusted_github_token()
        if not token:
            return {'status': 'PENDING_HUMAN', 'reason': 'GITHUB_TOKEN not provided, cannot verify.'}
            
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
        req = urllib.request.Request(api_url, headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OrgV5-Approvals-Verifier'
        })
        
        authorized_approvers = [u.strip().lower() for u in os.environ.get('AUTHORIZED_APPROVERS', 'j8goncalves').split(',') if u.strip()]
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                comments = json.loads(response.read().decode('utf-8'))
                
                for comment in comments:
                    cid = str(comment.get('id', ''))
                    canonical_comment_id = f"{owner.lower()}/{repo.lower()}#issuecomment-{cid}"

                    if is_approval_consumed(canonical_comment_id, root):
                        continue

                    if comment_id and cid != str(comment_id):
                        continue
                        
                    body = comment.get('body', '')
                    author_login = comment.get('user', {}).get('login', '').lower()
                    author_assoc = comment.get('author_association', '')
                    
                    # Check authorized approver identity and association
                    if author_login not in authorized_approvers or author_assoc not in ('OWNER', 'MEMBER', 'COLLABORATOR'):
                        continue
                        
                    # Check for revocation or expiration
                    if 'REVOKED' in body or 'EXPIRED' in body:
                        continue
                        
                    target_match = (f"APPROVE_TARGET: {expected_target}" in body) or (f"TARGET: {expected_target}" in body) or (f"GATE: {expected_target}" in body)
                    run_match = f"RUN_ID: {expected_run_id}" in body
                    decision_match = ("DECISION: APPROVE" in body) or ("APPROVE" in body)
                    
                    if not (target_match and run_match and decision_match):
                        continue
                        
                    if expected_sha and (f"SHA: {expected_sha}" not in body and f"HASH: {expected_sha}" not in body and f"COMMIT: {expected_sha}" not in body):
                        continue
                        
                    if expected_candidate_id and (f"CANDIDATE: {expected_candidate_id}" not in body and f"CANDIDATE_ID: {expected_candidate_id}" not in body):
                        continue
                        
                    cand_match = re.search(r'CANDIDATE(?:_ID)?:\s*([A-Za-z0-9_-]+)', body)
                    content_sha_match = re.search(r'CONTENT_SHA(?:256)?:\s*([a-fA-F0-9]{64})', body)
                    candidate_digest_match = re.search(r'CANDIDATE_DIGEST:\s*([a-fA-F0-9]{64})', body)
                    sha_match = re.search(r'(?:SHA|HASH|COMMIT)(?:_256)?:\s*([a-fA-F0-9]{32,64})', body)
                    
                    comment_url = comment.get('html_url', reference)

                    # Atomically mark consumed within the lock
                    if canonical_comment_id:
                        mark_approval_consumed(canonical_comment_id, expected_target, expected_run_id, root=root)
                    mark_approval_consumed(reference, expected_target, expected_run_id, root=root)
                    if comment_url != reference:
                        mark_approval_consumed(comment_url, expected_target, expected_run_id, root=root)

                    return {
                        'status': 'APPROVED',
                        'actor': comment.get('user', {}).get('login'),
                        'author_association': author_assoc,
                        'verified_at': stamp(),
                        'comment_url': comment_url,
                        'comment_id': cid,
                        'canonical_id': canonical_comment_id,
                        'sha256': sha_match.group(1) if sha_match else None,
                        'candidate_id': cand_match.group(1) if cand_match else None,
                        'content_sha256': content_sha_match.group(1) if content_sha_match else None,
                        'candidate_digest': candidate_digest_match.group(1) if candidate_digest_match else None
                    }
                    
                return {'status': 'PENDING_HUMAN', 'reason': f'No matching valid approval comment found for target {expected_target} in run {expected_run_id}'}
                
        except Exception as e:
            from .control import WorkflowError
            if isinstance(e, WorkflowError):
                raise
            return {'status': 'PENDING_HUMAN', 'reason': f'GitHub API check failed: {str(e)}'}

def verify_and_consume_human_approval(
    reference: str, 
    expected_target: str, 
    expected_run_id: str, 
    expected_sha: str = None,
    expected_candidate_id: str = None,
    root: Path = None
) -> dict:
    """
    Alias for verify_human_approval, which performs atomic verification and consumption.
    """
    return verify_human_approval(
        reference=reference,
        expected_target=expected_target,
        expected_run_id=expected_run_id,
        expected_sha=expected_sha,
        expected_candidate_id=expected_candidate_id,
        root=root
    )
