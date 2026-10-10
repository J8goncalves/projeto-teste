---
trigger: always_on
---
# Segurança V5

Não exponha segredos, `.env`, credenciais, PII, logs de usuários, tokens, recursos destrutivos nem ferramentas privilegiadas aos modelos. Proteção real requer isolamento IDE/sandbox, escopos MCP, branch protection, checks de CI e aprovação humana. Hooks V4 desativados por falta de validação; não os trate como proteção. Todo scanner deve mostrar comando e evidência; todo teste deve ter execução real. Risco crítico ou impossibilidade de verificar controles => BLOCKED, não PASS. Não realize deploy nem upgrade de custo/escopo sem autorização.
