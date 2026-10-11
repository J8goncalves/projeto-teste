# Plano do Piloto de Produto — Fase E

**Projeto:** `J8goncalves/projeto-teste`  
**Fase:** Fase E — Produto, Usabilidade e Valor de Negócio  
**Data:** 10 de Outubro de 2026  
**Status:** Proposta para Homologação Humana  

---

## 1. Problema do Cliente e Proposta de Valor

### 1.1 O Problema
Equipes de engenharia e operações assistidas por múltiplos agentes autônomos enfrentam gargalos críticos:
1. **Perda de Contexto e Retrabalho:** Handoffs manuais entre agentes geram perda de rastreabilidade, dependências incompletas e especificações ambíguas.
2. **Falta de Governança e Risco de Alucinação:** Agentes realizam alterações no produto sem validação independente de qualidade, acessibilidade ou segurança.
3. **Fadiga de Aprovação Humana:** Aprovações humanas desestruturadas sem evidências auditáveis (screenshots, logs reais de execução) levam a aprovações cegas ou bloqueios operacionais contínuos.

### 1.2 Proposta de Valor
O **Task Manager Autônomo e Governado** resolve esses problemas entregando:
- **Gestão de Tarefas com Rastreabilidade de Ponta a Ponta:** Cada tarefa possui critérios de aceitação formais, lineage auditável e garantia de integridade criptográfica.
- **Transparência Operacional e Autonomia Segura:** O produto expõe em tempo real o estado das atividades, artefatos gerados, evidências de testes visuais e pareceres independentes.
- **Simplicidade e Resiliência Local:** Funciona localmente, com zero dependências externas em tempo de execução, tempo de carregamento inferior a 200ms e conformidade WCAG 2.2 AA.

---

## 2. Jornada do Usuário e Backlog Priorizado

### 2.1 Jornada do Usuário
1. **Entrada e Planejamento:** O usuário define o backlog prioritário de tarefas com critérios de aceitação estruturados.
2. **Execução e Acompanhamento:** Agentes executam tarefas seguindo rigorosamente os contratos de handoff. O usuário visualiza o status e as dependências no quadro interativo.
3. **Inspeção de Evidências:** Antes de qualquer transição crítica (deploy, conclusão), o usuário inspeciona evidências reais capturadas (screenshots de browser, relatórios de segurança).
4. **Decisão e Conclusão:** O usuário emite aprovação fundamentada com anti-replay garantido.

### 2.2 Backlog Priorizado (Fase E)

| ID | User Story | Critérios de Aceitação (Gherkin) | Prioridade |
| :--- | :--- | :--- | :---: |
| **US-01** | **Criação de Tarefas com Critérios Estruturados**<br>*Como* usuário,<br>*quero* criar tarefas com título, descrição e critérios de aceitação,<br>*para que* o trabalho tenha escopo claro. | **Given** a tela do Task Manager aberta,<br>**When** preencho título, descrição e clico em "Adicionar",<br>**Then** a tarefa é criada com ID único e status `TODO`. | **P0** |
| **US-02** | **Quadro Interativo de Estados (Kanban)**<br>*Como* usuário,<br>*quero* mover tarefas entre `TODO`, `IN_PROGRESS` e `DONE`,<br>*para que* eu acompanhe o fluxo de entrega. | **Given** uma tarefa existente,<br>**When** clico no controle de avanço de estado,<br>**Then** a tarefa transita para o próximo estado e o timestamp é gravado. | **P0** |
| **US-03** | **Persistência Local Resiliente e Integridade**<br>*Como* usuário,<br>*quero* que minhas tarefas sejam salvas localmente com verificação de integridade,<br>*para que* eu não perca dados após recarregar a página. | **Given** tarefas cadastradas,<br>**When** a página é recarregada,<br>**Then** o estado é restaurado com hash íntegro de dados. | **P0** |
| **US-04** | **Filtros e Busca Textual Rápida**<br>*Como* usuário,<br>*quero* buscar tarefas por palavras-chave e filtrar por status,<br>**para que** eu encontre itens críticos instantaneamente. | **Given** múltiplas tarefas no quadro,<br>**When** digito um termo na busca,<br>**Then** a visualização filtra os itens em menos de 50ms. | **P1** |
| **US-05** | **Exportação e Importação com Assinatura SHA-256**<br>*Como* auditor ou operador,<br>*quero* exportar o snapshot do quadro com hash de integridade,<br>*para que* eu possa auditar ou migrar o estado com segurança. | **Given** o quadro populado,<br>**When** clico em "Exportar",<br>**Then** um arquivo JSON é baixado contendo o digest SHA-256 dos dados. | **P1** |

---

## 3. Arquitetura Proporcional do Produto

A arquitetura do Task Manager foi desenhada sob o princípio de **proporcionalidade estrita**: sem frameworks desnecessários, sem servidores backend pesados para o MVP, e com máxima performance e auditabilidade.

```
+--------------------------------------------------------------+
|                     Interface Web (SPA)                      |
|                                                              |
|   +-----------------------+     +------------------------+   |
|   |  Task Board Component |     | Search/Filter Controls |   |
|   +-----------------------+     +------------------------+   |
|               |                              |               |
+---------------+------------------------------+---------------+
                |                              |
+--------------------------------------------------------------+
|                    Application / Store                       |
|                                                              |
|   - TaskStore: CRUD, State Machine transitions               |
|   - IntegrityManager: SHA-256 hashing & validation           |
|   - EventBus: State change notifications                     |
+--------------------------------------------------------------+
                |
+--------------------------------------------------------------+
|                    Persistence Adapter                       |
|                                                              |
|   - LocalStorage Engine (com fail-safe & quota check)        |
|   - JSON Import / Export Engine                              |
+--------------------------------------------------------------+
```

