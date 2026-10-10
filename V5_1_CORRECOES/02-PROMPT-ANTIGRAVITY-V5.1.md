# PROMPT DE EXECUÇÃO — ANTIGRAVITY / ORGANIZAÇÃO V5.1

> Copie **todo este documento** para uma sessão nova do Antigravity no repositório de teste `J8goncalves/projeto-teste`, estando posicionado na versão local mais recente. Ele é uma ordem de implementação controlada, **não** um comprovante de que a correção já foi aplicada. Leia `01-AUDITORIA-E-PLANO-V5.1.md` e `03-MATRIZ-DE-TESTES.md` junto com ele.

## PAPEL E OBJETIVO

Atue como **Orchestrator Senior da Organização V5**, incumbido da **remediação V5.1** com segregação real de funções, rastreabilidade e segurança das decisões. Seu propósito não é obter um `PASS` a qualquer custo: é tornar a arquitetura verificável, com gates que continuam funcionando quando um agente falha, recusa, alucina, declara outro papel ou perde o contexto.

Você dispõe da autorização do proprietário para alterar e commitar o repositório de teste; isso **não** inclui autorização para falsificar aprovações humanas, contornar barreiras de segurança de provedores, enviar dados sensíveis a serviços externos, destruir histórico ou implantar em produção. As aprovações humanas obrigatórias continuam obrigatórias.

## PRINCÍPIOS NÃO NEGOCIÁVEIS

1. O Orchestrator só coordena. Não redija PRD, arquitetura, laudo de QA, parecer de segurança ou parecer de implementação fingindo outro papel. Pode fornecer comandos diagnósticos e evidências auxiliares **claramente identificadas** como sua coleta, nunca assiná-las como parecer independente.
2. **Dois níveis de validação diferentes**: schema/sha validam formato/integridade; identidade/atestado e provas de execução validam autoria e fatos. Não os confunda.
3. Artefato de outro agente só é consumido se schema e pré-requisitos são válidos, a origem está autenticada no nível disponível, hashes e lineage conferem e a revisão independente foi realmente realizada.
4. Nunca preencha entradas obrigatórias com informações fictícias para superar gates. Se um requisito é inaplicável a um microprojeto, corrija o contrato condicionado ao risco e registre `NOT_APPLICABLE` justificável.
5. No terceiro ciclo de REWORK ou discussão improdutiva, transite para `ESCALATED` e consulte o proprietário. Sem loops infinitos.
6. Não trate fallback de scanner/PowerShell como prova de independência de Security. Não tente contornar guardrails da plataforma ou esconder recusas. Aplique análise defensiva adequada e revisor distinto autorizado.
7. Não use `--actor human`, `role`, hashes, links ou arquivos criados pelo próprio modelo como **comprovação isolada** de autorização ou identidade humana.
8. Em falhas de GitHub, Memanto, navegador, Antigravity ou runner, classifique a condição corretamente (`BLOCKED`, `PENDING`, `UNVERIFIED`) e continue apenas tarefas reversíveis e permitidas.
9. Preserve a simplicidade: não adicione LangGraph, outro agente, banco vetorial, broker, Kafka, n8n ou ferramentas pagas sem demonstrar necessidade concreta. Já há 19 perfis na V5; prefira fortalecer controles.
10. Toda mudança de regra passa por teste de regressão e revisão independente. `org_v5` não deve mudar silenciosamente no meio de uma run, sem versionamento e invalidação dos resultados afetados.

## FASE A — AUDITORIA DE BASELINE (SEM ALTERAR O PROJETO)

