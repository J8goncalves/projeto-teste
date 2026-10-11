import sys
import json
import os
import datetime
import re
from pathlib import Path

def resolve_workspace_root(data):
    wp = data.get("workspacePaths", [])
    if wp and isinstance(wp, list) and wp[0]:
        return Path(wp[0]).resolve()
    return Path(__file__).resolve().parents[3]

def resolve_run_id(data, args, workspace_root):
    # 1. Environment variable
    env_run = os.environ.get("AGY_RUN_ID", "").strip()
    if env_run:
        return env_run

    # 2. Data payload
    for k in ("runId", "run_id", "run"):
        val = str(data.get(k, "")).strip()
        if val:
            return val

    # 3. Tool args
    for k in ("run_id", "run", "runId"):
        val = str(args.get(k, "")).strip()
        if val:
            return val

    cmd = args.get("CommandLine", "")
    if isinstance(cmd, str) and cmd:
        m = re.search(r'--run\s+([A-Za-z0-9_-]+)', cmd)
        if m:
            return m.group(1).strip()

    # 4. runs/CURRENT (only if directory runs/<run_id> actually exists)
    curr_file = workspace_root / "runs" / "CURRENT"
    if curr_file.exists():
        try:
            cand = curr_file.read_text(encoding="utf-8").strip()
            if cand and (workspace_root / "runs" / cand).is_dir():
                return cand
        except Exception:
            pass

    # 5. Fallback: unassigned
    return None

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({}))
            return

        data = json.loads(raw_input)
        workspace_root = resolve_workspace_root(data)

        tool_call = data.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        step_idx = data.get("stepIdx", 0)
        conversation_id = data.get("conversationId", "")
        error_msg = data.get("error", "")

        run_id = resolve_run_id(data, args, workspace_root)

        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event_type": "TOOL_CALL",
            "run_id": run_id,
            "conversation_id": conversation_id,
            "step_idx": step_idx,
            "tool_name": tool_name,
            "status": "ERROR" if error_msg else "SUCCESS",
            "error": error_msg
        }

        # Subagent delegation handling
        if tool_name == "invoke_subagent":
            subagents_spec = args.get("Subagents", [])
            delegations = []
            for sub in subagents_spec:
                delegations.append({
                    "role": sub.get("Role", "UNKNOWN"),
                    "type_name": sub.get("TypeName", "UNKNOWN"),
                    "model": sub.get("Model", "inherit"),
                    "assurance": "UNVERIFIED/ROLE_ONLY"
                })
            event["delegations"] = delegations
            event["event_type"] = "SUBAGENT_DELEGATION"

        # Canonical run write
        if run_id:
            run_telem_dir = workspace_root / "runs" / run_id / "telemetry"
            run_telem_dir.mkdir(parents=True, exist_ok=True)
            with open(run_telem_dir / "events.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Global workspace write (dual write)
        global_telem_dir = workspace_root / "telemetry"
        global_telem_dir.mkdir(parents=True, exist_ok=True)
        with open(global_telem_dir / "events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print(json.dumps({}))
    except Exception as e:
        try:
            err_log = workspace_root / ".agents" / "state" / "hook-errors.log"
            err_log.parent.mkdir(parents=True, exist_ok=True)
            with open(err_log, "a", encoding="utf-8") as f:
                f.write(f"posttool_events exception: {str(e)}\n")
        except Exception:
            pass
        print(json.dumps({}))

if __name__ == "__main__":
    main()
