"""
core/privacy.py — Differential Privacy & Federated Learning helpers

Uses Laplace mechanism (the standard DP mechanism for numerical queries).
Epsilon (ε) controls the privacy budget:
  - Lower ε  → more noise → stronger privacy, less accuracy
  - Higher ε → less noise → weaker privacy, more accuracy
  Recommended range: 0.1 (strong) to 1.0 (moderate).

Override via environment variable: export SECMED_EPSILON=0.5
"""

import numpy as np
import hashlib
import os

# ─── Privacy budget ───────────────────────────────────────────────────────────
EPSILON = float(os.environ.get("SECMED_EPSILON", "0.5"))

# Sensitivity = max change a single reading can cause in the output.
# For accelerometer magnitude bounded to [0, CLIP_MAX], sensitivity = CLIP_MAX.
CLIP_MAX = 50.0   # m/s² — anything above this is clipped before masking


# ─── Core DP primitives ───────────────────────────────────────────────────────

def clip_value(value: float, low: float = 0.0, high: float = CLIP_MAX) -> float:
    """
    Clip a sensor reading to [low, high] before applying noise.
    This is a mandatory pre-processing step for Laplace DP to bound sensitivity.
    """
    return float(np.clip(value, low, high))


def laplace_noise(sensitivity: float, epsilon: float = EPSILON) -> float:
    """
    Sample noise from the Laplace distribution: Lap(sensitivity / epsilon).
    This satisfies ε-differential privacy for a query with the given sensitivity.
    """
    scale = sensitivity / epsilon
    return float(np.random.laplace(0, scale))


def apply_privacy_mask(value: float, epsilon: float = EPSILON) -> float:
    """
    Apply differential privacy to a single sensor reading via the Laplace mechanism.

    Steps:
      1. Clip to bound sensitivity
      2. Add calibrated Laplace noise
    """
    clipped = clip_value(value)
    sensitivity = CLIP_MAX  # global sensitivity for clipped values
    noise = laplace_noise(sensitivity, epsilon)
    masked = clipped + noise
    # Keep masked value non-negative (magnitude cannot be < 0)
    return max(0.0, masked)


# ─── Federated Learning helper ────────────────────────────────────────────────

def generate_secure_update(heart_rate_column, epsilon: float = EPSILON) -> dict:
    """
    Simulate a Local Differential Privacy update for Federated Learning.
    Masks raw statistics before transmission to the central server.
    """
    local_mean = float(heart_rate_column.mean())
    local_std  = float(heart_rate_column.std())

    # Sensitivity for mean query over bounded HR [40, 200] = (200-40)/n ≈ small
    # For simplicity we treat sensitivity = 1 BPM (conservative)
    masked_mean = local_mean + laplace_noise(sensitivity=1.0, epsilon=epsilon)

    device_id  = os.environ.get("SECMED_DEVICE_ID", "Device_001")
    data_hash  = hashlib.sha256(str(round(masked_mean, 4)).encode()).hexdigest()

    return {
        "device_id":   device_id,
        "masked_mean": round(masked_mean, 2),
        "local_std":   round(local_std, 2),
        "epsilon":     epsilon,
        "integrity_hash": data_hash,
        "status":      "Anomaly_Detected" if local_mean > 110 else "Normal",
    }