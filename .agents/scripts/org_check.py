"""V5 bootstrap structure check; no external package dependency."""
import sys
import json
import re
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

hooks_path = root/'.agents'/'hooks.json'
if not hooks_path.exists():
    errors.append('missing hooks.json')
else:
    try:
        hooks = json.loads(hooks_path.read_text(encoding='utf-8'))
        for group_name, group_cfg in hooks.items():
            if not isinstance(group_cfg, dict):
                continue
            for event_key, handlers in group_cfg.items():
                if event_key == "enabled" or not isinstance(handlers, list):
                    continue
                for item in handlers:
                    hook_list = item.get("hooks", []) if isinstance(item, dict) and "hooks" in item else [item]
                    for h in hook_list:
                        if isinstance(h, dict) and h.get("type") == "command":
                            cmd = h.get("command", "")
                            # Check referenced script exists
                            script_match = re.search(r'scripts[\\/]hooks[\\/]([a-zA-Z0-9_\-\.]+)', cmd)
                            if script_match:
                                script_file = root/'.agents'/'scripts'/'hooks'/script_match.group(1)
                                if not script_file.exists():
                                    errors.append(f'hook handler script missing: {script_match.group(1)}')
    except Exception as e:
        errors.append(f'invalid hooks.json syntax: {str(e)}')

for path in ('AGENTS.md','docs/architecture/v5-blueprint.md','org_v5/control.py','org_v5/memory.py'):
    if not (root/path).exists():errors.append(f'missing critical file: {path}')
print(json.dumps({'roles':len(ROLES),'contracts':len(CONTRACTS),'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(1 if errors else 0)
