# Auditoria da V4 — 2026-10-10

**Fonte verificada:** árvore e conteúdos lidos diretamente do repositório `J8goncalves/projeto-teste`, branch `main`, SHA `f668df03403915cd8a657bac30461f39f51e0846`.

## Achados confirmados

| Gravidade | Arquivo | Falha verificável | Tratamento V5 |
|---|---|---|---|
| CRITICAL | `.agents/scripts/hooks/pretool_guard.py` | arquivo vazio (0 bytes) | hooks não são considerados proteção válida; controles por CLI/CI e permissões externas |
| CRITICAL | `.agents/scripts/state.py` | linha de transição diz explicitamente `# Mocking transitions.json validation for simplicity`; gate-check e approve imprimem OK sem efetuar checks | fluxo V5 com estados sequenciais, documentos aceitos e aprovação registrada |
| CRITICAL | `.agents/scripts/memory_ops.py` | `brief` gera fato fictício; `commit`, `export` retornam OK sem executar | Memanto on-prem real, falha fechada, candidatos e recibo |
| HIGH | `.agents/scripts/tests/test_all.py` | 8 testes `assertTrue(True)` | suíte nova com testes de fluxos positivos/negativos reais |
| HIGH | `.agents/hooks.json` e `.agents/scripts/org_check.py` | hooks enabled:true vs org_check reprova qualquer hook enabled | desativar até teste da configuração de hooks instalada, sem falsa garantia |
| HIGH | `README.md` | descreve estrutura legada, não a atual | README V5 e roteiro de instalação verificável |
| HIGH | `docs/Migration/v4-migration-report.md` | registra Memanto 0.2.26 em backend cloud/não configurado durante migração | gate explícito de integração real |
| MEDIUM | `.agents/scripts/hooks/posttool_events.py`, `postinvocation_budget.py` | imprimem `{}` sem validação funcional | manter hooks desativados, planejar novo teste da IDE |

A V5 **não declara** consertadas as permissões de GitHub, o runtime do Antigravity, o Docker ou o backend Memanto do usuário: estes itens precisam de execução no ambiente real. O relatório V4 declarou vários controles concluídos; a presença de stubs invalida tomar aquelas declarações como prova de efetividade.

## Decisões de migração
- Não apagar histórico de migração V4, arquivos atuais ou decisões anteriores; manter referências para auditoria.
- Arquivos da V4 que podem executar ações falsas são marcados **retired** no overlay e passam a falhar intencionalmente.
- Não ativar hooks até conferir APIs/eventos, caminhos Windows, interação de `deny` e `ask`, bypass por terminais/subagentes, e fail-closed empírico.
- Suíte V5 substitui os placeholders; CI obriga novos testes (se branch protection exigir check).
