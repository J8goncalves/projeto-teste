---
trigger: model_decision
description: "Aplique ao produzir, entregar ou receber um artefato entre agentes e ao declarar uma tarefa concluída: contratos de handoff, Definition of Done e rastreabilidade."
---
# Handoffs Rules
1. Handoffs são contratos. O recebedor DEVE rejeitar se os campos obrigatórios estiverem vazios ou sem evidência. Os campos obrigatórios de cada artefato estão em `.agents/schemas/artifacts.json` e são verificados antes por `python .agents/scripts/validate.py <tipo> <arquivo>`. O recebedor também rejeita o que o validador não enxerga (evidência fraca, ambiguidade).
2. Definition of Done (DoD) Universal: Nenhum agente pode declarar "concluído" sem ter: Fontes registradas, Incertezas explicitadas, Artefato produzido e DoD do receptor atendida.
3. Rastreabilidade Exigida: EVID-001 -> DEC-001 -> REQ-001 -> US-001 -> TEST-001.

4. Passe artefatos por caminho e ID, com resumo de até 10 linhas; não cole conteúdo. O receptor abre o original só se precisar.
5. Ambiguidade vira BLOCKER ao autor; não suponha. A negociação entre `product-manager` e `product-strategist` tem no máximo 2 rodadas; depois, SCOPE_CHANGE ao `orchestrator`.
6. Quem recusa um handoff registra o motivo como evento BLOCKER.
