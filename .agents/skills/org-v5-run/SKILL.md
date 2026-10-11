---
name: org-v5-run
description: Execute agent handoffs through auditable contracts, independent reviews, and execution policies.
---
# Executar run governada V5.2

1. Leia `AGENTS.md`, `docs/architecture/v5-blueprint.md`, `docs/architecture/fase-f-autonomia-e-aprendizado.md` e `org_v5/contracts.py`. Nunca reative scripts V4 antigos.
2. Crie run: `python -m org_v5.cli init --run RUN-EXEMPLO --goal "Objetivo" --level 2 --policy STANDARD|TURBO_SANDBOX`.
   - `TURBO_SANDBOX`: para trabalho em branch de feature/sandbox. Permite avançar `BUILD` e candidato de `RELEASE` automaticamente com evento auditável `POLICY_AUTO_APPROVED`.
   - `STANDARD`: padrão com gates humanos formais via GitHub.
3. **Delegação nativa obrigatória:** Identifique a natureza da demanda. Para toda atividade especializada (pesquisa, estratégia, arquitetura, código, QA, segurança), selecione o papel adequado via `org_v5/contracts.py` e execute `invoke_subagent` nativo do Antigravity antes de qualquer produção de conteúdo. É expressamente proibido simular subagentes via `set_actor_context(...)`, variáveis de ambiente ou execução direta pelo Orquestrador. Antes de pesquisar, recupere memória com `memory-brief`; se offline, marque bloqueio de memória e continue apenas com Git/source autorizado.
4. **Verificação do retorno real:** Somente considere o trabalho executado após receber a resposta do subagente com evidência observável da chamada. Se `invoke_subagent` falhar ou não estiver disponível, registre bloqueio (`DELEGACAO_NAO_EXECUTADA`) em vez de declarar sucesso ou assumir o papel. Em um **teste simples de delegação** sem ciclo de produto completo, não invente documentação nem execute gates desnecessários: basta demonstrar a chamada real ao especialista, o retorno e a distinção clara entre coordenação e trabalho especializado.
5. Requisito de entrada para fluxo governado: todos os IDs de `input_ids` devem existir na run e estar `ACCEPT` por papel independente (`prod_id != rev_id`).
6. Envie `python -m org_v5.cli validate <json>` e `submit --run RUN-EXEMPLO <json>` apenas quando aplicável ao fluxo governado, sempre com dados e evidências verdadeiras.
7. **Revisão independente por subagente:** Acione nova invocação independente para revisão quando o contrato exigir. O revisor (`rev_id != prod_id`) confere fontes, aceitação, escopo e execução real; execute `review --run ... --artifact ... --reviewer ... --verdict ACCEPT|REWORK|REJECT --reason "..."`.
8. Só então `advance --run ... --to ...`. Em `STANDARD`, etapas humanas exigem `approve` com referência real a aprovação GitHub verificada.
9. Três ciclos de correção bloqueiam em `ESCALATED`. Nunca promova progresso omitindo artefatos ou mascarando ausência de delegação.
10. Registre eventos de telemetria das invocações e emita o relatório auditável final com `python -m org_v5.cli report --run RUN-EXEMPLO`.
11. Exporte `resume-package` antes de trocar de modelo, janela de contexto ou sessão.

