from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import json
import os
import socket
from core.security import generate_zkp_proof
from core.privacy import apply_privacy_mask

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from any client (phone, browser, etc.)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_FILE  = os.path.join(BASE_DIR, "live_alerts.json")
STREAM_FILE  = os.path.join(BASE_DIR, "live_stream.json")

# --- Thread-safe file locks (prevents race condition / JSON corruption) ---
_alerts_lock = threading.Lock()
_stream_lock = threading.Lock()

# --- Calibrated threshold ---
# Depending on the mobile device, Sensor Logger might report linear acceleration
# (Standard accelerometer includes gravity ~9.8 m/s²).
# We set the default threshold to 3.0 so physical flips/shakes trigger anomalies.
# Override via environment variable: export SECMED_THRESHOLD=3.0
MOVEMENT_THRESHOLD = float(os.environ.get("SECMED_THRESHOLD", "3.0"))

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read_json(path):
    """Safely read a JSON list file; return [] on any error."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _extend_json(path, lock, new_entries, max_items=2000):
    """
    Thread-safe, crash-safe batch append.
    Writes to a temp file then swaps so readers always see a complete JSON file.
    """
    if not new_entries:
        return
        
    with lock:
        records = _read_json(path)
        records.extend(new_entries)
        
        # Keep only the last `max_items`
        if len(records) > max_items:
            records = records[-max_items:]

        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(records, f, indent=2)
        
        try:
            os.replace(tmp, path)
        except PermissionError:
            try:
                if os.path.exists(path): os.remove(path)
                os.rename(tmp, path)
            except Exception:
                with open(path, "w") as f:
                    json.dump(records, f, indent=2)
                if os.path.exists(tmp): os.remove(tmp)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/status", methods=["GET"])
def status():
    """Connectivity check — Sensor Logger / client can ping this."""
    return jsonify({
        "status": "online",
        "server": "SecureMed-Fed",
        "threshold": MOVEMENT_THRESHOLD,
        "current_time_ms": int(time.time() * 1000)
    }), 200


@app.route("/", methods=["POST"])
def secure_ingest():
    data = request.get_json(silent=True)
    if not data or "payload" not in data:
        return jsonify({"status": "error", "message": "Missing payload"}), 400

    stream_batch = []
    alert_batch  = []

    for sensor in data["payload"]:
        if sensor.get("name") not in ["accelerometer", "linear_acceleration"]:
            continue

        v   = sensor.get("values", {})
        x   = v.get("x", 0)
        y   = v.get("y", 0)
        z   = v.get("z", 0)
        mag = (x**2 + y**2 + z**2) ** 0.5

        now           = time.time()
        timestamp_str = f"{now:.3f}"
        time_str      = time.strftime("%H:%M:%S", time.localtime(now)) + f".{int((now % 1) * 1000):03d}"

        # Every reading goes to the live stream
        stream_batch.append({
            "time":      time_str,
            "timestamp": timestamp_str,
            "x":         round(x, 4),
            "y":         round(y, 4),
            "z":         round(z, 4),
            "mag":       round(mag, 4),
        })

        # Only anomalies get the full security treatment
        if mag > MOVEMENT_THRESHOLD:
            safe_mag = apply_privacy_mask(mag)
            proof    = generate_zkp_proof(safe_mag, timestamp_str)

            alert_batch.append({
                "time":       time_str,
                "timestamp":  timestamp_str,
                "mag":        round(mag, 4),
                "masked_mag": round(safe_mag, 4),
                "proof":      proof,
            })
            print(f"[ALERT] Anomaly detected @ {time_str}  mag={mag:.2f}  proof={proof[:16]}…")

    # Batch write to disk once per request
    _extend_json(STREAM_FILE, _stream_lock, stream_batch)
    _extend_json(ALERTS_FILE, _alerts_lock, alert_batch)

    return jsonify({"status": "secure_received"}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────────────────────

def _get_local_ip():
    """Return the machine's LAN IP so the user can configure Sensor Logger."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = _get_local_ip()
    print("=" * 60)
    print("  SecureMed-Fed  --  Secure IoT Ingestion Server")
    print("=" * 60)
    print(f"  Local endpoint : http://{local_ip}:5000/")
    print(f"  Status check   : http://{local_ip}:5000/status")
    print(f"  Movement threshold : {MOVEMENT_THRESHOLD} m/s2")
    print()
    print("  >> Configure Sensor Logger:")
    print(f"     URL    -> http://{local_ip}:5000/")
    print("     Method -> POST")
    print("     Sensor -> Accelerometer  (interval: 100 ms)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)