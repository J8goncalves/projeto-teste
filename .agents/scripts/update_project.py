import os

filepath = '.agents/rules/project.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Frontmatter
frontmatter = """---
trigger: always_on
description: "Regras do projeto: colaboração entre agentes, Git, arquitetura, código, segurança e testes."
---
"""

if not content.startswith('---'):
    content = frontmatter + content

# 2. Colaboração Inter-Agentes
lines = content.split('\n')
new_lines = []
in_collab = False
for line in lines:
    if line.startswith('## Colaboração Inter-Agentes'):
        in_collab = True
        new_lines.append(line)
        continue
    
    if in_collab and line.startswith('## '):
        in_collab = False
        
    if in_collab and line.strip().startswith('1.'):
        line += ' Security e DevOps/FinOps participam do DESIGN (modelo de ameaças, requisitos de segurança, custo e observabilidade) antes do Gate 2.'
    elif in_collab and line.strip().startswith('2.'):
        line += ' Em caso de ambiguidade, devolve BLOCKER ao PM; não supõe.'
    elif in_collab and line.strip().startswith('3.'):
        line += ' Depois do CI local verde, QA e Security revisam em paralelo. O merge na branch principal exige aprovação humana (Gate 3).'
    
    new_lines.append(line)

content = '\n'.join(new_lines)

if "Nesta organização, 'autorização'" not in content:
    content = content.replace('## Colaboração Inter-Agentes\n', "## Colaboração Inter-Agentes\nNesta organização, 'autorização' significa aprovação humana registrada num gate (`state.py approve`) ou concedida no prompt de permissão do Antigravity.\n")

if 'Teste de reversibilidade' not in content:
    content = content.replace('## Git', 'Teste de reversibilidade: se desfazer a decisão custa mais de um dia de trabalho ou afeta dados ou contratos, ela é difícil de reverter e exige ADR em `docs/adr/`; caso contrário, justifique no PR.\n\n## Git')

if 'Uma branch por tarefa' not in content:
    content = content.replace('## Code', 'Uma branch por tarefa. Commits seguem Conventional Commits com o ID do requisito no escopo (`feat(REQ-021): ...`). `git push` e merge pedem aprovação humana.\n\n## Code')

if 'Fluxos críticos de interface' not in content:
    content = content.replace('## Security', 'Fluxos críticos de interface têm teste E2E como código commitado (Playwright, quando houver interface web). A exploração manual no navegador complementa e não substitui.\n\n## Security')

if 'Deploy, gasto e acesso a dados pessoais exigem aprovação humana' not in content:
    content += '\nDeploy, gasto e acesso a dados pessoais exigem aprovação humana (ver `autonomy.md`).\n'

if 'Operação dos agentes' not in content:
    content += '\nOperação dos agentes: ver `governance.md`, `operations.md`, `autonomy.md`, `vetoes.md` e `permissions.md`.\n'

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('project.md updated')
