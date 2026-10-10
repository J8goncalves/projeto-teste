import os

def verify_actor_identity(expected_role: str) -> dict:
    """
    Verifies the identity of the current actor using runner-injected context.
    If context is missing, returns UNVERIFIED.
    """
    agent_id = os.environ.get('AGY_AGENT_INSTANCE_ID')
    assigned_role = os.environ.get('AGY_ASSIGNED_ROLE')
    
    if not agent_id or not assigned_role:
        return {'assurance': 'UNVERIFIED', 'reason': 'no execution context provided by runner'}
    
    if assigned_role != expected_role:
        raise ValueError(f"Actor identity mismatch: expected {expected_role}, got {assigned_role}")
        
    return {'assurance': 'VERIFIED', 'agent_id': agent_id, 'role': assigned_role}

def verify_independence(producer_identity: dict, reviewer_identity: dict) -> bool:
    """
    Ensures that the producer and reviewer are not the same instance.
    """
    prod_assurance = producer_identity.get('assurance')
    rev_assurance = reviewer_identity.get('assurance')
    
    if prod_assurance == 'UNVERIFIED' or rev_assurance == 'UNVERIFIED':
        # If unverified, we cannot guarantee independence cryptographically.
        # It must be treated as unverified.
        return False
        
    prod_id = producer_identity.get('agent_id')
    rev_id = reviewer_identity.get('agent_id')
    
    if prod_id == rev_id:
        return False
        
    return True
