---
name: org-v5-memory
description: Retrieve and curate on-prem AI Memory knowledge with human-approved writes and fail-closed semantics.
---
# AI Memory V5.1 (akitaonrails/ai-memory)

- Política: GitHub = registro oficial de decisões, PRDs, ADRs e evidência; `RESUME_PACKAGE_v5` = continuidade de run; AI Memory = índice FTS5 e wiki operacional auxiliar, não fonte da verdade.
- Status real: `python -m org_v5.cli memory-status`. Backend cloud, CLI ausente ou falta de configuração => `DENIED`. **Não simular que a memória funciona**.
- Leitura real: `python -m org_v5.cli memory-brief --role qa --topic "..."`; revise e verifique cada item antes de decidir.
- Proponha por JSON (`memory-propose`) com ID, fonte, tags, confiança, proveniência, tipo e propósito; não grave dados pessoais, segredos, logs ou documentos inteiros.
- Só `memory-promote` após decisão humana com referência GitHub válida e pré-registrada (`approve --target MEMORY_WRITE`). Verifique recibo e faça leitura posterior para confirmar persistência no ambiente real.
- Nunca use comandos diretos de modificação de páginas a partir de agentes; somente o wrapper auditável `org_v5`. Nunca coloque tokens nos logs.
