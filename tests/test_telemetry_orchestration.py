import unittest
import tempfile
import shutil
import json
import os
import subprocess
from pathlib import Path
from org_v5 import control, telemetry, cli
from org_v5.identity import set_actor_context, clear_actor_context

class TelemetryOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        # Setup git repo in test dir to support branch detection
        subprocess.run(['git', 'init'], cwd=str(self.root), capture_output=True, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Tester'], cwd=str(self.root), capture_output=True, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=str(self.root), capture_output=True, check=True)
        subprocess.run(['git', 'checkout', '-b', 'feature/test-telemetry'], cwd=str(self.root), capture_output=True, check=True)
        os.environ['AGY_GIT_BRANCH'] = 'feature/test-telemetry'
        if 'AGY_RUN_ID' in os.environ:
            del os.environ['AGY_RUN_ID']
        clear_actor_context()

    def tearDown(self):
        clear_actor_context()
        if 'AGY_RUN_ID' in os.environ:
            del os.environ['AGY_RUN_ID']
        if 'AGY_GIT_BRANCH' in os.environ:
            del os.environ['AGY_GIT_BRANCH']
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. Strict run_id resolution hierarchy
    def test_run_id_resolution_hierarchy(self):
        # 1a. Environment variable has highest priority
        os.environ['AGY_RUN_ID'] = 'RUN-ENV-001'
        self.assertEqual(telemetry.resolve_run_id({'runId': 'RUN-PAYLOAD-002'}, root=self.root), 'RUN-ENV-001')
        del os.environ['AGY_RUN_ID']

        # 1b. Data payload priority over args and runs/CURRENT
        self.assertEqual(telemetry.resolve_run_id({'run_id': 'RUN-PAYLOAD-002'}, args={'run_id': 'RUN-ARGS-003'}, root=self.root), 'RUN-PAYLOAD-002')

        # 1c. Tool args priority over runs/CURRENT
        self.assertEqual(telemetry.resolve_run_id({}, args={'run': 'RUN-ARGS-003'}, root=self.root), 'RUN-ARGS-003')

        # 1d. CommandLine parsing in args
        self.assertEqual(telemetry.resolve_run_id({}, args={'CommandLine': 'python -m org_v5.cli submit --run RUN-CMD-004 file.json'}, root=self.root), 'RUN-CMD-004')

        # 1e. runs/CURRENT fallback (only if folder exists)
        control.init(self.root, 'RUN-CURR-005', 'Goal', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        self.assertEqual(telemetry.resolve_run_id({}, args={}, root=self.root), 'RUN-CURR-005')

        # 1f. If runs/CURRENT points to non-existent folder, resolve to None (unassigned)
        (self.root / 'runs' / 'CURRENT').write_text('NON-EXISTENT-RUN', encoding='utf-8')
        self.assertIsNone(telemetry.resolve_run_id({}, args={}, root=self.root))

        # 1g. Completely empty resolves to None
        (self.root / 'runs' / 'CURRENT').unlink()
        self.assertIsNone(telemetry.resolve_run_id({}, args={}, root=self.root))

    # 2. Dual write: canonical run log and consolidated workspace log
    def test_dual_write_and_unassigned_events(self):
        control.init(self.root, 'RUN-DUAL-001', 'Dual write test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')

        # Log event with run_id
        ev1 = telemetry.log_event(self.root, 'RUN-DUAL-001', {'event_type': 'TEST_EVENT', 'detail': 'run-specific'})

        # Verify written to canonical run file
        run_events = telemetry.read_events(self.root, 'RUN-DUAL-001')
        self.assertTrue(any(e.get('detail') == 'run-specific' for e in run_events))

        # Verify also written to workspace-wide log
        global_file = self.root / 'telemetry' / 'events.jsonl'
        self.assertTrue(global_file.exists())
        global_events = [json.loads(line) for line in global_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertTrue(any(e.get('detail') == 'run-specific' and e.get('run_id') == 'RUN-DUAL-001' for e in global_events))

        # Log unassigned event (run_id=None)
        telemetry.log_event(self.root, None, {'event_type': 'ORPHAN_EVENT', 'detail': 'no-run'})

        # Unassigned event MUST NOT be written to the run directory
        run_events_after = telemetry.read_events(self.root, 'RUN-DUAL-001')
        self.assertFalse(any(e.get('event_type') == 'ORPHAN_EVENT' for e in run_events_after))

        # Unassigned event MUST be recorded in the global log with run_id: None
        global_events_after = [json.loads(line) for line in global_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        orphan_found = any(e.get('event_type') == 'ORPHAN_EVENT' and e.get('run_id') is None for e in global_events_after)
        self.assertTrue(orphan_found)

    # 3. Tracked invocations update canonical log
    def test_tracked_invocations_update_canonical_log(self):
        control.init(self.root, 'RUN-GOV-001', 'Gov test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')

        # Verify run starts without telemetry events (NÃO VERIFICÁVEL)
        rep = telemetry.generate_report(self.root, 'RUN-GOV-001')
        self.assertEqual(rep['telemetry_verification'], 'NÃO VERIFICÁVEL')

        # Real tracked invocation
        with telemetry.track_invocation(self.root, 'RUN-GOV-001', 'orchestrator', 'inst-orch-1', 'inv-001') as inv:
            inv.add_artifact('ART-INTAKE-001')

        events = telemetry.read_events(self.root, 'RUN-GOV-001')
        self.assertTrue(any(e.get('event_type') == 'invocation_start' and e.get('role') == 'orchestrator' for e in events))
        self.assertTrue(any(e.get('event_type') == 'invocation_end' and e.get('role') == 'orchestrator' for e in events))

        rep = telemetry.generate_report(self.root, 'RUN-GOV-001')
        self.assertEqual(rep['telemetry_verification'], 'VERIFIED_EVENTS')
        self.assertEqual(len(rep['agents_effective']), 1)
        self.assertEqual(rep['agents_effective'][0]['role'], 'orchestrator')

    # 4. CLI report reads real events produced by hooks and governance
    def test_cli_report_reads_hook_and_governance_events(self):
        control.init(self.root, 'RUN-REP-001', 'Report test', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')

        # Simulate hook logging SUBAGENT_DELEGATION
        telemetry.log_event(self.root, 'RUN-REP-001', {
            'event_type': 'SUBAGENT_DELEGATION',
            'conversation_id': 'conv-sub-123',
            'step_idx': 1,
            'tool_name': 'invoke_subagent',
            'delegations': [
                {'role': 'product-manager', 'type_name': 'product-manager', 'model': 'inherit', 'assurance': 'UNVERIFIED/ROLE_ONLY'}
            ]
        })

        # Simulate hook logging TOOL_CALL
        telemetry.log_event(self.root, 'RUN-REP-001', {
            'event_type': 'TOOL_CALL',
            'conversation_id': 'conv-sub-123',
            'step_idx': 2,
            'tool_name': 'view_file',
            'status': 'SUCCESS'
        })

        report = telemetry.generate_report(self.root, 'RUN-REP-001')
        self.assertEqual(report['telemetry_verification'], 'VERIFIED_EVENTS')
        self.assertIn('events_summary', report)
        self.assertEqual(report['events_summary']['subagent_delegations_count'], 1)
        self.assertEqual(report['events_summary']['tool_calls_count'], 1)

        # Product manager delegated role should be reflected in effective agents
        pm_agent = next((a for a in report['agents_effective'] if a['role'] == 'product-manager'), None)
        self.assertIsNotNone(pm_agent)
        self.assertEqual(pm_agent['instances'], ['conv-sub-123'])

    # 5. Isolation between multiple concurrent runs
    def test_isolation_between_concurrent_runs(self):
        control.init(self.root, 'RUN-CONCUR-A', 'Run A', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')
        control.init(self.root, 'RUN-CONCUR-B', 'Run B', 1, 'ENGINEERING_SMALL', 'TURBO_SANDBOX')

        # Log event specifically for A
        telemetry.log_event(self.root, 'RUN-CONCUR-A', {'event_type': 'ACTION_A', 'detail': 'only-in-a'})
        # Log event specifically for B
        telemetry.log_event(self.root, 'RUN-CONCUR-B', {'event_type': 'ACTION_B', 'detail': 'only-in-b'})

        events_a = telemetry.read_events(self.root, 'RUN-CONCUR-A')
        events_b = telemetry.read_events(self.root, 'RUN-CONCUR-B')

        self.assertTrue(any(e.get('event_type') == 'ACTION_A' for e in events_a))
        self.assertFalse(any(e.get('event_type') == 'ACTION_B' for e in events_a))

        self.assertTrue(any(e.get('event_type') == 'ACTION_B' for e in events_b))
        self.assertFalse(any(e.get('event_type') == 'ACTION_A' for e in events_b))

if __name__ == '__main__':
    unittest.main()
