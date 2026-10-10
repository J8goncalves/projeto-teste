---
trigger: model_decision
description: "Ative em memória, curadoria, transição entre modelos, briefing e pesquisa."
---
# AI Memory V5

Git canônico > pacote de retomada > Memanto semântico. `python -m org_v5.cli memory-status` deve verificar backend local antes de ler ou gravar. Sem conexão: MEMORY_OFFLINE; não invente memória. Sem escrita direta no CLI Memanto. `memory-propose` gera candidato com fonte DEC/EVID, TTL, confiança e minimização; `memory-promote` só com registro explícito de aprovação humana e recibo. Consulte `.agents/skills/org-v5-memory/SKILL.md`.
