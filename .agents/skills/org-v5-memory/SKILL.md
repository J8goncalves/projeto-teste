---
name: org-v5-memory
description: Retrieve and curate on-prem Memanto knowledge with human-approved writes and fail-closed semantics.
---
# AI Memory V5

- Política: GitHub = registro oficial de decisões, PRDs, ADRs e evidência; `RESUME_PACKAGE_v5` = continuidade de run; Memanto = índice semântico operacional auxiliar, não fonte da verdade.
- Status real: `python -m org_v5.cli memory-status`. Backend cloud, CLI ausente ou falta de configuração => `DENIED`. **Não simular que a memória funciona**.
- Leitura real: `python -m org_v5.cli memory-brief --role qa --topic "..."`; revise e verifique cada item antes de decidir.
- Proponha por JSON (`memory-propose`) com ID, fonte, tags, confiança, proveniência, tipo e propósito; não grave dados pessoais, segredos, logs ou documentos inteiros.
- Só `memory-promote` após decisão humana com referência GitHub válida e pré-registrada (`approve --target MEMORY_WRITE`). Verifique recibo e faça leitura posterior para confirmar persistência no ambiente real.
- Nunca use `memanto remember`, `edit`, `forget`, `connect` ou `memory sync` diretamente a partir de agentes; somente o wrapper auditável. Nunca coloque tokens nos logs.
- Atenção: a opção `--tool antigravity` e outros argumentos precisam ser confrontados com `memanto --help` da versão instalada antes do primeiro uso produtivo.
