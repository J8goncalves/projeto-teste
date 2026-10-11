---
trigger: model_decision
description: "Aplique ao escrever, revisar ou commitar código: princípios Karpathy, TDD observável, diagnóstico metódico, Clean Code e Conventional Commits."
---
# Padrões e Convenções de Código

## 1. Princípios Fundamentais (Inspirados em Karpathy Guidelines)
1. **Pensar Antes de Codar:**
   - Explicitar premissas. Havendo ambiguidade material, apresente as opções em vez de presumir silenciosamente.
   - Pergunte apenas quando a resposta alterar a decisão, o escopo, os critérios de aceite ou o risco.
   - Se existir alternativa mais simples, aponte-a. Rejeite complexidade especulativa.
2. **Simplicidade Primeiro:**
   - Escreva o código mínimo que resolve o problema solicitado. Zero código especulativo.
   - Não crie abstrações, classes base ou event buses para código de uso único (KISS / YAGNI).
   - Não implemente flexibilidade ou configurabilidade que não foi solicitada.
3. **Mudanças Cirúrgicas:**
   - Altere estritamente o necessário para a tarefa.
   - Não reformate, não reordene e não reescreva arquivos ou trechos não relacionados.
   - Preserve estilo do arquivo existente e mantenha diffs fáceis de auditar.
4. **Sucesso por Comportamento Observável:**
   - Sucesso é comprovado por execução real e saída observada, nunca por suposição.
   - Se escreveu código, execute o teste ou comando correspondente e inspecione a saída.

## 2. Disciplina de TDD e Engenharia (Matt Pocock)
1. **Red -> Green -> Verify em Fatias Verticais:**
   - Teste primeiro o comportamento observável na interface externa (UI/DOM ou API pública).
   - Evite asserções tautológicas (`assertTrue(True)`) ou testes acoplados a detalhes internos de implementação.
   - Mocks de unidade não substituem integração nem verificação ponta a ponta.
2. **Diagnóstico Metódico de Defeitos (Diagnosing Bugs):**
   - **Reprodução Mínima:** Crie um comando, teste ou script que falhe reproduzindo o sintoma exato antes de tocar no código de produção.
   - **Hipótese Testável:** Formule hipótese clara sobre a causa raiz e valide com a menor modificação possível.
   - **Mesma Prova:** Verifique o sucesso rodando **exatamente o mesmo teste/comando** de reprodução anterior.
   - **Regressão:** Adicione o caso reproduzido à suíte permanente de regressão.

## 3. Padrão de Commits e Higiene
1. **Conventional Commits:**
   `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`.
2. **Higiene Pré-Submissão:**
   - Rode localmente lint, testes e verificação de integridade antes de solicitar revisão.
   - Não suba código com erros de console, warnings não tratados ou credenciais expostas.
