---
name: org-intake
description: Faz a triagem de uma nova demanda, define Nível 1, 2 ou 3, flags, roster e orçamento, e cria a run. Use ao receber qualquer pedido novo antes de acionar agentes.
---

## Processo de Intake

1. Entenda a demanda em até uma rodada de perguntas ao humano (use `ask_question` se disponível; se não, pergunte em texto). Só pergunte o que mudar o nível ou o escopo.
2. Pontue de 0 a 2 cada critério: reversibilidade (0 fácil de reverter, 2 irreversível), custo do erro, incerteza de demanda, sensibilidade (dados pessoais, jurídico, segurança), esforço estimado. Soma 0 a 3 = Nível 1; 4 a 6 = Nível 2; 7 a 10 = Nível 3.
3. Aplique as elevações de `levels.json`: dado pessoal exige no mínimo Nível 2 e ativa `legal-compliance` e `security-reviewer`; ação irreversível ou gasto acima do limite (hoje: qualquer gasto) exigem Nível 3. Escolha sempre o menor nível que atenda.
4. Defina as flags: `dados_pessoais`, `irreversivel`, `gasto`, `setor_regulado`, `release` (haverá release?).
5. Monte o roster do nível (base mais condicionais cuja condição se aplique) e o orçamento (`invocacoes_max`).
6. Rode `python .agents/scripts/state.py init --slug <slug> --nivel <N> --title "<título>" --flag ...`, preencha `runs/<run>/intake.md` (tipo `intake`: Problema; Critérios de sucesso; Restrições; Flags; Nível; Pontuação da triagem; Orçamento; Roster) e valide com `validate.py intake`.
7. Gate 0 (Nível 2 e 3): `state.py gate-check 0`. Se estiver ambíguo, no máximo mais uma rodada de perguntas.
8. Peça briefing de memória (`python .agents/scripts/memory_ops.py brief --role orchestrator`) e anexe ao `intake.md` só os itens que mudam o escopo.
