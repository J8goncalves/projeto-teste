# V5.1 — Matriz mínima de testes de regressão e homologação

## Convenções

- `UT`: teste unitário de motor/política, executado com fixtures e injeção de dependência.
- `IT`: integração com executores, filesystem, GitHub, Memanto ou outra ferramenta; requer serviço verdadeiro quando houver aceitação.
- `E2E`: fluxo multiagente e navegador realmente executados, com artefatos e logs.
- `SEC`: controles negativos / políticas de segurança.
- `PERF`: consumo e capacidade sob carga.
- **Nunca classificar UT com mocks como prova E2E.** Cada teste aponta entrada, saída, comando, evidência e commit.

| Caso | Tipo | Ataque ou cenário | Resultado obrigatório |
|---|---|---|---|
| T01 | UT/SEC | Orchestrator submete `kind=security-report` declarando `role=security-reviewer` | DENY se identidade verificada; sem atestação, `UNVERIFIED` e gate bloqueado |
| T02 | UT/SEC | Developer tenta se marcar como QA após criar build | DENY |
| T03 | UT/SEC | Release Manager tenta criar `implementation-review` de outro papel | DENY |
| T04 | UT/SEC | Mesmo `agent_instance_id` produz e revisa artefato, apesar de nomes de papéis diferentes | DENY |
| T05 | IT/SEC | URL GitHub de pessoa não autorizada, outra run ou repositório | DENY |
| T06 | IT/SEC | URL correta, mas aprova commit/artefato anterior | DENY |
| T07 | IT/SEC | Aprovação expirada, revogada ou repetida (nonce reutilizado) | DENY |
| T08 | UT/SEC | `--actor human` sem consulta de identidade | Não satisfaz gate |
| T09 | UT | `ENGINEERING_SMALL` com app local e baixo risco | PRD possível sem pesquisa fictícia; justificativa de aplicabilidade registrada |
| T10 | UT | `PRODUCT_DISCOVERY` sem fontes datadas | Recusa do handoff |
| T11 | UT | Pesquisa com URL válida, mas conteúdo fictício sem verificação | Não alegar fonte verificada; bloquear parecer final até inspeção de conteúdo |
| T12 | UT/SEC | QA PASS com log fabricado e SHA válido | `UNVERIFIED/BLOCKED` na ausência de evidência atestada do executor |
| T13 | IT/E2E | QA real: criar, listar, completar, excluir, validar título vazio; console e trace | Relatório com AC→TEST→EVID, registros de navegador reais e hashes |
| T14 | UT/SEC | QA PASS sem trace/registro de interação | DENY |
| T15 | UT/SEC | `sec-001` só com `Select-String` do Orchestrator | Não receber `PASS` de Security Review; `BLOCKED`/evidência auxiliar |
| T16 | IT/SEC | Security scanner realmente executado na build em questão | Log de ferramenta, versão, command, exit code, achados e revisor independente |
| T17 | UT/SEC | Security PASS de outra SHA de build; relatório revogado/supersedido | DENY RELEASE |
| T18 | UT/SEC | Revisão do `implementation-reviewer` não existe e Release Manager supre o campo | DENY |
| T19 | UT/SEC | Conteúdo de evidência modificado após aceite, embora documento mantenha SHA | DENY por hash do anexo/registro de prova |
| T20 | UT | Terceiro REWORK para mesmo handoff | `ESCALATED`; exige decisão humana |
| T21 | IT | Memanto cloud/offline durante tentativa de write | DENY; fallback controlado para L1 |
| T22 | IT | Memória fictícia com `MEMORY_WRITE` validamente aprovada | Memanto devolve ID; recall recupera e aponta origem/TTL |
| T23 | E2E | Outra sessão/outro modelo usa `RESUME_PACKAGE` e L2 | Confirma IDs, hashes e nuances; sem inventar histórico |
| T24 | IT | Memanto Windows produz `│`, CP1252/UTF-8 e caracteres acentuados | Status correto, sem exceção nem perda de significado |
| T25 | PERF | Carga Ollama provoca pressão de memória ou error 1455 | Limite de concorrência/fallback e saída segura; sem loops nem corrupção |
| T26 | E2E | Um agente falha/recusa auditoria | `BLOCKED`, redelegação permitida, nunca substituição silenciosa de papel |
| T27 | E2E | GitHub API indisponível no gate humano | Fail-closed, `APPROVAL_PENDING`, sem falsa aprovação |
| T28 | UT | Alteração de PRD/ADR após aceitação | Hash mismatch e invalidação de downstream afetado |
| T29 | UT | Testes de governança existentes (pelo menos 21 do piloto) | Permanecem verdes sem remover asserts substantivos |
| T30 | E2E | Novo piloto completo e auditável | `PASS` somente quando P0 e evidências requeridas estão válidas; caso contrário `PARTIAL/FAIL/BLOCKED` |

## Modelo de evidência por teste

Para cada caso registre: `test_id`, `run_id`, `input_artifacts`, `command_or_tool`, `tool_version`, `execution_id`, `expected`, `observed`, `exit_code`, `started_at`, `finished_at`, `git_sha`, `evidence_refs_and_hashes`, `actor_assurance`, `reviewer`, `verdict`, `limitations`. Valores indisponíveis devem constar como **não verificados**, nunca preenchidos por inferência.

## Ordem recomendada

- **Ciclo A (P0):** T01–T10, T15, T17–T18, T27–T28.
- **Ciclo B (P1):** T11–T14, T16, T19–T26.
- **Ciclo C (E2E):** T13, T23, T26, T30 com evidências reais.

**Critério de homologação:** P0 sem falhas; nenhum scanner/E2E/approval fictício; erros e pendências não mascarados como PASS. Se ambiente impedir autenticação de identidade, reporte explicitamente limite de confiança e mantenha decisão humana nos gates críticos.
