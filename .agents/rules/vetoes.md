---
trigger: model_decision
description: "Aplique ao emitir, receber ou resolver um veto, bloqueio crítico, override ou escalonamento."
---
# Política de vetos

## Quem pode vetar
`critical-reviewer`, `legal-compliance` (Discovery); `security-reviewer`, `qa`, `devops-finops` (Delivery).

## Severidade mínima
Só veto de severidade CRITICAL ou HIGH bloqueia. MEDIUM e LOW viram achados no backlog e não param o fluxo.
- CRITICAL: violação legal clara; exploração de vulnerabilidade comprovada; perda de dados; custo acima de 2 vezes o orçamento; premissa central invalidada por evidência.
- HIGH: falha relevante com caminho de correção conhecido; ausência de observabilidade ou de rollback; requisito intestável; custo acima do orçamento aprovado.

## Conteúdo obrigatório
Todo veto traz evidência (EVID, teste reprodutível, link verificável) e pelo menos uma remediação. Sem isso, não é veto: é comentário.

## Fluxo
1. O agente registra o evento VETO (`events.py append --type VETO ...`).
2. O `orchestrator` congela a transição e devolve ao responsável (`developer`, `architect` ou `product-manager`) com a remediação.
3. O responsável corrige e pede nova avaliação. Quem recebeu o veto não pode ignorá-lo nem reclassificá-lo.
4. No máximo 3 ciclos (veto, correção, nova avaliação). No 4º, a run vai para ESCALATED.
5. Fechamento: quem confirma que a remediação resolveu registra `VETO_CLOSED` com resultado FIXED. Se houve escalonamento, o humano decide e o resultado é registrado em `VETO_CLOSED`: ACCEPT (o veto vale; replanejar), REJECT (veto improcedente; justificativa obrigatória) ou OVERRIDE (o humano assume o risco, com dono, prazo e mitigação; registre também o evento `OVERRIDE`; vira DEC e uma memória `fact` com tag `risk-open`). `sem_veto_aberto` só é verdadeiro quando todo VETO tem `VETO_CLOSED`.

## Quem pode sobrepor
Security, Legal e DevOps/FinOps: somente o humano. Critical Reviewer: o `ceo` recomenda (Nível 3) e o humano decide; no Nível 2, qualquer veto não resolvido no 1º ciclo vai ao humano.

## Calibração
`python .agents/scripts/events.py stats` mostra vetos por agente (procedentes, rejeitados). Agente com mais da metade dos vetos rejeitados em 10 runs, ou que nunca veta nos casos com falha plantada (`evals/`), tem o card revisto no Agent CI.
