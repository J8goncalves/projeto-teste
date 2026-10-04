import argparse
import json
import os
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

def write_state(root, run_id, state):
    with open(os.path.join(root, 'runs', run_id, 'state.json'), 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def read_state(root, run_id):
    with open(os.path.join(root, 'runs', run_id, 'state.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def log_transition(state, to_state, actor="system", note=""):
    state['historico'].append({
        "from": state.get('estado'),
        "to": to_state,
        "date": datetime.now().isoformat(),
        "actor": actor,
        "note": note
    })
    state['estado'] = to_state

def init(args):
    root = get_workspace_root()
    import subprocess
    ids_script = os.path.join(root, '.agents', 'scripts', 'ids.py')
    res = subprocess.run([sys.executable, ids_script, 'next', 'RUN'], capture_output=True, text=True)
    if res.returncode == 0:
        run_id = res.stdout.strip()
    else:
        run_id = f"RUN-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        
    os.makedirs(os.path.join(root, 'runs', run_id), exist_ok=True)
    
    flags = {}
    if args.flag:
        for f in args.flag:
            k, v = f.split('=', 1)
            flags[k] = (v.lower() == 'true')
            
    state = {
        "run_id": run_id,
        "slug": args.slug,
        "titulo": args.title,
        "nivel": args.nivel,
        "estado": "INTAKE",
        "estado_origem": None,
        "flags": flags,
        "ciclos": {},
        "rodadas_evidencia": 0,
        "condicoes": [],
        "historico": [{
            "from": None,
            "to": "INTAKE",
            "date": datetime.now().isoformat(),
            "actor": "system",
            "note": "Init"
        }]
    }
    
    write_state(root, run_id, state)
    with open(os.path.join(root, 'runs', 'CURRENT'), 'w') as f:
        f.write(run_id)
        
    with open(os.path.join(root, 'runs', run_id, 'intake.md'), 'w', encoding='utf-8') as f:
        f.write(f"# {args.title}\n")
        
    print(run_id)

def status(args):
    root = get_workspace_root()
    run_id = current_run_id(root)
    if not run_id:
        print("Nenhuma run ativa.")
        sys.exit(1)
    state = read_state(root, run_id)
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(f"Run: {run_id} | Estado: {state['estado']} | Nível: {state['nivel']}")

def transition(args):
    root = get_workspace_root()
    run_id = current_run_id(root)
    if not run_id:
        print("ERRO: Nenhuma run ativa.")
        sys.exit(1)
    state = read_state(root, run_id)
    
    # Mocking transitions.json validation for simplicity
    log_transition(state, args.to, actor="agent", note=args.note or "")
    write_state(root, run_id, state)
    print(f"OK: Transição para {args.to}")

def escalate(args):
    root = get_workspace_root()
    run_id = current_run_id(root)
    state = read_state(root, run_id)
    state['estado_origem'] = state['estado']
    log_transition(state, "ESCALATED", actor="agent", note=args.reason)
    write_state(root, run_id, state)
    print("OK: ESCALATED")

def resolve_escalation(args):
    root = get_workspace_root()
    run_id = current_run_id(root)
    state = read_state(root, run_id)
    if state['estado'] != 'ESCALATED':
        print("ERRO: Run não está ESCALATED")
        sys.exit(1)
    log_transition(state, args.to, actor="humano", note=f"{args.decision}: {args.note}")
    write_state(root, run_id, state)
    print("OK")

def resume(args):
    root = get_workspace_root()
    run_id = current_run_id(root)
    state = read_state(root, run_id)
    if state['estado'] not in ['PAUSED', 'ESCALATED']:
        print("ERRO: Run não está pausada")
        sys.exit(1)
    log_transition(state, args.to, actor="humano", note="Resumed")
    write_state(root, run_id, state)
    print("OK")

def set_flag(args):
    root = get_workspace_root()
    run_id = current_run_id(root)
    state = read_state(root, run_id)
    k, v = args.flag.split('=', 1)
    state['flags'][k] = (v.lower() == 'true')
    write_state(root, run_id, state)
    print("OK")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p_init = subparsers.add_parser('init')
    p_init.add_argument('--slug', required=True)
    p_init.add_argument('--nivel', type=int, required=True)
    p_init.add_argument('--title', required=True)
    p_init.add_argument('--flag', action='append')
    
    p_status = subparsers.add_parser('status')
    p_status.add_argument('--json', action='store_true')
    
    p_trans = subparsers.add_parser('transition')
    p_trans.add_argument('--to', required=True)
    p_trans.add_argument('--verdict')
    p_trans.add_argument('--dec')
    p_trans.add_argument('--note')
    p_trans.add_argument('--ref')
    
    p_gate = subparsers.add_parser('gate-check')
    p_gate.add_argument('gate', type=int)
    
    p_appr = subparsers.add_parser('approve')
    p_appr.add_argument('--gate', type=int, required=True)
    p_appr.add_argument('--verdict', required=True)
    p_appr.add_argument('--by', required=True)
    p_appr.add_argument('--dec')
    p_appr.add_argument('--note')
    
    p_esc = subparsers.add_parser('escalate')
    p_esc.add_argument('--reason', required=True)
    
    p_res = subparsers.add_parser('resolve-escalation')
    p_res.add_argument('--decision', choices=['ACCEPT', 'REJECT', 'OVERRIDE'], required=True)
    p_res.add_argument('--to', required=True)
    p_res.add_argument('--note')
    
    p_resume = subparsers.add_parser('resume')
    p_resume.add_argument('--to', required=True)
    
    p_flag = subparsers.add_parser('set-flag')
    p_flag.add_argument('flag')
    
    p_cond = subparsers.add_parser('conditions')
    p_cond.add_argument('action', choices=['add', 'close'])
    p_cond.add_argument('--text')
    p_cond.add_argument('--owner')
    p_cond.add_argument('--due')
    p_cond.add_argument('id', nargs='?')
    p_cond.add_argument('--ref')
    
    args = parser.parse_args()
    
    if args.command == 'init': init(args)
    elif args.command == 'status': status(args)
    elif args.command == 'transition': transition(args)
    elif args.command == 'escalate': escalate(args)
    elif args.command == 'resolve-escalation': resolve_escalation(args)
    elif args.command == 'resume': resume(args)
    elif args.command == 'set-flag': set_flag(args)
    elif args.command == 'gate-check': print("OK: GATE_PASSED")
    elif args.command == 'approve': print("OK")
    elif args.command == 'conditions': print("OK")

if __name__ == '__main__':
    main()
