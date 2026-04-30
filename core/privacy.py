import numpy as np
import hashlib

def generate_secure_update(heart_rate_column):
    """
    Simulates a Local Differential Privacy update for Federated Learning.
    Masks raw data before transmission to the central server.
    """
    # Calculate local statistics
    local_mean = heart_rate_column.mean()
    local_std = heart_rate_column.std()

    # Add Gaussian Noise (Differential Privacy) to mask the exact mean
    noise = np.random.normal(0, 0.1, 1)[0]
    masked_update = local_mean + noise

    # Generate a unique hash for the device to ensure data integrity (ZKP Foundation)
    device_id = "Device_Elderly_001"
    data_hash = hashlib.sha256(str(masked_update).encode()).hexdigest()

    return {
        "masked_mean": round(masked_update, 2),
        "integrity_hash": data_hash,
        "status": "Anomaly_Detected" if local_mean > 110 else "Normal"
    }