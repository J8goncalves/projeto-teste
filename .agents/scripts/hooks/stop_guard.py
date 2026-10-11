import sys
import json
import os
import re
from pathlib import Path

def resolve_workspace_root(data):
    wp = data.get("workspacePaths", [])
    if wp and isinstance(wp, list) and wp[0]:
        return Path(wp[0]).resolve()
    return Path(__file__).resolve().parents[3]

def get_actionable_pending_reviews(workspace_root, run_id):
    """
    Deriva pendencias reais a partir do contrato canonico de org_v5/control.py.
    Verifica artifacts submetidos sem review ACCEPT, e valida se o estado permite continuidade.
    """
    state_file = workspace_root / "runs" / run_id / "state.json"
    if not state_file.exists():
        return []
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        phase = st.get("phase", st.get("status", ""))
        # Estados terminais ou de escalonamento nao permitem progresso acionavel
        if phase in ("ESCALATED", "PAUSED", "CLOSED"):
            return []

        artifacts = st.get("artifacts", {})
        accepted = st.get("accepted", {})

        pending = []
        for art_id in artifacts.keys():
            if art_id not in accepted:
                pending.append(art_id)
        return pending
    except Exception:
        return []

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
        workspace_root = resolve_workspace_root(data)

        term_reason = data.get("terminationReason", "")
        error_msg = data.get("error", "")
        fully_idle = data.get("fullyIdle", True)
        conv_id = data.get("conversationId", "default")

        # 1. Se o termino foi por erro, STOP ou condicao fatal, sempre autorizar termino imediato
        if term_reason in ("error", "max_steps_exceeded") or error_msg or not fully_idle:
            print(json.dumps({"decision": "terminate", "reason": f"Termino autorizado por condicao de parada: {term_reason}"}))
            return

        stop_file = workspace_root / ".agents" / "state" / "STOP"
        if stop_file.exists():
            print(json.dumps({"decision": "terminate", "reason": "STOP ativo, encerramento permitido"}))
            return

        # 2. Obter run_id atual
        curr_run_file = workspace_root / "runs" / "CURRENT"
        current_run_id = "no_run"
        if curr_run_file.exists():
            try:
                current_run_id = curr_run_file.read_text(encoding="utf-8").strip() or "no_run"
            except Exception:
                current_run_id = "no_run"

        # 3. Derivar pendencias reais do modelo canonico de org_v5/control.py (R08)
        actionable_pending = get_actionable_pending_reviews(workspace_root, current_run_id) if current_run_id != "no_run" else []

        # 4. Chave de estado composta e isolada por run + conversa (R07)
        safe_conv = re.sub(r'[^a-zA-Z0-9_\-]', '_', conv_id)[:32] or "default"
        safe_run = re.sub(r'[^a-zA-Z0-9_\-]', '_', current_run_id)[:32] or "no_run"
        state_dir = workspace_root / ".agents" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"stop_attempts_{safe_run}_{safe_conv}.txt"

        attempts = 0
        if state_file.exists():
            try:
                attempts = int(state_file.read_text(encoding="utf-8").strip())
            except Exception:
                attempts = 0

        if actionable_pending and attempts < 2:
            attempts += 1
            state_file.write_text(str(attempts), encoding="utf-8")
            pending_desc = ", ".join(actionable_pending[:3])
            print(json.dumps({
                "decision": "continue",
                "reason": f"Pendencia acionavel detectada no modelo canonico ({pending_desc}). Tentativa {attempts}/2."
            }))
            return

        # Permitir encerramento e limpar estado da chave desta execucao
        if state_file.exists():
            try:
                state_file.unlink()
            except Exception:
                pass
        print(json.dumps({"decision": "terminate", "reason": "Sem pendencias verificaveis ou limite de tentativas atingido."}))

    except Exception as e:
        print(json.dumps({"decision": "terminate", "reason": f"Erro interno stop_guard: {str(e)}"}))

if __name__ == "__main__":
    main()
