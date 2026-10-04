---
trigger: always_on
description: "Regras do projeto: colaboração entre agentes, Git, arquitetura, código, segurança e testes."
---
# Project Rules

## Colaboração Inter-Agentes
Nesta organização, 'autorização' significa aprovação humana registrada num gate (`state.py approve`) ou concedida no prompt de permissão do Antigravity.
 - Cada entrega técnica deve iniciar pela definição do PM e Arquiteto.
 - O Developer só implementa após entendimento claro dos critérios de aceitação.
 - O QA e Security devem aprovar as mudanças antes do merge para branches principais e voltar para o Developer em caso de correções necessárias.

## General

Este projeto deve priorizar:

1. Simplicidade
2. Manutenibilidade
3. Segurança
4. Testabilidade
5. Observabilidade
6. Escalabilidade
7. UI e UX Design 

## Architecture

Nunca introduza uma nova tecnologia sem justificar a decisão.

Antes de alterar arquitetura existente:

1. identifique a arquitetura atual;
2. explique o problema;
3. proponha alternativas;
4. escolha uma solução;
5. documente a decisão.

Teste de reversibilidade: se desfazer a decisão custa mais de um dia de trabalho ou afeta dados ou contratos, ela é difícil de reverter e exige ADR em `docs/adr/`; caso contrário, justifique no PR.

## Git

Sempre trabalhar em branches apropriadas.

Nunca alterar diretamente a branch principal sem autorização.
- Branch principal: `main` (código pronto para produção).
- Branches de funcionalidade: `feature/<nome-da-feature>`.
- Branches de correção: `fix/<nome-do-bug>`.
- Branches de melhoria técnica/refatoração: `refactor/<nome-da-tarefa>`.

Uma branch por tarefa. Commits seguem Conventional Commits com o ID do requisito no escopo (`feat(REQ-021): ...`). `git push` e merge pedem aprovação humana.

## Code

Código deve:

- ser legível;
- seguir padrões existentes;
- evitar duplicação;
- possuir testes quando aplicável.

Fluxos críticos de interface têm teste E2E como código commitado (Playwright, quando houver interface web). A exploração manual no navegador complementa e não substitui.

## Security

Nunca:

- colocar secrets no código;
- expor tokens;
- usar credenciais reais;
- acessar produção sem autorização.

## Testing

Funcionalidades novas devem possuir testes apropriados incluindo de integração.

Deploy, gasto e acesso a dados pessoais exigem aprovação humana (ver `autonomy.md`).

Operação dos agentes: ver `governance.md`, `operations.md`, `autonomy.md`, `vetoes.md` e `permissions.md`.
