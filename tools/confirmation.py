"""
Shared confirmation token utilities for destructive operations.
"""

import time
import secrets
import threading
from typing import Dict, Any, Optional

# Store pending deletion confirmations with expiration
# Structure: {"token": {"key": identifier, "expires": timestamp, "context": {...}}}
pending_confirmations = {}

# Lock for thread-safe access
confirmation_lock = threading.Lock()


def clean_expired_tokens():
    """Remove expired confirmation tokens."""
    with confirmation_lock:
        current_time = time.time()
        expired = [t for t, d in pending_confirmations.items() if d["expires"] < current_time]
        for t in expired:
            del pending_confirmations[t]


def create_confirmation_token(key: str, context: Dict[str, Any], ttl: int = 600) -> str:
    """
    Create a confirmation token for a pending destructive operation.

    Args:
        key: A unique identifier for what's being confirmed (e.g. hostname, group name)
        context: Arbitrary data to store with the token (records to delete, etc.)
        ttl: Time-to-live in seconds (default 10 minutes)

    Returns:
        The generated token string
    """
    token = secrets.token_hex(16)
    with confirmation_lock:
        pending_confirmations[token] = {
            "key": key,
            "expires": time.time() + ttl,
            "context": context
        }
    return token


def validate_confirmation_token(token: str, expected_key: str) -> Optional[Dict[str, Any]]:
    """
    Validate and consume a confirmation token.

    Args:
        token: The token to validate
        expected_key: The expected key that was used when creating the token

    Returns:
        The stored context if valid, None if invalid/expired.
        Sets an 'error' key in the return dict if there's a mismatch.
    """
    clean_expired_tokens()
    with confirmation_lock:
        if token not in pending_confirmations:
            return None

        token_data = pending_confirmations[token]

        if token_data["key"] != expected_key:
            return {"error": f"Token was issued for '{token_data['key']}', not '{expected_key}'"}

        context = token_data["context"]
        del pending_confirmations[token]
        return context


def resolve_targets(pihole_clients, piholes=None, pihole=None):
    """
    Resolve which Pi-hole clients to target.

    Args:
        pihole_clients: Dict of all Pi-hole clients
        piholes: Optional list of Pi-hole names (for multi-target tools)
        pihole: Optional single Pi-hole name (for single-target tools)

    Returns:
        List of target names, or None with error dict if invalid
    """
    if pihole is not None:
        if pihole not in pihole_clients:
            return None, {"status": "error", "message": f"Pi-hole '{pihole}' not found"}
        return [pihole], None

    if piholes is not None:
        targets = [p for p in piholes if p in pihole_clients]
        if not targets:
            return None, {"status": "error", "message": "No valid Pi-hole names provided"}
        return targets, None

    return list(pihole_clients.keys()), None
