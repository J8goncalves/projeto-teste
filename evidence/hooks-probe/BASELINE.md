# Baseline de Hooks e Ambiente - V5.2 Entrega 1

**Data:** 2026-10-11  
**Branch:** `feature/v5.2-entrega-1-hooks`  
**Commit Base:** `124faa59f41f5b0e9effcb065a7c774ff647edeb`  

---

## 1. Inventário de Arquivos e Configurações de Hooks

### 1.1 Configuração Local (`.agents/hooks.json`)
O arquivo `.agents/hooks.json` encontra-se com os 4 grupos definidos porém desativados (`enabled: false`) e com arrays de handlers vazios:
```json
{
  "org-guard": {"enabled": false, "PreToolUse": []},
  "org-budget": {"enabled": false, "PostInvocation": []},
  "org-state": {"enabled": false, "PreInvocation": []},
  "org-events": {"enabled": false, "PostToolUse": []}
}
```

### 1.2 Configuração Global e Plugins
- `~/.gemini/config/hooks.json`: Não existe no sistema (`The system cannot find the file specified`).
- Nenhuma interceptação global ativa via pasta de configuração de usuário.

### 1.3 Handlers Existentes em `.agents/scripts/hooks/`
- `.agents/scripts/hooks/pretool_guard.py`: 0 bytes (vazio).
- `.agents/scripts/hooks/posttool_events.py`: 380 bytes (retorna `{}` passivo).
- `.agents/scripts/hooks/postinvocation_budget.py`: 386 bytes (retorna `{}` passivo).
- `.agents/scripts/hooks/preinvocation_state.py`: 627 bytes (injeta aviso se `.agents/state/STOP` existir).

---

## 2. Ambiente de Execução e Python Runtime

- **Sistema Operacional:** Windows 11 (Windows 10.0.26100), Shell PowerShell 5.1.
- **Python no PATH Global:** `python` e `py` falham (apontam para stubs da Microsoft Store ou comandos não configurados).
- **Interpretador Venv Funcional:**
  `D:\Antigravity Projects\projeto-teste\.venv\Scripts\python.exe` (Python 3.14.8).
- **Diretriz de Hooks:** Todos os comandos de hooks configurados em `.agents/hooks.json` devem invocar expressamente `.\\.venv\\Scripts\\python.exe` ou caminho absoluto do executável venv para garantir portabilidade e execução confiável.

---

## 3. Estado de Governança e Proteções
- **Trava de Proteção:** `.agents/state/PROTECT_ORG` está ativo (`LOCKED`).
- Nenhuma alteração destrutiva ou manutenção nos arquivos do Core (`.agents/`, `org_v5/`) pode ocorrer sem log de auditoria e liberação explícita.

---

## 4. Resultados da Suíte de Testes Existente (Baseline)

Comando executado:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Contagem de Testes:
- **Total de testes:** 66
- **Testes Aprovados (Passed):** 65
- **Falhas (Failures):** 0
- **Erros (Errors):** 0
- **Ignorados (Skipped):** 1 (`test_scenario_7c_fast_recall_and_status_without_ollama` - AI Memory on-prem live backend indisponível em runtime de teste isolado)
- **Tempo de Execução:** 12.981s
- **Status Geral:** 100% dos testes executados com sucesso (OK).

---

## 5. Limites de Observabilidade dos Hooks no Runtime Atual
- A plataforma Antigravity executa os hooks via stdin/stdout em processos filhos sincronizados com as ferramentas e invocações.
- As saídas para `stderr` são descartadas ou capturadas em logs internos da ferramenta; portanto, todo log de telemetria ou auditoria de hook deve ser persistido em arquivo local (`telemetry/events.jsonl`, `.agents/state/hook-errors.log`) com codificação UTF-8 sem BOM.
- Os retornos via stdout devem ser JSON estrito em uma única linha ou bloco parseável (`sys.stdout.reconfigure(encoding='utf-8')`).
