import os

os.makedirs('intelligence/decisions', exist_ok=True)

t1 = """# Decision Memo

**DEC:** [DEC-###]   **Run:** [RUN-AAAA-MM-NNNN]   **Iniciativa:** [slug]
**Autor:** [ceo ou nome_do_humano]
**Data:** [AAAA-MM-DD]

## 1. Veredito Recomendado e Confiança
- **Veredito:** [GO / GO CONDICIONADO / VALIDAR ANTES / PIVOT / NO-GO]
- **Confiança:** [Baixa / Média / Alta]

## 2. Pergunta de Decisão e Contexto
- [problema, impacto e oportunidade]

## 3. Premissas Críticas
| Premissa | EVID | Força | Status |
| :--- | :--- | :-: | :--- |

## 4. Síntese (até 5 linhas por item, com link para o original)
- Mercado e concorrência (`market-researcher`):
- Consumidor (`customer-researcher`):
- Estratégia de produto e requisitos de UX (`product-strategist`):
- Go-to-market (`marketing-strategist`, se ativo):
- Risco, compliance e jurídico (`critical-reviewer`, `legal-compliance`):

## 5. Divergências do Comitê
- [posições, evidências e como foram tratadas; ou escaladas ao humano]

## 6. Opções de Decisão (obrigatório apenas no Nível 3)
- **Opção A (Recomendada):** prós e contras
- **Opção B (Conservadora):** prós e contras
- **Opção C (Ousada):** prós e contras

## 7. Condições e Próximos Passos do Veredito
- GO CONDICIONADO: condição | dono | prazo | como verificar
- VALIDAR ANTES: o que validar | critério de sucesso | como
- PIVOT: nova hipótese | o que muda
- NO-GO: motivo registrado

## 8. O que mudaria esta recomendação
- [fatos ou resultados que inverteriam o veredito]

## 9. Decisões Pendentes do Humano
- [ ] Aprovar: [decisão]
- [ ] Aprovar orçamento e tempo: [estimativa]
- [ ] Próximo passo após aprovação: acionar `product-manager` com o Handoff Package.

## 10. Fontes
- [EVID e links]
"""

t2 = """# Decision Package

**Run:** [RUN-AAAA-MM-NNNN]   **Iniciativa:** [slug]   **Nível:** [1, 2 ou 3]
**Montado por:** `orchestrator` (de forma mecânica, sem opinião)
**Data:** [AAAA-MM-DD]

## Pergunta de decisão
[uma frase]

## Premissas críticas e força da evidência
| Premissa | EVID | Força | Status |
| :--- | :--- | :-: | :--- |

## Divergências entre agentes
[quem diverge, em quê, evidências de cada lado, rodadas de debate usadas]

## Vetos abertos
[eventos VETO sem VETO_CLOSED, ou "nenhum"]

## Riscos abertos
[riscos e RISK-IDs, ou "nenhum"]

## Custo consumido
[invocações usadas, limite do nível, percentual]

## Artefatos originais
[caminhos: market-research, customer-research, product-strategy, gtm-strategy (se houver), critical-review, legal-compliance-review (se houver), validation-plan e experiment-result (se houver), tracking-plan]
"""

t3 = """# Handoff Package

**DEC:** [DEC-###]   **Run:** [RUN-AAAA-MM-NNNN]   **Iniciativa:** [slug]
**Montado por:** `orchestrator`, com o escopo do `product-strategist`
**Data:** [AAAA-MM-DD]

## Escopo do MVP
- IN:
- OUT:

## Not Doing List
[itens e motivo]

## North Star e critérios de sucesso e de kill
[métricas, limiares, janela]

## Restrições jurídicas e de compliance
[linhas prontas para virar REQ, cada uma com a fonte no parecer do `legal-compliance`. Exemplo de formato: "Todos os dados de log devem ser anonimizados. Fonte: legal-compliance-review.md, seção X."]

## Diretrizes de negócio
[restrições de negócio, por exemplo "KISS. Solução local primeiro."; decisões de arquitetura são do `architect`]

## Condições (se GO CONDICIONADO)
[condição | dono | prazo | verificação]

## Orçamento e nível
[nível, limite de invocações, limite de gasto]

## Artefatos originais
[links obrigatórios; o `product-manager` lê os originais, não só este resumo]
"""

with open('intelligence/decisions/_TEMPLATE-decision-memo.md', 'w', encoding='utf-8') as f: f.write(t1)
with open('intelligence/decisions/_TEMPLATE-decision-package.md', 'w', encoding='utf-8') as f: f.write(t2)
with open('intelligence/decisions/_TEMPLATE-handoff-package.md', 'w', encoding='utf-8') as f: f.write(t3)
