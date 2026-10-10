# Organização de Agentes — Revisão Independente V5 e Plano de Correção V5.1

**Data de avaliação:** 10/10/2026  
**Run observada:** `run-pilot-v5-002`  
**Fonte primária da execução:** `v5_pilot_report.md`, fornecido pelo usuário.  
**Código analisado:** `org-v5-pilot-main-ready.zip` (base V5 anterior ao piloto).  
**Status do acesso à branch real:** não verificado: o conector GitHub retornou HTTP 404 nas consultas anteriores. Portanto, o relatório não audita os arquivos efetivamente modificados no Windows/Antigravity.  
**Veredito da revisão documental:** **PARTIAL, com bloqueios críticos de homologação**. Não alterar retrospectivamente o `PASS` registrado pelo agente; registrar **contestação de avaliação** e a evidência das divergências.

## 1. Escopo e limitações

A revisão avalia separadamente: (A) fatos alegados no relatório final, (B) capacidades observáveis no código V5 de referência, (C) inferências que exigem teste adicional. O documento **não comprova** que os testes com navegador, a delegação por subagentes, o scan de segurança, as aprovações, os commits locais nem o recall Memanto tenham sido executados como relatados; para isso são necessários logs, artefatos e trilhas da branch local. Tampouco pressupõe que a versão atual ainda contenha todos os defeitos do pacote anterior, pois houve hotfix de encoding e possível alteração de scripts durante o piloto.

### O que foi efetivamente relatado

- A execução declarou `PASS`, com delegação para PM, Architect, Developer, QA, Security e Release Manager.
- PM produziu PRD e também *mock artifacts* de pesquisa para satisfazer dependências obrigatórias do CLI.
- Developer declarou testes Node e commit `45c5b7859cea45ad375aada9615cd4912f9c6bab`.
- QA declarou usar Chrome DevTools MCP com interações de navegador e evidências; o relatório **não anexa** traces, screenshots ou logs brutos.
- Security Reviewer foi impedido de concluir análise; o Orchestrator executou `Select-String` e materializou evidências em `sec-001`.
- Release Manager foi inicializado com `RESUME_PACKAGE` e teria gerado `impl-001` e `release.json`.
- Memanto ficou `CONNECTED_ON_PREM`, mas `mem-pilot-001` permaneceu **proposta pendente**, sem homologação de write/recall.
- Foram reportados bug de encoding e erro de memória/paging do Windows `1455` sob carga do Ollama.

### O que o código-base V5 permite constatar

- `org_v5/control.py::submit` valida `role` fornecido no documento, mas não verifica uma identidade de executor autenticada. `review` recebe uma string `reviewer` pela CLI; não existe prova forte de que outro agente executou a revisão.
- `org_v5/control.py::approval` requer `actor == 'human'` e URL prefixada por `https://github.com/`, sem consultar a API do GitHub para verificar autor, autenticação, permissões, tipo da aprovação, hash, escopo ou expiração.
- `org_v5/control.py::REQUIRED` exige `market-research` e `critical-review` para atingir `PLANNING`; `INPUT_REQUIREMENTS['prd']` também obriga ambos. Isso pode provocar documentos artificiais em tarefas sem necessidade de pesquisa.
- `org_v5/control.py::validate_proof` compara SHA-256 do **arquivo** de log e confirma que caminhos locais existem/não estão vazios. Isso não atesta que a ferramenta foi executada, que o evento ocorreu, nem a autoria. O conteúdo de outros arquivos referidos em `evidence_refs` não tem hash pinado nessa função.
- `org_v5/contracts.py::validate` confere estrutura de QA e scanner listados para `PASS`, mas não verifica execução de scanner, cobertura semântica ou independência real.
- `org_v5/control.py::REVIEWERS` exige que `implementation-review` seja revisado por `critical-reviewer`; o relatório atribui geração de `impl-001` ao `release_manager`, o que requer inspeção da trilha real para saber como foi registrado.
- `org_v5/memory.py::promote` usa uma aprovação registrada no estado, chama o CLI Memanto e exige recibo não vazio, mas isso, por si, não demonstra recall consistente posterior.
- `org_v5/control.py::advance` pode selecionar **qualquer** artefato aceito do tipo exigido no conjunto da run, sem necessariamente exigir que o conjunto pertença à mesma versão de build/revisão/release ou revalidar status contemporâneo/temporal da evidência; precisa de lineage específica.

