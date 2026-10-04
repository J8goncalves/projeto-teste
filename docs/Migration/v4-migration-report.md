# Relatório da migração para a Arquitetura V4

Fonte das decisões: `docs/Migration/PROMPT-antigravity-migracao-v4.md` (versão 1.0, 2026-10-04).
Branch: `chore/org-v4-migration`. Tag do estado inicial: `pre-org-v4`.

## Resumo

Migração em andamento. Fases concluídas abaixo; cada fase tem um commit local (sem `push`).

## Fases concluídas

### F0. Preparação e inventário

**Decisões do humano (P1, 2026-10-04):**

1. Árvore não estava limpa. O humano mandou seguir o padrão do prompt. Para isso, criei a branch `chore/org-v4-migration` e commitei nela as mudanças pendentes do autor como linha de base (`e31b97b chore(org-v4): baseline pre-migracao`). A tag `pre-org-v4` aponta para esse commit. A `main` não foi alterada. Nada foi enviado ao remoto.
2. Python: usar o interpretador do projeto, `.venv\Scripts\python.exe` (CPython 3.14.8, criado com `uv`). `python`, `python3` e `py` do sistema não funcionam (o `python` é o atalho da Microsoft Store).
3. Memanto: o humano informa que o Memanto está rodando local com Ollama e Docker. Veja a divergência em "Ambiente".
4. Cards em subpastas: seguir o prompt, ou seja, mover para `.agents/agents/<nome>.md` (feito na F1).
5. Arquivos inexistentes (por exemplo `company-architecture.md`) podem ser criados; reportar ao final de cada fase.

**Ambiente (somente leitura):**

| Item | Resultado |
| :--- | :--- |
| Sistema operacional | Windows 11 (10.0.26300) |
| Python | `.venv\Scripts\python.exe`, 3.14.8 |
| Git | 2.50.1.windows.1, `core.autocrlf=true` |
| Docker | 28.3.2, em execução. Contêineres: `ollama_ai` (11434), `postgres_knowledge`, `n8n_knowledge_base`, `web_knowledge`, `github-mcp-server` |
| Antigravity | `agy` não está no PATH; versão não detectável |
| `memanto --version` | 0.2.26 (`.venv\Scripts\memanto.exe`; não está no PATH do sistema) |
| `memanto status` / `config show` | Backend `cloud`, API Key não configurada, Server URL `localhost:8000`, agente ativo `none`, sessão inativa, "MEMANTO is not configured". `~/.memanto/` contém apenas `connections.json` |

> Divergência registrada: o humano informa que o Memanto está local com Ollama e Docker, mas o CLI do `.venv` ainda reporta backend `cloud`, sem agente ativo, e não há contêiner do servidor Memanto rodando (só o `ollama_ai`). Possível causa: o servidor e a configuração on-prem estão em outra instalação ou outro perfil. Por orientação do humano, a migração segue; ajustar o backend para on-prem e criar o agente `org-core` são passos humanos (F9-H4). Enquanto isso não for feito, `memory_ops.py status` deve responder `NEGADO`.

**Conferência do esperado (F0.4):**

| Esperado | Encontrado |
| :--- | :--- |
| 15 cards em `.agents/agents/` | 15 cards, mas em subpastas: `business/` (ceo, critical-reviewer, customer-researcher, legal-compliance, market-researcher, marketing-strategist, orchestrator, product-strategist), `engineering/` (architect, developer, devops-finops, product-manager, qa, security), `validation/` (experiment-designer) |
| 9 regras em `.agents/rules/` | 9 regras presentes; só `business-governance.md` tem frontmatter (sem `trigger`) |
| `feature-lifecycle.md` | `.agents/workflows/feature-lifecycle.md` (workflow; tratado em F6.0 e F7-T4) |
| `_TEMPLATE-decision-memo.md` | `intelligence/decisions/_TEMPLATE-decision-memo.md` |
| `company-architecture.md` | Não existe. Será criado na F7-T5 |
| Skill `memanto-memory` do conector | `.agent/skills/memanto/SKILL.md` (pasta `memanto`, `name: memanto-memory`, template 1.0.1) |

**Itens existentes a respeitar (F0.5):**

| Item | Situação |
| :--- | :--- |
| `AGENTS.md`, `GEMINI.md` | Não existem |
| `.agents/hooks.json`, `.agents/mcp_config.json`, `.agents/rules.json` | Não existem |
| `.agents/workflows/` | 1 arquivo: `feature-lifecycle.md` |
| `.agents/skills/` | Não existe |
| Seção `MEMANTO-MANAGED-SECTION` | Não encontrada em nenhum arquivo |
| `.gitignore` | Existe; será mesclado na F1.7 |
| MCP, plugins e skills de terceiros no workspace | Nenhum MCP no workspace; skill de terceiro: `.agent/skills/memanto/` (preexistente) |
| `tasks/`, `evals/` | Não existem |

**Higiene observada (entrada para a F1):** 13 dos 15 cards com BOM (exceto `critical-reviewer` e `market-researcher`); BOM também em `evidence.md`, `governance.md`, `handoffs.md` e `memory.md`. Codificação corrompida em `architect`, `developer`, `marketing-strategist`, `product-manager`, `product-strategist`, `qa` e `security` (Tipo A e Tipo B), como previsto.

**Observação de caminho:** a pasta existente é `docs/Migration/` (M maiúsculo). O prompt usa `docs/migration/`. No Windows os dois nomes são a mesma pasta. Mantive a pasta existente; os arquivos novos ficam nela.

**Criados na F0:** `.agents/scripts/_lib.py` (funções comuns dos scripts), `.agents/scripts/inventory.py`, `docs/Migration/inventory.md`, este relatório.
**Alterados na F0:** nenhum arquivo do projeto (só o commit da linha de base).
**Instalados na F0:** nada.

## Remoções

Nenhuma até o momento.

## Movimentos de conteúdo

Nenhum até o momento.

## Textos reconstruídos

Ver `docs/Migration/encoding-review.md` (a partir da F1).

## Testes e resultados

Pendente (F3 e F8).

## Pendências humanas

Ver `docs/setup/HUMAN-STEPS.md` (F9). Já identificadas: configurar o Memanto on-prem e criar o agente `org-core` (F9-H4).

## Verificação das decisões D01 a D35

Pendente (F8).

## Pressupostos e desvios

- P-01: Baseline das mudanças pendentes commitada na branch de migração antes da tag `pre-org-v4` (decisão do humano em P1).
- P-02: Comando Python dos scripts e hooks: `.venv/Scripts/python.exe` (Windows). Em outro sistema, ajuste para `.venv/bin/python`.
- P-03: Pasta `docs/Migration/` mantida com M maiúsculo.

## F1 - Higienização e CRLF
- Normalização para LF realizada com sucesso.
- Mojibake mecânico corrigido via script.
- Mojibake irreversível (Type B) corrigido via inferência de contexto e registrado em encoding-review.md.
- Problemas de tabulação corrigidos.
- Arquivo .gitignore atualizado.
- Substituições de vocabulário concluídas (ceo-orchestrator -> orchestrator/ceo, security-engineer -> security-reviewer, CONDITIONAL GO -> GO CONDICIONADO).
- O checker de higiene foi criado e passa com sucesso.
