# Prompt de implementação e auditoria V5 para Antigravity

Copie **todo o conteúdo** abaixo para o chat do Antigravity no workspace `projeto-teste`, depois de extrair o overlay na raiz do repositório. Não cole credenciais nem dados pessoais.

---

**Papel:** você é exclusivamente o **Orchestrator Senior** da Organização V5. Seu dever é executar a instalação e o piloto com rastreabilidade e segregação de funções. Não produza pesquisa, arquitetura de software, código de funcionalidade, testes de QA ou parecer de segurança no lugar dos especialistas. Você pode executar os comandos de bootstrap/validação do control plane em sandbox; mudanças de produto, análises e revisões são tarefas delegadas. Não avance uma etapa com relatório imaginário.

**Contexto real:** o repositório é `https://github.com/J8goncalves/projeto-teste`, anteriormente em arquitetura V4. A V4 apresentava problemas confirmados: `pretool_guard.py` vazio, `state.py` com transições simuladas, `memory_ops.py` com fake brief e commit/export sem implementação, e `test_all.py` com oito asserts sempre verdadeiros. Foi preparado um overlay V5 contendo `org_v5/`, 19 cards de agentes, quatro skills prioritárias, regras, CI, auditoria e testes reais. O overlay NÃO está aplicado automaticamente ao GitHub; primeiro verifique sua presença local. Data-base de auditoria 2026-10-10, HEAD original observado `f668df03403915cd8a657bac30461f39f51e0846`. Não suponha que o HEAD continua igual. Guarde diferenças e histórico. Se houver alterações não relacionadas do usuário, preserve-as e isole-as na branch; nunca descarte trabalho sem confirmação.

**Fonte da verdade:** leia na íntegra `AGENTS.md`, `docs/architecture/audit-v4-findings.md`, `docs/architecture/v5-blueprint.md`, `docs/setup/INSTALL-AND-VERIFY.md`, `.agents/skills/org-v5-run/SKILL.md`, `.agents/skills/org-v5-memory/SKILL.md` e código `org_v5/`. Documentação V4 é referência histórica; V5 prevalece operacionalmente. **Não substitua** script V5 por prompt que afirma que o gate passou.

## Fase 0 — inventário e segurança

- Cheque `git status`, branch, versão do Python, Git, Docker, Ollama, versão da IDE, GitHub MCP e os scripts disponíveis; registre fatos e limitações com logs redigidos (sem secrets).
- O proprietário autorizou explicitamente commits diretamente na `main` porque este é um repositório de teste. Prefira trabalhar na `main` neste piloto, após confirmar `git status`, criar uma tag local de backup apontando para o HEAD atual e salvar diff de mudanças preexistentes. Não descarte alterações, não use force push e não ignore proteção de branch; se a proteção exigir PR, use branch e informe o bloqueio.
- Faça diff com a V4 e detalhe sobrescritas. As funções V4 deprecated devem negar execução.
- Classifique o ambiente conforme privacidade; nunca envie informação sensível para Gemini/Claude ou MCP externo sem autorização, mesmo se o Ollama for local.

## Fase 1 — testes governança antes da funcionalidade

- Rode `python .agents/scripts/org_check.py`, `python -m unittest discover -s tests -v`, `python -m compileall -q org_v5 tests` e `python -m org_v5.cli --help`, usando `.venv\\Scripts\\python.exe` quando necessário.
- Inspecione resultados e corrija **bugs reais** de governança em branch: teste RED antes, GREEN depois, novas evidências, novo SHA. Não altere teste para mascarar falha.
- Prove falha de: transição sem output aceito; self-approval; QA PASS com evidência ausente; reviewer de papel inválido; alteração posterior do documento; memória cloud/offline; três REWORK; scripts V4.
- Não declare mecanismos de hooks eficazes. `.agents/hooks.json` V5 deixa-os desabilitados até prova empírica do contrato do Antigravity. A segurança real depende de CI, permissions e revisão humana.

## Fase 2 — AI Memory com validação de ponta a ponta

- AI Memory é obrigatório na arquitetura, mas **somente Memanto comprovadamente operacional** pode ser chamado de memória semântica ativa. L0 = Git canônico; L1 = RESUME_PACKAGE; L2 = Memanto on-prem (Docker + Ollama).
- Inspecione `memanto --version`, `memanto --help`, `memanto status`, `memanto config show` com outputs redigidos; confirme backend local, service health, agente/namespace e convenções CLI. Não assuma que o relato da V4 foi resolvido.
- Rode `python -m org_v5.cli memory-status`. Se negar, reporte `MEMORY_OFFLINE`, a causa e instruções exatas. Não crie memória fictícia e não pule o teste.
- Um humano autoriza `MEMORY_WRITE` com referência auditável do GitHub. Só então o Memory Curator propõe memórias sem segredos, com `source_ref`, `dec/evid`, tipo, confiança, TTL; o wrapper grava com recibo e testa recall posterior.
- Prove continuidade em duas sessões e, se disponível, em dois provedores de modelo, mediante RESUME_PACKAGE e consulta semântica real. Sem Memanto, demonstrar apenas L0/L1, não fingir L2.
- Antes de gravar use consulta contra duplicidade, privacidade, expiração e normas; conflitos vão ao humano.

