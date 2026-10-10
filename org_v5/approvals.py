import os
import re
import urllib.request
import json
from datetime import datetime, timezone

def stamp(): return datetime.now(timezone.utc).isoformat()

def verify_human_approval(reference: str, expected_target: str, expected_run_id: str, expected_sha: str = None) -> dict:
    """
    Validates a human approval by querying the GitHub API.
    Fails closed if it cannot verify.
    """
    if not reference.startswith('https://github.com/'):
        raise ValueError("Invalid reference URL: must be a GitHub URL")
        
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        return {'status': 'PENDING_HUMAN', 'reason': 'GITHUB_TOKEN not provided, cannot verify.'}
        
    # Extract API URL (e.g., https://github.com/owner/repo/issues/1 -> https://api.github.com/repos/owner/repo/issues/1/comments)
    # This is simplified for the sake of the pilot.
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/(issues|pull)/(\d+)', reference)
    if not match:
        return {'status': 'PENDING_HUMAN', 'reason': 'Unrecognized GitHub URL format.'}
        
    owner, repo, type_, number = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    
    req = urllib.request.Request(api_url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            comments = json.loads(response.read().decode('utf-8'))
            
            # Look for a comment that contains the approval payload
            for comment in comments:
                body = comment.get('body', '')
                author_assoc = comment.get('author_association', '')
                if author_assoc not in ('OWNER', 'MEMBER', 'COLLABORATOR'):
                    continue
                    
                if f"APPROVE_TARGET: {expected_target}" in body and f"RUN_ID: {expected_run_id}" in body:
                    if expected_sha and f"SHA: {expected_sha}" not in body:
                        continue
                    
                    return {
                        'status': 'APPROVED',
                        'actor': comment['user']['login'],
                        'author_association': author_assoc,
                        'verified_at': stamp(),
                        'comment_url': comment['html_url']
                    }
            
            return {'status': 'PENDING_HUMAN', 'reason': 'No matching approval comment from authorized collaborator found.'}
            
    except Exception as e:
        return {'status': 'PENDING_HUMAN', 'reason': f'GitHub API check failed: {str(e)}'}
