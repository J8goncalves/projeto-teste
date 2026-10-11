import unittest
from pathlib import Path
from unittest.mock import patch
import os
import shutil
import json

from org_v5 import control, cli, approvals
from org_v5.identity import set_actor_context, clear_actor_context
from org_v5.contracts import validate, load, digest

class V51GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('tests/tmp_v5_1')
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)
        control.init(self.root, 'RUN-TEST', 'Test V5.1', 3, 'ENGINEERING_SMALL')
        # Setup mock environment
        self.secret = 'test-runner-secret'
        set_actor_context('agent-123', 'orchestrator', self.secret)
        
    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)
        clear_actor_context()
        
    def doc(self, kind='intake', role='orchestrator', aid='A001', inputs=None):
        from org_v5.contracts import CONTRACTS
        sections = {k: 'Concrete detail' for k in CONTRACTS[kind][1]}
        return dict(id=aid, run_id='RUN-TEST', kind=kind, role=role, version='5.0', 
                    status='submitted', summary='Finding', input_ids=inputs or [], 
                    evidence_refs=[], sections=sections)
                    
    def seed_build_dependencies(self):
        # Use real submissions and independent reviewers to seed an accepted chain.
        set_actor_context('agent-123', 'orchestrator', self.secret)
        upstream=self.doc('intake','orchestrator',aid='A001')
        control.submit(self.root,'RUN-TEST',upstream)
        set_actor_context('agent-2', 'critical-reviewer', self.secret)
        control.review(self.root,'RUN-TEST','A001','critical-reviewer','ACCEPT','reviewed')
        
        set_actor_context('agent-pm', 'product-manager', self.secret)
        prd=self.doc('prd','product-manager',aid='A004',inputs=['A001'])
        prd['sections']['stories']=[{'id':'US-1','as_a':'buyer','i_want':'add item','so_that':'save','acceptance_ids':['AC-1']}]
        prd['sections']['acceptance_criteria']=[{'id':'AC-1','given':'open','when':'click','then':'saved'}]
        control.submit(self.root,'RUN-TEST',prd)
        set_actor_context('agent-qa', 'qa', self.secret)
        control.review(self.root,'RUN-TEST','A004','qa','ACCEPT','reviewed')
        
        set_actor_context('agent-arch', 'architect', self.secret)
        adr=self.doc('architecture','architect',aid='A005',inputs=['A004'])
        control.submit(self.root,'RUN-TEST',adr)
        set_actor_context('agent-sec', 'security-reviewer', self.secret)
        control.review(self.root,'RUN-TEST','A005','security-reviewer','ACCEPT','reviewed')
        
        set_actor_context('agent-dev', 'developer', self.secret)
        build = self.doc('build', 'developer', aid='B001', inputs=['A005'])
        control.submit(self.root, 'RUN-TEST', build)
        set_actor_context('agent-ir', 'implementation-reviewer', self.secret)
        control.review(self.root, 'RUN-TEST', 'B001', 'implementation-reviewer', 'ACCEPT', 'reviewed')
        return 'B001'

    def test_T01_orchestrator_submits_security_report_denied(self):
        # Orchestrator (in env) tries to submit security-report claiming to be security-reviewer
        build_id = self.seed_build_dependencies()
        import hashlib
        os.environ['AGY_ASSIGNED_ROLE'] = 'orchestrator'
        d = self.doc('security-report', 'security-reviewer', aid='S001', inputs=[build_id])
        d['verdict'] = 'PASS'
        (self.root / 'f').write_bytes(b'scan output')
        d['execution'] = {'real_execution': True, 'command': 'x', 'exit_code': 0, 'output_ref': 'f', 'output_sha256': hashlib.sha256(b'scan output').hexdigest(), 'tool':'x', 'version':'1', 'started_at':'1', 'finished_at':'1', 'environment':'1', 'commit_sha':'1'}
        d['sections']['scans'] = ['scan']
        with self.assertRaises(ValueError) as ctx:
            control.submit(self.root, 'RUN-TEST', d)
        self.assertIn("Actor identity mismatch", str(ctx.exception))
        
    def test_T15_lineage_error_on_release(self):
        # Developer submete B001. QA aprova B001.
        # Developer submete B002. Sec aprova B002.
        # Release Manager tenta fundir QA de B001 com Sec de B002
        b1 = self.seed_build_dependencies()
        
        set_actor_context('agent-dev2', 'developer', self.secret)
        b2 = self.doc('build', 'developer', aid='B002', inputs=['A005'])
        control.submit(self.root, 'RUN-TEST', b2)
        set_actor_context('agent-ir2', 'implementation-reviewer', self.secret)
        control.review(self.root, 'RUN-TEST', 'B002', 'implementation-reviewer', 'ACCEPT', 'reviewed')
        
        # Sec reviews B002
        import hashlib
        set_actor_context('agent-sec2', 'security-reviewer', self.secret)
        s = self.doc('security-report', 'security-reviewer', aid='S002', inputs=['B002'])
        s['verdict'] = 'PASS'
        (self.root / 's').write_bytes(b'scan output')
        s['execution'] = {'real_execution': True, 'command': 'x', 'exit_code': 0, 'output_ref': 's', 'output_sha256': hashlib.sha256(b'scan output').hexdigest(), 'tool':'x', 'version':'1', 'started_at':'1', 'finished_at':'1', 'environment':'1', 'commit_sha':'1'}
        s['sections']['scans'] = ['scan']
        control.submit(self.root, 'RUN-TEST', s)
        set_actor_context('agent-ir3', 'implementation-reviewer', self.secret)
        control.review(self.root, 'RUN-TEST', 'S002', 'implementation-reviewer', 'ACCEPT', 'reviewed')
        
        # QA reviews B001
        set_actor_context('agent-qa2', 'qa', self.secret)
        q = self.doc('qa-report', 'qa', aid='Q001', inputs=[b1])
        q['verdict'] = 'PASS'
        (self.root / 'q').write_bytes(b'qa output')
        q['execution'] = {'real_execution': True, 'command': 'x', 'exit_code': 0, 'output_ref': 'q', 'output_sha256': hashlib.sha256(b'qa output').hexdigest(), 'tool':'x', 'version':'1', 'started_at':'1', 'finished_at':'1', 'environment':'1', 'commit_sha':'1'}
        q['sections']['method'] = 'browser-interactive'
        q['sections']['acceptance_mapping']=[{'criterion':'AC-001','result':'PASS'}]
        q['sections']['interactions']=[{'target':'#save','action':'click','expected':'saved','observed':'saved','evidence_ref':'docs/evidence.md'}]
        
        (self.root / 'docs').mkdir(exist_ok=True)
        (self.root / 'docs/evidence.md').write_text('evidence')
        
        control.submit(self.root, 'RUN-TEST', q)
        set_actor_context('agent-ir4', 'implementation-reviewer', self.secret)
        control.review(self.root, 'RUN-TEST', 'Q001', 'implementation-reviewer', 'ACCEPT', 'reviewed')
        
        # IR for B002
        set_actor_context('agent-ir5', 'implementation-reviewer', self.secret)
        ir = self.doc('implementation-review', 'implementation-reviewer', aid='IR001', inputs=['Q001', 'S002'])
        control.submit(self.root, 'RUN-TEST', ir)
        set_actor_context('agent-cr1', 'critical-reviewer', self.secret)
        control.review(self.root, 'RUN-TEST', 'IR001', 'critical-reviewer', 'ACCEPT', 'reviewed')
        
        # Release manager tries to submit
        set_actor_context('agent-rm', 'release-manager', self.secret)
        rm = self.doc('release', 'release-manager', aid='RM001', inputs=['Q001', 'S002', 'IR001'])
        
        with self.assertRaises(control.WorkflowError) as ctx:
            control.submit(self.root, 'RUN-TEST', rm)
        self.assertIn('lineage error: release includes reports from diverging builds', str(ctx.exception))
        
    def test_T18_approval_faking(self):
        self.seed_build_dependencies()
        s = control.read(self.root, 'RUN-TEST')
        s['approvals']['BUILD'] = {'actor': 'fake_hacker', 'decision': 'APPROVE', 'reference': 'fake', 'at': '2026-10-10'}
        s['phase'] = 'DESIGN'
        control.save(self.root, s)
        # Advance BUILD should fail because verified != True
        with self.assertRaises(control.WorkflowError) as ctx:
            control.advance(self.root, 'RUN-TEST', 'BUILD')
        self.assertIn("no recorded verified human approval for BUILD", str(ctx.exception))
        
    def test_T04_same_instance_review_denied(self):
        # Even if role claims to be different, same agent instance ID fails verification
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'agent-same'
        os.environ['AGY_ASSIGNED_ROLE'] = 'orchestrator'
        d = self.doc('intake', 'orchestrator')
        control.submit(self.root, 'RUN-TEST', d)
        
        os.environ['AGY_ASSIGNED_ROLE'] = 'product-manager' # same instance!
        with self.assertRaises(control.WorkflowError) as ctx:
            control.review(self.root, 'RUN-TEST', 'A001', 'product-manager', 'ACCEPT', 'looks good')
        self.assertIn("same agent instance cannot review its own artifact", str(ctx.exception))

    def test_T09_engineering_small_no_market_research(self):
        # In ENGINEERING_SMALL, PRD can be submitted without market-research upstream
        os.environ['AGY_ASSIGNED_ROLE'] = 'orchestrator'
        intake = self.doc('intake', 'orchestrator', 'INT01')
        control.submit(self.root, 'RUN-TEST', intake)
        os.environ['AGY_ASSIGNED_ROLE'] = 'product-manager'
        
        # critical-reviewer does the review for intake
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'agent-crit'
        os.environ['AGY_ASSIGNED_ROLE'] = 'critical-reviewer'
        control.review(self.root, 'RUN-TEST', 'INT01', 'critical-reviewer', 'ACCEPT', 'ok')
        
        # PM submits PRD directly
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'agent-pm'
        os.environ['AGY_ASSIGNED_ROLE'] = 'product-manager'
        prd = self.doc('prd', 'product-manager', 'PRD01', ['INT01'])
        prd['sections']['stories']=[{'id':'US-1','as_a':'buyer','i_want':'add item','so_that':'save','acceptance_ids':['AC-1']}]
        prd['sections']['acceptance_criteria']=[{'id':'AC-1','given':'open','when':'click','then':'saved'}]
        # Should NOT fail due to missing predecessors
        control.submit(self.root, 'RUN-TEST', prd)

    @patch('org_v5.approvals.urllib.request.urlopen')
    def test_T05_github_approval_fail_closed(self, mock_urlopen):
        approvals.set_trusted_github_token('fake_token')
        mock_urlopen.side_effect = Exception("API Error")
        with self.assertRaises(control.WorkflowError) as ctx:
            control.approval(self.root, 'RUN-TEST', 'BUILD', 'APPROVE', 'human', 'https://github.com/J8goncalves/projeto-teste/issues/1', expected_sha='a'*64)
        self.assertIn("APPROVAL_PENDING: GitHub API check failed: API Error", str(ctx.exception))
        

    def test_T14_qa_pass_without_interaction_fails(self):
        b1 = self.seed_build_dependencies()
        os.environ['AGY_ASSIGNED_ROLE'] = 'qa'
        os.environ['AGY_AGENT_INSTANCE_ID'] = 'agent-qa3'
        q = self.doc('qa-report', 'qa', aid='Q002', inputs=[b1])
        q['verdict'] = 'PASS'
        (self.root / 'q2').write_bytes(b'qa output')
        q['execution'] = {'real_execution': True, 'command': 'x', 'exit_code': 0, 'output_ref': 'q2', 'output_sha256': __import__('hashlib').sha256(b'qa output').hexdigest(), 'tool':'x', 'version':'1', 'started_at':'1', 'finished_at':'1', 'environment':'1', 'commit_sha':'1'}
        q['sections']['method'] = 'browser-interactive'
        q['sections']['acceptance_mapping']=[{'criterion':'AC-001','result':'PASS'}]
        q['sections']['interactions'] = []
        with self.assertRaises(Exception) as ctx:
            control.submit(self.root, 'RUN-TEST', q)
        self.assertIn('QA PASS requires documented real UI interactions with evidence', str(ctx.exception))

    def test_T19_evidence_tampering_denied(self):
        b1 = self.seed_build_dependencies()
        set_actor_context('agent-sec3', 'security-reviewer', self.secret)
        s = self.doc('security-report', 'security-reviewer', aid='S003', inputs=[b1])
        s['verdict'] = 'PASS'
        (self.root / 's3').write_bytes(b'scan output')
        s['execution'] = {'real_execution': True, 'command': 'x', 'exit_code': 0, 'output_ref': 's3', 'output_sha256': __import__('hashlib').sha256(b'scan output').hexdigest(), 'tool':'x', 'version':'1', 'started_at':'1', 'finished_at':'1', 'environment':'1', 'commit_sha':'1'}
        s['sections']['scans'] = ['scan']
        control.submit(self.root, 'RUN-TEST', s)
        (self.root / 's3').write_bytes(b'hacked scan output')
        set_actor_context('agent-ir6', 'implementation-reviewer', self.secret)
        with self.assertRaises(Exception) as ctx:
            control.review(self.root, 'RUN-TEST', 'S003', 'implementation-reviewer', 'ACCEPT', 'reviewed')
        self.assertIn('execution output SHA-256 absent/mismatch', str(ctx.exception))

    def test_T23_tampered_resume_package_rejected(self):
        self.seed_build_dependencies()
        pkg = control.resume_package(self.root, 'RUN-TEST')
        self.assertEqual(pkg['schema'], 'RESUME_PACKAGE_v5')
        
        # Tamper with an accepted artifact on disk
        target_art = pkg['accepted_artifacts'][0]
        file_path = self.root / target_art['path']
        original_bytes = file_path.read_bytes()
        file_path.write_bytes(b'{"tampered": true}')
        
        # Validation by the successor agent: recalculate sha256 and assert mismatch
        mismatches = []
        for a in pkg['accepted_artifacts']:
            computed = control.digest(control.load(self.root / a['path']))
            if computed != a['sha256']:
                mismatches.append(a['id'])
                
        self.assertIn(target_art['id'], mismatches)
        
        # Restore
        file_path.write_bytes(original_bytes)

if __name__ == '__main__':
    unittest.main()

