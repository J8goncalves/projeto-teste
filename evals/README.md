# Suíte de Avaliação dos Agentes (Agent CI)

## Como Usar
Execute essa suíte antes de qualquer mudança estrutural na organização (regras, cards, políticas, scripts, hooks). 
- Para rodar um caso manualmente: simule a entrada com o `orchestrator` utilizando o projeto em `evals/fixtures/todo-api/`.
- Nenhuma modificação deve ser mergeada se gerar regressões.

## Formato dos Casos
- **Objetivo**
- **Preparação**
- **Entrada**
- **Comportamento esperado**
- **Critério de aprovação**
- **Como medir**

## Critérios de Aceite
- Nenhuma regressão entre execuções.
- Falhas plantadas detectadas.
- Custo sem aumento acima de 20%.
