# Plano do Piloto de Produto — Fase E (Opção A: Task Manager Simples e Excelente)

**Projeto:** `J8goncalves/projeto-teste`  
**Fase:** Fase E — Produto, Usabilidade e Valor de Negócio  
**Data:** 10 de Outubro de 2026  
**Status:** Aprovado para Execução (Opção A)  
**Escopo Autorizado:** Task Manager simples, local, responsivo e excelente em UI/UX, construído e auditado pela organização multiagente V5.1.1 (sem poluição de console de agentes na interface do usuário).

---

## 1. Problema do Cliente e Proposta de Valor

### 1.1 O Problema
Profissionais e equipes técnicas precisam de uma ferramenta de gestão de tarefas diárias que seja:
1. **Rápida e Sem Distrações:** Sem necessidade de login complexo, onboarding longo, servidores externos lentos ou telemetria invasiva.
2. **Confiável e Resiliente Localmente:** Que garanta persistência segura em `localStorage`, proteção contra corrupção acidental de dados e migração transparente de versões legadas sem perda de histórico.
3. **Acessível e Universal (WCAG 2.2 AA):** Operável com total fluidez por teclado, com alto contraste, fontes legíveis e alvos de toque adequados para dispositivos móveis (>= 44x44px).
4. **Auditável com Integridade Criptográfica:** Que permita exportar e importar o estado das tarefas com digest SHA-256 para verificação de integridade dos dados locais.

### 1.2 Proposta de Valor (Opção A)
O **Task Manager Pessoal e de Equipe** entrega:
- **Fluxo Visual Intuitivo:** Gestão estruturada em três estados (`TODO`, `IN_PROGRESS`, `DONE`) com transição bidirecional simples e feedback imediato.
- **Campos Estruturados:** Título obrigatório com validação em tempo real, descrição detalhada opcional e critérios de aceitação.
- **Experiência de Uso Fluida:** Busca instantânea por texto (< 10ms) e filtros por estado em tempo real.
- **Acessibilidade Inclusiva:** Diálogo de confirmação customizado acessível (sem uso do `confirm()` bloqueante nativo do navegador), foco visível aprimorado e conformidade com WCAG 2.2 AA.
- **Portabilidade Segura:** Exportação e importação de JSON estruturado com digest de integridade SHA-256 (claramente identificado como digest de integridade, não assinatura digital autenticada) e sanitização estrita via APIs seguras do DOM (imunidade a XSS).

> **Nota de Governança:** Os 19 papéis de agentes da V5.1.1, seus contratos de handoff, revisões independentes e checagens de segurança operam exclusivamente nos **bastidores de engenharia**. O produto final entrega uma experiência de usuário limpa, focada exclusivamente no gerenciamento de tarefas do usuário.

---

## 2. Jornada do Usuário e Backlog Priorizado

### 2.1 Jornada do Usuário
1. **Abertura e Carregamento:** A aplicação carrega instantaneamente (< 100ms) sem requisições de rede externas. Caso existam tarefas de versões legadas no `localStorage`, a migração ocorre de forma silenciosa e sem perda.
2. **Criação de Tarefas:** O usuário adiciona uma tarefa informando título obrigatório e, opcionalmente, descrição e critérios de conclusão.
3. **Execução e Movimentação:** O usuário transita a tarefa de `TODO` para `IN_PROGRESS` ao iniciar o trabalho, e para `DONE` ao concluir (podendo retornar o estado caso necessário).
4. **Busca e Filtragem:** Conforme o volume de tarefas cresce, o usuário digita palavras-chave na busca ou alterna os filtros (`Todos`, `A Fazer`, `Em Andamento`, `Concluídas`).
5. **Remoção com Diálogo Acessível:** Ao solicitar a exclusão de uma tarefa, um modal acessível in-app solicita confirmação com foco preso e suporte a teclado (`Escape` para cancelar, `Enter` para confirmar), eliminando caixas nativas intrusivas.
6. **Backup e Portabilidade:** O usuário exporta suas tarefas em arquivo JSON contendo metadados de versão e digest de integridade SHA-256, ou restaura tarefas a partir de um backup validado.

---