## 2. Matriz de achados e ações

| ID | Prioridade | Achado e impacto | Correção V5.1 | Evidência de conclusão |
|---|---|---|---|---|
| GOV-001 | P0 | Identidade de produtor/revisor informada pelo chamador, sem autenticação confiável | Passar contexto de execução atestado pelo host; aceitar somente papéis vinculados à invocação real. Sem atestação do host, tratar como `UNVERIFIED` e exigir gate humano em tarefas críticas | Teste de falsificação de role por orchestrator retorna DENY |
| GOV-002 | P0 | Aprovação `actor=human` + qualquer URL GitHub não é autenticação | Resolver URL via GitHub API/identidade autenticada, verificar allowlist, escopo, nonce, run, artefato SHA, decisão e prazo; fail-closed | URL fictícia, comentário de bot e URL de outra run são rejeitados |
| GOV-003 | P0 | Conflito de função: Orchestrator gerou `sec-001`; Release Manager teria produzido `impl-001` | Matriz SoD por run/artefato; reviewer e release não podem produzir/substituir relatórios críticos; fallback escalonado | Security e implementation review independentes de produtor e orquestrador |
| GOV-004 | P0 | Pesquisa mockada para superar contrato rígido | Rotas separadas `ENGINEERING_SMALL`, `PRODUCT_DISCOVERY`, `RESEARCH`, `PRODUCTION`; gates proporcionais ao risco; `NOT_APPLICABLE` justificado e aprovado onde pertinente | Task manager simples chega ao PRD sem pesquisa falsa; produto mercadológico segue exigindo fontes reais |
| GOV-005 | P0 | Aceitação/RELEASE com base em presença de artefatos, sem cadeia segura de autoria e versões | Release manifest imutável com IDs, hashes, commit, autores atestados, vereditos, status e aprovações vinculadas ao mesmo build | `sec` de outra build, relatório supersedido ou origem não verificada bloqueiam release |
| EVID-001 | P1 | Hash de log e existência de prova não demonstram execução real | Registro assinado/atestável pelo runner: comando, ferramenta, versão, horários, exit code, commit, environment, run, anexos e hash de cada evidência | `PASS` fictício com log fabricado é negado ou marcado não verificável |
| EVID-002 | P1 | Critérios de QA e segurança insuficientes semanticamente | Matriz AC→TEST→EVID; navegador real para UI; scanner adequado + revisão humana/independente para segurança; limitações e falhas explícitas | Cobertura por critério, traces reais, achados e scans autenticáveis |
| MEM-001 | P1 | L2 apenas conectado, proposta `mem-pilot-001` não persistida | Aprovação humana **de escopo exato** para candidato sintético; gravação, recibo com ID, busca, nova sessão/outro modelo, hash da origem, deduplicação e expiração | Evidências de write+recall cruzado e teste negativo offline/cloud |
| RES-001 | P1 | Erro Windows 1455, pressão de recursos de Ollama | Políticas de concorrência/memória, benchmark de modelo local, fallback remoto autorizado, liberação de contexto/modelos e monitoramento | Duas execuções seguidas sem OOM, com logs de recursos; falha simulada não provoca loops |
| FAIL-001 | P1 | Recusa de Security Reviewer levou à substituição de papel | Capturar falha exata; tarefa defensiva corretamente delimitada; fallback para outro modelo/serviço autorizado ou scanners independentes, sem burlar restrições; bloqueio até revisão competente | Falha não promove `sec` nem `RELEASE`; handoff a revisor distinto demonstrado |
| REL-001 | P1 | `RELEASE` ambiguamente descrito como autorização de produção | Separar `RELEASE_READY`, `MERGE_APPROVED`, `DEPLOY_APPROVED`, `DEPLOYED`; ausência de deploy deve constar no relatório | Nenhum gate de produção satisfeito por artefato de teste local |
| OBS-001 | P2 | Relatório final sem logs brutos e links verificáveis; `PASS` excessivo | Gerador de relatório independente: evidência, proveniência, cobertura, limitações; estados PASS/PARTIAL/FAIL/BLOCKED | Auditoria reproduzível por pessoa que não esteve na sessão |
| GOV-006 | P2 | Drift do pacote V5 após correções 'em voo' | Inventário git diff baseline→branch; CI para código de governança, changelog/ADR e revisão externa | SHA, diff, testes e responsáveis registrados |

