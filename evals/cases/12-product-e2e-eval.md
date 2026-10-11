# 12-product-e2e-eval.md
**Eixo de Avaliação:** Eixo 2 — Product E2E Evaluation (Task Manager Piloto A)

## Objetivo
Avaliar o comportamento real da aplicação web no navegador, validando jornada do usuário, transições de estado, persistência de dados pós-refresh, acessibilidade por teclado (WCAG 2.2 AA) e ausência de erros de console.

## Preparação
- Servidor local ativo servindo `src/index.html` e `src/app.js`.
- Chrome DevTools MCP conectado e operando em navegador real.

## Entrada
1. Criação de nova tarefa com título e descrição opcional.
2. Tentativa de criação com título vazio (validação de campo obrigatório acessível).
3. Transição de estado: `TODO -> IN_PROGRESS -> DONE` e reversão `DONE -> IN_PROGRESS`.
4. Edição de título e exclusão com diálogo proporcional de confirmação.
5. Recarregar a página (F5 / reload) e inspecionar restauração íntegra de `localStorage`.
6. Simulação de dado corrompido em `localStorage` para verificar fail-safe sem perda de dados.
7. Navegação completa por teclado (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`) sem uso de mouse.
8. Redimensionamento de viewport para mobile (390x844) e desktop (1440x900).

## Comportamento Esperado
- Cada interação de usuário reflete imediatamente no DOM.
- Todos os elementos interativos possuem anel de foco visível e alvo de toque >= 44x44px.
- Nenhuma exceção não tratada no console do navegador (`get_console_message`).
- Screenshots reais capturadas e associadas aos critérios de aceite.

## Critério de Aprovação
- 100% dos fluxos P0 observados e aprovados com evidências visuais de navegador.
- Zero erros de console ou violações de Content Security Policy.
- WCAG 2.2 AA: contraste >= 4.5:1, foco visível, formulários com labels acessíveis.

## Como Medir
- Ações interativas via Chrome DevTools MCP (`click`, `type_text`, `take_snapshot`, `take_screenshot`).
- Mapeamento explícito de critérios de aceite (AC) a observações reais no relatório de QA.