### 2.2 Backlog Detalhado (User Stories e Critérios de Aceitação Gherkin)

#### [P0] US-01: Criação de Tarefas Estruturadas
- **Como** usuário,  
  **quero** criar tarefas fornecendo título obrigatório, descrição e critérios de conclusão opcionais,  
  **para que** minhas atividades tenham escopo claro e objetivo.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Criação com dados válidos
    Given que estou na tela do Task Manager
    When informo o título "Finalizar documentação da API", descrição "Detalhar endpoints REST" e clico em "Adicionar Tarefa"
    Then a tarefa é criada com ID único no estado "TODO"
    And os campos de entrada são limpos
    And a contagem de tarefas é atualizada em tempo real

  Scenario: Tentativa de criação com título vazio
    Given que estou na tela do Task Manager
    When clico em "Adicionar Tarefa" sem preencher o título
    Then uma mensagem de erro acessível é exibida indicando obrigatoriedade do título
    And o foco permanece no campo de título
    And nenhuma tarefa é adicionada
  ```

#### [P0] US-02: Máquina de Estados e Transições Bidirecionais
- **Como** usuário,  
  **quero** mover minhas tarefas entre `TODO` (A Fazer), `IN_PROGRESS` (Em Andamento) e `DONE` (Concluída),  
  **para que** eu visualize claramente o progresso do meu fluxo de trabalho.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Avanço de estado TODO para IN_PROGRESS e DONE
    Given uma tarefa no estado "TODO"
    When clico na ação "Iniciar"
    Then o status da tarefa é alterado para "IN_PROGRESS"
    And quando clico na ação "Concluir"
    Then o status da tarefa é alterado para "DONE"

  Scenario: Retorno de estado DONE para IN_PROGRESS
    Given uma tarefa no estado "DONE"
    When clico na ação "Reabrir"
    Then o status da tarefa retorna para "IN_PROGRESS"
  ```

#### [P0] US-03: Exclusão com Modal de Confirmação Acessível
- **Como** usuário,  
  **quero** que a exclusão de uma tarefa seja confirmada por um modal visual e acessível (sem `confirm()` nativo),  
  **para que** eu evite perdas acidentais sem sofrer interrupções bloqueantes do navegador.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Confirmação de exclusão pelo modal
    Given uma tarefa existente na lista
    When clico no botão "Excluir" da tarefa
    Then um modal de confirmação acessível é aberto com foco no botão de confirmação
    And quando clico em "Confirmar Exclusão"
    Then a tarefa é removida da lista e do armazenamento local
    And o modal é fechado e o foco é devolvido adequadamente

  Scenario: Cancelamento de exclusão
    Given o modal de confirmação aberto
    When clico em "Cancelar" ou pressiono a tecla "Escape"
    Then o modal é fechado sem remover a tarefa
  ```

#### [P0] US-04: Persistência Local Resiliente e Migração de Dados Legados
- **Como** usuário,  
  **quero** que meus dados sejam salvos no `localStorage` de forma íntegra e que versões antigas de dados sejam migradas automaticamente,  
  **para que** eu não perca tarefas criadas em versões anteriores da aplicação.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Migração transparente de dados legados
    Given que o localStorage contém tarefas no formato legado [{"title": "Tarefa Antiga", "done": false}]
    When a aplicação é inicializada
    Then a tarefa legada é convertida para o formato estruturado com id, title, status "TODO", createdAt e updatedAt
    And os dados migrados são salvos no novo esquema sem perda de conteúdo

  Scenario: Proteção contra corrupção do localStorage
    Given que o item de armazenamento no localStorage contém JSON corrompido
    When a aplicação é inicializada
    Then a aplicação recupera com lista vazia segura em vez de travar com erro não tratado
    And emite alerta informativo no console
  ```

