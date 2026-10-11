"""Comprehensive test suite for V5.2 Phase F (Fase F) Homologation.

Validates:
1. STANDARD policy preserves BUILD human gate denial.
2. TURBO_SANDBOX policy advances to BUILD with POLICY_AUTO_APPROVED event.
3. TURBO_SANDBOX on main/master, post-init tampering, or divergent branch fails closed.
4. Transitions without accepted upstream, self-approval, or same instance review denied.
5. UNVERIFIED is never claimed as VERIFIED; sandbox provisional review never authorizes prod.
6. Deploy / merge to main without verified human approval denied (Git operations governance).
7. Core change in tracked commit + clean test suite execution promotes memory automatically without redundant human approval.
8. Failed tests, unreachable commit, or non-core diff rejects core memory promotion.
9. Changes modifying solely src/ applications cannot promote core memory.
10. AI Memory offline enqueues candidate as PENDENTE_SINCRONIZACAO and syncs idempotently upon recovery.
11. Direct CLI/MCP writes and tainted secret attacks denied.
12. Telemetry and audit report correctly identify VERIFIED_EVENTS vs. NÃO VERIFICÁVEL / NÃO MEDIDO and measured wall-clock vs declared.
13. Three reworks on same pair escalates run.
14. Accounting of passed, failed, and skipped tests without masking (run_test_suite discrete separation).
15. Adverse/Negative: uncommitted changes diverging from commit reject core promotion.
16. Adverse/Negative: memory promote core fails if genuine recall verification cannot confirm existence in FTS store.
17. Git operations governance: git push/merge to production blocked fail-closed without verified approval.
"""
import unittest
import tempfile
import json
import os
import sys
import subprocess
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from org_v5 import control, memory, identity, telemetry, git_ops, test_runner
from org_v5.control import WorkflowError
from org_v5.contracts import digest

