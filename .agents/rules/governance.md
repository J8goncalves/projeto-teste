---
trigger: always_on
description: "Governança da organização de agentes: Dual-Track, níveis, gates, bloqueios, autonomia e papéis."
---
# Governance & Gates
1. Dual-Track Agile: Discovery Track e Delivery Track correm em paralelo e se falam. Enquanto uma fatia é construída (BUILD, VERIFY), o Discovery da próxima pode correr em outra run (no máximo 1 run em DISCOVERY e 1 em BUILD ou VERIFY ao mesmo tempo, salvo decisão humana). O estado de cada run fica em `runs/<run-id>/state.json` e só muda por `python .agents/scripts/state.py`, a pedido do `orchestrator` (ou do humano nos gates).
2. Níveis de análise (definidos no INTAKE pela skill `org-intake`; escolha o menor nível que atenda):
   - Nível 1 (Ajuste): ajuste, bug ou pergunta pontual, reversível. Sem Discovery, sem memo, sem CEO. Gate 3 (e Gate 4 se houver release).
   - Nível 2 (Enxuto): funcionalidade nova com incerteza moderada. Discovery enxuto, memo curto, sem CEO. Gates 0 (automático), 1, 2 (automático), 3 e 4.
   - Nível 3 (Completo): iniciativa ou produto novo, alto custo de erro, dado pessoal em escala, ação irreversível ou gasto. Discovery completo com experimento medido; o `ceo` recomenda. Gates 0 a 4.
   - Elevação obrigatória: dado pessoal exige no mínimo Nível 2 (com `legal-compliance` e `security-reviewer`); ação irreversível ou gasto acima do limite exige Nível 3.
3. Gates de Aprovação:
   - Gate 0 (Discovery): Entendemos o problema? Verificação automática no INTAKE (Nível 2+); o humano só entra se houver ambiguidade.
   - Gate 1 (Business): Existe evidência para investir? O `ceo` apenas recomenda (Nível 3); o HUMANO decide (A1) entre GO, GO CONDICIONADO, VALIDAR ANTES, PIVOT e NO-GO.
   - Gate 2 (Arch): A solução é tecnicamente viável e sustentável? Política aplicada por script com Security e DevOps/FinOps; o humano decide se a decisão for irreversível (A1).
   - Gate 3 (PR): Foi construído o que foi decidido? O merge exige aprovação humana (A2).
   - Gate 4 (Release): É seguro, observável e sustentável? O release exige aprovação humana (A2); `legal-compliance` participa quando houver dado pessoal.
   Critérios, donos e requisitos de cada gate: `.agents/policies/transitions.json`. Aprovações humanas são registradas por `state.py approve`.
4. Comunicação de Bloqueios: sempre retorne no formato TYPE, FROM, TO, ISSUE, IMPACT, RECOMMENDATION e acrescente SEVERITY, EVIDENCE, CYCLE e REF. Tipos: BLOCKER, QUESTION, SCOPE_CHANGE, RISK, COST_ALERT, VETO, VETO_CLOSED, ESCALATION, OVERRIDE. Registre com `python .agents/scripts/events.py append`. Detalhes de vetos em `vetoes.md`.
5. Autonomia: A0 a A3 por tipo de ação (`autonomy.md`). Nenhum agente eleva a própria autonomia.
6. Papéis: apenas o `orchestrator` invoca subagentes e pede transições de estado. Nenhum agente aprova o próprio trabalho. Agentes não executam `memanto` diretamente (`memory.md`).
7. Parada: se a run estiver em ESCALATED ou PAUSED, ou se existir o arquivo `.agents/state/STOP`, pare e aguarde o humano.
