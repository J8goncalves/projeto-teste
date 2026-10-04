import sys
import json
import os

def main():
    try:
        print(json.dumps({}))
    except Exception as e:
        os.makedirs(".agents/state", exist_ok=True)
        with open(".agents/state/hook-errors.log", "a", encoding="utf-8") as f:
            f.write(f"posttool_events: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()
