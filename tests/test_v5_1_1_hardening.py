"""Regression and hardening test suite for V5.1.1 Governance Hotfix (H01-H05).

Demonstrates deterministic rejection of the 7 mandatory vulnerability scenarios:
1. Unverified reviewer attempting ACCEPT on critical gates.
2. Agent altering os.environ attempting self-approval.
3. GitHub approval pointing to incorrect repo, run, or hash.
4. Replay / reuse of human approval across gates or runs.
5. Escalation resolution with arbitrary URL without verified approval.
6. Memory promotion without valid, specific, and current approval (hash mismatch / candidate mismatch / replay).
7. Institutional memory write via unauthorized alternative path / removal of legacy aliases.
"""
import unittest
import os
import shutil
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from org_v5 import control, memory, approvals
from org_v5.identity import set_actor_context, clear_actor_context, sign_runner_token, verify_actor_identity
from org_v5.contracts import validate, digest

class V511HardeningTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('tests/tmp_v5_1_1')
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)
        self.run_id = 'RUN-H05-001'
        control.init(self.root, self.run_id, 'Hardening Test Run', 3, 'ENGINEERING_SMALL')
        self.secret = 'runner-master-secret-999'
        set_actor_context('agent-orchestrator', 'orchestrator', self.secret)
        
    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)
        clear_actor_context()
        
    def doc(self, kind='intake', role='orchestrator', aid='A001', inputs=None):
        from org_v5.contracts import CONTRACTS
        sections = {k: 'Hardened verification section evidence' for k in CONTRACTS[kind][1]}
        return dict(
            id=aid, run_id=self.run_id, kind=kind, role=role, version='5.0',
            status='submitted', summary='Hardening verification artifact',
            input_ids=inputs or [], evidence_refs=[], sections=sections
        )

    def seed_up_to_build(self):
        set_actor_context('agent-orch', 'orchestrator', self.secret)
        intake = self.doc('intake', 'orchestrator', 'INTAKE-01')
        control.submit(self.root, self.run_id, intake)
        set_actor_context('agent-crit', 'critical-reviewer', self.secret)
        control.review(self.root, self.run_id, 'INTAKE-01', 'critical-reviewer', 'ACCEPT', 'reviewed intake')

        set_actor_context('agent-pm', 'product-manager', self.secret)
        prd = self.doc('prd', 'product-manager', 'PRD-01', ['INTAKE-01'])
        prd['sections']['stories'] = [{'id': 'US-1', 'as_a': 'user', 'i_want': 'tasks', 'so_that': 'work', 'acceptance_ids': ['AC-1']}]
        prd['sections']['acceptance_criteria'] = [{'id': 'AC-1', 'given': 'init', 'when': 'action', 'then': 'done'}]
        control.submit(self.root, self.run_id, prd)
        set_actor_context('agent-qa', 'qa', self.secret)
        control.review(self.root, self.run_id, 'PRD-01', 'qa', 'ACCEPT', 'reviewed prd')

        set_actor_context('agent-arch', 'architect', self.secret)
        adr = self.doc('architecture', 'architect', 'ARCH-01', ['PRD-01'])
        control.submit(self.root, self.run_id, adr)
        set_actor_context('agent-sec', 'security-reviewer', self.secret)
        control.review(self.root, self.run_id, 'ARCH-01', 'security-reviewer', 'ACCEPT', 'reviewed arch')

        set_actor_context('agent-dev', 'developer', self.secret)
        build = self.doc('build', 'developer', 'BUILD-01', ['ARCH-01'])
        control.submit(self.root, self.run_id, build)
        return 'BUILD-01'

    # --------------------------------------------------------------------------
    # Scenario 1: Revisor não verificado tentando emitir ACCEPT em gate crítico
    # --------------------------------------------------------------------------
    def test_scenario_1_unverified_reviewer_accept_critical_gate_rejected(self):
        build_id = self.seed_up_to_build()
        # Unverified reviewer: only env vars, no runner token/secret
        os.environ.pop('AGY_RUNNER_SECRET', None)
        os.environ.pop('AGY_RUNNER_TOKEN', None)
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'unverified-agent-99'
        os.environ['AGY_ASSIGNED_ROLE'] = 'implementation-reviewer'
        
        ident = verify_actor_identity('implementation-reviewer')
        self.assertEqual(ident['assurance'], 'UNVERIFIED')
        
        with self.assertRaises(control.WorkflowError) as ctx:
            control.review(self.root, self.run_id, build_id, 'implementation-reviewer', 'ACCEPT', 'unverified approval attempt')
        self.assertIn("critical gate 'build' requires verified independent reviewer", str(ctx.exception))

    # --------------------------------------------------------------------------
    # Scenario 2: Agente alterando os.environ para tentar autoaprovação
    # --------------------------------------------------------------------------
    def test_scenario_2_agent_tampering_environ_self_approval_rejected(self):
        build_id = self.seed_up_to_build()
        # Developer tries to impersonate reviewer by modifying os.environ directly
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'spoofed-ir-agent'
        os.environ['AGY_ASSIGNED_ROLE'] = 'implementation-reviewer'
        # Because developer cannot forge AGY_RUNNER_TOKEN without knowing the runner secret,
        # assurance remains UNVERIFIED
        with self.assertRaises(control.WorkflowError) as ctx:
            control.review(self.root, self.run_id, build_id, 'implementation-reviewer', 'ACCEPT', 'spoofed self-review')
        self.assertIn("critical gate 'build' requires verified independent reviewer", str(ctx.exception))
        
        # If developer retains its original instance ID, it is rejected by same instance check
        set_actor_context('agent-dev', 'implementation-reviewer', self.secret)
        with self.assertRaises(control.WorkflowError) as ctx2:
            control.review(self.root, self.run_id, build_id, 'implementation-reviewer', 'ACCEPT', 'same instance review')
        self.assertIn("same agent instance cannot review its own artifact", str(ctx2.exception))

    def test_scenario_2b_adversary_reading_secret_in_environ_forging_hmac_rejected(self):
        """
        Adversary agent that discovers or injects AGY_RUNNER_SECRET into os.environ,
        generates a valid HMAC with it, and attempts to assume reviewer role.
        The environment is flagged as compromised (UNVERIFIED) and critical review is blocked.
        """
        build_id = self.seed_up_to_build()
        leaked_secret = 'stolen-runner-secret-xyz'
        os.environ['AGY_RUNNER_SECRET'] = leaked_secret
        forged_token = sign_runner_token('rogue-agent', 'implementation-reviewer', leaked_secret)
        os.environ['AGY_RUNNER_TOKEN'] = forged_token
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'rogue-agent'
        os.environ['AGY_ASSIGNED_ROLE'] = 'implementation-reviewer'

        ident = verify_actor_identity('implementation-reviewer')
        self.assertEqual(ident['assurance'], 'UNVERIFIED')
        self.assertIn('AGY_RUNNER_SECRET exposed in agent process environment', ident['reason'])

        with self.assertRaises(control.WorkflowError) as ctx:
            control.review(self.root, self.run_id, build_id, 'implementation-reviewer', 'ACCEPT', 'forged token attempt')
        self.assertIn("critical gate 'build' requires verified independent reviewer", str(ctx.exception))

    def test_scenario_2c_github_token_isolated_from_executing_agents(self):
        """
        GITHUB_TOKEN is stripped from os.environ upon setting agent execution context,
        preventing code-executing agents from accessing credentials.
        """
        os.environ['GITHUB_TOKEN'] = 'super-secret-gh-token'
        set_actor_context('agent-worker', 'developer', self.secret)
        self.assertNotIn('GITHUB_TOKEN', os.environ, "GITHUB_TOKEN must not remain in os.environ for executing agents")
        from org_v5.approvals import get_trusted_github_token
        self.assertEqual(get_trusted_github_token(), 'super-secret-gh-token')

    # --------------------------------------------------------------------------
    # Scenario 3: Aprovação GitHub apontando para repositório, run ou hash incorreto
    # --------------------------------------------------------------------------
    def test_scenario_3a_missing_expected_sha_rejected(self):
        """Calling control.approval on pertinent gates without expected_sha is blocked."""
        with self.assertRaises(control.WorkflowError) as ctx:
            control.approval(self.root, self.run_id, 'BUILD', 'APPROVE', 'human', 'https://github.com/J8goncalves/projeto-teste/issues/1')
        self.assertIn("requires an explicit or state-derived immutable expected_sha", str(ctx.exception))

    def test_scenario_3b_cross_repository_approval_rejected(self):
        # Human approval pointing to foreign repository
        foreign_url = 'https://github.com/evil-attacker/malicious-repo/issues/10'
        with self.assertRaises(control.WorkflowError) as ctx:
            control.approval(self.root, self.run_id, 'BUILD', 'APPROVE', 'human', foreign_url, expected_sha='dummy_sha')
        self.assertIn("Cross-repository approval rejected", str(ctx.exception))

    @patch('org_v5.approvals.urllib.request.urlopen')
    def test_scenario_3c_wrong_run_id_or_hash_approval_rejected(self, mock_urlopen):
        os.environ['GITHUB_TOKEN'] = 'test-token'
        # Comment payload with mismatched run ID
        fake_response = [{
            'id': 1001,
            'user': {'login': 'j8goncalves'},
            'author_association': 'OWNER',
            'html_url': 'https://github.com/J8goncalves/projeto-teste/issues/1#issuecomment-1001',
            'body': 'APPROVE_TARGET: BUILD\nRUN_ID: RUN-OTHER-999\nDECISION: APPROVE\nSHA: expected-sha'
        }]
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(fake_response).encode('utf-8')
        
        target_url = 'https://github.com/J8goncalves/projeto-teste/issues/1'
        with self.assertRaises(control.WorkflowError) as ctx:
            control.approval(self.root, self.run_id, 'BUILD', 'APPROVE', 'human', target_url, expected_sha='expected-sha')
        self.assertIn("No matching valid approval comment found", str(ctx.exception))

    # --------------------------------------------------------------------------
    # Scenario 4: Reutilização de aprovação humana entre gates ou runs (anti-replay)
    # --------------------------------------------------------------------------
    @patch('org_v5.approvals.urllib.request.urlopen')
    def test_scenario_4a_human_approval_replay_rejected(self, mock_urlopen):
        os.environ['GITHUB_TOKEN'] = 'test-token'
        fake_response = [{
            'id': 2001,
            'user': {'login': 'j8goncalves'},
            'author_association': 'OWNER',
            'html_url': 'https://github.com/J8goncalves/projeto-teste/issues/1#issuecomment-2001',
            'body': f'APPROVE_TARGET: BUILD\nRUN_ID: {self.run_id}\nDECISION: APPROVE\nSHA: sha-build-001'
        }]
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(fake_response).encode('utf-8')
        
        ref = 'https://github.com/J8goncalves/projeto-teste/issues/1#issuecomment-2001'
        control.approval(self.root, self.run_id, 'BUILD', 'APPROVE', 'human', ref, expected_sha='sha-build-001')
        
        # Attacker tries to reuse the same comment reference for gate RELEASE
        with self.assertRaises(control.WorkflowError) as ctx:
            control.approval(self.root, self.run_id, 'RELEASE', 'APPROVE', 'human', ref, expected_sha='sha-build-001')
        self.assertIn("replay error: approval reference already used for gate BUILD", str(ctx.exception))

    @patch('org_v5.approvals.urllib.request.urlopen')
    def test_scenario_4b_canonical_comment_id_cross_url_replay_rejected(self, mock_urlopen):
        """
        Anti-replay by canonical comment ID: Approving via generic issue URL consumes comment 3001.
        Reusing it via specific #issuecomment-3001 URL on another run or gate is rejected.
        """
        os.environ['GITHUB_TOKEN'] = 'test-token'
        fake_response = [{
            'id': 3001,
            'user': {'login': 'j8goncalves'},
            'author_association': 'OWNER',
            'html_url': 'https://github.com/J8goncalves/projeto-teste/issues/10#issuecomment-3001',
            'body': f'APPROVE_TARGET: BUILD\nRUN_ID: {self.run_id}\nDECISION: APPROVE\nSHA: sha-canon-01'
        }]
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(fake_response).encode('utf-8')

        # Approve using issue URL
        issue_url = 'https://github.com/J8goncalves/projeto-teste/issues/10'
        control.approval(self.root, self.run_id, 'BUILD', 'APPROVE', 'human', issue_url, expected_sha='sha-canon-01')

        # Now attempt replay in a separate run using direct comment fragment URL
        run2 = 'RUN-H05-002'
        control.init(self.root, run2, 'Second Run', 3, 'ENGINEERING_SMALL')
        comment_url = 'https://github.com/J8goncalves/projeto-teste/issues/10#issuecomment-3001'
        with self.assertRaises(control.WorkflowError) as ctx:
            control.approval(self.root, run2, 'BUILD', 'APPROVE', 'human', comment_url, expected_sha='sha-canon-01')
        self.assertIn("Approval replay detected", str(ctx.exception))

    def test_scenario_4c_anti_replay_store_corruption_fails_closed(self):
        """Fail-closed behavior: reading corrupted anti-replay store blocks execution."""
        consumed_path = approvals.get_consumed_approvals_path(self.root)
        consumed_path.parent.mkdir(parents=True, exist_ok=True)
        consumed_path.write_text("CORRUPTED-NOT-JSON-CONTENT", encoding='utf-8')

        with self.assertRaises(control.WorkflowError) as ctx:
            approvals.is_approval_consumed("https://github.com/J8goncalves/projeto-teste/issues/1", self.root)
        self.assertIn("Anti-replay registry read failure (fail-closed)", str(ctx.exception))

    def test_scenario_4d_concurrent_anti_replay_marking_and_detection(self):
        """Concurrency test: multiple concurrent operations consuming approvals safely without registry loss."""
        import concurrent.futures
        keys = [f"j8goncalves/projeto-teste#issuecomment-{i}" for i in range(20)]
        
        def consume(k):
            approvals.mark_approval_consumed(k, 'BUILD', self.run_id, self.root)
            return approvals.is_approval_consumed(k, self.root)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(consume, keys))
            
        self.assertTrue(all(results))
        for k in keys:
            self.assertTrue(approvals.is_approval_consumed(k, self.root))

    # --------------------------------------------------------------------------
    # Scenario 5: Encerramento de escalação com URL arbitrária sem aprovação válida
    # --------------------------------------------------------------------------
    def test_scenario_5_arbitrary_url_escalation_resume_rejected(self):
        control.escalate(self.root, self.run_id, 'Unrecoverable anomaly')
        s = control.read(self.root, self.run_id)
        self.assertEqual(s['phase'], 'ESCALATED')
        
        # Arbitrary URL resolution without verified human approval
        with self.assertRaises(control.WorkflowError) as ctx:
            control.resume(self.root, self.run_id, 'https://github.com/arbitrary/random-link')
        self.assertIn("ESCALATION_RESUME_DENIED", str(ctx.exception))

    # --------------------------------------------------------------------------
    # Scenario 6: Promoção de memória sem aprovação válida, específica e atual
    # --------------------------------------------------------------------------
    @patch('org_v5.memory.ai_memory_cli')
    def test_scenario_6_memory_promotion_strict_binding_and_replay_prevention(self, mock_cli):
        mock_cli.return_value = 'wrote page memories/decision/MC001.md'
        proposal = dict(
            id='MC001', role='qa', type='decision',
            text='Enforce automated interaction tests with durable screenshot traces.',
            tags=['dec-001', 'qa'], confidence=0.9, provenance='observed',
            source_ref='docs/evidence.md', reason='Governance baseline'
        )
        memory.propose(self.root, self.run_id, proposal)
        cand_text_hash = hashlib.sha256(proposal['text'].encode('utf-8')).hexdigest()
        cand_digest = memory.candidate_digest(proposal)
        
        # 6a. Attempting promote without human approval in state
        with self.assertRaises(control.WorkflowError) as ctx1:
            memory.promote(self.root, self.run_id, 'MC001', 'https://github.com/J8goncalves/projeto-teste/issues/5')
        self.assertIn("human memory-write approval with exact matching reference", str(ctx1.exception))
        
        # Record approval specifically bound to MC001, full digest, and text hash
        app_ref = 'https://github.com/J8goncalves/projeto-teste/issues/5#issuecomment-99'
        state = control.read(self.root, self.run_id)
        state['approvals']['MEMORY_WRITE'] = {
            'actor': 'j8goncalves', 'decision': 'APPROVE', 'reference': app_ref,
            'verified': True, 'candidate_id': 'MC001', 'content_sha256': cand_text_hash,
            'candidate_digest': cand_digest
        }
        control.save(self.root, state)
        
        # 6b. Candidate mismatch: trying to promote MC002 with approval for MC001
        with self.assertRaises(control.WorkflowError) as ctx2:
            memory.promote(self.root, self.run_id, 'MC002', app_ref)
        self.assertIn("approval is bound to candidate MC001, not MC002", str(ctx2.exception))
        
        # 6c. Content tampering: modifying candidate on disk after approval
        cand_path = self.root / 'runs' / self.run_id / 'memory-candidates' / 'MC001.json'
        cand_data = json.loads(cand_path.read_text(encoding='utf-8'))
        cand_data['text'] = 'Tampered content after human approval was granted.'
        cand_path.write_text(json.dumps(cand_data), encoding='utf-8')
        
        with self.assertRaises(control.WorkflowError) as ctx3:
            memory.promote(self.root, self.run_id, 'MC001', app_ref)
        self.assertIn("candidate text modified after approval: content hash mismatch", str(ctx3.exception))

        # 6c-2. Metadata tampering (e.g. changing tags, reason, or provenance)
        cand_data['text'] = proposal['text']
        cand_data['tags'] = ['dec-001', 'qa', 'malicious-injected-tag']
        cand_path.write_text(json.dumps(cand_data), encoding='utf-8')
        with self.assertRaises(control.WorkflowError) as ctx_meta:
            memory.promote(self.root, self.run_id, 'MC001', app_ref)
        self.assertIn("candidate full specification modified after approval", str(ctx_meta.exception))
        
        # Restore valid content and promote successfully
        cand_data['tags'] = proposal['tags']
        cand_path.write_text(json.dumps(cand_data), encoding='utf-8')
        res = memory.promote(self.root, self.run_id, 'MC001', app_ref)
        self.assertEqual(res['status'], 'stored')
        
        # 6d. Replay prevention: promoting same candidate or reusing approval again
        with self.assertRaises(control.WorkflowError) as ctx4:
            memory.promote(self.root, self.run_id, 'MC001', app_ref)
        self.assertIn("approval reference already consumed", str(ctx4.exception))

    # --------------------------------------------------------------------------
    # Scenario 7: Gravação de memória institucional por caminho alternativo não autorizado
    # --------------------------------------------------------------------------
    def test_scenario_7a_direct_cli_mcp_write_blocked_outside_promote(self):
        """Direct CLI/MCP write commands are intercepted and forbidden outside promote()."""
        with self.assertRaises(control.WorkflowError) as ctx:
            memory.ai_memory_cli(['write-page', '--path', 'memories/fact/rogue.md', '--body', 'rogue body'])
        self.assertIn("Direct write via CLI/MCP forbidden", str(ctx.exception))

    def test_scenario_7b_unauthorized_memory_write_path_blocked(self):
        # Verify that legacy alias memanto was permanently deleted
        self.assertFalse(hasattr(memory, 'memanto'), "Legacy alias 'memanto' must be removed in V5.1.1")
        
        # Verify candidate cannot be stored directly if unapproved
        with self.assertRaises(control.WorkflowError):
            memory.promote(self.root, self.run_id, 'NONEXISTENT', 'https://github.com/fake')

    def test_scenario_7c_fast_recall_and_status_without_ollama(self):
        """Verify memory recall and status function via SQLite FTS5."""
        stat = memory.status()
        self.assertTrue(stat['connected'])
        self.assertIn('ai-memory', stat['status_excerpt'].lower())
        hits = memory.recall('decision', limit=1)
        self.assertIsInstance(hits, list)

if __name__ == '__main__':
    unittest.main()
