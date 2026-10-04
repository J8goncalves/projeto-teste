# Fluxo Nível 2

- INTAKE com Gate 0 automático.
- DISCOVERY enxuto:
  - `market-researcher` e `customer-researcher` (cache de fontes compartilhado).
  - Depois, `product-strategist`.
  - Depois, `critical-reviewer` (e `legal-compliance` com gatilho; `marketing-strategist` se monetização estiver na decisão; `experiment-designer` se premissa crítica estiver abaixo de E1).
  - `data-analytics` produz o tracking plan.
- Elaboração do Decision Package.
- Gate 1: humano decide analisando o pacote diretamente (sem recomendação do `ceo`).
- PLANNING: `product-manager` assume, com revisão de testabilidade feita pelo `qa`.
- DESIGN: `architect` elabora de forma enxuta junto com `security-reviewer` e `devops-finops`.
- Gate 2 automático.
- BUILD.
- VERIFY: CI local, depois `qa` e `security-reviewer` em paralelo; o `architect` revisa o PR.
- Gate 3 e Gate 4 (decisões pelo humano).
- PRODUCTION.
- MEASURE (`data-analytics` reporta as métricas).
- LEARN (até 3 memórias geradas).