#### [P0] US-05: Design Responsivo, Usabilidade e Acessibilidade WCAG 2.2 AA
- **Como** usuário em dispositivos móveis ou desktop,  
  **quero** uma interface limpa, com alvos de toque confortáveis (>= 44x44px), foco visível claro e alto contraste,  
  **para que** eu possa usar a ferramenta confortavelmente em qualquer dispositivo e com tecnologias assistivas.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Usabilidade em tela mobile (390x844)
    Given um dispositivo móvel com viewport de 390x844
    When acesso o Task Manager
    Then o layout reorganiza os controles em coluna única sem rolagem horizontal indesejada
    And todos os botões e áreas interativas mantêm dimensão mínima de 44x44px

  Scenario: Navegação por teclado e foco visível
    Given que navego usando a tecla Tab
    When foco qualquer controle interativo (input, botão, filtro)
    Then um anel de foco bem delineado (outline destacado com contraste >= 3:1) é claramente visível
  ```

#### [P1] US-06: Busca Textual Rápida e Filtros por Status
- **Como** usuário,  
  **quero** filtrar tarefas por status e buscar por termos no título ou descrição em tempo real,  
  **para que** eu encontre atividades específicas instantaneamente.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Filtro por status
    Given tarefas distribuídas em TODO, IN_PROGRESS e DONE
    When seleciono o filtro "Em Andamento"
    Then apenas as tarefas com status "IN_PROGRESS" são exibidas na lista

  Scenario: Busca textual por palavra-chave
    Given tarefas com diferentes títulos e descrições
    When digito "documentação" no campo de busca
    Then a lista exibe apenas as tarefas contendo o termo correspondente no título ou na descrição
  ```

#### [P1] US-07: Exportação e Importação com Digest de Integridade SHA-256
- **Como** usuário técnico ou auditor,  
  **quero** exportar minhas tarefas para JSON acompanhadas de um digest SHA-256 e importá-las com verificação de integridade,  
  **para que** eu possa realizar backups e transferências confiáveis.
- **Critérios de Aceitação (Gherkin):**
  ```gherkin
  Scenario: Exportação com digest SHA-256
    Given tarefas salvas no sistema
    When aciono "Exportar Tarefas (JSON)"
    Then um arquivo JSON formatado é gerado contendo a lista de tarefas, versão do esquema, timestamp e o campo "integrity_sha256"

  Scenario: Importação válida com verificação de integridade
    Given um arquivo JSON de backup exportado pelo sistema
    When realizo a importação do arquivo
    Then o digest SHA-256 é recalculado sobre a carga útil de tarefas
    And se coincidente com o valor registrado, as tarefas são restauradas com sucesso

  Scenario: Rejeição de arquivo adulterado ou inválido
    Given um arquivo JSON cujo conteúdo foi adulterado ou com esquema incorreto
    When tento importar o arquivo
    Then a importação é bloqueada, exibindo erro claro de integridade/formato sem corromper as tarefas atuais
  ```

---

## 3. Arquitetura Proporcional e Estratégia de Migração

### 3.1 Arquitetura em Camadas
```
+---------------------------------------------------------------------------------+
|                                 Camada de UI                                    |
|   - Formulário de Criação (Campos Semânticos, Validação Acessível)               |
|   - Barra de Busca e Filtros Rápidos (Todos, A Fazer, Em Andamento, Concluídas)  |
|   - Lista e Cartões de Tarefa (Estados, Badges de Status, Ações Contextuais)    |
|   - Modal de Confirmação de Exclusão (Acessível, Focus Trap, Escape Key)        |
|   - Painel de Backup (Exportação / Importação com Digest SHA-256)               |
+---------------------------------------------------------------------------------+
                                       │
                                       ▼
+---------------------------------------------------------------------------------+
|                                Camada de Domínio                                |
|   - TaskStore: CRUD, Validações, Transições de Estado (TODO ↔ IN_PROGRESS ↔ DONE)|
|   - IntegrityService: Cálculo e Verificação de Digest SHA-256 (Web Crypto API)  |
+---------------------------------------------------------------------------------+
                                       │
                                       ▼
+---------------------------------------------------------------------------------+
|                             Camada de Persistência                              |
|   - LocalStorageAdapter: Persistência síncrona com fail-safe e detecção de cota |
|   - MigrationEngine: Conversão transparente de esquemas legados (v0 -> v1)      |
+---------------------------------------------------------------------------------+
```

