# Arquitetura da Organização
**Versão V4, 2026-10-04**

## Visão Geral V4

Nesta versão, a organização de agentes opera estruturada em **Níveis de Execução**, **Gates de Decisão**, e **Control Plane** isolado do fluxo heurístico.

**Níveis (1 a 3):**
- **Nível 1:** Ajustes e pequenos fixes. Sem Discovery profundo, vai direto ao planejamento e Build.
- **Nível 2:** Iniciativas e features normais. Envolve Discovery formal, planejamento, design, build e Gates 0 a 4. 
- **Nível 3:** Alta complexidade/Risco. Exige o CEO no loop recomendando, com evidência primária (E2) e opções.

**Gates (0 a 4):**
- Gate 0: Automático de triagem.
- Gate 1: Humano decide (GO, GO CONDICIONADO, VALIDAR ANTES, PIVOT, NO-GO) com base no Decision Package.
- Gate 2: Validação de requisitos, ADRs, ameaças, custo (automático ou humano).
- Gate 3: Merge (Humano).
- Gate 4: Release (Humano).

**Autonomia e Control Plane:**
Autonomia varia de A0 (Tudo Humano) a A3 (Agente age sem perguntar). O **Control Plane** garante a imutabilidade do estado via scripts Python (`state.py`, `events.py`, `budget.py`, `validate.py`) e Hooks, bloqueando ferramentas em estados proibidos. Política de memória rigorosa filtra a "sujeira", e consolida dados valiosos via `memory_ops.py` (`RISK`, `INCIDENT`, `CONSTRAINT`).

**Os 16 Agentes:**
O roster agora é padronizado e inclui, além dos engenheiros e do Orchestrator: CEO, Product Strategist, Market Researcher, Customer Researcher, Marketing Strategist, Critical Reviewer, Legal Compliance, Experiment Designer e Data Analytics.

## Diagramas da Arquitetura V4

### Visão Geral

```mermaid
flowchart TD
    classDef human fill:#B3E65F,stroke:#6E9A24,color:#2F440B
    classDef lead fill:#9CE6FF,stroke:#2C97BB,color:#1C4657
    classDef biz fill:#FFE86D,stroke:#A28E26,color:#574900
    classDef eng fill:#DDDDD8,stroke:#8A8A7E,color:#434339
    classDef ctrl fill:#FFA3D6,stroke:#C26DA3,color:#5C1D44

    HUMAN(["Humano / Board"]):::human
    CEO["CEO: recomenda no Nível 3"]:::lead
    ORCH["Chief Orchestrator: roteia e aplica políticas"]:::lead

    subgraph CP["Control Plane: scripts, políticas e hooks, sem LLM"]
        SM["Máquina de estados"]:::ctrl
        EVL["Log de eventos"]:::ctrl
        POL["Permissões, orçamento e autonomia"]:::ctrl
        VAL["Validadores e rastreabilidade"]:::ctrl
        MEM[("Memanto: memória curada")]:::ctrl
        KS["Kill switch"]:::ctrl
    end

    subgraph DT["Discovery Track"]
        MR["Market Researcher"]:::biz
        CUST["Customer Researcher"]:::biz
        PS["Product Strategist"]:::biz
        MKT["Marketing Strategist"]:::biz
        CR["Critical Reviewer"]:::biz
        LEGAL["Legal e Compliance"]:::biz
        EXP["Experiment Designer"]:::biz
        DATA["Data e Analytics"]:::biz
    end

    subgraph LT["Delivery Track"]
        PM["Product Manager"]:::eng
        ARCH["Software Architect"]:::eng
        SEC["Security Reviewer"]:::eng
        DEV["Developer"]:::eng
        QA["QA Engineer"]:::eng
        OPS["DevOps e FinOps"]:::eng
    end

    HUMAN -->|"Demanda"| ORCH
    ORCH -.->|"Decision Package no Nível 3"| CEO
    CEO -->|"Recomendação"| HUMAN
    ORCH <-->|"Estado, políticas e eventos"| CP
    ORCH -->|"Tarefas por fatia"| DT
    ORCH -->|"Tarefas por fatia"| LT
    DT -.->|"Artefatos, vetos e candidatos a memória"| CP
    LT -.->|"Artefatos, vetos e candidatos a memória"| CP
    CP -.->|"Briefings mínimos"| DT
    CP -.->|"Briefings mínimos"| LT
    HUMAN ==>|"Gates e overrides"| CP
```

