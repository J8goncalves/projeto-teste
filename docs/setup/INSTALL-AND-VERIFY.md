# Instalação e verificação — Antigravity V5 no Windows

> **Escopo:** overlay do piloto no repositório público `J8goncalves/projeto-teste`. Arquivos existentes da V4 são preservados salvo sobrescritas explícitas deste pacote. O overlay não é um dump completo do repositório nem carrega os binários das aplicações.

## 0. Pré-requisitos e segurança de dados

- GitHub conectado com `contents: write` no repositório se for usar GitHub connector; caso contrário aplique localmente via Antigravity e `git push` com a credencial do seu PC.
- Windows 11, Git e Python 3.11+. O relatório do V4 informa `.venv/Scripts/python.exe` com Python 3.14.8; confirme isso no ambiente **atual**, porque relatórios antigos não substituem teste.
- Docker e Ollama opcionais para testes básicos; obrigatórios para o Memanto on-prem proposto. Sem servidor Memanto pronto, a suíte pode passar, mas o gate de integração real permanece **BLOCKED**.
- Backup da branch e diff antes de copiar o overlay. **Nunca comite `.env`, secret, tokens, documentos com PII, traces contendo credenciais ou dumps de memória.** `runs/` é ignorado no Git; armazene RESUME_PACKAGE sanitizado como documento aprovado para persistência além da máquina.

## 1. Preparar a main de teste e aplicar overlay

No terminal PowerShell do Antigravity, na raiz do projeto:

```powershell
git status --short
git branch --show-current
git tag backup/pre-org-v5-$(Get-Date -Format yyyyMMdd-HHmmss)
# O proprietário autorizou alterações diretas na main deste repositório de teste.
# Se branch protection impedir, crie uma branch e abra PR.
# Extraia org-v5-pilot.zip em uma pasta temporária externa ao repositório.
# Copie SOMENTE o conteúdo do diretório org-v5-pilot/ para a raiz do repo,
# mantendo os arquivos não mencionados. Inspecione o diff antes de prosseguir.
git status --short
git diff -- AGENTS.md .agents/hooks.json .agents/scripts/state.py .agents/scripts/memory_ops.py
```

Este pacote não foi enviado pelo conector GitHub porque a API retornou `403 Resource not accessible by integration` ao tentar criar a branch. Não trate o ZIP como commit remoto. O Antigravity deve aplicar os arquivos no ambiente local e criar o PR após validação.

## 2. Teste do plano de controle

```powershell
.\.venv\Scripts\python.exe .agents/scripts/org_check.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q org_v5 tests
.\.venv\Scripts\python.exe -m org_v5.cli --help
```

Esperado: verificações de estrutura sem erros e 20+ testes reais. Verifique também que V4 agora **nega**:

```powershell
.\.venv\Scripts\python.exe .agents/scripts/state.py transition --to BUILD
.\.venv\Scripts\python.exe .agents/scripts/memory_ops.py brief --role qa
```

Esperado: exit code diferente de zero. Se imprimir OK, há sobreposição do legado e a instalação **falhou**.

## 3. Memanto / AI Memory — teste real obrigatório

```powershell
.\.venv\Scripts\memanto.exe --version
.\.venv\Scripts\memanto.exe status
.\.venv\Scripts\memanto.exe config show
.\.venv\Scripts\python.exe -m org_v5.cli memory-status
```

Não copie segredos nem output que contenha tokens para o chat. Na migração V4, o CLI estava em backend `cloud` e não configurado. Não assuma que isto foi corrigido apenas por ter Docker e Ollama instalados. Siga o instalador/guia do Memanto da versão disponível (`memanto` para seleção On-Prem) e verifique serviço Docker, health e acesso local. Se o binário só existe no `.venv`, defina `MEMANTO_BIN` apontando para esse executável.

O wrapper exige `Backend: on-prem` ou `Backend: local` no resultado de `status`. **Pode ser preciso adaptar o parser ao output real da versão instalada**, por ADR e testes, jamais enfraquecer a condição para passar. Após aprovação humana registrada de memória, execute: proposta → promoção → recibo → recall em nova sessão e, idealmente, no segundo modelo (Gemini/Claude/Ollama) com documentos canônicos preservados. Uma resposta do modelo **não prova** gravação.

Links para referências oficiais: https://github.com/moorcheh-ai/memanto e https://docs.memanto.ai/ .

## 4. Antigravity — validação de carregamento e hooks

