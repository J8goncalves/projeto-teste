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
        
        # Check STOP
        stop_file = workspace_root / ".agents" / "state" / "STOP"
        if stop_file.exists():
            print(json.dumps({
                "injectSteps": [
                    {"ephemeralMessage": "KILL SWITCH ATIVO (.agents/state/STOP): Run parada imediatamente. Nao execute acoes modificadoras. Registre apenas relatorio de parada e aguarde o humano."}
                ]
            }))
            return

        # Check ESCALATED or PAUSED using canonical phase
        curr_file = workspace_root / "runs" / "CURRENT"
        if curr_file.exists():
            try:
                run_id = curr_file.read_text(encoding="utf-8").strip()
                st_file = workspace_root / "runs" / run_id / "state.json"
                if st_file.exists():
                    st = json.loads(st_file.read_text(encoding="utf-8"))
                    phase = st.get("phase", st.get("status", ""))
                    if phase in ("ESCALATED", "PAUSED"):
                        print(json.dumps({
                            "injectSteps": [
                                {"ephemeralMessage": f"ESTADO DA RUN: {phase}. Execucao congelada. Permitidas apenas operacoes de inspecao, auditoria e emissao de relatorio de bloqueio."}
                            ]
                        }))
                        return
            except Exception:
                pass

        print(json.dumps({}))
    except Exception as e:
        print(json.dumps({}))

if __name__ == "__main__":
    main()
