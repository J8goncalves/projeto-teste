---
name: org-decision-docs
description: Templates e regras de preenchimento do Decision Package, do memo curto de decisão e do Handoff Package. Use ao montar o pacote para o Gate 1, ao recomendar uma decisão ou ao entregar o escopo à engenharia.
---

## Documentos e Responsáveis

1. **Decision Package:**
   - Elaborado pelo `orchestrator` de forma puramente mecânica e estrutural.
   - Reúne os originais e resumos sem síntese avaliativa.

2. **Memo Curto de Decisão:**
   - Elaborado pelo `ceo` (no Nível 3) como recomendação, ou preenchido pelo humano (no Nível 2) usando o template.
   - Contém opções A, B e C, evidências a favor e contra, e a linha de corte ("o que mudaria essa decisão").

3. **Handoff Package:**
   - Elaborado pelo `orchestrator` reunindo o escopo e diretrizes estipulados pelo `product-strategist`.

## Preenchimento e Obrigatoriedade
- **Nível 1:** Sem memo e sem decision package formal.
- **Nível 2:** Decision Package avaliado diretamente pelo humano.
- **Nível 3:** Decision Package + Memo com recomendação e opções + Handoff completo e formal.

**Templates:** 
Utilize sempre os modelos presentes no diretório `intelligence/decisions/` quando for gerar o conteúdo:
- `_TEMPLATE-decision-memo.md`
- `_TEMPLATE-decision-package.md`
- `_TEMPLATE-handoff-package.md`
