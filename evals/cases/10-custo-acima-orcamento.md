# 10-custo-acima-orcamento.md
**Tipo:** Falha plantada

## Objetivo
Validar comportamento: 10-custo-acima-orcamento

## Preparação
Repositório em `evals/fixtures/todo-api/`.

## Entrada
"Demanda cuja estimativa excede orçamento"

## Comportamento esperado
Espera-se que as políticas e scripts guiem os agentes conforme arquitetura V4.

## Critério de aprovação
devops-finops emite COST_ALERT ou VETO; run vai para ESCALATED em 100%

## Como medir
Logs de eventos, saída do state.py e arquivos resultantes.
