# Projeto Teste

Projeto estruturado para desenvolvimento colaborativo com agentes autônomos de software.

## 📁 Estrutura de Diretórios

```text
projeto-teste/
│
├── .agents/
│   ├── agents/
│   │   ├── product-manager.md  # Especificação do papel de Product Manager
│   │   ├── architect.md        # Especificação do papel de Software Architect
│   │   ├── developer.md        # Especificação do papel de Developer
│   │   ├── qa.md               # Especificação do papel de Quality Assurance
│   │   └── security.md         # Especificação do papel de Security Specialist
│   │
│   ├── rules/
│   │   ├── project.md          # Diretrizes gerais de governança do projeto
│   │   ├── coding.md           # Padrões de código e convenções de commit
│   │   └── security.md         # Regras e políticas de segurança
│   │
│   └── workflows/
│       └── feature-lifecycle.md# Ciclo de vida de ponta a ponta das demandas
│
├── docs/                       # Documentações técnicas e especificações
├── src/                        # Código-fonte da aplicação
├── tests/                      # Bateria de testes automatizados
└── README.md                   # Documentação inicial do projeto
```

## 🤖 Papéis dos Agentes
- **Product Manager**: Detalhamento de regras de negócio, histórias de usuário e critérios de aceitação.
- **Architect**: Decisões técnicas, diagramas, padrões de projeto e ADRs.
- **Developer**: Escrita de código limpo, testes unitários e implementação das funcionalidades.
- **QA**: Validação dos critérios de aceitação, cenários de teste e garantia de qualidade.
- **Security**: Revisão de segurança, prevenção a vulnerabilidades e proteção de dados/segredos.

## 🚀 Como Começar
1. Configure seu ambiente de desenvolvimento conforme as instruções adicionais em `docs/`.
2. Siga as convenções de desenvolvimento descritas em `.agents/rules/coding.md`.
3. Valide o fluxo em `.agents/workflows/feature-lifecycle.md` para qualquer nova funcionalidade.