### Máquina de Estados

```mermaid
stateDiagram-v2
    [*] --> INTAKE
    INTAKE --> DISCOVERY : Nível 2 ou 3 e Gate 0 ok
    INTAKE --> PLANNING : Nível 1 ou demanda já validada
    DISCOVERY --> DISCOVERY : evidência extra, máximo 2 rodadas
    DISCOVERY --> GATE1 : pacote de decisão pronto
    DISCOVERY --> CLOSED : critério de kill atingido
    GATE1 --> PLANNING : GO ou GO CONDICIONADO
    GATE1 --> DISCOVERY : VALIDAR ANTES ou PIVOT
    GATE1 --> CLOSED : NO-GO
    PLANNING --> DESIGN : PRD validado
    PLANNING --> BUILD : Nível 1
    DESIGN --> GATE2 : ADRs, ameaças, custo e observabilidade
    GATE2 --> BUILD : aprovado
    GATE2 --> DESIGN : veto ou reprovação
    BUILD --> VERIFY : PR aberto e CI local verde
    VERIFY --> BUILD : falha ou veto
    VERIFY --> DESIGN : defeito de arquitetura
    VERIFY --> PLANNING : requisito intestável
    VERIFY --> GATE3 : QA, Security e arquitetura aprovam
    GATE3 --> BUILD : reprovado
    GATE3 --> GATE4 : merge com release
    GATE3 --> LEARN : merge sem release
    GATE4 --> PRODUCTION : release aprovado
    GATE4 --> BUILD : reprovado
    PRODUCTION --> MEASURE : janela de coleta definida
    MEASURE --> LEARN : relatório de resultado
    LEARN --> DISCOVERY : nova hipótese
    LEARN --> CLOSED : iniciativa encerrada
    CLOSED --> [*]
```

Observação para o documento: de qualquer estado a run pode ir para ESCALATED (motivo registrado, por vetos sem solução em 3 ciclos, orçamento esgotado ou comportamento anômalo) ou PAUSED (humano); a saída desses dois estados é sempre decisão humana.

## Elenco e Ferramentas Principais
*Nota: Ferramentas estão padronizadas usando a infraestrutura nativa do Antigravity ou CLI (e.g. `search_web`, `read_url_content`, `Semgrep`, `gitleaks`, `Trivy`, etc.).*

| Agente | Responsabilidades | Ferramentas Atribuídas |
| :--- | :--- | :--- |
| **orchestrator** | Gestão de fluxo, contratos, roteamento, orçamentos. | Nenhuma de pesquisa (coordena via scripts) |
| **ceo** | Recomendações estratégicas e desempates (Nível 3). | `search_web`, arquivos e scripts locais |
| **market-researcher** | Inteligência de mercado e concorrentes. | `search_web`, `read_url_content`, etc. |
| **customer-researcher**| VoC e pesquisa primária com clientes. | `search_web`, `read_url_content` |
| **product-strategist** | JTBD, ICP, pricing, proposta de valor. | `search_web`, leitura de arquivos |
| **marketing-strategist**| Go-to-Market, unit economics. | `search_web`, leitura de arquivos |
| **critical-reviewer** | Red Team, premissas assassinas e pre-mortem. | `search_web`, arquivos |
| **legal-compliance** | Risco legal, tradução de normas para engenharia. | `search_web`, arquivos |
| **experiment-designer**| Plano de validação, métodos (fake doors, etc). | `search_web`, arquivos |
| **data-analytics** | Métricas de sucesso, tracking plan, mensuração. | `search_web`, arquivos (só leitura) |
| **product-manager** | Requisitos, histórias de usuário, PRD, backlog. | Nenhuma de pesquisa externa |
| **architect** | Modelagem (C4, Mermaid), ADRs, desenho técnico. | Nenhuma (usa código local) |
| **developer** | Escrita e testes de código, CI local. | Git, compilers, linting |
| **security-reviewer** | Ameaças (Semgrep, gitleaks, Trivy), CI de risco. | Scanners, leitura de código |
| **qa** | Planejamento de testes, E2E (Playwright), CWV. | Chrome DevTools MCP (ou CLI) |
| **devops-finops** | FinOps, releases, observabilidade, CI/CD, custos. | CLI e scripts de ambiente |
