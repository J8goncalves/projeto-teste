import sys
import json
import os
from pathlib import Path

def resolve_workspace_root(data):
    wp = data.get("workspacePaths", [])
    if wp and isinstance(wp, list) and wp[0]:
        return Path(wp[0]).resolve()
    return Path(__file__).resolve().parents[3]

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
        # Sanitize conv_id for file name
        safe_conv = "".join(c for c in conv_id if c.isalnum() or c in ("-", "_"))[:64] or "default"

        # Regra 1: Se o termino foi por erro ou max_steps_exceeded, ou erro presente, sempre permitir
        if term_reason in ("error", "max_steps_exceeded") or error_msg or not fully_idle:
            print(json.dumps({"decision": "terminate", "reason": f"Termino autorizado por condicao de parada: {term_reason}"}))
            return

        # Regra 2: Se STOP estiver ativo
        stop_file = workspace_root / ".agents" / "state" / "STOP"
        if stop_file.exists():
            print(json.dumps({"decision": "terminate", "reason": "STOP ativo, encerramento permitido"}))
            return

        # Regra 3: Limite de tentativas isolado por sessao / conversa (P1-09)
        state_dir = workspace_root / ".agents" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"stop_attempts_{safe_conv}.txt"
        
        attempts = 0
        if state_file.exists():
            try:
                attempts = int(state_file.read_text(encoding="utf-8").strip())
            except Exception:
                attempts = 0

        # Verificar se ha pendencia verificavel (ex: CURRENT run tem artefato submitted sem review)
        has_verifiable_pending = False
        pending_desc = ""
        curr_run_file = workspace_root / "runs" / "CURRENT"
        if curr_run_file.exists():
            try:
                run_id = curr_run_file.read_text(encoding="utf-8").strip()
                st_file = workspace_root / "runs" / run_id / "state.json"
                if st_file.exists():
                    st = json.loads(st_file.read_text(encoding="utf-8"))
                    pending_reviews = st.get("pending_reviews", [])
                    if pending_reviews:
                        has_verifiable_pending = True
                        pending_desc = f"Artefatos pendentes de revisao: {pending_reviews}"
            except Exception:
                pass

        if has_verifiable_pending and attempts < 2:
            attempts += 1
            state_file.write_text(str(attempts), encoding="utf-8")
            print(json.dumps({
                "decision": "continue",
                "reason": f"Pendencia verificavel detectada ({pending_desc}). Tentativa {attempts}/2."
            }))
            return

        # Permitir encerramento e limpar estado da sessao
        if state_file.exists():
            try:
                state_file.unlink()
            except Exception:
                pass
        print(json.dumps({"decision": "terminate", "reason": "Sem pendencias verificaveis ou limite atingido."}))

    except Exception as e:
        print(json.dumps({"decision": "terminate", "reason": f"Erro interno stop_guard: {str(e)}"}))

if __name__ == "__main__":
    main()
