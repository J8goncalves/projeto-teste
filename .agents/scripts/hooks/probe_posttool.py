import sys
import json
import os
import datetime

# Find workspace root: script is in <root>/.agents/scripts/hooks/
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
original_cwd = os.getcwd()

# Ensure we can write relative to workspace root
os.chdir(workspace_root)

# Immediate execution marker
log_dir = "evidence/hooks-probe"
os.makedirs(log_dir, exist_ok=True)
with open(os.path.join(log_dir, "probe_invoked.log"), "a", encoding="utf-8") as f:
    f.write(f"INVOKED AT {datetime.datetime.now().isoformat()} ORIGINAL_CWD={original_cwd} ARGV={sys.argv}\n")

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        raw_input = sys.stdin.read()
        
        with open(os.path.join(log_dir, "probe_posttool_stdin_raw.txt"), "w", encoding="utf-8") as f:
            f.write(raw_input)

        parsed = {}
        if raw_input.strip():
            try:
                parsed = json.loads(raw_input)
            except Exception as pe:
                parsed = {"parse_error": str(pe), "raw": raw_input[:500]}

        schema_analysis = {
            "hook_invoked": True,
            "original_cwd": original_cwd,
            "workspace_root": workspace_root,
            "top_level_keys": list(parsed.keys()),
            "keys_types": {k: type(v).__name__ for k, v in parsed.items()},
            "toolCall": {
                "name": parsed.get("toolCall", {}).get("name") if isinstance(parsed.get("toolCall"), dict) else None,
                "args_keys": list(parsed.get("toolCall", {}).get("args", {}).keys()) if isinstance(parsed.get("toolCall"), dict) and isinstance(parsed.get("toolCall", {}).get("args"), dict) else None,
                "args_types": {k: type(v).__name__ for k, v in parsed.get("toolCall", {}).get("args", {}).items()} if isinstance(parsed.get("toolCall"), dict) and isinstance(parsed.get("toolCall", {}).get("args"), dict) else None,
            },
            "stepIdx": parsed.get("stepIdx"),
            "stepIdx_type": type(parsed.get("stepIdx")).__name__,
            "error": parsed.get("error"),
            "error_type": type(parsed.get("error")).__name__,
            "conversationId_present": "conversationId" in parsed,
            "workspacePaths": parsed.get("workspacePaths"),
            "transcriptPath_present": "transcriptPath" in parsed,
            "artifactDirectoryPath_present": "artifactDirectoryPath" in parsed,
            "modelName": parsed.get("modelName"),
        }

        with open(os.path.join(log_dir, "posttool_probe_raw.json"), "w", encoding="utf-8") as f:
            json.dump(schema_analysis, f, indent=2, ensure_ascii=False)

        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"probe_posttool: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