1. Descubra branch, HEAD SHA, arquivos modificados, tags locais, remotes, commits e diferenças em relação à V5 original. Inspecione `org_v5/control.py`, `contracts.py`, `cli.py`, `memory.py`, `.agents/agents/*.md`, `.agents/hooks.json`, `tests/`, `.github/workflows/`.
2. Inspecione `runs/run-pilot-v5-002/` e os documentos `prd-001`, `arch-001`, `build-001`, `qa-001`, `sec-001`, `impl-001`, `release.json`, `RESUME_PACKAGE` e `mem-pilot-001`, se existirem. Registre apenas caminhos e hashes necessários; evite ler ou expor segredos.
3. Confira se `qa-001` tem traces/screenshots/logs reais com hashes; se `sec-001` dependeu de `Select-String` pelo Orchestrator; quem produziu `impl-001`; qual GitHub identity/approval suportou gates; se há IDs de sessão de subagentes.
4. Verifique o hotfix Windows CP1252/UTF-8, a causa reportada do erro OS 1455 e a execução efetiva dos testes. Não confie apenas no relatório final.
5. Preserve todos os arquivos da run antiga, inclusive seu `PASS` histórico. Crie uma **revisão independente V5.1** com resultado `PARTIAL` e evidência. Não regrave a conclusão passada nem fabrique evidência retroativa.
6. Crie tag de backup no commit atual. Faça snapshot de alterações não commitadas, preferindo commit explícito autorizado, antes de iniciar refatorações. Utilize branch de correção isolada `fix/org-v5-1-governance` para o trabalho (o proprietário também autorizou alterações na main, mas organize commits reversíveis e só integre após validação; nenhuma ação de produção).

**Saída:** relatório de baseline com HEAD, diffs, pendências de verificação, inconsistências e risco de regressão. Se não conseguir inspecionar a run real, declare a lacuna e não invente dados.

## FASE B — CONTROLES P0 (IMPLEMENTAR PRIMEIRO)

### B1 — Identidade e segregação de funções

Projete um mecanismo `ExecutionContext`/`AgentAttestation` **fornecido pelo runner confiável**, com `run_id`, `execution_id`, `agent_instance_id`, `assigned_role`, `parent_id`, `started_at`, `code_sha`, `tool_session_id`, `assurance_level`. O agente não pode gerar livremente uma credencial e validá-la contra si mesmo.

1. Separe `assert_role_claim` de `verify_actor_identity` e `verify_independence`.
2. Nunca confie em `doc['role']` ou `--reviewer` como autenticação. Se o Antigravity não fornecer informação confiável de identidade por subagente, registre `identity_assurance: UNVERIFIED`; com esse estado, a revisão **não** libera sozinho um gate crítico. Exija confirmação humana autenticada quando necessário.
3. Implemente matriz de SoD por artefato e run. O mesmo executor, mesmo Orchestrator ou mesmo revisor de release não deve produzir e aceitar laudos de segurança/QA/implementação em situações incompatíveis. Documente substitutos habilitados e como uma redelegação é comprovada.
4. Use `source_execution_ref`, `producer_identity`, `reviewer_identity`, `sha256`, `commit_sha`, `reviewed_artifact_hash`, `lineage` e `actor_assurance` como campos, mas não os trate como prova se foram autodeclarados.
5. Testes negativos T01–T04 e T15/T18 obrigatórios. **Meta:** reproduzir a falha original e bloquear a promoção de `sec-001` fabricado por outro papel.

### B2 — Aprovação humana autenticada

Refatore `approval()`/CLI para **nunca** aceitar `--actor human` + URL como prova. Use autorização validada pela plataforma (GitHub PR review/issue comment com GitHub API e credenciais somente no processo confiável, ou sistema de aprovação que realmente ateste o usuário).

- Capture run ID, gate, SHA do artefato, commit, nonce, ação, risco, expiração e aprovador autorizado.
- Verifique pela API a identidade do autor, escopo exato, evento não revogado e freshness; estabeleça política de falha fechada.
- Rejeite URL inventada, aprovações de outra run, hash antigo, usuário não autorizado, replay e timeout.
- Nunca publique tokens/secrets em docs/logs. Não crie uma aprovação humana de teste como se tivesse sido feita pelo proprietário.
- Se não houver integração capaz de verificar isso, suporte `PENDING_HUMAN`, bloqueando `RELEASE_READY`, merge/produção e `MEMORY_WRITE` conforme matriz.

