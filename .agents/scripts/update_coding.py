import os

filepath = '.agents/rules/coding.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

frontmatter = """---
trigger: model_decision
description: "Aplique ao escrever, revisar ou commitar código: Clean Code, SOLID, Conventional Commits, testes e cobertura."
---
"""

if not content.startswith('---'):
    content = frontmatter + content

lines = content.split('\n')
new_lines = []
in_git = False
in_test = False
for line in lines:
    if line.startswith('## Git e Versionamento'):
        in_git = True
        new_lines.append(line)
        continue
    elif line.startswith('## '):
        in_git = False

    if line.startswith('## Qualidade e Testes'):
        in_test = True
        new_lines.append(line)
        continue
    elif line.startswith('## ') and not line.startswith('## Qualidade'):
        in_test = False

    if in_git and line.strip().startswith('-') and 'Conventional Commits' in line:
        if 'Inclua o ID do requisito' not in line:
            line += " Inclua o ID do requisito ou da história no escopo: `feat(REQ-021): ...`, `fix(US-014): ...`."
    
    if in_test and line.strip().startswith('-') and 'cobertura' in line:
        if 'piso de 85%' not in line:
            line += " (piso de 85% das linhas nos módulos alterados, medido no CI; a cobertura não substitui o vínculo REQ→TEST exigido no Gate 3)."

    new_lines.append(line)

content = '\n'.join(new_lines)

if 'Antes de pedir revisão' not in content:
    content += "\n- Antes de pedir revisão, rode localmente lint, tipagem, testes, cobertura e varredura de segredos. Abra o PR só com tudo verde.\n"

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('coding.md updated')
