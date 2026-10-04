import os

filepath = '.agents/rules/evidence.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

frontmatter = """---
trigger: model_decision
description: "Aplique ao fazer afirmações factuais, registrar evidências, decidir ou revisar premissas: formato, força E0 a E2, mínimo por nível e status."
---
"""

if not content.startswith('---'):
    content = frontmatter + content

addition = """
5. Registro: `intelligence/evidence/registry.jsonl`, criado por `python .agents/scripts/evidence.py add`. Campos: id, claim, type (fato, estimativa, hipotese), strength (E0, E1, E2), status, source, published_at (data da fonte), retrieved_at, interpretation, confidence (Alta, Média, Baixa), review_by, owner, run_id.
6. Força: E0 = inferência ou opinião sem fonte; E1 = fonte oficial ou secundária citada, com URL e data; E2 = dado próprio (entrevista real, experimento executado, tráfego, vendas, telemetria). "Fonte primária oficial" (ex.: IBGE) é E1; E2 exige dado coletado por nós, registrado com fonte iniciada por `own:` (ex.: `own:experiments/exp-001`).
7. Mínimo por nível (premissas críticas): Nível 1 nenhum; Nível 2 E1; Nível 3 E2, ou aceite de risco assinado pelo humano no memo. E0 nunca sustenta uma decisão: vira hipótese com critério de validação.
8. Confiança: Alta = 0,90 ou mais; Média = 0,70 a 0,89; Baixa = 0,60 a 0,69. Abaixo de 0,60 não se grava em memória.
9. Rótulos de `research-integrity.md` e força: [FATO] ou [DADO] com fonte oficial ou secundária = E1; com dado próprio = E2; [INFERÊNCIA], [OPINIÃO] e [HIPÓTESE] = E0 até serem validadas.
"""

if '5. Registro' not in content:
    content += addition

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('evidence.md updated')
