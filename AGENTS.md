# ORGANIZAÇÃO V5 — PILOTO GOVERNADO (substitui instruções V4)

**Objetivo:** validar agentes de produto/marketing/engenharia com handoffs determinísticos, AI Memory sem falsificação, revisão independente e gates auditáveis.

1. `org_v5/contracts.py` define formatos, responsáveis e pré-requisitos. `org_v5/control.py` define a máquina de estados. Artefato sem validação **não** pode ser usado por outro agente. JSON aprovado é imutável e protegido por SHA-256.
2. Orquestrador **não executa** pesquisa, arquitetura, implementação, QA, auditoria de segurança nem aprova entregas. Especialistas **não** assumem papéis adjacentes em caso de erro. Revisor nunca é autor do próprio artefato; perfis aceitos estão em `REVIEWERS`.
3. Comece pelo `python -m unittest discover -s tests -v`; rode `python -m org_v5.cli --help`. As rotas V4 de `.agents/scripts/state.py`, `.agents/scripts/memory_ops.py` e demais comandos antigos não são autorizadas para uma run V5.
4. Para cada passo, use a skill `.agents/skills/org-v5-run/SKILL.md`: intake → revisão → discovery → revisão → planejamento/PRD → arquitetura → desenvolvimento/testes → QA interativo + security → release somente com aprovação humana → learn. A transição é registrada no CLI V5.
5. Nas pesquisas, exija método, fontes com URL/data/alegação, benchmarking comparável, limitações, risco, custo e razão. Alegações baseadas apenas em experiência empírica são hipóteses.
6. QA deve operar a aplicação REAL no navegador e registrar cliques/formulários, expected/observed, console/rede, outputs de execução e rastreabilidade aos ACs. Nunca promover mocks ou asserts vazios como PASS. Security deve executar scans realmente e registrar logs/evidências.
7. Limite de três devoluções no mesmo par papel→revisor→tipo; na terceira, `ESCALATED`. Debate circular vai ao humano imediatamente. Parada geral: `.agents/state/STOP`.
8. Aprovações humanas para entrada em BUILD, RELEASE, CLOSED, MEMORY_WRITE; as referências GitHub exigem validação humana externa. Um CLI local **não autentica identidade**, e não substitui branch protection e reviewers do GitHub.
9. AI Memory em três camadas: Git = decisões e documentos canônicos; `resume-package` = continuidade independente do modelo; AI Memory (`akitaonrails/ai-memory`) local/on-prem = wiki FTS5 e memória operacional auxiliar. Não fingir conexão. `memory-status` deve comprovar backend local; sem isso, reporte **MEMORY_OFFLINE**. Escritas por proposta, revisão e aprovação humana.
10. Dados sigilosos e pessoais: minimização, mascaramento, classificação; em caso de incerteza, não enviar a LLM externa nem a logs/artefatos. MCPs somente com privilégio mínimo e aprovação. Não ativar hooks V4 não auditados.
11. Preferência por solução simples: não usar orquestrador externo, event bus, vários frameworks ou vector DB sem medição comparativa justificar.
12. Antigravity usa perfis como instruções; enforcement existe nos scripts e na CI somente quando invocados; não anuncie que hooks ou permissões do IDE estão protegendo algo sem teste empírico da versão instalada.

**Ler primeiro:** `docs/architecture/v5-blueprint.md`, `docs/setup/INSTALL-AND-VERIFY.md` e `docs/prompts/ANTIGRAVITY-BOOTSTRAP.md`.
