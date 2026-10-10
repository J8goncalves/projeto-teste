import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from org_v5 import control, memory
from org_v5.contracts import validate, digest

class GovernanceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);control.init(self.root,'RUN-TEST','test',2)
 def doc(self,kind='intake',role='orchestrator',aid='A001',inputs=None):
  from org_v5.contracts import CONTRACTS
  sections={k:'Concrete, substantive observed detail' for k in CONTRACTS[kind][1]}
  return dict(id=aid,run_id='RUN-TEST',kind=kind,role=role,version='5.0',status='submitted',summary='Observed finding',input_ids=inputs or [],evidence_refs=['docs/evidence.md'],sections=sections)
 def test_fake_or_incomplete_fails(self):
  d=self.doc();d['sections']['goal']='TBD';self.assertIn('placeholder section: goal',validate(d))
 def test_unknown_source_fails(self):
  d=self.doc('market-research','market-researcher');self.assertTrue(validate(d))
 def test_unaccepted_upstream_denied(self):
  with self.assertRaises(control.WorkflowError):control.submit(self.root,'RUN-TEST',self.doc('prd','product-manager','B001',['A001']))
 def test_self_approval_denied(self):
  control.submit(self.root,'RUN-TEST',self.doc())
  with self.assertRaises(control.WorkflowError):control.review(self.root,'RUN-TEST','A001','orchestrator','ACCEPT','checked')
 def test_orchestrator_cannot_review(self):
  d=self.doc('intake','orchestrator');control.submit(self.root,'RUN-TEST',d)
  with self.assertRaises(control.WorkflowError):control.review(self.root,'RUN-TEST','A001','orchestrator','ACCEPT','checked')
 def test_tampering_detected(self):
  control.submit(self.root,'RUN-TEST',self.doc());path=self.root/'runs/RUN-TEST/artifacts/A001.json'
  d=control.read(self.root,'RUN-TEST');import json
  x=json.loads(path.read_text());x['summary']='altered';path.write_text(json.dumps(x))
  with self.assertRaises(control.WorkflowError):control.review(self.root,'RUN-TEST','A001','critical-reviewer','ACCEPT','checked')
 def test_missing_gate_fails(self):
  with self.assertRaises(control.WorkflowError):control.advance(self.root,'RUN-TEST','DISCOVERY')
 def test_nonsequential_gate_fails(self):
  with self.assertRaises(control.WorkflowError):control.advance(self.root,'RUN-TEST','RELEASE')
 def test_real_accepted_artifact_advances(self):
  control.submit(self.root,'RUN-TEST',self.doc());control.review(self.root,'RUN-TEST','A001','critical-reviewer','ACCEPT','independent review')
  self.assertEqual(control.advance(self.root,'RUN-TEST','DISCOVERY'),'DISCOVERY')
 def test_review_3_rounds_escalates(self):
  control.submit(self.root,'RUN-TEST',self.doc())
  for _ in range(3):control.review(self.root,'RUN-TEST','A001','critical-reviewer','REWORK','needs evidence')
  self.assertEqual(control.read(self.root,'RUN-TEST')['phase'],'ESCALATED')
  with self.assertRaises(control.WorkflowError):control.advance(self.root,'RUN-TEST','DISCOVERY')
 def test_qa_pass_needs_real_ui_evidence(self):
  d=self.doc('qa-report','qa');d['verdict']='PASS'
  self.assertIn('PASS requires real_execution, command, exit_code=0 and output_ref',validate(d))
  self.assertIn('QA PASS requires browser-interactive method',validate(d))
 def test_real_qa_log_must_exist(self):
  self.seed_build_dependencies()
  # For the evidence-specific test, prepare a legitimate build predecessor.
  build=self.doc('build','developer',aid='A006',inputs=['A005'])
  control.submit(self.root,'RUN-TEST',build)
  control.review(self.root,'RUN-TEST','A006','qa','ACCEPT','reviewed')
  d=self.doc('qa-report','qa',aid='A007',inputs=['A006'])
  d['verdict']='PASS';d['sections']['method']='browser-interactive'
  d['sections']['acceptance_mapping']=[{'criterion':'AC-001','result':'PASS'}]
  d['sections']['interactions']=[{'target':'#save','action':'click','expected':'saved','observed':'saved','evidence_ref':'evidence/missing-trace.zip'}]
  d['execution']={'real_execution':True,'command':'pytest -q','exit_code':0,'output_ref':'evidence/fake.log','output_sha256':'abc'}
  self.assertEqual(validate(d),[])
  with self.assertRaises(control.WorkflowError):control.submit(self.root,'RUN-TEST',d)
 def test_reviewer_role_is_restricted(self):
  control.submit(self.root,'RUN-TEST',self.doc())
  with self.assertRaises(control.WorkflowError):control.review(self.root,'RUN-TEST','A001','developer','ACCEPT','checked')
 def test_security_pass_needs_real_scans(self):
  d=self.doc('security-report','security-reviewer');d['verdict']='PASS'
  self.assertTrue(any('security PASS requires scanner list' in e for e in validate(d)))
 def test_human_approval_required(self):
  # Construct a valid accepted dependency graph, not orphan reports.
  self.seed_build_dependencies()
  s=control.read(self.root,'RUN-TEST');s['phase']='DESIGN';control.save(self.root,s)
  with self.assertRaises(control.WorkflowError):control.advance(self.root,'RUN-TEST','BUILD')
  with patch('org_v5.control.verify_human_approval', return_value={'status':'APPROVED', 'actor':'human', 'verified_at':'now'}):
      control.approval(self.root,'RUN-TEST','BUILD','APPROVE','human','https://github.com/x/y/issues/1')
  self.assertEqual(control.advance(self.root,'RUN-TEST','BUILD'),'BUILD')
 def test_kill_switch_denies_writes(self):
  (self.root/'.agents/state').mkdir(parents=True)
  (self.root/'.agents/state/STOP').write_text('stop')
  with self.assertRaises(control.WorkflowError):control.submit(self.root,'RUN-TEST',self.doc())
 def test_memory_does_not_fake_success(self):
  with patch('org_v5.memory.memanto',return_value='Backend: cloud'):
   with self.assertRaises(control.WorkflowError):memory.status()
 def test_memory_offline_denied(self):
  with patch('org_v5.memory.memanto',side_effect=control.WorkflowError('offline')):
   with self.assertRaises(control.WorkflowError):memory.brief('qa','tests')
 def test_no_promote_without_human_approval(self):
  proposal=dict(id='MC001',role='qa',type='learning',text='Run browser interaction tests and attach a durable trace for each acceptance criterion.',tags=['evid-001','qa'],confidence=.8,provenance='observed',source_ref='docs/evidence.md',reason='reusable')
  memory.propose(self.root,'RUN-TEST',proposal)
  with self.assertRaises(control.WorkflowError):memory.promote(self.root,'RUN-TEST','MC001','https://github.com/x/y/issues/1')
 def test_required_predecessor_kind_denied(self):
  with self.assertRaises(control.WorkflowError) as ctx:
   control.submit(self.root,'RUN-TEST',self.doc('architecture','architect'))
  self.assertIn('missing required predecessor',str(ctx.exception))
 def seed_build_dependencies(self):
  # Use real submissions and independent reviewers to seed an accepted chain.
  upstream=self.doc('intake','orchestrator',aid='A001')
  control.submit(self.root,'RUN-TEST',upstream)
  control.review(self.root,'RUN-TEST','A001','critical-reviewer','ACCEPT','reviewed')
  market=self.doc('market-research','market-researcher',aid='A002',inputs=['A001'])
  market['sections']['sources']=[{'url':'https://example.com/report','accessed':'2026-10-10','claim':'test source'}]
  control.submit(self.root,'RUN-TEST',market)
  control.review(self.root,'RUN-TEST','A002','critical-reviewer','ACCEPT','reviewed')
  critique=self.doc('critical-review','critical-reviewer',aid='A003',inputs=['A002'])
  critique['sections']['sources']=[{'url':'https://example.com/report','accessed':'2026-10-10','claim':'test source'}]
  control.submit(self.root,'RUN-TEST',critique)
  control.review(self.root,'RUN-TEST','A003','ceo','ACCEPT','reviewed')
  prd=self.doc('prd','product-manager',aid='A004',inputs=['A002','A003'])
  prd['sections']['stories']=[{'id':'US-1','as_a':'buyer','i_want':'add item','so_that':'save','acceptance_ids':['AC-1']}]
  prd['sections']['acceptance_criteria']=[{'id':'AC-1','given':'open','when':'click','then':'saved'}]
  control.submit(self.root,'RUN-TEST',prd)
  control.review(self.root,'RUN-TEST','A004','qa','ACCEPT','reviewed')
  adr=self.doc('architecture','architect',aid='A005',inputs=['A004'])
  control.submit(self.root,'RUN-TEST',adr)
  control.review(self.root,'RUN-TEST','A005','security-reviewer','ACCEPT','reviewed')
 def test_resume_package_contains_hashes(self):
  control.submit(self.root,'RUN-TEST',self.doc());control.review(self.root,'RUN-TEST','A001','critical-reviewer','ACCEPT','checked')
  package=control.resume_package(self.root,'RUN-TEST')
  self.assertEqual(package['accepted_artifacts'][0]['sha256'],digest(self.doc()))

if __name__=='__main__':unittest.main()