### 3.2 Estratégia de Migração de Dados Legados
1. **Detecção:** Ao carregar a chave `tasks` do `localStorage`, o parser analisa a estrutura dos itens.
2. **Esquema Legado (v0):** Formato `{ title: string, done: boolean }`.
3. **Conversão para Esquema v1:**
   ```javascript
   {
     id: generateUniqueId(),
     title: legacyItem.title,
     description: '',
     criteria: '',
     status: legacyItem.done ? 'DONE' : 'TODO',
     createdAt: new Date().toISOString(),
     updatedAt: new Date().toISOString()
   }
   ```
4. **Persistência Imediata:** O array migrado é salvo no novo formato, mantendo integridade e compatibilidade futura.

---

## 4. Diretrizes de UI/UX e WCAG 2.2 AA

1. **Tokens de Design e Cores de Alto Contraste:**
   - Fundo principal: `#f8fafc` (fundo limpo e suave)
   - Superfície de cartões: `#ffffff` com borda sutil `#e2e8f0`
   - Texto principal: `#0f172a` (contraste de 14.5:1 contra branco)
   - Texto secundário: `#475569` (contraste de 5.8:1 contra branco)
   - Cor primária (Brand): `#2563eb` (contraste 4.6:1 contra branco)
   - Status TODO: `#64748b` (neutro escuro)
   - Status IN_PROGRESS: `#d97706` (âmbar escuro, contraste >= 4.5:1)
   - Status DONE: `#16a34a` (verde floresta, contraste >= 4.5:1)
   - Ação Perigosa (Exclusão): `#dc2626` (vermelho vivo, contraste >= 4.5:1)

2. **Alvos de Toque e Espaçamento:**
   - Todos os botões possuem altura mínima de 44px e padding de clique adequado.
   - Espaçamento de separação vertical entre itens interativos de pelo menos 8px.

3. **Navegação por Teclado e Foco Visível:**
   - Indicador de foco bem destacado: `outline: 3px solid #2563eb; outline-offset: 2px;`.
   - Gerenciamento de foco ao abrir e fechar o modal de confirmação.

---

## 5. Plano de QA e Segurança Real

1. **Testes Automatizados (Node.js Test Runner):**
   - Criação com validação de campos obrigatórios.
   - Transições de estado válidas e reversíveis.
   - Detecção e migração bem-sucedida de formatos legados.
   - Resiliência a entradas vazias, caracteres especiais e corrupção de armazenamento.
   - Exportação e importação de JSON com verificação de integridade SHA-256.

2. **QA Real em Navegador via Chrome DevTools MCP:**
   - Execução em servidor local HTTP.
   - Verificação em desktop (1280x800) e mobile emulado (390x844).
   - Teste de fluxo interativo completo: adição, busca, filtro, transição, abertura de modal e exclusão.
   - Registro de evidências fotográficas reais em `evidence/`.
   - Inspeção de console para garantia de 0 erros e 0 warnings.

3. **Auditoria de Segurança:**
   - **Prevenção de XSS:** Renderização de conteúdo de texto exclusivamente através de `textContent` e nós DOM criados programaticamente.
   - **Content Security Policy (CSP):** Meta tag estrita sem fontes de scripts não seguras:
     ```html
     <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:;">
     ```
   - **Clareza de Criptografia:** Identificação explícita de que SHA-256 é utilizado para verificação de integridade de dados e não como assinatura digital autenticada de autoridade.

---

## 6. Critérios de Conclusão da Fase E (DoD)

- [x] E0: Baseline medido e registrado.
- [x] E1: Incorporação seletiva concluída com testes e CI verde.
- [ ] E2.1: `docs/product/phase-e-pilot-plan.md` atualizado com o escopo autorizado da Opção A.
- [ ] E2.2: Implementação de UI/UX e regras em `src/index.html` e `src/app.js` cumprindo P0 e P1.
- [ ] E2.3: Suíte de testes atualizada e passando (`node tests/test_task_manager.js`).
- [ ] E2.4: Sessão de QA executada em navegador real via Chrome DevTools MCP com evidências reais capturadas.
- [ ] E2.5: Parecer de Design Critique e Security Review registrados.
- [ ] E2.6: Relatório de resultados `docs/product/phase-e-pilot-results.md` publicado.
- [ ] E2.7: Commit da Etapa E2 e apresentação do resumo final para homologação humana.
