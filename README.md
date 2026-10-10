# Organização V5 — Base de validação de agentes

Este é um overlay para o projeto-teste original. A proposta V5 corrige os principais *false greens* encontrados na V4 e implementa um control plane local, contratos JSON verificáveis, 19 perfis seniorizados, revisão independente, três ciclos máximos, critérios de QA e Security baseados em execução e camada de AI Memory com Memanto local.

## Pré-requisito
Python 3.11+ (`.venv\\Scripts\\python.exe` no Windows do projeto). Sem dependências Python adicionais para o plano de controle e seus testes.

## Teste inicial
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m org_v5.cli --help
.\.venv\Scripts\python.exe -m org_v5.cli memory-status
```

`memory-status` deve **falhar** até que a conexão on-prem ao Memanto seja realmente confirmada; não o desabilite para obter verde falso.

Veja `docs/setup/INSTALL-AND-VERIFY.md`, `docs/architecture/v5-blueprint.md`, `docs/architecture/audit-v4-findings.md` e `docs/prompts/ANTIGRAVITY-BOOTSTRAP.md`.

**Atenção:** copiar um overlay não instala integração do Antigravity nem torna prompts em controles de segurança. Use branch, testes e PR com proteção. Nenhum deploy produtivo automático.