Leia https://antigravity.google/docs/rules/ e https://antigravity.google/docs/hooks/ na versão instalada. Confirme no painel de customizações que as regras da pasta são carregadas; solicite ao agente o nome e resumo da rule V5 e mande localizar o contrato `qa-report`. Ative **nenhum hook V4** só porque o JSON diz `enabled: true`: o guard V4 estava vazio e os demais eram no-op. Primeiro audite as APIs de hook, prove um `deny` observável para uma ação-teste inofensiva, ateste que o mesmo vale para subagentes/terminal, em Windows e sem alterar uma conta externa. Só então implemente hook V5 e CI de bloqueio (nova ADR).

Os workflows V4 devem ser tratados como legado: a documentação Antigravity indica aposentadoria em **19 de outubro de 2026**. Use skills em `.agents/skills/`.

## 5. GitHub — proteção fora do prompt

1. Configure branch protection/ruleset para `main` com PR obrigatório, no mínimo uma revisão de pessoa autorizada, checks `org-v5-governance` exigidos e proibição de bypass, se disponível.
2. Revise `CODEOWNERS` e escopo de tokens; não deixe uma mesma conta bot alterar política de segurança e aprovar o próprio PR.
3. Faça push da branch e abra PR **sem merge automático**. Revise diff, especialmente mudanças nos caminhos `.agents/scripts`, `.agents/rules`, `.agents/hooks.json` e `AGENTS.md`.
4. Verifique GitHub Actions executado no **commit SHA** correto. CI verde não é prova de integração Antigravity, UI real ou Memanto; essas evidências vêm dos pilotos de execução.

## 6. Teste comportamental completo

**A. Controles negativos:** tente autoaprovação (deve negar), PASS do QA sem trace (negar), gate sem documento aceito (negar), edição após SHA registrado (negar), três REWORK consecutivos (ESCALATED), memória cloud/offline (MEMORY_OFFLINE), teste V4 (negar).

**B. Engenheiros:** peça um microprojeto local com um campo, um botão e um feedback que permita abrir no navegador. PM produz US/AC Given-When-Then, Architect elabora alternativas simples, Developer implementa + executa unitários, QA usa Playwright/browser real e entrega evidências de clicar/preencher/console, Security roda SAST/dependências de verdade. Se uma ferramenta não estiver disponível, marcar BLOCKED e propor instalação open-source depois de revisão.

**C. Negócio:** solicite benchmark restrito a três concorrentes reais em uma data definida; Market Research produz URLs, tradeoffs e incerteza; Critical Reviewer devolve recomendações com fonte fraca; Product Strategist propõe decisão. Não permitir estimativa numérica inventada.

**D. Retomada:** interrompa a sessão, gere `resume-package`, abra outro modelo, confira hashes e duas decisões verificáveis; só depois compare semantic recall do Memanto.

Em cada caso registre: `run_id`, data/versão, entradas, passos, resultado real, artefatos/trace, bloqueios, custo e decisão humana. Um único FAIL mantém a etapa bloqueada.

## 7. Definição de pronto do piloto

- `org_check` verde; unitários completos; smoke CLI comprovado; check da CI executado no PR.
- Antigravity executou de fato vários papéis independentes, houve pelo menos um REWORK e retorno responsável, sem autoaprovação.
- Memanto verificado com store/recall real e recibos; caso contrário status explícito **MEMORY_OFFLINE** e arquitetura não considerada 100% validada.
- QA clicou em UI real, registrou trace/console, scanner real gerou outputs e o revisor conferiu evidências.
- Branch protection e permissões externas confirmadas por humano; não fazer deploy em produção.

## Aplicador opcional com backup e pré-visualização

Se quiser instalar os arquivos do ZIP por script, extraia `org-v5-pilot/` **fora** da pasta Git. No PowerShell:

```powershell
& "C:\\caminho\\org-v5-pilot\\apply_overlay.ps1" -Repository "D:\\Antigravity Projects\\projeto-teste"
# Revise CREATE/REPLACE. Depois, para aplicar com backup de cada arquivo substituído:
& "C:\\caminho\\org-v5-pilot\\apply_overlay.ps1" -Repository "D:\\Antigravity Projects\\projeto-teste" -Apply
```

O instalador preserva arquivos preexistentes não contidos no overlay, cria backup dos arquivos sobrescritos na pasta temporária do Windows e não cria branch, PR, commit nem alteração em servidor remoto. Confirme a `main`, crie a tag de backup **antes** e não use force push. Nunca desative antimalware ou políticas de execução globalmente para rodar o script; se o Windows bloquear, copie manualmente os arquivos com diff e backup.
