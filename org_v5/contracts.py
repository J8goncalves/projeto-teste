"""Executable artifact contract rules. Roles and sections are deliberately explicit."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROLES = {
    'orchestrator', 'ceo', 'market-researcher', 'customer-researcher',
    'product-strategist', 'marketing-strategist', 'critical-reviewer',
    'legal-compliance', 'experiment-designer', 'data-analytics',
    'product-manager', 'architect', 'developer', 'security-reviewer',
    'qa', 'devops-finops', 'release-manager', 'memory-curator',
    'implementation-reviewer',
}
# Owner, required sections, handoff recipient. Optional roles can serve reviews.
CONTRACTS = {
    'intake': ('orchestrator', ['goal', 'scope', 'constraints', 'risk_level', 'definition_of_success']),
    'market-research': ('market-researcher', ['question', 'method', 'sources', 'benchmark', 'strengths', 'weaknesses', 'risks', 'recommendation', 'uncertainties']),
    'customer-research': ('customer-researcher', ['question', 'method', 'sources', 'findings', 'limitations', 'recommendation']),
    'strategy': ('product-strategist', ['problem', 'alternatives', 'evidence', 'tradeoffs', 'cost', 'risks', 'decision']),
    'marketing': ('marketing-strategist', ['segment', 'benchmark', 'sources', 'channels', 'unit_economics', 'risks', 'experiments']),
    'experiment': ('experiment-designer', ['hypothesis', 'metric', 'design', 'sample', 'stopping_rule', 'risks']),
    'analytics': ('data-analytics', ['metric_definitions', 'data_origin', 'method', 'limitations', 'results']),
    'legal': ('legal-compliance', ['scope', 'jurisdiction', 'sources', 'issues', 'risks', 'recommendation']),
    'critical-review': ('critical-reviewer', ['claims_checked', 'conflicts', 'evidence_gaps', 'risks', 'verdict']),
    'prd': ('product-manager', ['problem', 'scope', 'out_of_scope', 'stories', 'acceptance_criteria', 'business_rules', 'security', 'test_plan', 'risks']),
    'architecture': ('architect', ['requirements', 'options', 'simplest_viable', 'tradeoffs', 'financial_feasibility', 'security', 'adr', 'risks']),
    'build': ('developer', ['input_prd', 'architecture_ref', 'changes', 'unit_test_command', 'unit_test_output', 'integration_results', 'security_considerations', 'commit_ref']),
    'qa-report': ('qa', ['acceptance_mapping', 'environment', 'method', 'interactions', 'observations', 'console', 'evidence', 'limitations']),
    'security-report': ('security-reviewer', ['threats', 'scans', 'scan_outputs', 'manual_checks', 'findings', 'risk_rating', 'evidence']),
    'ops': ('devops-finops', ['topology', 'cost', 'rollback', 'observability', 'evidence']),
    'release': ('release-manager', ['build_ref', 'qa_ref', 'security_ref', 'rollback', 'approval_ref', 'verdict']),
    'memory-review': ('memory-curator', ['proposals', 'provenance', 'privacy', 'retention', 'duplicates', 'decision']),
    'implementation-review': ('implementation-reviewer', ['contracts', 'tests', 'policy_effectiveness', 'gaps', 'verdict']),
    'executive-decision': ('ceo', ['alternatives', 'benefits', 'downsides', 'risk', 'finance', 'sources', 'recommendation']),
}
RESEARCH_KINDS = {'market-research', 'customer-research', 'marketing', 'legal', 'critical-review'}
VERDICTS = {'PASS', 'FAIL', 'BLOCKED', 'NOT_RUN'}
URL_RE = re.compile(r'^https?://[^\s/]+(?:/[^\s]*)?$', re.I)

class ContractError(ValueError):
    pass

def digest(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def valid_ref(ref: str) -> bool:
    return bool(isinstance(ref,str) and (ref.startswith('https://') or ref.startswith('docs/') or ref.startswith('runs/') or ref.startswith('evidence/') or ref.startswith('intelligence/') or ref.startswith('src/') or ref.startswith('tests/')) and '..' not in ref and '\\' not in ref)

def validate(doc: dict) -> list[str]:
    errors = []
    if not isinstance(doc, dict):
        return ['document must be an object']
    kind = doc.get('kind')
    if kind not in CONTRACTS:
        return ['unknown kind']
    owner, required = CONTRACTS[kind]
    if doc.get('role') != owner:
        errors.append(f'role must be {owner}')
    for field in ('id','run_id','summary','version','status'):
        if not isinstance(doc.get(field), str) or not doc[field].strip():
            errors.append(f'{field} missing')
    if doc.get('status') != 'submitted':
        errors.append('status must be submitted')
    if doc.get('version') != '5.0':
        errors.append('version must be 5.0')
    sections = doc.get('sections')
    if not isinstance(sections, dict):
        return errors + ['sections must be an object']
    for field in required:
        value=sections.get(field)
        if value is None or value == '' or value == [] or value == {}:
            errors.append(f'missing section: {field}')
        elif isinstance(value, str) and value.strip().lower() in ('todo','tbd','mock','placeholder','none','n/a'):
            errors.append(f'placeholder section: {field}')
    for field in ('input_ids','evidence_refs'):
        if not isinstance(doc.get(field), list):
            errors.append(f'{field} must be array')
    for ref in doc.get('evidence_refs',[]) if isinstance(doc.get('evidence_refs'),list) else []:
        if not valid_ref(ref):
            errors.append(f'invalid evidence reference: {ref!r}')
    if kind in RESEARCH_KINDS:
        sources = sections.get('sources',[])
        if not isinstance(sources, list) or not sources:
            errors.append('research must include verifiable sources list')
        else:
            for s in sources:
                if not isinstance(s,dict) or not URL_RE.match(str(s.get('url',''))) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(s.get('accessed',''))) or not s.get('claim'):
                    errors.append('source requires url, accessed YYYY-MM-DD and supported claim')
    if kind == 'prd':
        stories=sections.get('stories',[])
        if not isinstance(stories,list) or not stories or any(not isinstance(s,dict) or not all(s.get(k) for k in ('id','as_a','i_want','so_that','acceptance_ids')) for s in stories):
            errors.append('stories require id, as_a, i_want, so_that, acceptance_ids')
        criteria=sections.get('acceptance_criteria',[])
        if not isinstance(criteria,list) or not criteria or any(not isinstance(c,dict) or not all(c.get(k) for k in ('id','given','when','then')) for c in criteria):
            errors.append('acceptance criteria require id, given, when, then')
        ids={c.get('id') for c in criteria if isinstance(c,dict)} if isinstance(criteria,list) else set()
        if isinstance(stories,list):
            for s in stories:
                if isinstance(s,dict) and not set(s.get('acceptance_ids',[]) if isinstance(s.get('acceptance_ids'),list) else []).issubset(ids):
                    errors.append('story references nonexistent acceptance criteria')
    if kind in {'qa-report','security-report'}:
        verdict=doc.get('verdict')
        if verdict not in VERDICTS:
            errors.append('explicit verdict required')
        if verdict=='PASS':
            ex=doc.get('execution')
            if not isinstance(ex,dict) or ex.get('real_execution') is not True or not ex.get('command') or ex.get('exit_code')!=0 or not ex.get('output_ref'):
                errors.append('PASS requires real_execution, command, exit_code=0 and output_ref')
            if kind=='qa-report':
                if sections.get('method')!='browser-interactive':
                    errors.append('QA PASS requires browser-interactive method')
                interactions=sections.get('interactions')
                if not isinstance(interactions,list) or not interactions or any(not isinstance(i,dict) or not all(i.get(k) for k in ('target','action','expected','observed','evidence_ref')) for i in interactions):
                    errors.append('QA PASS requires documented real UI interactions with evidence')
                if not isinstance(sections.get('acceptance_mapping'),list) or not sections['acceptance_mapping']:
                    errors.append('QA PASS requires traceable acceptance mapping')
            else:
                if not isinstance(sections.get('scans'),list) or not sections['scans']:
                    errors.append('security PASS requires scanner list')
    return errors

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))
