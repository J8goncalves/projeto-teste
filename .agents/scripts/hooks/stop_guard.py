import sys
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
os.chdir(workspace_root)

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
        term_reason = data.get("terminationReason", "")
        error_msg = data.get("error", "")
        fully_idle = data.get("fullyIdle", True)

        # Regra 1: Se o termino foi por erro ou max_steps_exceeded, ou erro presente, sempre permitir
        if term_reason in ("error", "max_steps_exceeded") or error_msg or not fully_idle:
            print(json.dumps({"decision": "terminate", "reason": f"Termino autorizado por condicao de parada: {term_reason}"}))
            return

        # Regra 2: Verificar se STOP esta ativo
        if os.path.exists(".agents/state/STOP"):
            print(json.dumps({"decision": "terminate", "reason": "STOP ativo, encerramento permitido"}))
            return

        # Regra 3: Limite de tentativas de continue (maximo 2)
        state_file = ".agents/state/stop_attempts.txt"
        attempts = 0
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    attempts = int(f.read().strip())
            except Exception:
                attempts = 0

        # Verificar se ha pendencia verificavel (ex: CURRENT run tem artefato submitted sem review)
        current_run = None
        has_verifiable_pending = False
        pending_desc = ""
        if os.path.exists("runs/CURRENT"):
            with open("runs/CURRENT", "r", encoding="utf-8") as f:
                current_run = f.read().strip()
        if current_run and os.path.exists(f"runs/{current_run}/state.json"):
            try:
                with open(f"runs/{current_run}/state.json", "r", encoding="utf-8") as f:
                    st = json.load(f)
                    pending_reviews = st.get("pending_reviews", [])
                    if pending_reviews:
                        has_verifiable_pending = True
                        pending_desc = f"Artefato pendente de revisao: {pending_reviews}"
            except Exception:
                pass

        if has_verifiable_pending and attempts < 2:
            attempts += 1
            os.makedirs(".agents/state", exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                f.write(str(attempts))
            print(json.dumps({
                "decision": "continue",
                "reason": f"Pendencia verificavel detectada ({pending_desc}). Tentativa {attempts}/2."
            }))
            return

        # Permitir encerramento
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
            except Exception:
                pass
        print(json.dumps({"decision": "terminate", "reason": "Sem pendencias verificaveis ou limite atingido."}))

    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"stop_guard exception: {str(e)}\n")
        print(json.dumps({"decision": "terminate", "reason": f"Erro interno stop_guard: {str(e)}"}))

if __name__ == "__main__":
    main()
