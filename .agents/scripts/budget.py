import argparse
import json
import os

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def get_current_run(root):
    curr_file = os.path.join(root, 'runs', 'CURRENT')
    if os.path.exists(curr_file):
        with open(curr_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def status(run):
    root = get_workspace_root()
    if not run:
        run = get_current_run(root)
    if not run:
        print("Nenhuma run ativa.")
        return
        
    usage_file = os.path.join(root, 'runs', run, 'usage.jsonl')
    state_file = os.path.join(root, 'runs', run, 'state.json')
    
    used = 0
    if os.path.exists(usage_file):
        with open(usage_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip(): used += 1
                
    nivel = 1
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            nivel = state.get('nivel', 1)
            
    limits_file = os.path.join(root, '.agents', 'policies', 'autonomy.json')
    limit = 100
    if os.path.exists(limits_file):
        with open(limits_file, 'r', encoding='utf-8') as f:
            limits = json.load(f)
            limit = limits.get('niveis', {}).get(str(nivel), {}).get('max_invocations', 100)
            
    pct = (used / limit * 100) if limit > 0 else 0
    print(f"Run {run} - Nível {nivel}")
    print(f"Invocações: {used} / {limit} ({pct:.1f}%)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['status'])
    parser.add_argument('--run', help="Run ID")
    args = parser.parse_args()
    
    if args.command == 'status':
        status(args.run)

if __name__ == '__main__':
    main()
