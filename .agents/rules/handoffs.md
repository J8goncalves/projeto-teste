---
trigger: model_decision
description: "Aplique ao produzir, entregar ou receber um artefato entre agentes: contratos de handoff, fatias verticais, Design Critique e Definition of Done."
---
# Handoffs Rules

1. **Handoffs são Contratos Auditáveis:** O recebedor DEVE rejeitar o artefato se os campos obrigatórios estiverem vazios, sem evidência ou ambíguos. Os schemas em `org_v5/contracts.py` definem a estrutura obrigatória, validada via `python -m org_v5.cli validate <arquivo.json>`.
2. **Fatias Verticais Demonstráveis (Matt Pocock / Paperclip):**
   - Decomponha o trabalho em fatias ponta a ponta (requisito -> interface -> persistência -> teste observável).
   - Concorrência é permitida apenas entre tarefas estritamente independentes.
3. **Protótipo Descartável de UI/Estado (Matt Pocock):**
   - Em caso de incerteza de UX ou máquina de estados, produza protótipo mínimo marcado explicitamente como `PROTOTYPE_NOT_PRODUCTION`.
   - Protótipos servem para validar a premissa de uso e nunca são promovidos diretamente como build de produção sem implementação rigorosa.
4. **Passo de Design Critique (Paperclip):**
   - Avaliação conjunta e objetiva por Product Manager, Developer e QA Independente cobrindo: clareza da ação primária, hierarquia visual, microcopy, estados vazio/carregando/erro/sucesso, responsividade (mobile 390x844 e desktop) e acessibilidade (teclado, foco e contraste).
5. **Revisão de Código em Dois Eixos Explícitos (Matt Pocock):**
   - **Eixo 1 (Standards & Segurança):** Manutenibilidade, ausência de complexidade desnecessária, código limpo, segurança proporcional.
   - **Eixo 2 (Aderência de Produto):** Rastreabilidade direta e atendimento integral dos critérios de aceite do PRD.
6. **Definition of Done (DoD) Universal:**
   - Nenhum agente pode declarar concluído sem: fontes e evidências reais registradas, incertezas explicitadas, artefato validado estruturalmente e aprovação por revisor independente.
7. **Rastreabilidade Exigida:** `EVID -> DEC -> REQ -> US -> TEST -> EXEC`.
8. **Resolução de Impasses:** Máximo de 2 rodadas de devolução no mesmo par; na 3ª rodada, escalação imediata (`ESCALATED`) com intervenção humana. Não crie loops de debate circular.
