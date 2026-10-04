---
name: org-gate
description: Avalia e registra a passagem pelos Gates 0 a 4 e a decisão do Gate 1. Use quando uma run chegar a um gate ou o humano precisar aprovar, reprovar ou decidir.
---

## Procedimento dos Gates

Para cada gate:
- **Gate 0:** Automático.
- **Gate 1:** Humano avalia o Decision Package e decide. No Nível 3, o `ceo` fornece um memo de recomendação com opções A, B, C.
- **Gate 2:** Avaliado via política (ou humano se for uma decisão irreversível/arquitetura crítica).
- **Gate 3 e Gate 4:** Decisão pelo humano.

## Avaliação e Registro
- Avalie o estado do gate com o comando: `python .agents/scripts/state.py gate-check N`
- O que apresentar ao humano (limite de 15 linhas): 
  - Critérios atendidos
  - Vetos ativos ou abertos
  - Nível de evidência
  - Custo atual estimado
  - Riscos identificados
  - Impacto e o que muda se aprovado.
- Como registrar a decisão: `python .agents/scripts/state.py approve --gate N --verdict <veredicto> --dec DEC-### --by humano` (o hook irá pedir a confirmação humana).

## Tratamento dos Vereditos do Gate 1
- **GO:** Prossegue para PLANNING.
- **GO CONDICIONADO:** Prossegue para PLANNING. Condições registradas com `state.py conditions add` (o Gate 2 só passa se forem fechadas).
- **VALIDAR ANTES:** Retorna ao DISCOVERY detalhando explicitamente *o que validar* e sob qual critério.
- **PIVOT:** Retorna ao DISCOVERY exigindo a formulação de uma nova hipótese central.
- **NO-GO:** Encerra a iniciativa e fecha a run (CLOSED).
