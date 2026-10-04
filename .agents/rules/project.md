# Project Rules

## Colaboração Inter-Agentes
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

## Git

Sempre trabalhar em branches apropriadas.

Nunca alterar diretamente a branch principal sem autorização.
- Branch principal: `main` (código pronto para produção).
- Branches de funcionalidade: `feature/<nome-da-feature>`.
- Branches de correção: `fix/<nome-do-bug>`.
- Branches de melhoria técnica/refatoração: `refactor/<nome-da-tarefa>`.

## Code

Código deve:

- ser legível;
- seguir padrões existentes;
- evitar duplicação;
- possuir testes quando aplicável.

## Security

Nunca:

- colocar secrets no código;
- expor tokens;
- usar credenciais reais;
- acessar produção sem autorização.

## Testing

Funcionalidades novas devem possuir testes apropriados incluindo de integração.
