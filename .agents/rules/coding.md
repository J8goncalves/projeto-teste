---
trigger: model_decision
description: "Aplique ao escrever, revisar ou commitar código: Clean Code, SOLID, Conventional Commits, testes e cobertura."
---
# Padrões e Convenções de Código

## Princípios Fundamentais
1. **Clean Code & SOLID**:
   - Nomes descritivos e autoexplicativos para variáveis, funções e classes.
   - Funções pequenas com responsabilidade única.
   - Evitar código duplicado (DRY) e abstrações desnecessárias prematuras (KISS / YAGNI).
   - Manter o padrão do banco de dados sempre pensando em performance.

2. **Padrão de Commits (Conventional Commits)**:
   Todos os commits devem seguir a convenção:
   - `feat:` nova funcionalidade para o usuário.
   - `fix:` correção de bug.
   - `docs:` alterações exclusivamente em documentação.
   - `style:` formatação e espaçamento, sem alteração de lógica.
   - `refactor:` refatoração de código que não altera comportamento público.
   - `test:` adição ou ajuste de testes.
   - `chore:` tarefas de manutenção, build, dependências ou CI/CD.

3. **Qualidade e Testes**:
   - Todo novo recurso deve vir acompanhado de testes unitários.
   - Manter cobertura de testes consistente em 85%.
   - Não subir código com warnings de linter ou erros de tipagem.

- Antes de pedir revisão, rode localmente lint, tipagem, testes, cobertura e varredura de segredos. Abra o PR só com tudo verde.
