---
name: org-v5-run
description: Execute agent handoffs through auditable contracts, independent reviews, and execution policies.
---
# Executar run governada V5.2

1. Leia `AGENTS.md`, `docs/architecture/v5-blueprint.md`, `docs/architecture/fase-f-autonomia-e-aprendizado.md` e `org_v5/contracts.py`. Nunca reative scripts V4 antigos.
2. Crie run: `python -m org_v5.cli init --run RUN-EXEMPLO --goal "Objetivo" --level 2 --policy STANDARD|TURBO_SANDBOX`.
   - `TURBO_SANDBOX`: para trabalho em branch de feature/sandbox. Permite avançar `BUILD` e candidato de `RELEASE` automaticamente com evento auditável `POLICY_AUTO_APPROVED`.
   - `STANDARD`: padrão com gates humanos formais via GitHub.
3. Atribua um especialista ao artefato com base no campo `role` do contrato. Antes de pesquisar, recupere memória com `memory-brief`; se offline, marque bloqueio de memória e continue apenas com Git/source autorizado.
4. Requisito de entrada: todos os IDs de `input_ids` devem existir na run e estar `ACCEPT` por papel independente (`prod_id != rev_id`).
5. Envie `python -m org_v5.cli validate <json>` e `submit --run RUN-EXEMPLO <json>`.
6. Revisor de outro papel confere fontes, aceitação, escopo e execução; execute `review --run ... --artifact ... --reviewer ... --verdict ACCEPT|REWORK|REJECT --reason "..."`.
7. Só então `advance --run ... --to ...`. Em `STANDARD`, etapas humanas exigem `approve` com referência real a aprovação GitHub verificada.
8. Três ciclos de correção bloqueiam em `ESCALATED`. Nunca promova progresso omitindo artefatos.
9. Registre eventos de telemetria das invocações e emita o relatório auditável final com `python -m org_v5.cli report --run RUN-EXEMPLO`.
10. Exporte `resume-package` antes de trocar de modelo, janela de contexto ou sessão.