Testes T05–T08 e T27.

### B3 — Fluxos proporcionais ao risco

Desfaça obrigatoriedade universal de `market-research`+`critical-review` para PRD de engenharia restrita. Defina ao menos `ENGINEERING_SMALL`, `PRODUCT_DISCOVERY`, `RESEARCH_ONLY`, `ENGINEERING_HIGH_RISK`, com critério de classificação, gatilhos de mudança de risco e contratos mínimos apropriados. `not_applicable` requer razão, autor e review independente.

- Aplicativo local pequeno: PRD + critérios Given/When/Then, arquitetura simples e análise de riscos proporcionais.
- Projeto mercadológico: benchmarking com fontes verdadeiras, data de acesso, método, confiança, pontos fortes/fracos, riscos, alternativas, decisão fundamentada e crítica independente.
- Nunca afirmar ter checado fonte só pela presença de URL.

Testes T09–T11.

### B4 — Linha de evidência e release

Vincule cada QA/Security/Implementation Review à **mesma versão imutável de build**, e cada gate ao conjunto certo de hashes, versões e decisões. Se uma prova for corrigida, invalide apenas descendentes afetados e registre supersessão, não mutação silenciosa.

O Release Manager não cria `implementation-review`. Ele só verifica e monta `release` com os identificadores previamente aceitos e uma decisão humana realmente autenticada quando exigida. Separe `RELEASE_READY`, `MERGE_APPROVED` e `DEPLOY_APPROVED` e documente que o piloto não fez deploy em produção.

Testes T17–T19 e T28.

**GATE B:** não avance para homologação com P0 abertas. Se Antigravity não puder atestar identidades, a implementação deve explicitar esse limite e manter os gates críticos humanos.

## FASE C — EVIDÊNCIA REAL, QA E SEGURANÇA (P1)

1. Crie contrato de evidências do runner com ferramenta+versão, comando, stdout/stderr/exit code, horários, commit SHA, ambiente, arquivos com SHA individual e atestado de origem fora do texto do modelo. Declarações de execução não substituem logs.
2. QA: interagir de verdade com UI via Chrome DevTools MCP/Playwright autorizado; testar criar, listar, marcar, excluir com confirmação, título vazio, persistência e erros de console; preencher AC→Teste→Evidência; não simular cliques ou traces.
3. Security: documentar ameaça/escopo, testar caminhos DOM (`innerHTML`, `textContent`, criação segura de elementos, escapes), validar uso do localStorage, dependências e segredos; executar scanners defensivos adequados e registrar limitações. Um `Select-String` simples **não** é parecer completo de segurança.
4. Investigar a recusa original com texto exato e modelo/versão, sem afirmar que toda revisão defensiva é proibida. Se um modelo recusar, tentar alternativa defensiva autorizada com revisor independente, ou `BLOCKED`.
5. Checar que `qa-report PASS` e `security-report PASS` exigem evidências reais **e** autoria/revisão compatíveis. Se falhar, não avance para RELEASE.

Testes T12–T19 e T26.

## FASE D — MEMANTO, CONTEXTO E RECURSOS (P1)

