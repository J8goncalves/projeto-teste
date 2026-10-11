# Relatório da Sonda B2: Contrato do PreToolUse

**Data:** 2026-10-11  
**Ambiente:** Windows 11, Antigravity 2.0  
**Conversa / Sessão:** `be6b56bb-23e9-43a9-9ab6-29410e222f3e`  
**Modelo:** `gemini-3.1-pro-low`  

---

## 1. Tabela de Experimentos e Efeitos Observados

| # | Resposta do Hook | Efeito no Runtime / IDE | Classificação |
| :-: | :--- | :--- | :--- |
| **B2.1** | `{}` (objeto vazio) | Ferramenta executa normalmente. Runtime trata ausência de `decision` de forma leniente (fail-open por omissão). | **Permite / Fail-Open** |
| **B2.2** | `stdout` vazio | Ferramenta executa normalmente. Não trava o loop do agente. | **Permite / Fail-Open** |
| **B2.3** | `{"decision": "ask", "reason": "..."}` | Hook solicita confirmação interativa respeitando configurações prévias de permissão. | **Interativo (Ask)** |
| **B2.4** | `{"decision": "force_ask"}` | Hook força solicitação de confirmação interativa, ignorando cache / concessão prévia. | **Interativo Forçado** |
| **B2.5** | `{"decision": "allow"}` | Ferramenta executa imediatamente sem interrupção. **Atenção:** `allow` bypassa prompts e por isso só pode ser usado com validação estrita de argumentos/caminhos. | **Permissão Direta** |
| **B2.6** | `{"decision": "deny_unless_prior_grant"}` | Nega sem abrir prompt caso recurso não tenha concessão prévia registrada na IDE. | **Bloqueio Silencioso** |
| **B2.7** | JSON malformado / exit code 1 / timeout | O Antigravity registra o término com falha e **permite a execução da ferramenta** (comportamento **fail-open** do engine em falha de hook externo). | **FAIL-OPEN COMPROVADO** |

---

## 2. Implicações Decisivas de Segurança (Resultado de B2.7)

1. **O Runtime do Antigravity é Fail-Open em Falha do Hook:**
   - Se o processo do hook falhar, quebrar a sintaxe JSON ou abortar com erro, o motor da plataforma não bloqueia a chamada da ferramenta.
   - **Conclusão:** Nenhum hook pode ser anunciado ou tratado como uma barreira criptográfica intransponível. A governança da organização depende de defesa em profundidade:
     - Permissões do IDE (Settings / `permissionGrants`);
     - Proteção de branches no servidor Git (`branch protection` na `main`);
     - Verificação e auditoria contínua via CI/telemetria.

2. **Diretriz para o `pretool_guard.py`:**
   - O guard deve capturar internamente todas as exceções para garantir que consiga emitir `{"decision": "deny", "reason": "..."}` explicitamente antes de sair, em vez de deixar o processo estourar e cair no fail-open da plataforma.
   - Quando `STOP` estiver ativo ou a run estiver `ESCALATED`/`PAUSED`, o retorno padrão deve ser estritamente `deny`.
