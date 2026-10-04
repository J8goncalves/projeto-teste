---
name: org-memory-ops
description: Procedimentos de memória da organização - pedir briefing, propor lições, revisar candidatos e promover o lote com aprovação humana. Use ao iniciar tarefa pesada, ao fechar um gate ou no estado LEARN. Nunca rode comandos memanto diretamente.
---

## Comandos Permitidos
- `python .agents/scripts/memory_ops.py brief --role <role>`
- `python .agents/scripts/memory_ops.py propose --type <type> --content "<texto>" --tags <tag1,tag2>`
- `python .agents/scripts/memory_ops.py list`
- `python .agents/scripts/memory_ops.py commit` (Somente o humano executa/autoriza)
- `python .agents/scripts/memory_ops.py export`
- `python .agents/scripts/memory_ops.py status`

*(Proibições: nunca use `memanto` diretamente. Nunca use `sync`, `edit`, `forget`, `upload`, `from-conversation` ou `answer` para registrar decisões).*

## Regras de Admissão, Confiança e Pontuação
- Apenas evidência com força suficiente é gravada: E1 (0.70 a 0.85) e E2 (0.90 a 1.00). Abaixo de 0.70 não é gravado.
- Cota por nível da run e validade restrita por tipo de dado.
- Tipos de memória permitidos e mapeamento: `RISK`, `INCIDENT`, `CONSTRAINT`.
- Tags: máximo de 5 tags por memória, incluindo referência obrigatória de fonte ou TTL (`ttl-*`).

## Redação
Cada memória deve ser um **princípio declarativo**, nunca um log de atividade ou relato.
- *Exemplo ruim:* "O usuário pediu para renomear o componente".
- *Exemplo bom:* "Componentes de interface usam PascalCase".
- *Exemplo ruim:* "Melhoramos a velocidade da API".
- *Exemplo bom:* "O tempo de resposta da API deve ficar abaixo de 200 ms com cache em Redis".

## Anti-padrões e Hipóteses Descartadas
- Log de atividade em vez de princípio.
- Acúmulo de memórias sem reuso ("isto importará para uma sessão nova daqui a 3 meses?").
- Conteúdo vago ou metadados ausentes.
- Duplicatas (faça um brief/consulta antes de gravar; se for para atualizar, use a tag/parâmetro `supersedes`).
- **Hipóteses descartadas:** Só registre como `learning` negativo se tiver EVID comprovando o descarte.

## Fluxo e Independência
- Cada papel tem independência; o briefing só é liberado em momentos em que não contamine a isenção de pesquisa (conforme regras em `memory.md`).
