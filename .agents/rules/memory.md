---
trigger: model_decision
description: "Aplique ao consultar ou propor memória (Memanto), ao iniciar tarefa pesada, ao fechar um gate ou no LEARN: papéis dos repositórios de conhecimento, admissão, tipos, tags, validade, leitura e proibições."
---
# Memory Rules (Memanto)
1. O Memanto é o Chief of Staff de memória da organização. Ele cuida do conhecimento institucional.
2. Antes de iniciar qualquer tarefa pesada, receba o "Briefing" temporal (o que sabemos agora vs o que sabíamos antes) por `python .agents/scripts/memory_ops.py brief` (nunca rode `memanto` diretamente). O briefing só é liberado nos estados INTAKE, DISCOVERY, PLANNING, DESIGN e LEARN, com no máximo 5 itens.
3. A fonte da verdade de documentos finais (PRDs, ADRs) é o Markdown no repositório. O Memanto guarda fatos operacionais, decisões fragmentadas e aprendizados temporais.
4. Não insira "ruído" na memória. Apenas informações que mereçam sobreviver ao ciclo de vida da tarefa.

## Papéis dos três repositórios de conhecimento
- Repositório (`docs/`, `docs/adr/`, `intelligence/decisions/`): fonte da verdade dos documentos e das decisões.
- `intelligence/knowledge-base/`: conhecimento de domínio em documentos (mercados, concorrentes, clientes, jurídico). Cada arquivo novo começa com uma ficha: `evid` (IDs), `data`, `revisar_em`, `autor` (agente) e `fonte`.
- Memanto: lição destilada, curta e reutilizável, sempre com ponteiro para DEC ou EVID. Não guarda documentos nem transcrições.

## Escrita
- Agentes não escrevem no Memanto. Propõem candidatos com `memory_ops.py propose` (arquivo `runs/<run>/memory-candidates.jsonl`).
- A promoção acontece em momentos fixos: fechamento de gate, resolução de veto ou override, pós-incidente, estado LEARN e fim da run. Quem grava é `memory_ops.py commit`, com aprovação humana do lote (A2).
- Teste de admissão (todos): (a) vai influenciar decisão futura em outra run; (b) não é derivável barato do repositório (se estiver num documento, guarde só o ponteiro); (c) tem proveniência (ref a DEC ou EVID, origem, data); (d) é específica e acionável (afirmação mais condição de aplicação); (e) não é duplicada (atualize em vez de criar); (f) tem solidez: evidência E1 ou superior, ou marcada como hipótese com validade curta.
- Pontuação (0 a 2 cada): impacto, reuso, custo de redescobrir, solidez. Entra com soma de 5 ou mais e solidez de pelo menos 1.
- Cota por run: Nível 1 = 1, Nível 2 = 3, Nível 3 = 8.
- Hipótese descartada: o rascunho nunca entra. A hipótese invalidada por evidência entra como `learning` negativo (o que tentamos, por que falhou, EVID).

## Tipos e tags
- Tipos permitidos: `decision`, `learning`, `error`, `fact`, `instruction`, `commitment`, `goal`. RISK = `fact` com tag `risk-open`; INCIDENT = `error`; CONSTRAINT = `instruction`. Não usar por padrão: `observation`, `artifact`, `event`, `context`, `preference`, `relationship`.
- Redija cada memória como princípio declarativo, nunca como relato ("o usuário disse", "escolhemos", "concordamos").
- Confiança e proveniência: E1 grava entre 0,70 e 0,85; E2 entre 0,90 e 1,00; abaixo de 0,70 não se grava. `decision` só com proveniência `explicit_statement` ou `validated`. Nunca `imported`.
- Tags (2 a 5, minúsculas com hífen): referência `dec-014` e/ou `evid-032` (obrigatória), `run-aaaa-mm-nnnn`, um domínio e uma tag de validade `ttl-30d`, `ttl-90d`, `ttl-180d`, `ttl-2y` ou `ttl-never` (obrigatória para `fact`). Flags opcionais: `risk-open`, `method` (aprendizado metodológico), `pinned`.
- Validade: preços e concorrentes `ttl-90d`; regulação `ttl-180d`; estrutura de mercado `ttl-2y`; fatos internos `ttl-never`. A política de expiração do Memanto aplica as tags.

## Leitura
- Briefing mínimo: no máximo 5 itens, similaridade de 0,8 ou mais, confiança de 0,7 ou mais, só memórias ativas.
- Independência: `market-researcher`, `customer-researcher`, `critical-reviewer` e `legal-compliance` recebem, antes de entregar o parecer, apenas `fact`, `instruction` e `learning` com tag `method`. Conclusões anteriores (`decision`) só chegam depois, para reconciliação.
- Prefira `recall` (itens auditáveis com IDs). O comando `answer` sintetiza com LLM e não serve para decisões.

## Proibido
- Rodar `memanto remember`, `edit`, `forget`, `upload`, `migrate`, `memory sync`, `memory expire`, `memory restore`, `policy`, `schedule`, `connect`, `serve` ou `remember --from-conversation`.
- Gravar dados pessoais, segredos, transcrições, rascunhos, saídas intermediárias, logs ou documentos inteiros.
- Atualizar conteúdo com `edit`. Para atualizar, grave a nova memória com a tag `supersedes-<id>` e expire a antiga (o `commit` faz isso com aprovação).

## Manutenção
- A manutenção noturna do Memanto (resumo, detecção de conflitos, expiração) é ligada pelo humano. Conflitos de alto impacto vão ao humano.
- Exportação para auditoria em Markdown versionado (`docs/memory-export/`), por `memory_ops.py export`.
- Revisão humana mensal das memórias mais usadas e das expiradas. Memória sem uso em 60 dias é candidata a remoção.
- Privacidade: backend on-prem obrigatório para dados da empresa. Retenção: `events.jsonl` 12 meses; `usage.jsonl` 90 dias.
