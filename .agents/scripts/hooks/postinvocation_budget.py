import sys
import json
import os
import datetime
from pathlib import Path

def resolve_workspace_root(data):
    wp = data.get("workspacePaths", [])
    if wp and isinstance(wp, list) and wp[0]:
        return Path(wp[0]).resolve()
    return Path(__file__).resolve().parents[3]

def resolve_run_id(data, workspace_root):
    env_run = os.environ.get("AGY_RUN_ID", "").strip()
    if env_run:
        return env_run
    for k in ("runId", "run_id", "run"):
        val = str(data.get(k, "")).strip()
        if val:
            return val
    curr_file = workspace_root / "runs" / "CURRENT"
    if curr_file.exists():
        try:
            cand = curr_file.read_text(encoding="utf-8").strip()
            if cand and (workspace_root / "runs" / cand).is_dir():
                return cand
        except Exception:
            pass
    return None

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
        workspace_root = resolve_workspace_root(data)
        invocation_num = data.get("invocationNum", 0)
        conversation_id = data.get("conversationId", "unknown")

        current_run = resolve_run_id(data, workspace_root)

        if current_run:
            run_dir = workspace_root / "runs" / current_run
            run_dir.mkdir(parents=True, exist_ok=True)
            usage_file = run_dir / "usage.jsonl"

            # Check if this conversation + invocationNum was already logged
            already_logged = False
            existing_count = 0
            if usage_file.exists():
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
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "conversation_id": conversation_id,
                    "invocation_num": invocation_num,
                    "model_name": data.get("modelName", "auto")
                }
                with open(usage_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                existing_count += 1

            # Check budget limits from levels.json
            level = 1
            state_file = run_dir / "state.json"
            if state_file.exists():
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        st = json.load(f)
                        level = st.get("level", st.get("nivel", 1))
                except Exception:
                    pass

            limit = 120
            levels_file = workspace_root / ".agents" / "policies" / "levels.json"
            if levels_file.exists():
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
        try:
            err_log = workspace_root / ".agents" / "state" / "hook-errors.log"
            err_log.parent.mkdir(parents=True, exist_ok=True)
            with open(err_log, "a", encoding="utf-8") as f:
                f.write(f"postinvocation_budget exception: {str(e)}\n")
        except Exception:
            pass
        print(json.dumps({}))

if __name__ == "__main__":
    main()
