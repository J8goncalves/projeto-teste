import os
import hmac
import hashlib

def sign_runner_token(agent_id: str, role: str, secret: str) -> str:
    """Signs an actor identity with runner secret using HMAC-SHA256."""
    msg = f"{agent_id}:{role}".encode('utf-8')
    return hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

def set_actor_context(agent_id: str, role: str, secret: str = None):
    """Sets actor context. If secret is provided, issues a cryptographically verified runner token."""
    os.environ['AGY_AGENT_INSTANCE_ID'] = agent_id
    os.environ['AGY_ASSIGNED_ROLE'] = role
    if secret:
        os.environ['AGY_RUNNER_SECRET'] = secret
        os.environ['AGY_RUNNER_TOKEN'] = sign_runner_token(agent_id, role, secret)
    else:
        os.environ.pop('AGY_RUNNER_TOKEN', None)

def clear_actor_context():
    """Clears actor context and runner tokens from environment."""
    for var in ('AGY_AGENT_INSTANCE_ID', 'AGY_ASSIGNED_ROLE', 'AGY_RUNNER_SECRET', 'AGY_RUNNER_TOKEN'):
        os.environ.pop(var, None)

def verify_actor_identity(expected_role: str) -> dict:
    """
    Verifies the identity of the current actor.
    Mutable environment variables without cryptographic proof are classified as UNVERIFIED metadata.
    Only identities signed with AGY_RUNNER_SECRET and matching AGY_RUNNER_TOKEN receive VERIFIED assurance.
    """
    agent_id = os.environ.get('AGY_AGENT_INSTANCE_ID')
    assigned_role = os.environ.get('AGY_ASSIGNED_ROLE')
    runner_token = os.environ.get('AGY_RUNNER_TOKEN')
    runner_secret = os.environ.get('AGY_RUNNER_SECRET')
    
    if not agent_id or not assigned_role:
        return {'assurance': 'UNVERIFIED', 'reason': 'no execution context provided by runner'}
    
    if assigned_role != expected_role:
        raise ValueError(f"Actor identity mismatch: expected {expected_role}, got {assigned_role}")
    
    # Check cryptographic runner attestation
    if runner_secret and runner_token:
        expected_token = sign_runner_token(agent_id, assigned_role, runner_secret)
        if hmac.compare_digest(runner_token, expected_token):
            return {'assurance': 'VERIFIED', 'agent_id': agent_id, 'role': assigned_role}
        else:
            return {'assurance': 'UNVERIFIED', 'reason': 'invalid runner signature', 'agent_id': agent_id, 'role': assigned_role}
            
    # Without runner secret/token, mutable env vars are strictly UNVERIFIED execution metadata
    return {'assurance': 'UNVERIFIED', 'reason': 'mutable environment variables without runner attestation', 'agent_id': agent_id, 'role': assigned_role}

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
