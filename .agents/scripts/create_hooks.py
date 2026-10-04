import json
import os

os.makedirs('.agents/scripts/hooks', exist_ok=True)

pretool = '''import sys
import json
import re
import os

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({}))
            return
        
        req = json.loads(input_data)
        tool = req.get("toolName", "")
        args = req.get("arguments", {})
        
        arg_val = ""
        if tool == "run_command":
            arg_val = args.get("CommandLine", "")
        else:
            arg_val = args.get("TargetFile", args.get("AbsolutePath", ""))
            
        with open(".agents/policies/guards.json", "r", encoding="utf-8") as f:
            guards = json.load(f)
            
        for g in guards:
            tools = g.get("ferramentas", [])
            if "*" in tools or tool in tools:
                padrao = g.get("padrao", "")
                if padrao == "existe .agents/state/STOP":
                    if os.path.exists(".agents/state/STOP"):
                        print(json.dumps({"decision": g["decisao"], "reason": g["motivo"]}))
                        return
                elif "estado da run em ESCALATED ou PAUSED" in padrao:
                    # simplificação: fallback sem ver arquivo
                    pass
                else:
                    if padrao and re.search(padrao, str(arg_val), re.IGNORECASE):
                        print(json.dumps({"decision": g["decisao"], "reason": g["motivo"]}))
                        return
        
        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"pretool_guard: {str(e)}\\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
'''

with open('.agents/scripts/hooks/pretool_guard.py', 'w', encoding='utf-8') as f:
    f.write(pretool)

postinv = '''import sys
import json
import os

def main():
    try:
        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"postinvocation_budget: {str(e)}\\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
'''
with open('.agents/scripts/hooks/postinvocation_budget.py', 'w', encoding='utf-8') as f:
    f.write(postinv)

preinv = '''import sys
import json
import os

def main():
    try:
        if os.path.exists(".agents/state/STOP"):
            print(json.dumps({"messages": [{"role": "user", "content": "Run parada. Não execute ações. Registre apenas BLOCKER ou o relatório e aguarde o humano."}]}))
            return
        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"preinvocation_state: {str(e)}\\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
'''
with open('.agents/scripts/hooks/preinvocation_state.py', 'w', encoding='utf-8') as f:
    f.write(preinv)

posttool = '''import sys
import json
import os

def main():
    try:
        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"posttool_events: {str(e)}\\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
'''
with open('.agents/scripts/hooks/posttool_events.py', 'w', encoding='utf-8') as f:
    f.write(posttool)

# Create .agents/hooks.json
hooks_json = {
  "org-guard": {
    "enabled": False,
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {"type": "command", "command": ".\\.venv\\Scripts\\python.exe .agents/scripts/hooks/pretool_guard.py", "timeout": 10}
        ]
      }
    ]
  },
  "org-budget": {
    "enabled": False,
    "PostInvocation": [
      {"type": "command", "command": ".\\.venv\\Scripts\\python.exe .agents/scripts/hooks/postinvocation_budget.py", "timeout": 10}
    ]
  },
  "org-state": {
    "enabled": False,
    "PreInvocation": [
      {"type": "command", "command": ".\\.venv\\Scripts\\python.exe .agents/scripts/hooks/preinvocation_state.py", "timeout": 10}
    ]
  },
  "org-events": {
    "enabled": False,
    "PostToolUse": [
      {
        "matcher": "invoke_subagent|run_command",
        "hooks": [
          {"type": "command", "command": ".\\.venv\\Scripts\\python.exe .agents/scripts/hooks/posttool_events.py", "timeout": 10}
        ]
      }
    ]
  }
}

if os.path.exists(".agents/hooks.json"):
    with open(".agents/hooks.json", "r", encoding="utf-8") as f:
        existing = json.load(f)
    existing.update(hooks_json)
    hooks_json = existing

with open(".agents/hooks.json", "w", encoding="utf-8") as f:
    json.dump(hooks_json, f, indent=2, ensure_ascii=False)

print('Hooks and hooks.json created')
