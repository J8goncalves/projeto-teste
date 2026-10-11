---
trigger: always_on
---
# Governança V5.1.1

1. **Autoridade e Contratos:**
   - `AGENTS.md` e contratos/scripts `org_v5` são a fonte canônica absoluta da organização.
   - Cada etapa exige artefato JSON estruturado, hash SHA-256 e revisão independente.
   - Autoaprovação é terminantemente proibida. O autor de um artefato nunca pode revisá-lo.
2. **Avaliações em Dois Eixos (Evals):**
   - **Eixo 1 (Agent / Runner Evals):** Execução de comandos, papéis, handoffs, detecção de contaminação e recuperação de falha.
   - **Eixo 2 (Product E2E Evals):** Interação real da pessoa com a aplicação em navegador, jornada, fluxo, persistência e acessibilidade (WCAG 2.2 AA).
   - O veredito PASS do Eixo 1 jamais pode ser promovido como PASS do Eixo 2.
3. **Retrospectiva Contínua (Matt Pocock):**
   - Ao final de cada ciclo macro, execute retrospectiva enxuta: `Problema Observado -> Causa Raiz -> Atualização Preventiva -> Evidência de Regressão`.
4. **Fronteira de Confiança e Fail-Closed:**
   - A ferramenta local não autentica humanos: aprovações para gates críticos (`BUILD`, `RELEASE`, `MEMORY_WRITE`) exigem validação criptográfica ou aprovação humana externa no GitHub com anti-replay atômico.
   - Quando a garantia do ator for `UNVERIFIED`, operações críticas permanecem bloqueadas fail-closed.
5. **Resolução de Impasses:**
   - Limite de 2 devoluções no mesmo par papel->revisor. Na 3ª rodada, estado `ESCALATED` obrigatório com intervenção humana.