## 3. Solução-alvo: controles executáveis, não apenas prompts

### 3.1 SoD / identidade (P0)

1. Cada invocação recebe `execution_id`, `run_id`, `assigned_role`, `agent_instance_id`, `tool_session_id`, `code_sha` e `parent_task_id` de um **executor confiável fora do controle do próprio agente**. O documento pode mencionar o executor, mas **não serve como atestado de autoria**.
2. `submit`/`review`/`approve` devem consumir um token de curta duração ou contexto autenticado emitido pelo executor; o CLI nunca deve acreditar em `--role=security-reviewer` isoladamente.
3. Para ambientes onde o Antigravity não expõe identidade confiável por subagente: registrar `identity_assurance=UNVERIFIED`, bloquear aceites automáticos críticos e exigir validação humana autenticada. Não fabricar assinaturas ou alegar segurança criptográfica que a plataforma não oferece.
4. O Orchestrator pode coletar diagnóstico técnico **auxiliar** em caso de falha; não pode assinar `security-report`, `qa-report` nem `implementation-review` como especialista. O parecer deve indicar claramente `BLOCKED` até revisão independente.
5. O Reviewer de implementação não é o Release Manager, nem substituto do Security Reviewer. Rejeitar conflito de papéis mesmo quando documentos passam por validação estrutural.

### 3.2 Aprovação humana (P0)

- Criar solicitação registrada em GitHub (issue/PR/check) com `run_id`, gate, ação exata, artifact ID e SHA, branch/commit, riscos, limites, TTL e nonce único; sem segredos.
- Verificar a aprovação pela API autenticada: autor `login` autorizado, estado/decisão, timestamp posterior à solicitação, nonce exato, PR/issue correto e status atual do artefato. Um texto ou URL digitado pelo modelo não é aprovação humana.
- Ligar cada aprovação a **um único alvo**; mudanças de hash, escopo, commit, risco, versão ou prazo invalidam a decisão. Registrar revogação.
- Sem acesso confiável à API de autenticação, registrar `APPROVAL_PENDING/UNVERIFIABLE` e impedir ação crítica. Não aceitar `--actor human` como substituto.

### 3.3 Políticas proporcionais ao risco (P0)

| Trilha | Quando usar | Artefatos mínimos antes de BUILD | Aprovações adicionais |
|---|---|---|---|
| `ENGINEERING_SMALL` | Bug, UI local, tarefa restrita, baixo risco | intake, PRD conciso com AC, arquitetura leve, teste e critérios de segurança | Gate humano apenas onde política exigir; **nunca** exigir mercado/marketing fictícios |
| `PRODUCT_DISCOVERY` | Ideia, oportunidade, PMF, estratégia | pesquisa com fontes, benchmark, riscos, parecer crítico, decisão, PRD | Gate de estratégia conforme risco/investimento |
| `RESEARCH_ONLY` | Mercado, marketing, jurídico, benchmark | pergunta, método, evidências rastreáveis, limitações e parecer independente | Aprovação humana se impacto estratégico/financeiro/legal |
| `ENGINEERING_HIGH_RISK` | Dados sensíveis, integração financeira, auth, deploy público, migrações | requisitos ampliados, threat model, ADR, privacidade, testes e revisão de segurança | Revisão humana e gates adicionais vinculados ao risco |

A ausência legítima de uma etapa deve ser documentada por `applicability_decision` com motivo e aprovador, nunca substituída por fonte falsa ou documento mockado. Fluxos de pesquisa mantêm exigência de pesquisa verdadeira e fonte datada.

### 3.4 Evidência e release lineage (P0/P1)

