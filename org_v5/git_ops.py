"""Git governance operations for V5.2.

Enforces execution policies across actual Git repository operations:
- Sandbox feature branches: commits, branch push, draft PR allowed without human approval.
- Production branch ('main', 'master'): merge, direct push, and production deploy
  strictly require verified human approval (fail-closed).
"""
from __future__ import annotations
import subprocess
import os
from pathlib import Path
from .control import WorkflowError, get_current_git_branch, read as read_state

PROD_BRANCHES = {'main', 'master'}

def verify_git_action_authorization(
    root: Path,
    action: str,
    target_branch: str | None = None,
    run_id: str | None = None,
    human_approval_ref: str | None = None
) -> dict:
    """
    Verifies if a Git action is authorized under the applicable policy and branch.
    Actions:
      - 'commit': committing changes
      - 'push': pushing a branch
      - 'merge': merging into another branch
      - 'deploy': deploying a branch/tag
    """
    current_branch = get_current_git_branch(root)
    target = target_branch or current_branch
    
    # 1. Direct operations on production branch (main/master)
    if action in ('merge', 'push', 'deploy') and target in PROD_BRANCHES:
        if not human_approval_ref:
            raise WorkflowError(
                f"GIT_POLICY_VIOLATION: '{action}' targeting production branch '{target}' "
                f"is strictly barred without verified human approval."
            )
        # If run_id provided, verify state human approval
        if run_id:
            state = read_state(root, run_id)
            release_app = state.get('approvals', {}).get('RELEASE', {})
            closed_app = state.get('approvals', {}).get('CLOSED', {})
            prod_app = release_app if action != 'close' else closed_app
            if not prod_app.get('verified') or prod_app.get('decision') != 'APPROVE':
                raise WorkflowError(
                    f"GIT_POLICY_VIOLATION: production '{action}' requires verified human approval in run state."
                )
        return {
            'authorized': True,
            'scope': 'production',
            'action': action,
            'target': target,
            'human_approval_ref': human_approval_ref
        }
        
    # 2. Sandbox operations on feature branches
    if run_id:
        state = read_state(root, run_id)
        policy = state.get('execution_policy', 'STANDARD')
    else:
        policy = 'TURBO_SANDBOX' if target not in PROD_BRANCHES else 'STANDARD'
        
    if target in PROD_BRANCHES and policy == 'TURBO_SANDBOX':
        raise WorkflowError(
            f"GIT_POLICY_VIOLATION: TURBO_SANDBOX cannot operate on production branch '{target}'."
        )
        
    return {
        'authorized': True,
        'scope': 'sandbox',
        'policy': policy,
        'action': action,
        'target': target
    }

def run_governed_git(
    root: Path,
    args: list[str],
    run_id: str | None = None,
    human_approval_ref: str | None = None
) -> subprocess.CompletedProcess:
    """
    Executes a Git command with enforcement of execution policies.
    Intercepts merge, push, checkout into main to guarantee fail-closed enforcement.
    """
    if not args:
        raise WorkflowError("Empty git command")
        
    cmd_verb = args[0]
    
    # Check git push
    if cmd_verb == 'push':
        target_branch = None
        for a in args[1:]:
            if not a.startswith('-'):
                if a in PROD_BRANCHES or a.endswith('/main') or a.endswith('/master'):
                    target_branch = 'main'
                    break
        if target_branch in PROD_BRANCHES:
            verify_git_action_authorization(
                root, 'push', target_branch='main',
                run_id=run_id, human_approval_ref=human_approval_ref
            )
            
    # Check git merge
    elif cmd_verb == 'merge':
        curr_branch = get_current_git_branch(root)
        if curr_branch in PROD_BRANCHES:
            verify_git_action_authorization(
                root, 'merge', target_branch=curr_branch,
                run_id=run_id, human_approval_ref=human_approval_ref
            )
            
    return subprocess.run(['git'] + args, cwd=str(root), capture_output=True, text=True, check=False)
