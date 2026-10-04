---
name: org-run
description: Conduz uma run governada, estado por estado, conforme o Nível (1, 2 ou 3). Use depois do triage para executar Discovery, planejamento, construção, verificação, release e aprendizado.
---

## Princípios da Run Governada

- Somente o `orchestrator` aciona e governa a run.
- Transições de estado devem ser feitas exclusivamente via `python .agents/scripts/state.py transition <novo_estado>`.
- Máximo de 3 subagentes invocados em paralelo.
- Envie briefings curtos aos agentes (fornecendo caminhos e IDs de artefatos, não o conteúdo completo).
- Valide cada handoff usando `python .agents/scripts/validate.py <artefato>`.
- Registre eventos de run adequadamente e respeite orçamentos, vetos e o limite máximo de ciclos estabelecido.

Leia apenas `references/nivel-N.md` correspondente ao nível da sua run para conduzir as etapas:
- Para Nível 1: `references/nivel-1.md`
- Para Nível 2: `references/nivel-2.md`
- Para Nível 3: `references/nivel-3.md`

## Tratamento de Vereditos (Gate 1)
- **GO e GO CONDICIONADO**: seguem para PLANNING.
  - No GO CONDICIONADO, registre as condições com `state.py conditions add`. O Gate 2 só passa se essas condições forem fechadas (`condicoes_fechadas`).
- **VALIDAR ANTES e PIVOT**: voltam ao DISCOVERY, contando rodada extra. PIVOT exige a formulação de nova hipótese.
- **NO-GO**: fecha a run.

## Comitê, Vetos e Orçamento
- Debate do comitê só com divergência material e máximo de 2 rodadas.
- Siga as regras e diretrizes de vetos em `vetoes.md`.
- Dual-Track é permitido (outra run de Discovery pode correr durante BUILD e VERIFY da run atual).
- Ao final de cada run, produza relatório curto de custo (`python .agents/scripts/budget.py status`).