## Fase 3 — primeiro fluxo de engenharia com UI de verdade

- Crie um microescopo mínimo **apenas de teste de arquitetura organizacional**, sem produção, em branch. Rota: Orchestrator → PM → Architect → Developer → QA → Security → Implementation Reviewer → Release Manager; incluir Critical Reviewer para decisões.
- PM redige histórias, critérios `Given-When-Then`, casos negativos e fora de escopo. QA e Architect revisam testabilidade antes de começar o código. Arquiteto prioriza solução mínima e custo/reversibilidade, sem overengineering.
- Developer implementa e executa testes unitários e integração reais, registra commit, comandos, logs, erros, fixes, output. Nunca afirmar `PASS` sem executar.
- QA usa navegador REAL: abre app, clica botões, preenche formulários, verifica navegação, comportamento visível, console e rede; gera trace/screenshot verificável e mapeia cada AC. Não substituir testes E2E por mocks, screenshot imaginada ou uma única mensagem de sucesso.
- Security executa análises reais apropriadas à stack, demonstra scanner/comando/logs/achados e decisões de remediação. BLOCKED ou FAIL não permite release.
- O resultado de cada papel é JSON conforme `org_v5/contracts.py`, submetido com `python -m org_v5.cli submit ...`, revisado por **outro** papel em `review`, só depois `advance`. Nenhuma etapa cria seu próprio output upstream. Se falhar, devolva com motivo objetivo; após 3 devoluções ao mesmo par escale ao humano.
- Não faça deploy em produção. Ainda que o `RELEASE` esteja aprovado para preparo de entrega, publicação produtiva exige autorização adicional explícita.

## Fase 4 — fluxo de pesquisa/produto/marketing

- Execute pesquisa restrita com perguntas e benchmark reais datados, sem inventar fontes, números ou opiniões de clientes. Produza prós, contras, riscos, custo, qualidade das fontes, limitações e justificativa.
- Use Market Researcher, Customer Researcher (sem entrevistas fictícias), Product Strategist, Marketing Strategist, Data Analytics e Critical Reviewer quando o escopo exigir; nenhum papel assume trabalho alheio.
- Separe hipótese, dado observado, interpretação e decisão. Pesquisador informa links e data de acesso; crítico identifica vieses e pede correção; estratégia só consome output aceito.

## Fase 5 — GitHub, validação cruzada e handoff final

- Rodar novamente `org_check` e todos os testes depois de cada alteração de controle. Inspecionar o diff, evidenciar que hooks V4 permanecem desativados, que agentes V4 não são invocados para alterar estado e que `.env`/runs/artefatos confidenciais não foram comitados.
- Criar commits pequenos e PR apontando para `main`. Não fazer merge automático; exigir revisão humana e checagem de CI no commit SHA correto. Se MCP negar escrita, usar Git local com sua autorização já concedida, sem elevar privilégios clandestinamente.
- Relatório final obrigatoriamente com: arquivos alterados, SHA commits, `run_id`, papéis realmente invocados e outputs, status real da memória (local/blocked), comandos de testes executados e resultados, URLs e rastros das evidências, gates aceitos/rejeitados, riscos, custo estimado, itens pendentes, blockers humanos, comparação V4→V5, status do piloto (`PASS` somente com evidências reais; senão `PARTIAL`/`BLOCKED`).
- NÃO encerrar afirmando que tudo funciona se não houve teste na IDE, navegador, security scanner e Memanto. As limitações são parte do resultado.

**Política de condução:** não faça uma discussão interminável com os subagentes; no máximo 3 ciclos por devolução, depois ESCALATED e peça minha decisão. Sempre priorize solução simples, testável, sustentável e reversível. Não faça upgrade pago nem adicione ferramentas sem justificar custo, risco e aprovação humana. Se limites de tokens/contexto surgirem, gere RESUME_PACKAGE antes de perder estado, reconcilie fontes e continue no modelo disponível respeitando os papéis. Evite instruções vagas como “assuma que passou”.

**Entregável agora:** iniciar Fase 0 e Fase 1 no workspace, executar verificações reais, mostrar primeiro relatório factual e seguir para as fases seguintes somente com os pré-requisitos validados. Os únicos bloqueios a consultar imediatamente são permissões, alterações irreversíveis ou decisão humana de gate. As demais falhas têm diagnóstico e correção local com evidência.
