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
        if not raw_input.strip():
            print(json.dumps({}))
            return

        data = json.loads(raw_input)
        tool_call = data.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        step_idx = data.get("stepIdx", 0)
        conversation_id = data.get("conversationId", "")
        error_msg = data.get("error", "")

        # Extract current run
        current_run = None
        if os.path.exists("runs/CURRENT"):
            with open("runs/CURRENT", "r", encoding="utf-8") as f:
                current_run = f.read().strip()

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "TOOL_CALL",
            "run_id": current_run,
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

        # Record in telemetry
        os.makedirs("telemetry", exist_ok=True)
        with open("telemetry/events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"posttool_events exception: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
