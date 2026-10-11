import sys
import json
import os
import datetime

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
        invocation_num = data.get("invocationNum", 0)
        conversation_id = data.get("conversationId", "unknown")

        current_run = None
        if os.path.exists("runs/CURRENT"):
            with open("runs/CURRENT", "r", encoding="utf-8") as f:
                current_run = f.read().strip()

        if current_run:
            run_dir = f"runs/{current_run}"
            os.makedirs(run_dir, exist_ok=True)
            usage_file = os.path.join(run_dir, "usage.jsonl")

            # Check if this conversation + invocationNum was already logged
            already_logged = False
            existing_count = 0
            if os.path.exists(usage_file):
                with open(usage_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        existing_count += 1
                        try:
                            entry = json.loads(line)
                            if entry.get("conversation_id") == conversation_id and entry.get("invocation_num") == invocation_num:
                                already_logged = True
                        except Exception:
                            pass

            if not already_logged:
                entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "conversation_id": conversation_id,
                    "invocation_num": invocation_num,
                    "model_name": data.get("modelName", "auto")
                }
                with open(usage_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                existing_count += 1

            # Check budget limits from levels.json
            level = 1
            state_file = os.path.join(run_dir, "state.json")
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        st = json.load(f)
                        level = st.get("level", st.get("nivel", 1))
                except Exception:
                    pass

            limit = 120
            levels_file = ".agents/policies/levels.json"
            if os.path.exists(levels_file):
                try:
                    with open(levels_file, "r", encoding="utf-8") as f:
                        lv_data = json.load(f)
                        limit = lv_data.get("niveis", {}).get(str(level), {}).get("invocacoes_max", 120)
                except Exception:
                    pass

            pct = existing_count / limit if limit > 0 else 0
            if pct >= 1.0:
                print(json.dumps({
                    "injectSteps": [
                        {"ephemeralMessage": f"AVISO DE ORCAMENTO: Limite de invocacoes atingido ({existing_count}/{limit}). Encerramento governado da execucao."}
                    ],
                    "terminationBehavior": "terminate"
                }))
                return
            elif pct >= 0.8:
                print(json.dumps({
                    "injectSteps": [
                        {"ephemeralMessage": f"AVISO DE ORCAMENTO: Run atingiu {int(pct*100)}% do limite ({existing_count}/{limit} invocacoes)."}
                    ]
                }))
                return

        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"postinvocation_budget exception: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
