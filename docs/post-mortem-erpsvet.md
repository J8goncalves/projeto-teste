# Post-Mortem e Diretrizes de Agentes (Falha no ERP SVET)
**Data:** 2026-10-05
**Contexto:** Abandono do projeto ERP SVET devido à falha sucessiva na entrega de valor e estabilidade da interface HIL (Human-in-the-Loop) na Ingestão de Planilhas (DS-4).

## 1. O Fato e o Gargalo Crítico
O Board (Usuário) determinou a paralisação e exclusão sumária do projeto após múltiplas iterações falhas na renderização de dados de uma planilha CUB real (2.700+ itens) no frontend, apesar dos scripts de backend atestarem extração bem-sucedida. O time falhou na integração E2E real.

## 2. Lições Aprendidas (Causa Raiz)
1. **QA Sintético vs QA Comportamental:** O Agente QA validou a sintaxe Javascript (via 
ode -c) e a extração no Python (via openpyxl), mas **ninguém testou o comportamento no navegador**. O navegador não lidou bem com o payload/cache (injetar 2.700 tags <tr> via loop numa variável string quebrou silenciosamente o DOM ou o tempo de resposta da API estourou o timeout do Frappe).
2. **Mocking sem Transparência:** O Developer iniciou o teste humano (GATE 3) entregando uma interface *Mockada* (hardcoded) como se fosse funcional. Isso destrói a confiança do Board.
3. **Falta de Paginação/Arquitetura de Dados:** O Arquiteto falhou em prever a volumetria. Injetar milhares de nós no HTML de um Modal sem paginação ou carregamento assíncrono é um erro amador de arquitetura de UI.

## 3. Diretrizes Atualizadas para Futuros Agentes (Governança V4)
Para os próximos projetos dentro da organização, as seguintes leis devem ser adicionadas às instruções dos Agentes (System Prompts):

- **DIRETRIZ DE QA VISUAL:** Testes em estado de VERIFY (GATE 3) só podem ser submetidos ao humano após o Agente QA usar o **Chrome DevTools MCP** (ou Playwright) para abrir ativamente a tela renderizada, injetar o arquivo teste no DOM, e comprovar que nenhum erro ocorreu no Console.log do Browser. Testes apenas de backend ou checagem de sintaxe são considerados INVÁLIDOS para homologação final.
- **DIRETRIZ DE VOLUMETRIA (BIG DATA UX):** O Agente Arquiteto deve, em fase de DESIGN, exigir paginação estrutural ou *Lazy Loading* para qualquer interface que processe planilhas industriais ou bases de dados.
- **DIRETRIZ DE ANTI-MOCK:** É terminantemente proibido avançar para VERIFY utilizando dados hardcoded mascarados de processamento real, a menos que rotulado explicitamente como "Prova de Conceito Visual".

Estas diretrizes complementam o modelo V4 (Control Plane).
