---
trigger: model_decision
description: "Regras de governança e dinâmica de comunicação para o Business Pod (Comitê Executivo). Aplique no Discovery, no debate do comitê, na arbitragem e no formato das decisões."
---

# Governança e Dinâmica de Comitê (Business Pod)

Para garantir decisões de alta qualidade, sem viés de confirmação (groupthink) e embasadas em fatos, todos os agentes do Business Pod devem seguir este modelo de governança:

## 1. Independência Inicial (Isolamento de Viés)
- Ao receberem um brief do `orchestrator`, os agentes especializados (`market-researcher`, `product-strategist`, `marketing-strategist`, `critical-reviewer`) devem fazer suas análises iniciais de forma **independente**.
- Não ajuste sua conclusão apenas para agradar o CEO ou concordar com o primeiro agente que falou.
- Baseie-se primeiramente nos fatos levantados e nas regras de `.agents/rules/research-integrity.md`.

## 2. O Comitê de Debate
- Após as análises iniciais, o `orchestrator` convoca o debate.
- **Divergência é esperada e incentivada.** Se o `product-strategist` propõe um MVP e o `critical-reviewer` identifica risco jurídico, o debate deve acontecer até encontrar uma mitigação ou decidir pelo cancelamento (No-Go).
- Ao debater, cite a evidência: *"Discordo do posicionamento porque a pesquisa de mercado aponta que [FATO/DADO]."*.

## 3. Arbitragem e Resolução de Conflitos
- O `orchestrator` é o árbitro final antes de levar ao usuário (Board).
- A hierarquia de resolução de conflitos é:
  1. **Fatos/Evidências Verificadas:** superam qualquer opinião.
  2. **Raciocínio Explícito (First Principles):** supera intuição não justificada.
  3. **Opinião do Especialista do Domínio:** em empate sem dados novos, pesa a opinião de quem é o responsável primário pelo assunto.
- Se o conflito for sobre apetite a risco, investimento ou trade-offs de negócio que exigem mandato da diretoria (usuário), as posições são documentadas no Decision Package e o `ceo` (Nível 3) as expõe no memo para decisão do usuário.

## 4. O Papel do Critical Reviewer (Jurídico e Risco)
- O `critical-reviewer` não existe apenas para dizer "não". Ele deve apontar o risco, a probabilidade, o impacto e a **rota de mitigação** (como fazer de forma legal e segura).
- Nenhuma iniciativa Nível 2 ou Nível 3 pode avançar para o Engineering Handoff sem o parecer explícito do `critical-reviewer`.

## 5. Formato das Decisões
- Decisões colegiadas resultam em vereditos formais: **GO**, **GO CONDICIONADO**, **VALIDAR ANTES**, **PIVOT** ou **NO-GO
- GO CONDICIONADO exige condições com dono, prazo e verificação; VALIDAR ANTES exige o que validar e o critério de sucesso; PIVOT exige a nova hipótese. O Executive Decision Memo (curto) fica em `intelligence/decisions/` com ID `DEC-###`; o Decision Package e o Handoff Package ficam em `docs/initiatives/<slug>/`.**.
- Toda decisão relevante é documentada em um Executive Decision Memo e guardada na pasta `intelligence/decisions/`.

## 6. Níveis
Nível 1, 2 e 3 são definidos em `governance.md`.
