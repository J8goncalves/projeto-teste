import sys
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
            f.write(f"preinvocation_state: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
