---
trigger: always_on
---
# Governança V5.2

1. **Autoridade e Contratos:**
   - `AGENTS.md` e contratos/scripts `org_v5` são a fonte canônica absoluta da organização.
   - Cada etapa exige artefato JSON estruturado, hash SHA-256 e revisão independente.
   - Autoaprovação é terminantemente proibida. O autor de um artefato nunca pode revisá-lo (`prod_id != rev_id`).
2. **Políticas de Execução (`execution_policy`):**
   - **STANDARD:** Política padrão e conservadora. Exige aprovação humana externa verificada no GitHub para entrada em `BUILD`, `RELEASE`, `CLOSED` e `MEMORY_WRITE`.
   - **TURBO_SANDBOX:** Autorizada exclusivamente em feature branches. Permite avanço automático para `BUILD` e pacote candidato de `RELEASE` com evento de política auditável (`POLICY_AUTO_APPROVED`), desde que pré-requisitos e revisões independentes estejam aprovados.
   - **Invariante de Produção:** Deploy em produção e merge na branch `main` permanecem estritamente bloqueados fail-closed em todas as políticas até autorização humana explícita.
3. **Identidade e Revisão em Sandbox:**
   - Subagentes operando localmente sem runner criptográfico isolado são identificados como `UNVERIFIED/ROLE_ONLY`.
   - Em `TURBO_SANDBOX`, revisões de artefatos críticos por instâncias distintas são aceitas como `SANDBOX_PROVISIONAL`. Jamais promover para `VERIFIED` nem utilizar para autorizar produção.
4. **Avaliações em Dois Eixos (Evals):**
   - **Eixo 1 (Agent / Runner Evals):** Execução de comandos, papéis, handoffs, detecção de contaminação e recuperação de falha.
   - **Eixo 2 (Product E2E Evals):** Interação real da pessoa com a aplicação em navegador, jornada, fluxo, persistência e acessibilidade (WCAG 2.2 AA).
   - O veredito PASS do Eixo 1 jamais pode ser promovido como PASS do Eixo 2.
5. **Telemetria e Relatório:**
   - Toda execução deve registrar eventos de invocação em `telemetry/events.jsonl`, auditáveis via `org_v5.cli report`.
   - Métricas não mensuradas pela plataforma devem ser exibidas honestamente como `NÃO MEDIDO`. Ausência de telemetria é rotulada como `NÃO VERIFICÁVEL`.
6. **Resolução de Impasses:**
   - Limite de 2 devoluções no mesmo par papel->revisor. Na 3ª rodada, estado `ESCALATED` obrigatório com intervenção humana.
