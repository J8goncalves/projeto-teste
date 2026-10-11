# ORGANIZAÇÃO V5.2 — AUTONOMIA GOVERNADA, IDENTIDADE E APRENDIZADO (substitui instruções V4 e V5.1)

**Objetivo:** validar agentes de produto/marketing/engenharia com handoffs determinísticos, AI Memory sem falsificação, revisão independente, telemetria auditável e gates calibrados por política executável.

1. `org_v5/contracts.py` define formatos, responsáveis e pré-requisitos. `org_v5/control.py` define a máquina de estados V5.2. Artefato sem validação **não** pode ser usado por outro agente. JSON aprovado é imutável e protegido por SHA-256.
2. **Políticas de Execução (`execution_policy`):**
   - `STANDARD` (default): exige aprovação humana verificada via GitHub para `BUILD`, `RELEASE`, `CLOSED` e `MEMORY_WRITE`.
   - `TURBO_SANDBOX`: autorizado exclusivamente em branches de feature/sandbox (proibido em `main` e `master`). Permite avanço automático para `BUILD` e pacote candidato de `RELEASE` com registro de evento de política auditável (`POLICY_AUTO_APPROVED`), desde que pré-requisitos e revisões independentes estejam cumpridos.
   - **Deploy externo e merge em `main` permanecem estritamente bloqueados fail-closed** até aprovação humana explícita verificada.
3. Orquestrador **não executa** pesquisa, arquitetura, implementação, QA, auditoria de segurança nem aprova entregas. Especialistas **não** assumem papéis adjacentes em caso de erro. Revisor nunca é autor do próprio artefato (`prod_id != rev_id`); perfis aceitos estão em `REVIEWERS`.
4. Em ambiente local sem autoridade externa, a garantia de identidade é honestamente registrada como `UNVERIFIED/ROLE_ONLY` ou `SANDBOX_PROVISIONAL`. Jamais forjar garantia `VERIFIED`.
5. Para cada passo, use a skill `.agents/skills/org-v5-run/SKILL.md`. As transições e invocações devem ser registradas na telemetria, auditáveis via `python -m org_v5.cli report --run <RUN_ID>`. Métricas não disponibilizadas pelo runtime (tokens por subagente e custo) devem ser explicitamente exibidas como **NÃO MEDIDO**.
6. Nas pesquisas, exija método, fontes com URL/data/alegação, benchmarking comparável, limitações, risco, custo e razão. Alegações baseadas apenas em experiência empírica são hipóteses.
7. QA deve operar a aplicação REAL no navegador e registrar cliques/formulários, expected/observed, console/rede, outputs de execução e rastreabilidade aos ACs. Nunca promover mocks ou asserts vazios como PASS. Security deve executar scans realmente e registrar logs/evidências.
8. Limite de três devoluções no mesmo par papel→revisor→tipo; na terceira, `ESCALATED`. Debate circular vai ao humano imediatamente. Parada geral: `.agents/state/STOP`.
9. AI Memory em três camadas:
   - Git = decisões e documentos canônicos;
   - `resume-package` = continuidade independente do modelo;
   - AI Memory (`akitaonrails/ai-memory`) local/on-prem = wiki FTS5 e memória operacional auxiliar. Não fingir conexão (`memory-status` obrigatório).
   - **Melhorias comprovadas do Core:** gravadas automaticamente via `memory-promote-core` com base em commit verificado, diff restrito ao core e suíte completa de testes com 100% PASS, sem exigir segunda aprovação humana para memória. Em caso de backend offline, enfileira como `PENDENTE_SINCRONIZACAO` para sincronização idempotente posterior (`memory-sync-pending`).
10. Dados sigilosos e pessoais: minimização, mascaramento, classificação; em caso de incerteza, não enviar a LLM externa nem a logs/artefatos. MCPs somente com privilégio mínimo e aprovação.
11. Antigravity usa perfis como instruções; enforcement existe nos scripts e na CI somente quando invocados; não anuncie que hooks ou permissões do IDE estão protegendo algo sem teste empírico da versão instalada.

**Ler primeiro:** `docs/architecture/v5-blueprint.md`, `docs/architecture/fase-f-autonomia-e-aprendizado.md`, `docs/adr/ADR-005-fase-f-autonomia-e-aprendizado.md`.
