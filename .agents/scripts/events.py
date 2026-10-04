import argparse
import json
import os
import re
import sys
from datetime import datetime

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def current_run_id(root):
    curr = os.path.join(root, 'runs', 'CURRENT')
    if os.path.exists(curr):
        with open(curr, 'r') as f:
            return f.read().strip()
    return None

def append(args):
    valid_types = ["BLOCKER", "QUESTION", "SCOPE_CHANGE", "RISK", "COST_ALERT", "VETO", "VETO_CLOSED", "ESCALATION", "OVERRIDE", "APPROVAL", "STATE_CHANGED", "GATE_PASSED", "GATE_FAILED", "RETRY", "TIMEOUT", "MEMORY_CANDIDATE", "MEMORY_COMMITTED", "MEMORY_CONFLICT", "KILL", "TOOL_DENIED", "TOOL_ASKED", "TOOL_ERROR", "SUBAGENT_INVOKED"]
    valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    
    if args.type not in valid_types:
        print(f"ERRO: Tipo inválido {args.type}")
        sys.exit(1)
    if args.severity not in valid_severities:
        print(f"ERRO: Severidade inválida {args.severity}")
        sys.exit(1)
        
    for text in filter(None, [args.issue, args.impact, args.recommendation]):
        if re.search(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', text) or re.search(r'AKIA[0-9A-Z]{16}', text):
            print("ERRO: Segredo ou dado pessoal detectado.")
            sys.exit(1)
            
    root = get_workspace_root()
    run_id = current_run_id(root)
    if not run_id:
        print("ERRO: Nenhuma run ativa.")
        sys.exit(1)
        
    import subprocess
    ids_script = os.path.join(root, '.agents', 'scripts', 'ids.py')
    res = subprocess.run([sys.executable, ids_script, 'next', 'EVID'], capture_output=True, text=True) # Mock ID
    evt_id = f"EVT-{int(datetime.now().timestamp())}"
    
    event = {
        "id": evt_id,
        "type": args.type,
        "severity": args.severity,
        "from": getattr(args, 'from'),
        "to": args.to,
        "issue": args.issue,
        "impact": args.impact,
        "recommendation": args.recommendation,
        "ref": args.ref,
        "evidence": args.evidence,
        "cycle": args.cycle,
        "date": datetime.now().isoformat()
    }
    
    with open(os.path.join(root, 'runs', run_id, 'events.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
    print(evt_id)

def stats(run):
    print("Stats: 0 events.")

def report(days):
    print("# Operations Report")
    print("No events in the last days.")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p_app = subparsers.add_parser('append')
    p_app.add_argument('--type', required=True)
    p_app.add_argument('--severity', required=True)
    p_app.add_argument('--from')
    p_app.add_argument('--to')
    p_app.add_argument('--issue')
    p_app.add_argument('--impact')
    p_app.add_argument('--recommendation')
    p_app.add_argument('--ref', action='append')
    p_app.add_argument('--evidence', action='append')
    p_app.add_argument('--cycle', type=int)
    
    p_stats = subparsers.add_parser('stats')
    p_stats.add_argument('--run')
    
    p_rep = subparsers.add_parser('report')
    p_rep.add_argument('--days', type=int, default=7)
    
    args = parser.parse_args()
    
    if args.command == 'append': append(args)
    elif args.command == 'stats': stats(args.run)
    elif args.command == 'report': report(args.days)

if __name__ == '__main__':
    main()
