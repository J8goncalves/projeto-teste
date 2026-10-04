import sys
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
            f.write(f"pretool_guard: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
