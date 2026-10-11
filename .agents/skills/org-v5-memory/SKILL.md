---
name: org-v5-memory
description: Retrieve and curate on-prem AI Memory knowledge with human-approved writes and core auto-promotion.
---
# AI Memory V5.2 (akitaonrails/ai-memory)

- Política: GitHub = registro oficial de decisões, PRDs, ADRs e evidência; `RESUME_PACKAGE_v5` = continuidade de run; AI Memory = índice FTS5 e wiki operacional auxiliar, não fonte da verdade.
- Status real: `python -m org_v5.cli memory-status`. Backend cloud, CLI ausente ou falta de configuração => `DENIED`. **Não simular que a memória funciona**.
- Leitura real: `python -m org_v5.cli memory-brief --role <role> --topic "..."`; revise e verifique cada item antes de decidir.
- Proposição: `memory-propose` gera candidato estruturado com ID, fonte, tags, confiança, proveniência, tipo (`learning`, `decision`, `error`) e justificativa (30-400 chars, sem segredos/PII).
- **Promoção padrão (produto/geral):** `memory-promote` após aprovação humana formal no GitHub (`approve --target MEMORY_WRITE`).
- **Promoção automática de Core:** `memory-promote-core --candidate <ID> --commit <SHA>` para melhorias comprovadas no core da organização (`org_v5/**`, `.agents/**`, testes, arquitetura). Valida diff do core e suíte completa de testes com 100% PASS, sem exigir segunda aprovação humana para memória.
- **Tolerância Offline:** se o backend estiver offline, grava na fila `memory-sync-queue/` com status `PENDENTE_SINCRONIZACAO` e sincroniza via `memory-sync-pending` quando restaurado.
- Nunca use comandos diretos de modificação de páginas (`write-page` via MCP/CLI); somente o wrapper auditável `org_v5`.
