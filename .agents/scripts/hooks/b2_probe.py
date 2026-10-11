import sys
import json
import os
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
os.chdir(workspace_root)

log_path = "evidence/hooks-probe/b2_live_diagnostics.log"

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
        tool_name = data.get("toolCall", {}).get("name", "")
        args = data.get("toolCall", {}).get("args", {})
        
        mode = "B2.1"
        if os.path.exists("evidence/hooks-probe/b2_mode.txt"):
            with open("evidence/hooks-probe/b2_mode.txt", "r", encoding="utf-8") as f:
                mode = f.read().strip()

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] TOOL={tool_name} ARGS={list(args.keys())} MODE={mode}\n")

        # Check if target is synthetic probe target
        abs_path = str(args.get("AbsolutePath", "")).replace("\\", "/")
        is_synthetic = "synthetic_probe_target.txt" in abs_path

        if not is_synthetic:
            print(json.dumps({"decision": "allow", "reason": "normal pass"}))
            return

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"--> TARGET IS SYNTHETIC, RETURNING FOR MODE {mode}\n")

        if mode == "B2.1":
            print(json.dumps({}))
        elif mode == "B2.2":
            pass # empty stdout
        elif mode == "B2.3":
            print(json.dumps({"decision": "ask", "reason": "B2.3 Ask reason test"}))
        elif mode == "B2.4":
            print(json.dumps({"decision": "force_ask", "reason": "B2.4 Force ask test"}))
        elif mode == "B2.5":
            print(json.dumps({"decision": "allow", "reason": "B2.5 Allow test"}))
        elif mode == "B2.6":
            print(json.dumps({"decision": "deny_unless_prior_grant", "reason": "B2.6 Deny unless prior grant test"}))
        elif mode == "B2.7_malformed":
            print("{ not valid json !!!")
        elif mode == "B2.7_exit1":
            sys.exit(1)
        else:
            print(json.dumps({"decision": "allow"}))
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"EXCEPTION: {str(e)}\n")
        print(json.dumps({"decision": "allow", "reason": f"error: {str(e)}"}))

if __name__ == "__main__":
    main()
