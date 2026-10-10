---
name: org-v5-run
description: Execute agent handoffs through auditable contracts and independent reviews.
---
# Executar run governada V5

1. Leia `AGENTS.md`, `docs/architecture/v5-blueprint.md` e `org_v5/contracts.py`. Nunca reative scripts V4 antigos.
2. Crie run: `python -m org_v5.cli init --run RUN-EXEMPLO --goal "Objetivo" --level 2`.
3. Atribua um especialista ao artefato com base no campo `role` do contrato. Antes de pesquisar, recupere memória com `memory-brief`; se offline, marque bloqueio de memória e continue apenas com Git/source autorizado.
4. Requisito de entrada: todos os IDs de `input_ids` devem existir na run e estar `ACCEPT` por papel independente.
5. Envie `python -m org_v5.cli validate <json>` e `submit --run RUN-EXEMPLO <json>`.
6. Revisor de outro papel confere fontes, aceitação, escopo e execução; execute `review --run ... --artifact ... --reviewer ... --verdict ACCEPT|REWORK|REJECT --reason "..."`.
7. Só então `advance --run ... --to ...`; etapas com aprovação humana exigem `approve` com referência real a aprovação GitHub (deve ser verificada externamente).
8. Três ciclos de correção bloqueiam em ESCALATED. Nunca promova progresso omitindo artefatos.
9. Exporte `resume-package` antes de trocar de modelo, janela de contexto ou sessão. Verifique identificadores e SHA de origem ao retornar.