- `RUN -> REQ -> PRD -> ADR -> BUILD(commit SHA) -> QA -> SECURITY -> IMPLEMENTATION_REVIEW -> RELEASE_READY`, com IDs/hashes/versão da mesma cadeia.
- Cada execução produz metadados capturados pelo runner, não pelo LLM: ferramenta+versão, comando normalizado, horário, status, commit SHA, ambiente, output SHA e hashes dos anexos.
- Browser QA: registrar navegador/versão, URL local, seletores, ações, comportamento esperado/observado, traces/screenshots, erros de console/rede, IDs AC, timestamps e resultado.
- Security: inventário de superfície de ataque, ameaças relevantes, código/fonte verificado, scanners realmente executados (ou `NOT_RUN`), achados, limitações, severidade, mitigação e revisor distinto.
- Verificação de release deve rejeitar prova ausente, alterada, de outro build, gerada pelo mesmo executor da implementação quando separação for mandatória, ou de revisão revogada. Revogar/superseder por evento imutável; não apagar logs antigos.

### 3.5 AI Memory e continuidade (P1)

- Fonte de verdade de decisões e requisitos: Git. Memanto L2: fatos e aprendizados curtos, datados, com `source_ref` + hash, tipo, confiança, TTL, tags, owner e política de privacidade. `RESUME_PACKAGE`: estado/artefatos aprovados e hashes, não substitui L2.
- Teste controlado: propor candidato totalmente fictício; coletar aprovação humana específica; promover uma vez; guardar `memory_id`/recibo; consultar por chave e semântica; iniciar sessão fria com outro modelo e exigir reprodução **correta** de fatos, ressalvas e referência; comparar resultados com fonte original. Sem aprovação, ficar `PENDING` sem interferir na engenharia.
- Deduplicar, atualizar por supersessão e testar expiração/invalidação de informação obsoleta; leitura de memória é **dado não confiável**, nunca instrução soberana.
- Capturar stdout/stderr de Memanto como bytes e decodificar com estratégia explícita; **não** converter Unicode para ASCII silenciosamente como mecanismo definitivo. Fix de Windows exige teste com CP1252, UTF-8 e box drawing e sem perda do significado de status.

### 3.6 Carga, modelos e serviços (P1)

- Medir RAM total/livre, commit/pagefile, VRAM, memória dos contêineres, `ollama ps`, tokens/latência. Não afirmar que Ollama sempre cabe; `1455` demanda investigação de pressão real de memória.
- Separar LLM e embeddings onde possível; fila de concorrência limitada e execução sequencial quando houver carga. Definir corte seguro antes de OOM e fallback só para conteúdo autorizado ao provedor externo.
- Matriz de modelo por papel **benchmarkada**: qualidade de PRD/ADR/QA/review, latência, custo marginal, confiabilidade e privacidade. Planos Gemini/Claude Pro não implicam automaticamente API programática disponível ou gratuita.
- Evitar adotar runtime, broker, vetor DB e novos serviços sem prova de necessidade; manter arquitetura simples primeiro.

## 4. Estratégia de implementação sem adulterar o histórico

### F0 — Congelamento e baseline (antes de editar)

1. Preservar a run `run-pilot-v5-002` e seus hashes na forma em que estão; copiar evidências e obter commit/tag de referência. Checar estado do worktree e diferenças no `org_v5/memory.py` e nos demais arquivos alterados durante o piloto.
2. Registrar `V5-INDEPENDENT-REVIEW`: `PARTIAL` e achados GOV-001.., mantendo o `PASS` original como declaração do agente, não como veredito homologado.
3. Não sobrescrever mudanças locais nem incorporar o pacote ZIP V5 antigo cegamente. Trabalhar na versão **atual da branch local**, em nova branch `fix/org-v5-1-governance` ou na `main` de teste com tag de backup e commits atômicos, conforme política/autorização do proprietário.

### F1 — P0: bloquear aprovações e impersonação

Refatorar `control.py`, `cli.py`, `contracts.py` com camadas `identity.py`, `approvals.py`, `lineage.py` (nomes sugeridos). Introduzir adapters para o executor e GitHub, com falha fechada quando indisponíveis. Migrar o schema de estado de forma versionada e não destrutiva. Não reescrever a run histórica.

### F2 — P0: remover falsa pesquisa e corrigir gates

Criar `workflow_mode`, `risk_profile`, `applicability_decision` e trilhas condicionais com transições realmente executadas e testes de cada perfil. Somente permitir `NOT_APPLICABLE` com razão compatível com o risco. Ajustar `README`, `AGENTS.md`, perfis e skills após alteração do motor.

