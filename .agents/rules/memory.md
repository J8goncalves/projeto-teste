---
trigger: model_decision
description: "Ative em memória, curadoria, transição entre modelos, briefing e pesquisa."
---
# AI Memory V5.2 (akitaonrails/ai-memory)

Git canônico > pacote de retomada > AI Memory FTS5 semântico. `python -m org_v5.cli memory-status` deve verificar backend local (`ai-memory-onprem`) antes de ler ou gravar. Sem conexão: MEMORY_OFFLINE; não invente memória. Sem escrita direta via CLI/MCP.
- **Memórias gerais:** `memory-propose` gera candidato com fonte DEC/EVID, TTL, confiança e minimização; `memory-promote` exige aprovação humana verificada (`MEMORY_WRITE`) e recibo.
- **Melhorias comprovadas do Core:** `memory-promote-core` promove candidatos de aprendizado do core (`org_v5/**`, `.agents/**`, testes, arquitetura) vinculados a commit SHA verificado e suíte completa de testes com 100% PASS, sem exigir segunda aprovação humana para memória.
- **Tolerância Offline:** caso o AI Memory esteja offline durante promoção do core, o candidato é enfileirado com status `PENDENTE_SINCRONIZACAO` e sincronizado idempotentemente via `memory-sync-pending` quando o backend retornar.
Consulte `.agents/skills/org-v5-memory/SKILL.md`.
