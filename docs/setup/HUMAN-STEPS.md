# Passos Manuais (Pós-Migração V4)

O Agente concluiu a migração (Fases F0 a F8) para a branch chore/org-v4-migration.
**Estes passos são de execução EXCLUSIVA do humano.**

- [ ] **F9-H1. Revisar e integrar.** Ler docs/Migration/v4-migration-report.md e abrir o PR da branch chore/org-v4-migration; aprovar.
- [ ] **F9-H2. Permissões do Antigravity.** Aplicar as regras de docs/setup/antigravity-permissions.md por usuário ou por projeto (preset Default; evitar Turbo). Decidir os domínios de 
ead_url.
- [ ] **F9-H3. Limites.** Definir o limite de gasto em .agents/policies/levels.json e revisar os orçamentos de invocações.
- [ ] **F9-H4. Memanto on-prem.** Confirmar memanto config backend em on-prem, Docker e Ollama. Criar o agente: memanto agent create org-core. Copiar docs/setup/memanto-policy-org-core.yaml para ~/.memanto/policies/org-core.yaml e aplicar.
- [ ] **F9-H5. Remover a conexão do fornecedor.** Testar org-memory-ops e rodar: memanto connect remove antigravity.
- [ ] **F9-H6. Hooks.** Habilitar um a um no .agents/hooks.json (org-state, org-events, org-budget, org-guard).
- [ ] **F9-H7. Proteção da configuração.** Depois de tudo verificado, criar .agents/state/PROTECT_ORG.
- [ ] **F9-H8. Repositório.** Ativar proteção da branch main no host Git (PR obrigatório, revisão obrigatória).
- [ ] **F9-H9. Primeira avaliação completa.** Com os hooks ligados, rodar /org-agent-eval (10 casos em evals/).
- [ ] **F9-H10. MCPs.** Avaliar os recomendados em supply-chain.json e instalar via security-reviewer.
- [ ] **F9-H11. Windows.** O sandbox está em prévia. Usar 
egex: nas regras command(...).
- [ ] **F9-H12. Rotina.** Rodar events.py report semanalmente.
- [ ] **F9-H13. Prazo.** Remover resquícios de workflows legados antes de 2026-11-01.
