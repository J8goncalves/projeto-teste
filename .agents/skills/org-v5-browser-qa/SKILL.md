---
name: org-v5-browser-qa
description: Perform genuine interactive browser QA with click evidence, network and console inspection, and traceable acceptance checks.
---
# QA funcional — sem falsos positivos

1. Receba PRD/ADR e build já aceitos. Traduza cada AC-### em cenário positivo, negativo e borda.
2. Inicie ambiente real apropriado; guarde comando, URL e SHA do build. Se o ambiente não subir, status BLOCKED e nenhum PASS.
3. Com ferramenta de navegador/Playwright real, clique nos elementos reais, preencha formulários e confirme o estado visível, requisição, mensagem, navegação e persistência. Consulte erros de console e rede.
4. Registre para cada interação `target`, `action`, `expected`, `observed`, `evidence_ref`. Não use screenshot não verificada, mock de API como substituto de E2E, `page.route` para fabricar sucesso, `assertTrue(True)` ou `test.skip` oculto.
5. Guarde relatório e trace/vídeo/screenshot no caminho de evidência da run (sem dados pessoais); confira que os arquivos realmente existem. Execute testes de integração e E2E, guarde `command`, `exit_code` e `output_ref`.
6. `PASS` só após todos os ACs pertinentes passarem em ambiente real. Caso contrário: `FAIL` com reprodução e impacto, ou `BLOCKED` caso não seja possível executar.
7. Audite com `org_v5/contracts.py` (`qa-report`); revisor independente confere evidência antes de `ACCEPT`.
