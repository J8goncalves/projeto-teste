"""V5 bootstrap structure check, policy integrity and dual-gate promotion verifier.
Version 5.2.
"""
import sys
import json
import re
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from org_v5.contracts import ROLES, CONTRACTS

def run_gate_a():
    """
    Gate A: CI Tecnica.
    Verifica integridade de agent cards, skills, hooks.json, scripts de hooks,
    schema e integridade de pretool_rules.json e arquivos criticos da organizacao.
    Sempre executavel de forma isolada sem depender de atestacao final.
    """
    errors = []

    # 1. Agent Cards
    for role in ROLES:
        p = root / '.agents' / 'agents' / f'{role}.md'
        if not p.exists() or 'Definition of Done' not in p.read_text(encoding='utf-8'):
            errors.append(f'agent card missing/incomplete: {role}')

    # 2. Skills
    for skill in ('org-v5-run', 'org-v5-memory', 'org-v5-browser-qa', 'org-v5-research'):
        if not (root / '.agents' / 'skills' / skill / 'SKILL.md').exists():
            errors.append(f'skill missing: {skill}')

    # 3. hooks.json
    hooks_path = root / '.agents' / 'hooks.json'
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
                                script_match = re.search(r'scripts[\\/]hooks[\\/]([a-zA-Z0-9_\-\.]+)', cmd)
                                if script_match:
                                    script_file = root / '.agents' / 'scripts' / 'hooks' / script_match.group(1)
                                    if not script_file.exists():
                                        errors.append(f'hook handler script missing: {script_match.group(1)}')
        except Exception as e:
            errors.append(f'invalid hooks.json syntax: {str(e)}')

    # 4. pretool_rules.json
    rules_path = root / '.agents' / 'policies' / 'pretool_rules.json'
    if not rules_path.exists():
        errors.append('missing pretool_rules.json')
    else:
        try:
            rules_data = json.loads(rules_path.read_text(encoding='utf-8'))
            if not isinstance(rules_data, dict) or rules_data.get("version") != "5.2":
                errors.append('invalid pretool_rules.json: expected version 5.2')
            if not isinstance(rules_data.get("deny_rules"), list):
                errors.append('invalid pretool_rules.json: deny_rules must be a list')
            if not isinstance(rules_data.get("allow_rules"), list):
                errors.append('invalid pretool_rules.json: allow_rules must be a list')
        except Exception as e:
            errors.append(f'invalid pretool_rules.json syntax: {str(e)}')

    # 5. Arquivos criticos
    for path in ('AGENTS.md', 'docs/architecture/v5-blueprint.md', 'org_v5/control.py', 'org_v5/memory.py'):
        if not (root / path).exists():
            errors.append(f'missing critical file: {path}')

    return errors

def main():
    errors = run_gate_a()
    res = {
        'gate': 'GATE_A_TECHNICAL_CI',
        'status': 'PASS' if not errors else 'FAIL',
        'roles': len(ROLES),
        'contracts': len(CONTRACTS),
        'errors': errors
    }
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
