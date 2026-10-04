import os

filepath = '.agents/rules/handoffs.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

frontmatter = """---
trigger: model_decision
description: "Aplique ao produzir, entregar ou receber um artefato entre agentes e ao declarar uma tarefa concluída: contratos de handoff, Definition of Done e rastreabilidade."
---
"""

if not content.startswith('---'):
    content = frontmatter + content

lines = content.split('\n')
new_lines = []
for line in lines:
    if line.strip().startswith('1.'):
        if 'Os campos obrigatórios' not in line:
            line += " Os campos obrigatórios de cada artefato estão em `.agents/schemas/artifacts.json` e são verificados antes por `python .agents/scripts/validate.py <tipo> <arquivo>`. O recebedor também rejeita o que o validador não enxerga (evidência fraca, ambiguidade)."
    elif line.strip().startswith('2.'):
        if 'DoD do receptor' not in line:
            line += " A 'DoD do receptor' é a seção Definition of Done do card do agente que recebe."
    elif line.strip().startswith('3.'):
        if 'EVID-001 -> DEC-001' not in line:
            line = "3. Rastreabilidade ponta a ponta. EVID-001 -> DEC-001 -> REQ-001 -> US-001 -> TEST-001 -> COMMIT -> REL. SRC (fonte) alimenta EVID; MEM (memória) aponta para DEC ou EVID. Commits levam o ID no escopo (`feat(REQ-021): ...`). `python .agents/scripts/trace_lint.py` lista os órfãos."
    new_lines.append(line)

content = '\n'.join(new_lines)

if '4. Passe artefatos por caminho e ID' not in content:
    content += "\n4. Passe artefatos por caminho e ID, com resumo de até 10 linhas; não cole conteúdo. O receptor abre o original só se precisar.\n"
    content += "5. Ambiguidade vira BLOCKER ao autor; não suponha. A negociação entre `product-manager` e `product-strategist` tem no máximo 2 rodadas; depois, SCOPE_CHANGE ao `orchestrator`.\n"
    content += "6. Quem recusa um handoff registra o motivo como evento BLOCKER.\n"

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('handoffs.md updated')