### Características Técnicas:
- **Tecnologia:** HTML5 Semântico, CSS Moderno (Design Tokens CSS Variables), JavaScript Vanilla Modular (ES6 Modules).
- **Zero Runtime Dependencies:** Elimina vulnerabilidades na cadeia de suprimentos (npm supply chain attacks).
- **Tamanho Total:** < 50 KB (carregamento instantâneo < 100ms).

---

## 4. Padrões de UI/UX e Acessibilidade (WCAG 2.2 AA)

1. **Estrutura Semântica:**
   - Uso estrito de `<header>`, `<main>`, `<section>`, `<article>`, `<button>`, `<input>`.
   - Hierarquia clara de cabeçalhos (`<h1>` até `<h3>`).
2. **Navegação por Teclado:**
   - Todos os elementos interativos operáveis exclusivamente via `Tab`, `Shift+Tab`, `Enter`, `Space` e `Escape`.
   - Anéis de foco visíveis (`outline: 2px solid #0056b3; outline-offset: 2px`) em todos os estados `:focus-visible`.
3. **Acessibilidade para Leitores de Tela:**
   - Atributos `aria-label`, `aria-describedby` e `aria-live="polite"` para alertas de alteração de estado.
   - Ícones acompanhados de texto acessível visível ou `aria-hidden="true"` com descrição alternativa.
4. **Contraste de Cores:**
   - Razão de contraste mínima de 4.5:1 para texto padrão e 3:1 para controles de interface e texto em destaque (testado contra paleta AA).
5. **Alvos de Toque (Touch Targets):**
   - Todos os botões e áreas clicáveis possuem dimensão mínima de 44x44px conforme WCAG 2.2 (Target Size Minimum).

---

## 5. Plano de Testes Reais e Segurança

### 5.1 Testes de QA com Navegador Real (Chrome DevTools MCP)
- **Execução Real:** O QA Specialist iniciará servidor local e interagirá diretamente com o browser via Chrome DevTools MCP.
- **Evidências Mandatórias:**
  - Screenshots de alta resolução para cada estado (`TODO`, `IN_PROGRESS`, `DONE`).
  - Gravação de logs de rede e console (validando ausência de warnings/erros).
  - Teste de fluxo completo (criação, edição, filtro, transição, persistência pós-refresh).

### 5.2 Testes de Acessibilidade Automatizados e Manuais
- Inspeção da árvore de acessibilidade via Chrome DevTools MCP.
- Auditoria de contraste e navegação por teclado.

### 5.3 Testes de Segurança de Código
- **Prevenção de XSS:** Uso estrito de `textContent` e APIs seguras do DOM; proibição de `innerHTML` com entradas de usuário.
- **Sanitização de Dados:** Validação de esquema estrito em qualquer dado carregado via `localStorage` ou importação de JSON.
- **Content Security Policy (CSP):** Meta tag estrita bloqueando scripts inline não autorizados e fontes externas:
  ```html
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self';">
  ```

---

## 6. Metas de Eficiência Operacional

| Métrica | Meta na Fase E | Mecanismo de Controle |
| :--- | :---: | :--- |
| **Tempo de Execução da Iteração** | < 15 minutos | Prompts focados, suíte de testes rápida (< 3s), handoffs bem tipados. |
| **Consumo de Tokens / Custo** | < \$0.20 por ciclo | Prompts enxutos, contexto incremental, eliminação de payloads redundantes. |
| **Taxa de Retrabalho (Rejection Rate)** | < 10% | Validação formal de contratos no intake; linting prévio antes de submit. |
| **Handoffs Eficientes** | 1 handoff por etapa | Evidências completas no envio inicial (`build`, `qa-report`, `security-report`). |

---

## 7. Matriz de Riscos Residuais

| ID | Risco Residual | Probabilidade | Impacto | Mitigação | Dono Designado |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **R1** | **Autenticação e integridade do AI Memory em múltiplos processos**<br>Servidor compartilhado pode sofrer concorrência ou colisão de tokens se múltiplos runners rodarem simultaneamente. | Baixa | Médio | Token por sessão isolada, lock em arquivo SQLite e fail-closed com verificação de digest em todas as escritas. | **Arquiteto / Lead Backend** |
| **R2** | **Isolamento de execução de agentes na IDE sem container**<br>Processos filhos de agentes compartilham o mesmo sistema operacional e podem ler memória não limpa. | Média | Alto | Strip mandatório de credenciais no ambiente (`set_actor_context`), garantia `UNVERIFIED` por padrão e aprovação humana externa obrigatória para gates críticos. | **Security Reviewer / Platform Lead** |
| **R3** | **Confiabilidade de aprovações por webhook vs. polling GitHub**<br>Rate limit da API do GitHub ou atrasos de rede podem atrasar verificação de comentários. | Baixa | Médio | Token de runner dedicado com cabeçalhos de cache, exponential backoff com limite de 10s e fail-closed explícito. | **Orquestrador / DevOps Lead** |
| **R4** | **Custos e limites de API em escala de produto**<br>Consumo excessivo de embeddings ou inferência de agentes se o escopo crescer descontroladamente. | Média | Baixo | Uso exclusivo de SQLite FTS5 para busca local sem LLM/Ollama, modelos leves (`flash_lite`/`inherit`) para tarefas de leitura. | **Product Manager / FinOps Lead** |

---

## 8. Próximos Passos
1. Aguardar aprovação humana formal deste plano de produto.
2. Iniciar a Sprint 1 da Fase E implementando os contratos de produto (`prd`, `architecture`, `build`, `qa-report`, `security-report`).
3. Manter todos os gates críticos bloqueados até verificação independente e aprovação humana fundamentada.
