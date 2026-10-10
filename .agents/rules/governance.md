---
trigger: always_on
---
# Governança V5

Em caso de divergência, `AGENTS.md` V5 e contratos/scripts `org_v5` prevalecem sobre documentos de migração V4 arquivados. Não use `.agents/scripts/state.py` e `.agents/scripts/validate.py` antigos (substituídos por falha fechada). Cada etapa exige artefatos JSON submetidos, hash e revisão independente; nunca se autoaprove, invente evidências ou passe gate sem validação. ESCALATED na terceira devolução ao mesmo par; escalar antes se houver risco material. A ferramenta local não autentica humanos: sempre conferir o approve real no GitHub protegido.
