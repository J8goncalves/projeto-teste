"""Examples: python -m org_v5.cli init --run RUN-DEMO --goal Demo --level 2 --policy TURBO_SANDBOX"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import control, memory, telemetry, git_ops, test_runner
from .contracts import load, validate

def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    p = argparse.ArgumentParser(description='V5.2 governed agent workflow; deny-by-default')
    p.add_argument('--root', default='.', help='project root (contains runs/)')
    sub = p.add_subparsers(dest='action', required=True)
    def addrun(parser): parser.add_argument('--run', required=True)
    
    x = sub.add_parser('init')
    addrun(x)
    x.add_argument('--goal', required=True)
    x.add_argument('--level', type=int, required=True)
    x.add_argument('--mode', default='ENGINEERING_SMALL')
    x.add_argument('--policy', default='STANDARD', choices=['STANDARD', 'TURBO_SANDBOX'])
    
    x = sub.add_parser('status'); addrun(x)
    x = sub.add_parser('report'); addrun(x)
    x = sub.add_parser('validate'); x.add_argument('file')
    x = sub.add_parser('submit'); addrun(x); x.add_argument('file')
    x = sub.add_parser('review'); addrun(x); x.add_argument('--artifact', required=True); x.add_argument('--reviewer', required=True); x.add_argument('--verdict', required=True); x.add_argument('--reason', required=True)
    x = sub.add_parser('approve'); addrun(x); x.add_argument('--target', required=True); x.add_argument('--decision', required=True); x.add_argument('--actor', required=True); x.add_argument('--reference', required=True)
    x = sub.add_parser('advance'); addrun(x); x.add_argument('--to', required=True)
    x = sub.add_parser('escalate'); addrun(x); x.add_argument('--reason', required=True)
    x = sub.add_parser('resolve'); addrun(x); x.add_argument('--reference', required=True)
    x = sub.add_parser('resume-package'); addrun(x)
    x = sub.add_parser('memory-status')
    x = sub.add_parser('memory-brief'); x.add_argument('--role', required=True); x.add_argument('--topic', required=True)
    x = sub.add_parser('memory-propose'); addrun(x); x.add_argument('file')
    x = sub.add_parser('memory-promote'); addrun(x); x.add_argument('--candidate', required=True); x.add_argument('--reference', required=True)
    x = sub.add_parser('memory-promote-core'); addrun(x); x.add_argument('--candidate', required=True); x.add_argument('--commit', required=True)
    x = sub.add_parser('memory-sync-pending'); addrun(x)
    x = sub.add_parser('run-tests')
    x.add_argument('--dir', default='tests')
    x.add_argument('--pattern', default='test*.py')
    x = sub.add_parser('git-check'); addrun(x)
    x.add_argument('--git-action', dest='git_action', required=True, choices=['push', 'merge', 'deploy'])
    x.add_argument('--target-branch')
    x.add_argument('--approval-ref')
    
    a = p.parse_args(argv)
    root = Path(a.root).resolve()
    try:
        if a.action == 'init':
            result = control.init(root, a.run, a.goal, a.level, a.mode, a.policy)
        elif a.action == 'status':
            result = control.read(root, a.run)
        elif a.action == 'report':
            result = telemetry.generate_report(root, a.run)
        elif a.action == 'validate':
            errors = validate(load(Path(a.file)))
            if errors: raise control.WorkflowError('; '.join(errors))
            result = {'valid': True, 'errors': []}
        elif a.action == 'submit':
            result = {'sha256': control.submit(root, a.run, load(Path(a.file)))}
        elif a.action == 'review':
            result = {'phase': control.review(root, a.run, a.artifact, a.reviewer, a.verdict, a.reason)}
        elif a.action == 'approve':
            control.approval(root, a.run, a.target, a.decision, a.actor, a.reference)
            result = {'recorded': True, 'authentication_note': 'GitHub approval must be independently verified'}
        elif a.action == 'advance':
            result = {'phase': control.advance(root, a.run, a.to)}
        elif a.action == 'escalate':
            control.escalate(root, a.run, a.reason)
            result = {'phase': 'ESCALATED'}
        elif a.action == 'resolve':
            control.resume(root, a.run, a.reference)
            result = {'resolved': True}
        elif a.action == 'resume-package':
            result = control.resume_package(root, a.run)
        elif a.action == 'memory-status':
            result = memory.status()
        elif a.action == 'memory-brief':
            result = memory.brief(a.role, a.topic)
        elif a.action == 'memory-propose':
            result = memory.propose(root, a.run, load(Path(a.file)))
        elif a.action == 'memory-promote':
            result = memory.promote(root, a.run, a.candidate, a.reference)
        elif a.action == 'memory-promote-core':
            result = memory.promote_core(root, a.run, a.candidate, a.commit)
        elif a.action == 'memory-sync-pending':
            result = memory.sync_pending_core(root, a.run)
        elif a.action == 'run-tests':
            result = test_runner.run_test_suite(a.dir, pattern=a.pattern, cwd=root)
        elif a.action == 'git-check':
            result = git_ops.verify_git_action_authorization(root, a.git_action, a.target_branch, a.run, a.approval_ref)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as e:
        p.exit(2, 'DENIED: ' + str(e) + '\n')

if __name__ == '__main__':
    main()
