---
name: org-agent-eval
description: Executa a suíte de avaliação dos agentes (Agent CI) antes de mudanças em cards, regras, políticas, hooks ou skills. Use sempre que for alterar a configuração da organização de agentes.
---

## Quando Rodar
Sempre que houver alteração em `.agents/**` (hooks, scripts, regras, policies, cards de agente, skills) ou no documento `AGENTS.md`. Nenhuma mudança de configuração de agentes pode ser mesclada sem essa execução.

## Como Rodar
- Utilize os casos definidos em `evals/cases/`. Cada caso possui:
  - Entrada
  - Comportamento esperado
  - Critério de aprovação
- Utilize o repositório descartável sem credenciais reais presente em `evals/fixtures/` para rodar os testes.

## Critérios de Aceite para a Mudança
- **Sem regressões:** Todas as avaliações que passavam antes devem continuar passando.
- **Detecção:** Todas as "falhas plantadas" nos casos de teste devem ser detectadas pelo respectivo agente ou sistema validador.
- **Custo:** O custo médio por run não pode apresentar aumento superior a 20% sem que exista justificativa material.

## Registro e Aprovação
- O registro dos resultados deve ser salvo em `evals/results/AAAA-MM-DD.md`.
- Toda mudança estrutural deve ser revisada pelo `security-reviewer` e aprovada via Pull Request pelo humano antes do merge.
