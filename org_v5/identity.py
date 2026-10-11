import os
import hmac
import hashlib

class RunnerAuthority:
    """Isolated authority that holds signing credentials in-memory, never in os.environ."""
    def __init__(self, secret: str = None):
        self._secret = secret or os.urandom(32).hex()

    def issue_token(self, agent_id: str, role: str) -> str:
        msg = f"{agent_id}:{role}".encode('utf-8')
        return hmac.new(self._secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

    def verify(self, agent_id: str, role: str, token: str) -> bool:
        if not token or not agent_id or not role:
            return False
        expected = self.issue_token(agent_id, role)
        return hmac.compare_digest(token, expected)

# Process-level default authority for trusted test harnesses and runner processes.
# Secrets are kept private in-memory and NEVER exported to os.environ.
_TRUSTED_RUNNER_AUTHORITY: RunnerAuthority | None = None

def get_runner_authority() -> RunnerAuthority | None:
    return _TRUSTED_RUNNER_AUTHORITY

def set_runner_authority(authority: RunnerAuthority | None):
    global _TRUSTED_RUNNER_AUTHORITY
    _TRUSTED_RUNNER_AUTHORITY = authority

def sign_runner_token(agent_id: str, role: str, secret: str) -> str:
    """Signs an actor identity with runner secret using HMAC-SHA256."""
    msg = f"{agent_id}:{role}".encode('utf-8')
    return hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

def set_actor_context(agent_id: str, role: str, secret_or_authority: str | RunnerAuthority = None):
    """
    Sets actor context.
    Ensures AGY_RUNNER_SECRET is NEVER placed in os.environ.
    Issues a token from the isolated RunnerAuthority or secret without exposing the secret to the environment.
    """
    global _TRUSTED_RUNNER_AUTHORITY
    os.environ['AGY_AGENT_INSTANCE_ID'] = agent_id
    os.environ['AGY_ASSIGNED_ROLE'] = role
    
    # Strip any leaked or adversary-injected runner secret from os.environ
    os.environ.pop('AGY_RUNNER_SECRET', None)
    
    # Retire GITHUB_TOKEN from executing agent's os.environ into runner memory
    if 'GITHUB_TOKEN' in os.environ:
        from .approvals import set_trusted_github_token
        set_trusted_github_token(os.environ.pop('GITHUB_TOKEN'))
    
    if isinstance(secret_or_authority, RunnerAuthority):
        _TRUSTED_RUNNER_AUTHORITY = secret_or_authority
        os.environ['AGY_RUNNER_TOKEN'] = secret_or_authority.issue_token(agent_id, role)
    elif isinstance(secret_or_authority, str):
        _TRUSTED_RUNNER_AUTHORITY = RunnerAuthority(secret_or_authority)
        os.environ['AGY_RUNNER_TOKEN'] = _TRUSTED_RUNNER_AUTHORITY.issue_token(agent_id, role)
    elif _TRUSTED_RUNNER_AUTHORITY is not None:
        os.environ['AGY_RUNNER_TOKEN'] = _TRUSTED_RUNNER_AUTHORITY.issue_token(agent_id, role)
    else:
        os.environ.pop('AGY_RUNNER_TOKEN', None)

def clear_actor_context():
    """Clears actor context and runner tokens from environment and resets authority."""
    global _TRUSTED_RUNNER_AUTHORITY
    _TRUSTED_RUNNER_AUTHORITY = None
    for var in ('AGY_AGENT_INSTANCE_ID', 'AGY_ASSIGNED_ROLE', 'AGY_RUNNER_SECRET', 'AGY_RUNNER_TOKEN'):
        os.environ.pop(var, None)
    from .approvals import set_trusted_github_token
    set_trusted_github_token(None)

def verify_actor_identity(expected_role: str) -> dict:
    """
    Verifies the identity of the current actor.
    If AGY_RUNNER_SECRET is present in os.environ, the environment is flagged as compromised
    and treated strictly as UNVERIFIED.
    Only identities verified against an isolated RunnerAuthority receive VERIFIED assurance.
    """
    agent_id = os.environ.get('AGY_AGENT_INSTANCE_ID')
    assigned_role = os.environ.get('AGY_ASSIGNED_ROLE')
    runner_token = os.environ.get('AGY_RUNNER_TOKEN')
    
    # Check for tainted environment: an agent environment containing the runner secret is compromised
    if 'AGY_RUNNER_SECRET' in os.environ:
        return {
            'assurance': 'UNVERIFIED', 
            'reason': 'compromised: AGY_RUNNER_SECRET exposed in agent process environment; independent attestation impossible',
            'agent_id': agent_id or 'unknown',
            'role': assigned_role or 'unknown'
        }
    
    if not agent_id or not assigned_role:
        return {'assurance': 'UNVERIFIED', 'reason': 'no execution context provided by runner'}
    
    if assigned_role != expected_role:
        raise ValueError(f"Actor identity mismatch: expected {expected_role}, got {assigned_role}")
    
    # Check cryptographic attestation via isolated authority
    if _TRUSTED_RUNNER_AUTHORITY and runner_token:
        if _TRUSTED_RUNNER_AUTHORITY.verify(agent_id, assigned_role, runner_token):
            return {'assurance': 'VERIFIED', 'agent_id': agent_id, 'role': assigned_role}
        else:
            return {'assurance': 'UNVERIFIED', 'reason': 'invalid runner signature', 'agent_id': agent_id, 'role': assigned_role}
            
    # Without isolated runner authority, mutable env vars are strictly UNVERIFIED execution metadata
    return {'assurance': 'UNVERIFIED', 'reason': 'mutable environment variables without isolated runner authority', 'agent_id': agent_id, 'role': assigned_role}

def verify_independence(producer_identity: dict, reviewer_identity: dict) -> bool:
    """
    Ensures that producer and reviewer are verifiably independent.
    If either identity is UNVERIFIED, cryptographic independence cannot be guaranteed.
    If agent IDs match, they are the same instance.
    """
    prod_assurance = producer_identity.get('assurance')
    rev_assurance = reviewer_identity.get('assurance')
    
    prod_id = producer_identity.get('agent_id')
    rev_id = reviewer_identity.get('agent_id')
    
    if not prod_id or not rev_id or prod_id == rev_id:
        return False
        
    if prod_assurance != 'VERIFIED' or rev_assurance != 'VERIFIED':
        return False
        
    return True
