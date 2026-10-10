"""V5 bootstrap structure check; no external package dependency."""
import sys
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from org_v5.contracts import ROLES, CONTRACTS
errors=[]
for role in ROLES:
    p=root/'.agents'/'agents'/f'{role}.md'
    if not p.exists() or 'Definition of Done' not in p.read_text(encoding='utf-8'):
        errors.append(f'agent card missing/incomplete: {role}')
for skill in ('org-v5-run','org-v5-memory','org-v5-browser-qa','org-v5-research'):
    if not (root/'.agents'/'skills'/skill/'SKILL.md').exists():errors.append(f'skill missing: {skill}')
hooks=json.loads((root/'.agents/hooks.json').read_text(encoding='utf-8'))
if any(isinstance(v,dict) and v.get('enabled') for v in hooks.values()):errors.append('hooks enabled without empirical validation; deny bootstrap')
for path in ('AGENTS.md','docs/architecture/v5-blueprint.md','org_v5/control.py','org_v5/memory.py'):
    if not (root/path).exists():errors.append(f'missing critical file: {path}')
print(json.dumps({'roles':len(ROLES),'contracts':len(CONTRACTS),'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(1 if errors else 0)
