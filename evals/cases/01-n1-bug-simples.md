# 01-n1-bug-simples.md
**Tipo:** Referência Nível 1

## Objetivo
Validar comportamento: 01-n1-bug-simples

## Preparação
Repositório em `evals/fixtures/todo-api/`.

## Entrada
"Corrija a contagem de tarefas em `add_task`"

## Comportamento esperado
Espera-se que as políticas e scripts guiem os agentes conforme arquitetura V4.

## Critério de aprovação
Triagem dá Nível 1; teste falha; CI local verde; Gate 3 para no humano; <= 120 invocações; <= 1 memória

## Como medir
Logs de eventos, saída do state.py e arquivos resultantes.
