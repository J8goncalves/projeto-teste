import os
import re
import sys

def check_hygiene():
    agents_dir = '.agents'
    
    TYPE_B_RE = re.compile(r'[\u01ce\u01dd\u01e6\u01fc\u0153\u00a6\u01d8\u01e4\u01f8\u01dc\u01ed\ufffd]')
    TAB_RE = re.compile(r'\t')
    
    errors = []
    
    for root, _, files in os.walk(agents_dir):
        if 'state' in root or 'scripts' in root:
            continue
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if TYPE_B_RE.search(line):
                            errors.append(f'{filepath}:{i+1}: Found mojibake')
                        if '\ufffd' in line:
                            errors.append(f'{filepath}:{i+1}: Found replacement char')
                        if TAB_RE.search(line):
                            errors.append(f'{filepath}:{i+1}: Found literal TAB')
                        if 'ceo-orchestrator' in line.lower():
                            errors.append(f'{filepath}:{i+1}: Found ceo-orchestrator')
                        if 'security-engineer' in line.lower():
                            errors.append(f'{filepath}:{i+1}: Found security-engineer')
                except Exception as e:
                    errors.append(f'Could not read {filepath}: {e}')
                    
    if errors:
        print("Hygiene check failed:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("Hygiene check passed!")

if __name__ == "__main__":
    check_hygiene()