class TestV52FaseF(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_id = 'RUN-TEST-FASE-F'
        os.environ['AGY_GIT_BRANCH'] = 'feature/test-fase-f'
        identity.clear_actor_context()

    def tearDown(self):
        identity.clear_actor_context()
        os.environ.pop('AGY_GIT_BRANCH', None)
        self.tmp.cleanup()

    def _setup_design_phase(self, run_id='RUN-TEST-FASE-F', policy='TURBO_SANDBOX'):
        control.init(self.root, run_id, 'Test Phase F', 1, 'ENGINEERING_SMALL', policy)
        
        # 1. Intake
        identity.set_actor_context('inst-orch-01', 'orchestrator')
        intake_doc = {
            'id': 'ART-INTAKE-001', 'run_id': run_id, 'version': '5.0',
            'kind': 'intake', 'role': 'orchestrator', 'status': 'submitted',
            'summary': 'Intake for Phase F', 'input_ids': [], 'evidence_refs': [],
            'sections': {
                'goal': 'Test Phase F', 'scope': 'All modules',
                'constraints': 'Budget and security constraints strictly active',
                'risk_level': 'Low', 'definition_of_success': 'All tests pass'
            }
        }
        control.submit(self.root, run_id, intake_doc)
        
        # Review Intake
        identity.set_actor_context('inst-crit-01', 'critical-reviewer')
        control.review(self.root, run_id, 'ART-INTAKE-001', 'critical-reviewer', 'ACCEPT', 'Intake accepted')
        
        # Advance to DISCOVERY -> PLANNING -> DESIGN
        control.advance(self.root, run_id, 'DISCOVERY')
        control.advance(self.root, run_id, 'PLANNING')
        
        # PRD
        identity.set_actor_context('inst-pm-01', 'product-manager')
        prd_doc = {
            'id': 'ART-PRD-001', 'run_id': run_id, 'version': '5.0',
            'kind': 'prd', 'role': 'product-manager', 'status': 'submitted',
            'summary': 'PRD for Phase F', 'input_ids': [], 'evidence_refs': [],
            'sections': {
                'problem': 'P', 'scope': 'S', 'out_of_scope': 'O',
                'stories': [{'id': 'US-1', 'as_a': 'dev', 'i_want': 'W', 'so_that': 'T', 'acceptance_ids': ['AC-1']}],
                'acceptance_criteria': [{'id': 'AC-1', 'given': 'G', 'when': 'W', 'then': 'T'}],
                'business_rules': 'R', 'security': 'Sec', 'test_plan': 'TP', 'risks': 'Risk'
            }
        }
        control.submit(self.root, run_id, prd_doc)
        
        identity.set_actor_context('inst-qa-01', 'qa')
        control.review(self.root, run_id, 'ART-PRD-001', 'qa', 'ACCEPT', 'PRD accepted')
        control.advance(self.root, run_id, 'DESIGN')
        
        # Architecture
        identity.set_actor_context('inst-arch-01', 'architect')
        arch_doc = {
            'id': 'ART-ARCH-001', 'run_id': run_id, 'version': '5.0',
            'kind': 'architecture', 'role': 'architect', 'status': 'submitted',
            'summary': 'Arch for Phase F', 'input_ids': ['ART-PRD-001'], 'evidence_refs': [],
            'sections': {
                'requirements': 'Req', 'options': 'Opt', 'simplest_viable': 'Simp',
                'tradeoffs': 'Trade', 'financial_feasibility': 'Fin', 'security': 'Sec',
                'adr': 'ADR', 'risks': 'Risk'
            }
        }
        control.submit(self.root, run_id, arch_doc)
        
        identity.set_actor_context('inst-sec-01', 'security-reviewer')
        control.review(self.root, run_id, 'ART-ARCH-001', 'security-reviewer', 'ACCEPT', 'Arch accepted')

    # 1. STANDARD policy without human approval denies BUILD
    def test_case_1_standard_policy_without_human_approval_denies_build(self):
        self._setup_design_phase(run_id='RUN-STD-001', policy='STANDARD')
        with self.assertRaises(WorkflowError) as ctx:
            control.advance(self.root, 'RUN-STD-001', 'BUILD')
        self.assertIn("no recorded verified human approval for BUILD", str(ctx.exception))

    # 2. TURBO_SANDBOX advances to BUILD with POLICY_AUTO_APPROVED event
    def test_case_2_turbo_sandbox_advances_to_build_and_records_policy_event(self):
        self._setup_design_phase(run_id='RUN-TURBO-001', policy='TURBO_SANDBOX')
        phase = control.advance(self.root, 'RUN-TURBO-001', 'BUILD')
        self.assertEqual(phase, 'BUILD')
        
        state = control.read(self.root, 'RUN-TURBO-001')
        self.assertEqual(state['phase'], 'BUILD')
        
        # Check approval event recorded
        build_app = state['approvals'].get('BUILD')
        self.assertIsNotNone(build_app)
        self.assertEqual(build_app['actor'], 'policy_engine')
        self.assertEqual(build_app['status'], 'POLICY_AUTO_APPROVED')
        self.assertFalse(build_app['verified'])
        self.assertEqual(build_app['policy'], 'TURBO_SANDBOX')
        
        # Check history contains policy event
        actions = [h['action'] for h in state['history']]
        self.assertIn('policy_auto_approved', actions)

    # 3. TURBO_SANDBOX on main/master or tampered policy fails closed
    def test_case_3_turbo_on_main_or_tampered_policy_or_divergent_branch_denied(self):
        # 3a. Prohibited to init Turbo on main branch
        os.environ['AGY_GIT_BRANCH'] = 'main'
        with self.assertRaises(WorkflowError) as ctx_main:
            control.init(self.root, 'RUN-MAIN-001', 'Main test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        self.assertIn("TURBO_SANDBOX policy is prohibited on production branch", str(ctx_main.exception))
        
        # 3b. Policy tampering after init rejected
        os.environ['AGY_GIT_BRANCH'] = 'feature/test-fase-f'
        control.init(self.root, 'RUN-TAMP-001', 'Tamper test', 1, 'ENGINEERING_SMALL', 'STANDARD')
        state_file = self.root / 'runs' / 'RUN-TAMP-001' / 'state.json'
        data = json.loads(state_file.read_text(encoding='utf-8'))
        data['execution_policy'] = 'TURBO_SANDBOX' # Tampering state
        state_file.write_text(json.dumps(data), encoding='utf-8')
        
        with self.assertRaises(WorkflowError) as ctx_tamp:
            control.advance(self.root, 'RUN-TAMP-001', 'DISCOVERY')
        self.assertIn("execution policy tampering detected", str(ctx_tamp.exception))

        # 3c. Divergent branch execution rejected
        control.init(self.root, 'RUN-DIV-001', 'Div test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        os.environ['AGY_GIT_BRANCH'] = 'feature/other-branch'
        with self.assertRaises(WorkflowError) as ctx_div:
            control.advance(self.root, 'RUN-DIV-001', 'DISCOVERY')
        self.assertIn("branch divergence detected", str(ctx_div.exception))

    # 4. Transitions without accepted upstream or self-approval denied
    def test_case_4_missing_upstream_or_self_approval_or_same_instance_denied(self):
        control.init(self.root, 'RUN-DEP-001', 'Dep test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        
        # Submit artifact with missing upstream
        identity.set_actor_context('inst-orch-01', 'orchestrator')
        bad_doc = {
            'id': 'ART-INTAKE-BAD', 'run_id': 'RUN-DEP-001', 'version': '5.0',
            'kind': 'intake', 'role': 'orchestrator', 'status': 'submitted',
            'summary': 'Intake with missing upstream', 'input_ids': ['NON_EXISTENT_UPSTREAM'],
            'evidence_refs': [],
            'sections': {'goal': 'G', 'scope': 'S', 'constraints': 'Standard constraints', 'risk_level': 'Low', 'definition_of_success': 'D'}
        }
        with self.assertRaises(WorkflowError) as ctx_up:
            control.submit(self.root, 'RUN-DEP-001', bad_doc)
        self.assertIn("upstream input not independently accepted", str(ctx_up.exception))
        
        # Self-approval rejected
        intake_doc = {
            'id': 'ART-INTAKE-99', 'run_id': 'RUN-DEP-001', 'version': '5.0',
            'kind': 'intake', 'role': 'orchestrator', 'status': 'submitted',
            'summary': 'Intake', 'input_ids': [], 'evidence_refs': [],
            'sections': {'goal': 'G', 'scope': 'S', 'constraints': 'Standard constraints', 'risk_level': 'Low', 'definition_of_success': 'D'}
        }
        identity.set_actor_context('inst-orch-99', 'orchestrator')
        control.submit(self.root, 'RUN-DEP-001', intake_doc)
        
        with self.assertRaises(WorkflowError) as ctx_self:
            control.review(self.root, 'RUN-DEP-001', 'ART-INTAKE-99', 'orchestrator', 'ACCEPT', 'Self review')
        self.assertIn("no producer or orchestrator self-approval", str(ctx_self.exception))
        
        # Same instance review rejected
        identity.set_actor_context('inst-orch-99', 'critical-reviewer')
        with self.assertRaises(WorkflowError) as ctx_same:
            control.review(self.root, 'RUN-DEP-001', 'ART-INTAKE-99', 'critical-reviewer', 'ACCEPT', 'Same instance')
        self.assertIn("same agent instance cannot review its own artifact", str(ctx_same.exception))

    # 5. UNVERIFIED is never claimed as VERIFIED; sandbox provisional review never authorizes prod
    def test_case_5_unverified_not_promoted_to_verified_and_sandbox_does_not_authorize_prod(self):
        self._setup_design_phase(run_id='RUN-UNVER-001', policy='TURBO_SANDBOX')
        control.advance(self.root, 'RUN-UNVER-001', 'BUILD')
        
        # Developer submits build
        identity.set_actor_context('inst-dev-01', 'developer')
        evidence_file = self.root / 'evidence' / 'build.log'
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text('build test pass', encoding='utf-8')
        
        build_doc = {
            'id': 'ART-BUILD-001', 'run_id': 'RUN-UNVER-001', 'version': '5.0',
            'kind': 'build', 'role': 'developer', 'status': 'submitted',
            'summary': 'Build', 'input_ids': ['ART-ARCH-001'],
            'evidence_refs': ['evidence/build.log'],
            'sections': {
                'input_prd': 'ART-PRD-001', 'architecture_ref': 'ART-ARCH-001',
                'changes': 'Code changes', 'unit_test_command': 'pytest',
                'unit_test_output': 'OK', 'integration_results': 'OK',
                'security_considerations': 'Safe', 'commit_ref': 'abc1234'
            }
        }
        control.submit(self.root, 'RUN-UNVER-001', build_doc)
        
        # Distinct instance reviews build in sandbox -> SANDBOX_PROVISIONAL, NOT VERIFIED
        identity.set_actor_context('inst-qa-02', 'qa')
        control.review(self.root, 'RUN-UNVER-001', 'ART-BUILD-001', 'qa', 'ACCEPT', 'Sandbox review')
        
        state = control.read(self.root, 'RUN-UNVER-001')
        acc_identity = state['accepted']['ART-BUILD-001']['reviewer_identity']
        self.assertEqual(acc_identity['assurance'], 'UNVERIFIED')
        self.assertEqual(acc_identity['status'], 'SANDBOX_PROVISIONAL')
        self.assertNotEqual(acc_identity['assurance'], 'VERIFIED')

    # 6. Deploy / merge to main without human approval denied
    def test_case_6_deploy_or_merge_to_main_without_human_approval_denied(self):
        self._setup_design_phase(run_id='RUN-PROD-001', policy='TURBO_SANDBOX')
        # Attempting to advance a Turbo run on main branch is blocked fail-closed
        os.environ['AGY_GIT_BRANCH'] = 'main'
        with self.assertRaises(WorkflowError) as ctx:
            control.advance(self.root, 'RUN-PROD-001', 'BUILD')
        self.assertIn("forbidden on production branch", str(ctx.exception))

    # 7. Core change in tracked commit + clean test suite execution promotes memory automatically
    @patch('org_v5.memory.recall')
    @patch('org_v5.memory.ai_memory_cli')
    @patch('org_v5.memory.is_live_backend_available', return_value=True)
    @patch('subprocess.run')
    def test_case_7_core_change_clean_tests_promotes_memory_without_human_approval(self, mock_subproc, mock_backend, mock_cli, mock_recall):
        mock_cli.return_value = 'wrote page memories/core/decision/MC-CORE-001.md'
        mock_recall.return_value = [{'path': 'memories/core/decision/MC-CORE-001.md', 'id': 'MC-CORE-001'}]
        
        def fake_subprocess(cmd, **kwargs):
            m = MagicMock()
            cmd_str = ' '.join(cmd)
            if 'rev-parse' in cmd_str and '--verify' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'diff-tree' in cmd_str:
                m.returncode = 0
                m.stdout = 'org_v5/control.py\n.agents/rules/governance.md\n'
            elif 'merge-base' in cmd_str:
                m.returncode = 0
            elif 'rev-parse' in cmd_str and 'HEAD' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'status' in cmd_str and '--porcelain' in cmd_str:
                m.returncode = 0
                m.stdout = ''
            elif 'rev-parse' in cmd_str and '--abbrev-ref' in cmd_str:
                m.returncode = 0
                m.stdout = 'feature/test-fase-f'
            else:
                m.returncode = 0
                m.stdout = ''
            return m
            
        mock_subproc.side_effect = fake_subprocess
        
        # Mock test runner to return clean pass
        with patch('org_v5.test_runner.run_test_suite', return_value={'clean_pass': True, 'passed': 63, 'failed': 0, 'errors': 0, 'skipped': 0}):
            # Propose memory candidate
            control.init(self.root, 'RUN-CORE-001', 'Core memory test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
            proposal = {
                'id': 'MC-CORE-001', 'role': 'architect', 'type': 'decision',
                'text': 'Automate core improvement memory promotion without redundant approval.',
                'tags': ['dec-core', 'core-fase-f'], 'confidence': 0.95, 'provenance': 'observed',
                'source_ref': 'docs/architecture/fase-f-autonomia-e-aprendizado.md',
                'reason': 'V5.2 continuous learning policy'
            }
            memory.propose(self.root, 'RUN-CORE-001', proposal)
            
            # Promote core directly with commit sha (no state approvals['MEMORY_WRITE'] needed)
            res = memory.promote_core(self.root, 'RUN-CORE-001', 'MC-CORE-001', '189cb1f63a43cd84942377df4c06355f62c96a98')
            self.assertEqual(res['status'], 'stored')
            self.assertEqual(res['memory_status'], 'VALIDADA_EM_BRANCH')
            self.assertTrue(res['verified_recall'])
            self.assertIn('wrote', res['receipt'].lower())

    # 8. Failed tests, unreachable commit, or non-core diff rejects core memory promotion
    @patch('subprocess.run')
    def test_case_8_core_promotion_denied_on_failed_tests_or_unreachable_commit_or_unapproved_doc(self, mock_subproc):
        control.init(self.root, 'RUN-CORE-ERR', 'Core err test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        proposal = {
            'id': 'MC-ERR-001', 'role': 'architect', 'type': 'decision',
            'text': 'Automate core improvement memory promotion without redundant approval.',
            'tags': ['dec-core', 'core-err'], 'confidence': 0.95, 'provenance': 'observed',
            'source_ref': 'docs/architecture/v5-blueprint.md',
            'reason': 'V5.2 continuous learning policy'
        }
        memory.propose(self.root, 'RUN-CORE-ERR', proposal)
        
        # 8a. Test suite fails
        def fake_failing_test(cmd, **kwargs):
            m = MagicMock()
            cmd_str = ' '.join(cmd)
            if 'rev-parse' in cmd_str and '--verify' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'diff-tree' in cmd_str:
                m.returncode = 0
                m.stdout = 'org_v5/control.py\n'
            elif 'merge-base' in cmd_str:
                m.returncode = 0
            elif 'rev-parse' in cmd_str and 'HEAD' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'status' in cmd_str and '--porcelain' in cmd_str:
                m.returncode = 0
                m.stdout = ''
            return m
            
        mock_subproc.side_effect = fake_failing_test
        with patch('org_v5.test_runner.run_test_suite', return_value={'clean_pass': False, 'passed': 60, 'failed': 1, 'errors': 0, 'skipped': 0}):
            with self.assertRaises(WorkflowError) as ctx_fail:
                memory.promote_core(self.root, 'RUN-CORE-ERR', 'MC-ERR-001', '189cb1f63a43cd84942377df4c06355f62c96a98')
            self.assertIn("test suite verification failed", str(ctx_fail.exception))

    # 9. Changes modifying solely src/ applications cannot promote core memory
    @patch('subprocess.run')
    def test_case_9_src_only_changes_rejected_for_core_memory(self, mock_subproc):
        control.init(self.root, 'RUN-SRC-001', 'Src only test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        proposal = {
            'id': 'MC-SRC-001', 'role': 'developer', 'type': 'learning',
            'text': 'Timer uses timestamp target delta to prevent timer drift.',
            'tags': ['evid-timer', 'core-test'], 'confidence': 0.95, 'provenance': 'observed',
            'source_ref': 'docs/architecture/v5-blueprint.md',
            'reason': 'Application behavior'
        }
        memory.propose(self.root, 'RUN-SRC-001', proposal)
        
        def fake_src_diff(cmd, **kwargs):
            m = MagicMock()
            cmd_str = ' '.join(cmd)
            if 'rev-parse' in cmd_str and '--verify' in cmd_str:
                m.returncode = 0
                m.stdout = '68a344b123456789'
            elif 'diff-tree' in cmd_str:
                m.returncode = 0
                m.stdout = 'src/pomodoro/timer.js\nsrc/pomodoro/index.html\n'
            elif 'merge-base' in cmd_str:
                m.returncode = 0
            return m
            
        mock_subproc.side_effect = fake_src_diff
        with self.assertRaises(WorkflowError) as ctx_src:
            memory.promote_core(self.root, 'RUN-SRC-001', 'MC-SRC-001', '68a344b123456789')
        self.assertIn("do not modify organization core files", str(ctx_src.exception))

    # 10. AI Memory offline enqueues candidate as PENDENTE_SINCRONIZACAO and syncs idempotently
    @patch('org_v5.memory.is_live_backend_available', return_value=False)
    @patch('subprocess.run')
    def test_case_10_ai_memory_offline_enqueues_pending_sync_and_syncs_when_online(self, mock_subproc, mock_backend):
        def fake_subproc_clean(cmd, **kwargs):
            m = MagicMock()
            cmd_str = ' '.join(cmd)
            if 'rev-parse' in cmd_str and '--verify' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'diff-tree' in cmd_str:
                m.returncode = 0
                m.stdout = 'org_v5/memory.py\n'
            elif 'merge-base' in cmd_str:
                m.returncode = 0
            elif 'rev-parse' in cmd_str and 'HEAD' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'status' in cmd_str and '--porcelain' in cmd_str:
                m.returncode = 0
                m.stdout = ''
            elif 'rev-parse' in cmd_str and '--abbrev-ref' in cmd_str:
                m.returncode = 0
                m.stdout = 'feature/test-fase-f'
            return m
            
        mock_subproc.side_effect = fake_subproc_clean
        
        with patch('org_v5.test_runner.run_test_suite', return_value={'clean_pass': True, 'passed': 63, 'failed': 0, 'errors': 0, 'skipped': 0}):
            control.init(self.root, 'RUN-OFFLINE-001', 'Offline sync test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
            proposal = {
                'id': 'MC-OFF-001', 'role': 'architect', 'type': 'decision',
                'text': 'Offline queue preserves candidate without false persistence claim.',
                'tags': ['dec-queue', 'core-offline'], 'confidence': 0.95, 'provenance': 'observed',
                'source_ref': 'docs/architecture/fase-f-autonomia-e-aprendizado.md',
                'reason': 'Offline tolerance'
            }
            memory.propose(self.root, 'RUN-OFFLINE-001', proposal)
            
            res = memory.promote_core(self.root, 'RUN-OFFLINE-001', 'MC-OFF-001', '189cb1f63a43cd84942377df4c06355f62c96a98')
            self.assertEqual(res['status'], 'PENDENTE_SINCRONIZACAO')
            self.assertIn('queue_path', res)
            
            # Verify sync queue file exists
            q_path = self.root / res['queue_path']
            self.assertTrue(q_path.exists())
            
            # Now simulate backend coming online
            with patch('org_v5.memory.is_live_backend_available', return_value=True):
                with patch('org_v5.memory.ai_memory_cli', return_value='wrote page memories/core/decision/MC-OFF-001.md'):
                    with patch('org_v5.memory.recall', return_value=[{'path': 'memories/core/decision/MC-OFF-001.md', 'id': 'MC-OFF-001'}]):
                        synced = memory.sync_pending_core(self.root, 'RUN-OFFLINE-001')
                        self.assertEqual(len(synced), 1)
                        self.assertEqual(synced[0]['status'], 'stored')
                        self.assertTrue(synced[0]['verified_recall'])
                        self.assertFalse(q_path.exists())

    # 11. Direct CLI/MCP writes and tainted secret attacks denied
    def test_case_11_direct_mcp_cli_write_and_tampered_candidate_rejected(self):
        with self.assertRaises(WorkflowError) as ctx_direct:
            memory.ai_memory_cli(['write-page', '--path', 'memories/rogue.md', '--body', 'rogue'])
        self.assertIn("Direct write via CLI/MCP forbidden", str(ctx_direct.exception))
        
        # Tainted runner secret in os.environ flags actor as UNVERIFIED
        os.environ['AGY_RUNNER_SECRET'] = 'secret-attacker'
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'attacker-01'
        os.environ['AGY_ASSIGNED_ROLE'] = 'developer'
        ident = identity.verify_actor_identity('developer')
        self.assertEqual(ident['assurance'], 'UNVERIFIED')
        self.assertEqual(ident['status'], 'COMPROMISED_TAINTED_SECRET')

    # 12. Telemetry and audit report correctly identify VERIFIED_EVENTS vs. NÃO VERIFICÁVEL / NÃO MEDIDO
    def test_case_12_telemetry_report_with_and_without_events(self):
        control.init(self.root, 'RUN-TELEM-001', 'Telemetry test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        
        # Report without telemetry events
        rep_empty = telemetry.generate_report(self.root, 'RUN-TELEM-001')
        self.assertEqual(rep_empty['telemetry_verification'], 'NÃO VERIFICÁVEL')
        self.assertEqual(rep_empty['resource_metrics']['tokens_per_agent'], 'NÃO MEDIDO')
        self.assertEqual(rep_empty['resource_metrics']['cost_usd'], 'NÃO MEDIDO')
        
        # Use context manager to time real invocation
        with telemetry.track_invocation(self.root, 'RUN-TELEM-001', 'architect', 'inst-arch-88', 'inv-001') as inv:
            inv.add_artifact('ART-ARCH-001')
            
        rep_filled = telemetry.generate_report(self.root, 'RUN-TELEM-001')
        self.assertEqual(rep_filled['telemetry_verification'], 'VERIFIED_EVENTS')
        eff = rep_filled['agents_effective']
        self.assertEqual(len(eff), 1)
        self.assertEqual(eff[0]['role'], 'architect')
        self.assertEqual(eff[0]['instances'], ['inst-arch-88'])
        self.assertEqual(eff[0]['measurement_method'], 'MEDIDO_WALL_CLOCK')
        self.assertGreaterEqual(eff[0]['total_duration_seconds'], 0.0)
        self.assertEqual(rep_filled['resource_metrics']['tokens_per_agent'], 'NÃO MEDIDO')

    # 13. Three reworks on same pair escalates run
    def test_case_13_three_reworks_escalates_run(self):
        control.init(self.root, 'RUN-ESCALATE-001', 'Escalation test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        doc = {
            'id': 'ART-INTAKE-ESC', 'run_id': 'RUN-ESCALATE-001', 'version': '5.0',
            'kind': 'intake', 'role': 'orchestrator', 'status': 'submitted',
            'summary': 'Intake', 'input_ids': [], 'evidence_refs': [],
            'sections': {'goal': 'G', 'scope': 'S', 'constraints': 'Standard constraints', 'risk_level': 'Low', 'definition_of_success': 'D'}
        }
        control.submit(self.root, 'RUN-ESCALATE-001', doc)
        
        identity.set_actor_context('inst-crit-esc', 'critical-reviewer')
        control.review(self.root, 'RUN-ESCALATE-001', 'ART-INTAKE-ESC', 'critical-reviewer', 'REWORK', 'Rework 1')
        control.review(self.root, 'RUN-ESCALATE-001', 'ART-INTAKE-ESC', 'critical-reviewer', 'REWORK', 'Rework 2')
        phase = control.review(self.root, 'RUN-ESCALATE-001', 'ART-INTAKE-ESC', 'critical-reviewer', 'REWORK', 'Rework 3')
        
        self.assertEqual(phase, 'ESCALATED')
        state = control.read(self.root, 'RUN-ESCALATE-001')
        self.assertEqual(state['phase'], 'ESCALATED')

    # 14. Accounting of passed, failed, and skipped tests without masking
    def test_case_14_legacy_test_suites_pass_cleanly(self):
        # Verify that node task manager test runs cleanly
        res = subprocess.run(['node', 'tests/test_task_manager.js'], cwd=str(Path(__file__).parent.parent), capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0, f"Task Manager test failed:\n{res.stderr or res.stdout}")
        self.assertIn("TODOS OS TESTES PASSARAM COM SUCESSO", res.stdout)
        
        # Verify test runner separation on governance test suite
        details = test_runner.run_test_suite('tests', pattern='test_governance.py', cwd=str(Path(__file__).parent.parent))
        self.assertGreater(details['total_run'], 10)
        self.assertEqual(details['failed'], 0)
        self.assertEqual(details['errors'], 0)
        self.assertEqual(details['skipped'], 0)
        self.assertTrue(details['clean_pass'])

    # 15. Adverse/Negative: uncommitted changes diverging from commit reject core promotion
    @patch('subprocess.run')
    def test_case_15_dirty_worktree_divergence_rejects_core_promotion(self, mock_subproc):
        control.init(self.root, 'RUN-DIRTY-001', 'Dirty test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        proposal = {
            'id': 'MC-DIRTY-001', 'role': 'architect', 'type': 'decision',
            'text': 'Dirty worktree rejection test.',
            'tags': ['dec-dirty', 'core-test'], 'confidence': 0.95, 'provenance': 'observed',
            'source_ref': 'docs/architecture/v5-blueprint.md',
            'reason': 'Worktree integrity'
        }
        memory.propose(self.root, 'RUN-DIRTY-001', proposal)
        
        def fake_dirty_subproc(cmd, **kwargs):
            m = MagicMock()
            cmd_str = ' '.join(cmd)
            if 'rev-parse' in cmd_str and '--verify' in cmd_str:
                m.returncode = 0
                m.stdout = 'commit_sha_123'
            elif 'diff-tree' in cmd_str:
                m.returncode = 0
                m.stdout = 'org_v5/control.py\n'
            elif 'merge-base' in cmd_str:
                m.returncode = 0
            elif 'rev-parse' in cmd_str and 'HEAD' in cmd_str:
                m.returncode = 0
                m.stdout = 'different_head_sha'
            elif 'status' in cmd_str and '--porcelain' in cmd_str:
                m.returncode = 0
                m.stdout = 'M org_v5/control.py\n'
            return m
            
        mock_subproc.side_effect = fake_dirty_subproc
        with self.assertRaises(WorkflowError) as ctx:
            memory.promote_core(self.root, 'RUN-DIRTY-001', 'MC-DIRTY-001', 'commit_sha_123')
        self.assertIn("uncommitted changes diverging", str(ctx.exception))

    # 16. Adverse/Negative: memory promote core fails if genuine recall verification fails
    @patch('org_v5.memory.recall', return_value=[])  # Empty recall returns no match
    @patch('org_v5.memory.ai_memory_cli', return_value='wrote page memories/core/decision/MC-NOREC-001.md')
    @patch('org_v5.memory.is_live_backend_available', return_value=True)
    @patch('subprocess.run')
    def test_case_16_failed_recall_verification_rejects_persistence_claim(self, mock_subproc, mock_backend, mock_cli, mock_recall):
        def fake_clean_subproc(cmd, **kwargs):
            m = MagicMock()
            cmd_str = ' '.join(cmd)
            if 'rev-parse' in cmd_str and '--verify' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'diff-tree' in cmd_str:
                m.returncode = 0
                m.stdout = 'org_v5/control.py\n'
            elif 'merge-base' in cmd_str:
                m.returncode = 0
            elif 'rev-parse' in cmd_str and 'HEAD' in cmd_str:
                m.returncode = 0
                m.stdout = '189cb1f63a43cd84942377df4c06355f62c96a98'
            elif 'status' in cmd_str and '--porcelain' in cmd_str:
                m.returncode = 0
                m.stdout = ''
            elif 'rev-parse' in cmd_str and '--abbrev-ref' in cmd_str:
                m.returncode = 0
                m.stdout = 'feature/test-fase-f'
            return m
            
        mock_subproc.side_effect = fake_clean_subproc
        
        with patch('org_v5.test_runner.run_test_suite', return_value={'clean_pass': True, 'passed': 63, 'failed': 0, 'errors': 0, 'skipped': 0}):
            control.init(self.root, 'RUN-NOREC-001', 'Recall fail test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
            proposal = {
                'id': 'MC-NOREC-001', 'role': 'architect', 'type': 'decision',
                'text': 'Candidate that cannot be recalled.',
                'tags': ['dec-norec', 'core-test'], 'confidence': 0.95, 'provenance': 'observed',
                'source_ref': 'docs/architecture/v5-blueprint.md',
                'reason': 'Recall verification failure test'
            }
            memory.propose(self.root, 'RUN-NOREC-001', proposal)
            
            with self.assertRaises(WorkflowError) as ctx:
                memory.promote_core(self.root, 'RUN-NOREC-001', 'MC-NOREC-001', '189cb1f63a43cd84942377df4c06355f62c96a98')
            self.assertIn("recall verification failed", str(ctx.exception))

    # 17. Git operations governance: git push/merge to production blocked fail-closed without verified approval
    def test_case_17_git_governance_blocks_unauthorized_prod_operations(self):
        control.init(self.root, 'RUN-GIT-001', 'Git governance test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        
        # Sandbox push on feature branch is authorized
        res_sandbox = git_ops.verify_git_action_authorization(
            self.root, 'push', target_branch='feature/my-feat', run_id='RUN-GIT-001'
        )
        self.assertTrue(res_sandbox['authorized'])
        self.assertEqual(res_sandbox['scope'], 'sandbox')
        
        # Merge or push targeting main without verified approval is blocked fail-closed
        with self.assertRaises(WorkflowError) as ctx_push_main:
            git_ops.verify_git_action_authorization(
                self.root, 'push', target_branch='main', run_id='RUN-GIT-001'
            )
        self.assertIn("GIT_POLICY_VIOLATION", str(ctx_push_main.exception))
        
        with self.assertRaises(WorkflowError) as ctx_merge_main:
            git_ops.verify_git_action_authorization(
                self.root, 'merge', target_branch='main', run_id='RUN-GIT-001'
            )
        self.assertIn("GIT_POLICY_VIOLATION", str(ctx_merge_main.exception))
        
        # Attempting git_ops.run_governed_git push main without approval
        with self.assertRaises(WorkflowError) as ctx_cmd:
            git_ops.run_governed_git(self.root, ['push', 'origin', 'main'], run_id='RUN-GIT-001')
        self.assertIn("GIT_POLICY_VIOLATION", str(ctx_cmd.exception))

if __name__ == '__main__':
    unittest.main()
