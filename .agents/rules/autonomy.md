---
trigger: model_decision
description: "Aplique antes de executar ação com efeito externo ou irreversível (merge, push, deploy, gasto, dados pessoais, contratos, mudança de regras) e ao decidir quem decide: níveis de autonomia A0 a A3 e direitos de decisão."
---
# Autonomia e direitos de decisão

## Níveis
A0 somente humano. A1 a IA recomenda, o humano decide e executa. A2 a IA executa com aprovação prévia do humano. A3 a IA executa com monitoramento (o humano revisa depois, pelo log). A4 não existe nesta organização.

## Nível padrão por ação
| Ação | Nível | Quem aprova |
| :--- | :-: | :--- |
| Pesquisa em fontes públicas; hipóteses, PRD e histórias | A3 | Revisão posterior |
| Abrir PR; refatorar dentro do repositório | A3 | Revisão posterior |
| Merge na branch principal (Gate 3) | A2 | Humano |
| Deploy em staging | A3 | Revisão posterior |
| Deploy em produção (Gate 4) | A2 | Humano |
| Experimento com tráfego real ou anúncios | A2 | Humano, com orçamento definido |
| Alteração de arquitetura irreversível | A1 | Humano |
| Gasto (limite atual: qualquer gasto) ou serviço pago | A1 | Humano |
| Acesso ou migração de dados pessoais ou sensíveis | A1 | Humano |
| Contrato ou comunicação externa em nome da empresa | A0 | Humano |
| Decisão do Gate 1 | A1 | Humano |
| Alterar cards, regras, políticas, hooks, scripts | A1 | Humano, via PR |
| Instalar MCP, skill ou plugin | A2 | Humano |
| Gravar ou apagar memória (`commit`, `forget`) | A2 | Humano |

Promoção de A2 para A3 só após 10 runs consecutivas sem incidente nessa ação, avaliação sem regressão e aprovação humana registrada como DEC. Qualquer incidente relacionado rebaixa automaticamente.

## Direitos de decisão
| Decisão | Quem decide |
| :--- | :--- |
| Repetir pesquisa, pedir evidência extra, retry | `orchestrator`, dentro do orçamento |
| Ajuste de escopo sem mudar ICP, North Star, MVP nem orçamento | `orchestrator`, com `product-manager` e `product-strategist` |
| Mudança de ICP, North Star, MVP ou orçamento da run | `ceo` recomenda (Nível 3); humano decide |
| Conflito entre agentes sem veto | `orchestrator`, aplicando a política |
| Gate 1 | Humano |
| Gates 3 e 4 | Humano |
| Override de veto de Security, Legal ou DevOps/FinOps | Somente humano |
| Override de veto do Critical Reviewer | `ceo` recomenda (Nível 3); humano decide |

Quem não souber o nível de uma ação trata como A1.
