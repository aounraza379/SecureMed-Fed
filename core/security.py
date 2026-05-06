"""
core/security.py — Zero-Knowledge Proof (ZKP) simulation layer

Uses HMAC-SHA256 for message authentication (keyed hash).
The secret key is loaded from the SECMED_SECRET_KEY environment variable
so it is never hardcoded into the public repo.

Usage:
    export SECMED_SECRET_KEY="your-secret-here"   # Linux / macOS
    $env:SECMED_SECRET_KEY="your-secret-here"     # PowerShell

If the variable is not set, a default demo key is used — fine for local dev,
NOT for production deployment.
"""

import hmac
import hashlib
import time
import os

# ─── Secret key (never hardcode in production) ────────────────────────────────
_SECRET_KEY = os.environ.get("SECMED_SECRET_KEY", "SECMED_DEV_KEY_2026").encode()


# ─── Core ZKP helpers ─────────────────────────────────────────────────────────

def generate_zkp_proof(magnitude: float, timestamp: str) -> str:
    """
    Generate a ZKP commitment using HMAC-SHA256.

    The proof binds the (masked) magnitude to a timestamp using a shared
    secret.  The doctor's dashboard can re-derive the HMAC and confirm the
    data was not tampered with — without ever seeing the raw value.

    Returns: hex-encoded HMAC digest (64 chars).
    """
    message = f"{round(magnitude, 4)}{timestamp}".encode()
    proof   = hmac.new(_SECRET_KEY, message, hashlib.sha256).hexdigest()
    return proof


def verify_zkp_proof(magnitude: float, timestamp: str, proof: str) -> bool:
    """
    Verify a previously generated ZKP proof.

    Returns True  → data is authentic and unmodified (VERIFIED ✅)
    Returns False → proof is invalid or data was tampered (INVALID ❌)
    """
    expected = generate_zkp_proof(magnitude, timestamp)
    # Use hmac.compare_digest to prevent timing-attack leaks
    return hmac.compare_digest(expected, proof)


def generate_emergency_proof(heart_rate: float, secret_key: str = None) -> dict:
    """
    Legacy helper — kept for backward compatibility.
    Generates a ZKP packet for a cardiac emergency event.
    """
    key       = (secret_key or os.environ.get("SECMED_SECRET_KEY", "SECMED_DEV_KEY_2026")).encode()
    timestamp = str(int(time.time()))
    message   = f"{heart_rate}{timestamp}".encode()
    commitment = hmac.new(key, message, hashlib.sha256).hexdigest()

    return {
        "commitment":          commitment,
        "is_emergency":        heart_rate > 120,
        "timestamp":           timestamp,
        "verification_status": "PENDING",
    }


def verify_emergency_proof(proof_packet: dict, original_commitment: str) -> dict:
    """Legacy helper — server-side verification of a cardiac emergency packet."""
    if hmac.compare_digest(proof_packet["commitment"], original_commitment):
        proof_packet["verification_status"] = "VERIFIED_AUTHENTIC"
    else:
        proof_packet["verification_status"] = "INVALID_PROOF"
    return proof_packet