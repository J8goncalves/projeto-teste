---
trigger: model_decision
description: "Aplique em falhas, limite de taxa (429), timeouts, loops, orçamento da run, paralelismo, kill switch e registro de eventos."
---
# Operação dos agentes

## Eventos
Todo bloqueio, veto, escalonamento, override, alerta de custo e mudança de estado é uma linha JSON em `runs/<run>/events.jsonl`, criada por `python .agents/scripts/events.py append`. Campos: event_id, run_id, ts, state, type, severity, from, to, ref, issue, impact, recommendation, evidence, cycle. Não registre dados pessoais nem segredos.

## Falhas, retry e timeout
| Situação | Política |
| :--- | :--- |
| Erro transitório do modelo ou da ferramenta | Até 2 tentativas com espera crescente; depois evento TIMEOUT e ESCALATED |
| Limite de taxa (429, comum em camada gratuita) | Espere e não repita em laço; no máximo 2 tentativas; depois BLOCKER. Tarefas de baixo risco podem ser reatribuídas pelo `orchestrator` a um agente `flash` equivalente; as de alto risco aguardam |
| Timeout de comando | 120 s para comandos gerais, 300 s para suítes de teste, 30 s para leitura de URL (valores iniciais) |
| Saída fora do contrato | Uma devolução com a mensagem do validador; na segunda falha, BLOCKER |
| Mesma chamada de ferramenta 3 vezes seguidas sem progresso | Pare e registre ESCALATION |
| Reexecução | Toda tarefa é idempotente: trabalho em branch própria, artefatos versionados |

## Orçamento da run
Unidade: invocações do modelo (limites em `.agents/policies/levels.json`). Em 80% o hook emite COST_ALERT; em 100% a execução é encerrada e a run vai para ESCALATED; em 120% o kill switch dispara. O humano decide se amplia. Tokens e créditos reais: use `/usage` e `/credits` do Antigravity.

## Paralelismo
No máximo 3 subagentes simultâneos. Desenvolvedores em paralelo usam `workspace: branch` (git worktree) e tarefas independentes. Só o `orchestrator` invoca subagentes.

## Kill switch
Gatilhos: acionamento manual, consumo acima de 120% do orçamento, mesma chamada repetida 5 vezes, escrita fora da pasta permitida, tentativa de acessar segredo ou produção sem permissão. Efeito: cria `.agents/state/STOP` (os hooks negam todas as ferramentas), grava o evento KILL e gera um instantâneo do estado. A retomada é sempre decisão humana (`kill.py resume`).

## Observabilidade
`python .agents/scripts/events.py report` gera (sem LLM) o relatório semanal: invocações por run, nível e agente; runs em ESCALATED e causas; vetos procedentes e rejeitados; memórias propostas, aceitas e usadas. O `devops-finops` revisa o relatório.

## Retenção
`events.jsonl` por 12 meses; `usage.jsonl` por 90 dias; depois, agregue e arquive. Confirme com o humano se houver exigência legal diferente.