1. Preservar `CONNECTED_ON_PREM` como conectividade, **não** homologação de persistência. Proposta `mem-pilot-001` permanece pendente até aprovação humana específica.
2. Preparar um candidato de teste totalmente sintético e solicitar consentimento `MEMORY_WRITE` com escopo exato. **Não grave nada persistente antes de verificar aprovação real**. Após a aprovação, testar `remember`, recibo/ID, `recall` semântico, nova sessão e outro modelo, conferir proveniência/hash, TTL, deduplicação e privacidade.
3. `RESUME_PACKAGE`: transferir apenas IDs, referências, hashes, decisões confirmadas, riscos, próximo passo e restrições; agente sucessor revalida conteúdo. Troca de modelo não pode propagar decisão ou evidência não verificada.
4. Corrigir encoding da CLI sem descartes silenciosos: Windows CP1252, UTF-8, box drawing `│`, stderr e locale; testes de regressão.
5. Analisar erro de Windows 1455 com recursos reais. Reduzir concorrência/carga Ollama e descarregar modelo quando adequado; medir, registrar latência, recursos e disponibilidade. Nenhum serviço pago ou API nova sem proposta de custo e autorização.
6. Registrar matriz de modelos por perfil baseada em teste: qualidade, latência, privacidade, custo e falhas; não supor que assinatura pessoal inclua acesso API.

Testes T21–T25.

## FASE E — VALIDAR EM CAMADAS

- Rodar testes unitários já existentes e todos os casos em `03-MATRIZ-DE-TESTES.md`; se algum item não puder ser executado, marcar `BLOCKED/NOT_RUN`, não `PASS`.
- Executar cenário negativo em que Orchestrator tenta criar parecer de Security Reviewer e Release Manager tenta se passar por Implementation Reviewer. Ambos devem ser bloqueados **na execução**, não apenas por instrução textual.
- Executar novamente um microprojeto real com 5+ especialistas, navegador e evidências. Comparar resultados V5 / V5.1 por indicadores: taxa de handoff correto, violações, falsos PASS, retomada, recursos e número de intervenções humanas.
- Se controle técnico de identidade não for possível no Antigravity, provar ao menos a detecção `UNVERIFIED` e o fail-closed nos gates críticos.
- Testar interrupção dos serviços, troca de sessão/modelo, alteração pós-review, revogação de aprovação, arquivo de prova falso, segurança indisponível, terceiro REWORK.

## FASE F — DOCUMENTAR E ENTREGAR

Entregáveis mínimos:

1. `docs/architecture/v5.1-independent-audit.md`: relato original versus auditoria independente, sem sobrescrever o original.
2. `docs/architecture/v5.1-adr.md`: ADR para identidade, gates, contingência e modos de workflow.
3. `docs/architecture/v5.1-migration.md`: passos e compatibilidade (V5→V5.1), sem destruir runs antigas.
4. `docs/architecture/v5.1-validation-report.md`: T01–T30, execução real, exit codes, SHA, logs, evidências e pendências.
5. Código e testes versionados para `org_v5`, com CI e docs alinhados.
6. Política de agente/modelo/MCP/permissões em conformidade com o que a versão instalada do Antigravity realmente suporta; se hook não foi testado, declarar `NOT_ENFORCED`.
7. Relatório de memória: conectado, proposta, aprovação autenticada, gravação, recall e nova sessão — cada qual com status próprio.
8. Relatório de custos/recursos e fallback do Ollama no Windows.
9. Commits atômicos por risco e resumo final PASS/PARTIAL/FAIL/BLOCKED **avaliado independentemente**.

Pare e solicite decisão humana somente se houver gate humano real, custos externos, acesso a dados sensíveis, merge/deploy público, ação destrutiva, impossibilidade de implementar controle crítico ou mais de três ciclos. Para as demais tarefas, avance de modo autônomo com evidências; **não substitua papéis nem simule aprovações para manter o fluxo andando**.

## CRITÉRIO FINAL DE ACEITE

Não declaro V5.1 pronta por número de arquivos ou 21 testes verdes. Declaro somente quando: P0 resolvidas/testadas, cadeia de revisão independente verificável ou explicitamente limitada, aprovação humana autenticada, testes reais de QA/Security, memória L2 comprovada ou pendente corretamente, recursos tratados e relatório reproduzível. A V5 pode ser funcional em algumas partes e ainda assim não estar homologada para operação autônoma de alto risco.
