import hashlib
import time

def generate_emergency_proof(heart_rate, secret_key="PATIENT_SECRET_001"):
    """
    Simulates a Zero-Knowledge Proof (ZKP) for emergency alerts.
    Verifies the severity of the event without exposing raw vitals.
    """
    timestamp = str(int(time.time()))

    # A "Commitment": A cryptographic hash of the data + a secret key
    # This acts as a 'digital seal' that cannot be altered.
    commitment = hashlib.sha256(f"{heart_rate}{secret_key}{timestamp}".encode()).hexdigest()

    # Define the 'Proof' condition (Is it a real emergency?)
    is_emergency = heart_rate > 120

    # Create the 'Proof' packet for the hospital
    # We send the commitment and the status, but NOT the secret_key or the exact heart_rate
    proof_packet = {
        "commitment": commitment,
        "is_emergency": is_emergency,
        "timestamp": timestamp,
        "verification_status": "PENDING"
    }

    return proof_packet

def verify_emergency_proof(proof_packet, original_commitment):
    """
    Simulates the server-side verification of the cryptographic seal.
    """
    if proof_packet["commitment"] == original_commitment:
        proof_packet["verification_status"] = "VERIFIED_AUTHENTIC"
    else:
        proof_packet["verification_status"] = "INVALID_PROOF"

    return proof_packet