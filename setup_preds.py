import json
import subprocess
import sys

def run_cmd(cmd):
    print("Running:", cmd)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print("ERROR:", res.stderr)
        print("OUTPUT:", res.stdout)
    else:
        print("SUCCESS:", res.stdout)

intake = {
  "id": "intake-001",
  "run_id": "run-pilot-v5-002",
  "summary": "Task Manager Intake",
  "version": "5.0",
  "status": "submitted",
  "role": "orchestrator",
  "kind": "intake",
  "input_ids": [],
  "evidence_refs": [],
  "sections": {
    "goal": "Task Manager Microproject",
    "scope": "Local task manager",
    "constraints": "No auth, no paid services",
    "risk_level": "Low",
    "definition_of_success": "Users can track tasks"
  }
}

market = {
  "id": "market-001",
  "run_id": "run-pilot-v5-002",
  "summary": "Task Manager Market Research",
  "version": "5.0",
  "status": "submitted",
  "role": "market-researcher",
  "kind": "market-research",
  "input_ids": ["intake-001"],
  "evidence_refs": [],
  "sections": {
    "question": "Is there a need for a local task manager?",
    "method": "Desk research",
    "sources": [{"url": "https://example.com", "accessed": "2026-10-10", "claim": "People need simple tools"}],
    "benchmark": "Existing simple tools",
    "strengths": "Simple and local",
    "weaknesses": "No sync",
    "risks": "Low engagement",
    "recommendation": "Proceed",
    "uncertainties": "No major uncertainties identified at this stage"
  }
}

crit = {
  "id": "crit-001",
  "run_id": "run-pilot-v5-002",
  "summary": "Critical Review",
  "version": "5.0",
  "status": "submitted",
  "role": "critical-reviewer",
  "kind": "critical-review",
  "input_ids": ["market-001"],
  "evidence_refs": [],
  "sections": {
    "claims_checked": "Need for simple tools",
    "conflicts": "No conflicting information found",
    "evidence_gaps": "Research appears solid",
    "risks": "Low risk overall",
    "verdict": "PASS",
    "sources": [{"url": "https://example.com/review", "accessed": "2026-10-10", "claim": "Tools are good"}]
  }
}

with open("runs/run-pilot-v5-002/intake.json", "w") as f: json.dump(intake, f)
with open("runs/run-pilot-v5-002/market.json", "w") as f: json.dump(market, f)
with open("runs/run-pilot-v5-002/crit.json", "w") as f: json.dump(crit, f)

p = ".venv\\Scripts\\python.exe"

run_cmd(f"{p} -m org_v5.cli submit --run run-pilot-v5-002 runs/run-pilot-v5-002/intake.json")
run_cmd(f"{p} -m org_v5.cli review --run run-pilot-v5-002 --artifact intake-001 --reviewer critical-reviewer --verdict ACCEPT --reason ok")

run_cmd(f"{p} -m org_v5.cli submit --run run-pilot-v5-002 runs/run-pilot-v5-002/market.json")
run_cmd(f"{p} -m org_v5.cli review --run run-pilot-v5-002 --artifact market-001 --reviewer critical-reviewer --verdict ACCEPT --reason ok")

run_cmd(f"{p} -m org_v5.cli submit --run run-pilot-v5-002 runs/run-pilot-v5-002/crit.json")
run_cmd(f"{p} -m org_v5.cli review --run run-pilot-v5-002 --artifact crit-001 --reviewer legal-compliance --verdict ACCEPT --reason ok")

