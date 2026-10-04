import argparse
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def next_id():
    root = get_workspace_root()
    ids_script = os.path.join(root, '.agents', 'scripts', 'ids.py')
    res = subprocess.run([sys.executable, ids_script, 'next', 'EVID'], capture_output=True, text=True)
    if res.returncode == 0:
        return res.stdout.strip()
    return f"EVID-MOCK-{int(datetime.now().timestamp())}"

def add(args):
    if args.strength == 'E0' and args.type == 'fato':
        print("ERRO: E0 não pode ter --type fato")
        sys.exit(1)
    if args.strength == 'E2' and not args.source.startswith('own:'):
        print("ERRO: E2 exige fonte com marca de dado próprio (own:...)")
        sys.exit(1)
        
    review_by = args.review_by
    if not review_by:
        months = 12 if args.fast_sector else 24
        d = datetime.strptime(args.retrieved, "%Y-%m-%d")
        # simple approx addition of months
        try:
            d = d.replace(year=d.year + months//12, month=(d.month + months%12)%12 or 12)
        except ValueError:
            d = d + timedelta(days=365*(months//12) + 30*(months%12))
        review_by = d.strftime("%Y-%m-%d")
        
    ev_id = next_id()
    record = {
        "id": ev_id,
        "claim": args.claim,
        "type": args.type,
        "strength": args.strength,
        "source": args.source,
        "published": args.published,
        "retrieved": args.retrieved,
        "interpretation": args.interpretation,
        "confidence": args.confidence,
        "owner": args.owner,
        "review_by": review_by,
        "status": "UNVERIFIED"
    }
    
    root = get_workspace_root()
    reg_dir = os.path.join(root, 'intelligence', 'evidence')
    os.makedirs(reg_dir, exist_ok=True)
    reg_file = os.path.join(reg_dir, 'registry.jsonl')
    
    with open(reg_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
    print(ev_id)

def set_status(ev_id, status):
    root = get_workspace_root()
    reg_file = os.path.join(root, 'intelligence', 'evidence', 'registry.jsonl')
    if not os.path.exists(reg_file):
        print("ERRO: registry.jsonl não encontrado")
        sys.exit(1)
        
    lines = []
    found = False
    with open(reg_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            if rec['id'] == ev_id:
                rec['status'] = status
                found = True
            lines.append(json.dumps(rec, ensure_ascii=False))
            
    if found:
        with open(reg_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print("OK")
    else:
        print("ERRO: ID não encontrado")
        sys.exit(1)

def check(min_strength, ids):
    levels = {'E0': 0, 'E1': 1, 'E2': 2}
    req_level = levels.get(min_strength, 0)
    
    root = get_workspace_root()
    reg_file = os.path.join(root, 'intelligence', 'evidence', 'registry.jsonl')
    if not os.path.exists(reg_file):
        print("ERRO: registry.jsonl não encontrado")
        sys.exit(1)
        
    records = {}
    with open(reg_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            rec = json.loads(line)
            records[rec['id']] = rec
            
    for ev_id in ids:
        if ev_id not in records:
            print(f"ERRO: Evidencia {ev_id} não encontrada")
            sys.exit(1)
        rec = records[ev_id]
        if levels.get(rec['strength'], 0) < req_level:
            print(f"ERRO: Evidencia {ev_id} ({rec['strength']}) menor que {min_strength}")
            sys.exit(1)
            
    print("OK")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p_add = subparsers.add_parser('add')
    p_add.add_argument('--claim', required=True)
    p_add.add_argument('--type', choices=['fato', 'estimativa', 'hipotese'], required=True)
    p_add.add_argument('--strength', choices=['E0', 'E1', 'E2'], required=True)
    p_add.add_argument('--source', required=True)
    p_add.add_argument('--published', required=True)
    p_add.add_argument('--retrieved', required=True)
    p_add.add_argument('--interpretation', required=True)
    p_add.add_argument('--confidence', choices=['Alta', 'Média', 'Baixa'], required=True)
    p_add.add_argument('--owner', required=True)
    p_add.add_argument('--review-by')
    p_add.add_argument('--fast-sector', action='store_true')
    
    p_set = subparsers.add_parser('set-status')
    p_set.add_argument('id')
    p_set.add_argument('status', choices=['VERIFIED', 'UNVERIFIED', 'CONTRADICTED', 'OUTDATED', 'SUPERSEDED'])
    
    p_chk = subparsers.add_parser('check')
    p_chk.add_argument('--min', default='E0', choices=['E0', 'E1', 'E2'])
    p_chk.add_argument('ids', nargs='+')
    
    args = parser.parse_args()
    
    if args.command == 'add': add(args)
    elif args.command == 'set-status': set_status(args.id, args.status)
    elif args.command == 'check': check(args.min, args.ids)

if __name__ == '__main__':
    main()
