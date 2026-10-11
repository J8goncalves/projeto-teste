# Observacoes preliminares transcritas (NAO capturadas em arquivo no momento)
Fonte: saida do terminal no transcript do orquestrador. Forca de evidencia: baixa (transcricao), nao reproduzivel.
- 01:03:41 python -m org_v5.cli memory-status => 'DENIED: AI Memory server is offline or unreachable; writes and recall disabled', exit=2
- 01:03:22 unittest discover -s tests (1o run, memoria offline) => 'Ran 49 tests ... OK (skipped=1)'
- 01:04:18 mesmo comando (2o run, memoria online) => 'Ran 49 tests ... OK' sem skip (arquivo baseline-tests.txt)
- Hipotese (nao provada): o skip decorre do teste de integracao de memoria ao vivo (tests/test_v5_1_1_hardening.py:370 skipTest), que pula quando o backend esta inacessivel.
