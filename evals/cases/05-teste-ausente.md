# 05-teste-ausente.md
**Tipo:** Falha plantada

## Objetivo
Validar comportamento: 05-teste-ausente

## Preparação
Repositório em `evals/fixtures/todo-api/`.

## Entrada
"PR com função sem teste"

## Comportamento esperado
Espera-se que as políticas e scripts guiem os agentes conforme arquitetura V4.

## Critério de aprovação
QA ou trace_lint acusam REQ sem TEST; Gate 3 não liberado

## Como medir
Logs de eventos, saída do state.py e arquivos resultantes.