### F3 — P1: evidência, QA e segurança

Implementar evidência provenance, metadados de runner, vínculo por commit e validação de artefatos de UI/scanner. Rodar teste E2E negativo: Orchestrator tenta submeter security review e falha; QA mockado tenta aprovar sem navegador e falha; security NOT_RUN não libera release.

### F4 — P1: memória, encoding e infraestrutura

Aplicar correção de encoding com testes; homologar Memanto com aprovação e readback; reduzir pressão de memória, medir e registrar consumo e estratégia de fallback autorizada.

### F5 — Piloto V5.1 (novo, independente)

Nova run pequena, preferencialmente **mesmo microescopo**, para comparar V5 versus V5.1; não reutilizar artefatos aprovados da V5 como autorização automática. Executar dois cenários: fluxo feliz real e falhas propositais (impersonação, recusa de modelo, troca de sessão, QA sem screenshot, GitHub indisponível, Memanto indisponível, mudança pós-aprovação). Reportar resultados por evidência.

### F6 — Consolidação

Atualizar políticas, testes, runbooks, docs, CI e modelos. Produzir relatório V5.1 com casos PASS/FAIL/BLOCKED, artefatos, SHA dos commits, testes reproduzíveis e decisões humanas necessárias. Merge/deploy separado por escopo; nada de produção por inferência.

## 5. Critérios de saída / Definition of Done V5.1

1. Todos os defeitos **P0** resolvidos e testes negativos demonstrados; nenhuma transição crítica só pelo texto do modelo.
2. Comprovação real ou explicitação `UNVERIFIED` de autoria e revisão; para qualquer componente crítico sem atestação, gate humano autenticado obrigatório.
3. Aprovações vinculadas a run, gate, artefato, hash, commit, identidade e TTL; alteração revoga a aprovação.
4. Rota `ENGINEERING_SMALL` não gera pesquisa fictícia; trilha `PRODUCT_DISCOVERY` não aceita pesquisa sem fonte verificável.
5. QA e Security independentes com evidência de execução e correspondência com a mesma build; relatório `BLOCKED` não é promovido.
6. Memanto L2: write+recall+nova sessão+outro modelo **comprovação** ou classificação explícita `PENDING/BLOCKED`, sem declarar homologação.
7. Testes automatizados de regressão e experimentos E2E executados contra runtime real do Antigravity; nenhum teste de mock alegado como E2E.
8. Operação sob limite de recursos medido sem erros ocultados; documentação e CI aprovadas.
9. Preservação integral de histórico, incluindo `PASS` do agente e contestação independente, sem editar evidência antiga.
10. Relatório final reproduzível, com permissões/gates humanos claramente identificados.

## 6. Perguntas que a auditoria dos artefatos da branch deve responder

- Qual modelo/identificador de sessão produziu `sec-001`? O hash tem log de scanner real, ou apenas `Select-String`?
- O que `qa-001` referencia exatamente (trace, screenshots, logs, console, interações)? Os arquivos ainda existem e os hashes conferem?
- `impl-001` foi de fato produzido pelo `implementation-reviewer` ou pelo Release Manager declarando outro papel?
- Quais revisões e aprovações GitHub têm autor humano autenticado e conteúdo vinculado ao SHA do build?
- A release descrita implicou merge ou deployment? O relatório não demonstra deploy real, e não se deve inferi-lo.
- Quais scripts foram alterados durante a run, por quem, e quais testes foram repetidos depois dessas mudanças?
- Como `RESUME_PACKAGE` foi transmitido e como o destinatário provou leitura e revalidação de hashes em uma sessão independente?
- Houve chamada Memanto `remember` real com ID e posterior `recall` após aprovação? O relatório afirma que **não**.

## 7. Decisão recomendada

**Autorizar preparação da V5.1 e correção das P0/P1 no repositório de teste; não declarar o piloto V5 homologado nem aprovar publicação em produção.** O objetivo não é descartar o V5, mas torná-lo mensuravelmente seguro e honesto quanto aos seus limites. O Antigravity deve executar a implementação com rastreabilidade, e o proprietário aprovar somente os gates realmente humanos.
