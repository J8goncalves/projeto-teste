# Kit de revisão e remediação da Organização V5.1

Este kit foi preparado a partir do relatório de execução da run `run-pilot-v5-002` e do pacote **original** `org-v5-pilot-main-ready.zip` fornecido nesta conversa. Ele não substitui nem altera o código **mais recente** no computador do usuário; alterações locais feitas pelo Antigravity durante o piloto precisam ser inspecionadas antes de implementar a remediação.

Arquivos:

- `01-AUDITORIA-E-PLANO-V5.1.md`: avaliação independente, diferenças entre relatado/constatado, prioridades P0–P2, arquitetura-alvo, fases e critérios de saída.
- `02-PROMPT-ANTIGRAVITY-V5.1.md`: prompt de execução para o Antigravity aplicar as correções no repositório de teste sem apagar histórico ou produzir falso PASS.
- `03-MATRIZ-DE-TESTES.md`: 30 cenários de regressão, integração e E2E, incluindo validações negativas contra falsificação de papéis, aprovações e resultados.

## Como utilizar

1. Leia a auditoria, destacando os controles P0.
2. Abra no Antigravity a versão mais atual do `J8goncalves/projeto-teste` e forneça o prompt com os dois outros arquivos como referência.
3. O Antigravity deverá começar auditando a **branch local real** e os artefatos históricos, depois propor/aplicar mudanças incrementais, com testes e logs.
4. Não publique uma declaração de `PASS` integral da V5.1 sem evidência independente. Não atribua autoria humana ou de subagente a registros autoindicados pelo modelo.

**Limitação:** não foi possível inspecionar remotamente a branch do piloto nesta revisão. O conector GitHub retornou 404 em consultas anteriores. Não alegamos que este kit já foi commitado ou aplicado.
