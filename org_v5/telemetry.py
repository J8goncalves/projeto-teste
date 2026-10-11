"""Execution telemetry and audit reporting for V5.2.

Provides verifiable logging of subagent invocations, handoffs, durations,
and generates structured reports distinguishing verified execution from
unverified or unmeasured metrics.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone

def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def get_telemetry_file(root: Path, run_id: str) -> Path:
    p = root / 'runs' / run_id / 'telemetry' / 'events.jsonl'
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def log_event(root: Path, run_id: str, event: dict) -> dict:
    """Logs a telemetry event to events.jsonl atomically."""
    path = get_telemetry_file(root, run_id)
    entry = dict(event)
    entry.setdefault('run_id', run_id)
    entry.setdefault('timestamp', stamp())
    line = json.dumps(entry, ensure_ascii=False) + '\n'
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line)
    return entry

def read_events(root: Path, run_id: str) -> list[dict]:
    """Reads all recorded telemetry events for a given run."""
    path = root / 'runs' / run_id / 'telemetry' / 'events.jsonl'
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events

def generate_report(root: Path, run_id: str) -> dict:
    """
    Generates a full auditable execution report for a run,
    binding state, artifacts, telemetry, handoffs, and resource metrics.
    """
    from .control import read as read_state, MODES, PHASES
    state = read_state(root, run_id)
    events = read_events(root, run_id)
    
    workflow_mode = state.get('workflow_mode', 'ENGINEERING_SMALL')
    execution_policy = state.get('execution_policy', 'STANDARD')
    
    # Justification text
    justification = (
        f"Modo de fluxo '{workflow_mode}' selecionado para nível de risco {state.get('level', 1)}. "
        f"Política de execução '{execution_policy}' vinculada à branch '{state.get('branch', 'unknown')}' "
        f"para governança auditável com proteção estrita de produção."
    )
    
    # Analyze events
    invocations_by_role: dict[str, list[dict]] = {}
    for ev in events:
        role = ev.get('role', 'unknown')
        invocations_by_role.setdefault(role, []).append(ev)
        
    effective_agents = []
    total_measured_duration = 0.0
    
    for role, role_events in sorted(invocations_by_role.items()):
        inst_ids = {e.get('instance_id') for e in role_events if e.get('instance_id')}
        durations = [float(e.get('duration_seconds', 0.0)) for e in role_events if e.get('duration_seconds') is not None]
        role_duration = sum(durations)
        total_measured_duration += role_duration
        
        arts = []
        for e in role_events:
            arts.extend(e.get('artifacts', []))
            
        effective_agents.append({
            'role': role,
            'instances': sorted(inst_ids) if inst_ids else ['NÃO VERIFICADO'],
            'invocations_count': len([e for e in role_events if e.get('event_type') in ('invocation_end', 'invocation') or not e.get('event_type')]),
            'total_duration_seconds': round(role_duration, 2),
            'artifacts_produced': arts,
            'assurance': 'VERIFIED' if any(e.get('assurance') == 'VERIFIED' for e in role_events) else 'UNVERIFIED/ROLE_ONLY'
        })
        
    # Planned vs. effective
    planned_for_mode = set()
    for phase_arts in MODES.get(workflow_mode, {}).values():
        for art_kind in phase_arts:
            from .contracts import CONTRACTS
            if art_kind in CONTRACTS:
                planned_for_mode.add(CONTRACTS[art_kind][0])
    planned_for_mode.add('orchestrator')
    
    effective_roles = {a['role'] for a in effective_agents}
    # Also add producers from artifacts if telemetry was unrecorded
    artifact_producers = {meta.get('role') for meta in state.get('artifacts', {}).values()}
    all_observed_roles = effective_roles.union(artifact_producers)
    
    declared_only = sorted(planned_for_mode - all_observed_roles)
    
    from .contracts import ROLES
    unnecessary = sorted(ROLES - planned_for_mode)
    
    # Artifacts breakdown
    artifacts_report = []
    for aid, meta in sorted(state.get('artifacts', {}).items()):
        is_accepted = aid in state.get('accepted', {})
        acc_info = state.get('accepted', {}).get(aid, {})
        artifacts_report.append({
            'id': aid,
            'kind': meta.get('kind'),
            'role': meta.get('role'),
            'sha256': meta.get('sha256'),
            'status': 'accepted' if is_accepted else 'submitted',
            'reviewer': acc_info.get('reviewer'),
            'reviewer_status': acc_info.get('reviewer_identity', {}).get('status', acc_info.get('reviewer_identity', {}).get('assurance', 'UNVERIFIED')),
            'submitted_at': meta.get('submitted_at'),
            'path': meta.get('path')
        })
        
    # Handoffs and history
    handoffs = []
    prev_role = None
    for item in state.get('history', []):
        act = item.get('action')
        if act == 'submitted':
            r = item.get('role')
            if prev_role and prev_role != r:
                handoffs.append({
                    'from_role': prev_role,
                    'to_role': r,
                    'at': item.get('at'),
                    'artifact': item.get('artifact')
                })
            prev_role = r
        elif act == 'review':
            r = item.get('reviewer')
            if prev_role and prev_role != r:
                handoffs.append({
                    'from_role': prev_role,
                    'to_role': r,
                    'at': item.get('at'),
                    'verdict': item.get('verdict')
                })
            prev_role = r
            
    # Gates and approvals
    gates_summary = {}
    for g in ('BUILD', 'VERIFY', 'RELEASE', 'CLOSED'):
        app = state.get('approvals', {}).get(g)
        if app:
            gates_summary[g] = {
                'status': app.get('status', 'APPROVED'),
                'decision': app.get('decision'),
                'actor': app.get('actor'),
                'rule': app.get('rule', 'HUMAN_VERIFIED'),
                'verified': app.get('verified', False)
            }
        else:
            gates_summary[g] = {'status': 'PENDING' if PHASES.index(state['phase']) < PHASES.index(g if g in PHASES else 'RELEASE') else 'NOT_REACHED'}
            
    # Compile final telemetry summary
    telemetry_status = "VERIFIED_EVENTS" if events else "NÃO VERIFICÁVEL"
    
    return {
        'schema': 'AUDIT_REPORT_V5_2',
        'run_id': run_id,
        'goal': state.get('goal'),
        'workflow_mode': workflow_mode,
        'execution_policy': execution_policy,
        'branch': state.get('branch', 'unknown'),
        'current_phase': state.get('phase'),
        'justification': justification,
        'telemetry_verification': telemetry_status,
        'agents_effective': effective_agents if events else [
            {
                'role': r,
                'instances': ['NÃO VERIFICÁVEL'],
                'invocations_count': len([aid for aid, m in state.get('artifacts', {}).items() if m.get('role') == r]),
                'total_duration_seconds': 'NÃO MEDIDO',
                'artifacts_produced': [aid for aid, m in state.get('artifacts', {}).items() if m.get('role') == r],
                'assurance': 'UNVERIFIED'
            }
            for r in sorted(artifact_producers)
        ],
        'agents_declared_only': declared_only,
        'agents_unnecessary': unnecessary,
        'artifacts': artifacts_report,
        'handoffs_count': len(handoffs),
        'handoffs': handoffs,
        'reworks_count': sum(state.get('corrections', {}).values()),
        'reworks_by_pair': state.get('corrections', {}),
        'gates': gates_summary,
        'resource_metrics': {
            'tokens_per_agent': "NÃO MEDIDO",
            'cost_usd': "NÃO MEDIDO",
            'total_measured_duration_seconds': round(total_measured_duration, 2) if events else "NÃO MEDIDO"
        }
    }
