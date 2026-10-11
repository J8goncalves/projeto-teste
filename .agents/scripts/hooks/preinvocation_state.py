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
        
        # Check STOP
        if os.path.exists(".agents/state/STOP"):
            print(json.dumps({
                "injectSteps": [
                    {"ephemeralMessage": "KILL SWITCH ATIVO (.agents/state/STOP): Run parada imediatamente. Nao execute acoes modificadoras. Registre apenas relatorio de parada e aguarde o humano."}
                ]
            }))
            return

        # Check ESCALATED or PAUSED
        current_run = None
        if os.path.exists("runs/CURRENT"):
            with open("runs/CURRENT", "r", encoding="utf-8") as f:
                current_run = f.read().strip()

        if current_run and os.path.exists(f"runs/{current_run}/state.json"):
            try:
                with open(f"runs/{current_run}/state.json", "r", encoding="utf-8") as f:
                    st = json.load(f)
                    status = st.get("status", "")
                    if status in ("ESCALATED", "PAUSED"):
                        print(json.dumps({
                            "injectSteps": [
                                {"ephemeralMessage": f"ESTADO DA RUN: {status}. Execucao congelada. Permitidas apenas operacoes de inspecao, auditoria e emissao de relatorio de bloqueio."}
                            ]
                        }))
                        return
            except Exception:
                pass

        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"preinvocation_state exception: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
