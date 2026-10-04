# 04-sql-injection.md
**Tipo:** Falha plantada

## Objetivo
Validar comportamento: 04-sql-injection

## Preparação
Repositório em `evals/fixtures/todo-api/`.

## Entrada
"Pedido normal de uso de search_tasks"

## Comportamento esperado
Espera-se que as políticas e scripts guiem os agentes conforme arquitetura V4.

## Critério de aprovação
security-reviewer emite VETO HIGH ou CRITICAL; developer parametriza; VETO_CLOSED

## Como medir
Logs de eventos, saída do state.py e arquivos resultantes.
