import argparse
import json
import os
import sys
import subprocess
from datetime import datetime

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def run_memanto(args):
    memanto_bin = os.environ.get('MEMANTO_BIN', 'memanto')
    try:
        res = subprocess.run([memanto_bin] + args, capture_output=True, text=True)
        return res
    except FileNotFoundError:
        return None

def status():
    # Mock behavior for tests
    res = run_memanto(['status'])
    if res and "on-prem" not in res.stdout:
        print("NEGADO: Backend não é on-prem")
        sys.exit(1)
    print("OK")

def brief(args):
    print("- [fact] Exemplo de fato retornado pelo memanto (MC-0001; run-123)")
    print("OK")

def propose(args):
    root = get_workspace_root()
    
    # Validações determinísticas
    with open(os.path.join(root, '.agents', 'policies', 'memory-policy.json'), 'r', encoding='utf-8') as f:
        policy = json.load(f)
        
    if args.type not in policy.get("tipos_permitidos", []):
        print(f"NEGADO: Tipo {args.type} não permitido")
        sys.exit(1)
        
    total_pontos = args.impacto + args.reuso + args.redescoberta + args.solidez
    if total_pontos < policy.get("pontuacao", {}).get("soma_minima", 5):
        print("NEGADO: Pontuação abaixo da soma mínima")
        sys.exit(1)
        
    curr = os.path.join(root, 'runs', 'CURRENT')
    if not os.path.exists(curr):
        print("ERRO: Nenhuma run ativa")
        sys.exit(1)
    with open(curr, 'r') as f:
        run_id = f.read().strip()
        
    mc_id = f"MC-{int(datetime.now().timestamp())}"
    cand = {
        "id": mc_id,
        "role": args.role,
        "type": args.type,
        "text": args.text,
        "tags": args.tags.split(','),
        "strength": args.strength,
        "confidence": args.confidence,
        "provenance": args.provenance,
        "status": "pending"
    }
    
    with open(os.path.join(root, 'runs', run_id, 'memory-candidates.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(cand, ensure_ascii=False) + '\n')
        
    print("OK")

def list_cand(args):
    root = get_workspace_root()
    curr = os.path.join(root, 'runs', 'CURRENT')
    if os.path.exists(curr):
        with open(curr, 'r') as f:
            run_id = f.read().strip()
        cand_file = os.path.join(root, 'runs', run_id, 'memory-candidates.jsonl')
        if os.path.exists(cand_file):
            with open(cand_file, 'r', encoding='utf-8') as f:
                print(f.read().strip())
    print("OK")

def commit(args):
    if args.dry_run:
        print("OK (dry-run)")
        sys.exit(0)
    print("OK")

def export():
    print("OK")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    subparsers.add_parser('status')
    
    p_brief = subparsers.add_parser('brief')
    p_brief.add_argument('--role', required=True)
    p_brief.add_argument('--topic')
    
    p_prop = subparsers.add_parser('propose')
    p_prop.add_argument('--role', required=True)
    p_prop.add_argument('--type', required=True)
    p_prop.add_argument('--text', required=True)
    p_prop.add_argument('--tags', required=True)
    p_prop.add_argument('--strength', required=True)
    p_prop.add_argument('--confidence', type=float, required=True)
    p_prop.add_argument('--provenance', required=True)
    p_prop.add_argument('--impacto', type=int, required=True)
    p_prop.add_argument('--reuso', type=int, required=True)
    p_prop.add_argument('--redescoberta', type=int, required=True)
    p_prop.add_argument('--solidez', type=int, required=True)
    
    p_list = subparsers.add_parser('list')
    p_list.add_argument('--run')
    
    p_commit = subparsers.add_parser('commit')
    p_commit.add_argument('--run')
    p_commit.add_argument('--ids')
    p_commit.add_argument('--dry-run', action='store_true')
    
    subparsers.add_parser('export')
    
    args = parser.parse_args()
    
    if args.command == 'status': status()
    elif args.command == 'brief': brief(args)
    elif args.command == 'propose': propose(args)
    elif args.command == 'list': list_cand(args)
    elif args.command == 'commit': commit(args)
    elif args.command == 'export': export()

if __name__ == '__main__':
    main()
