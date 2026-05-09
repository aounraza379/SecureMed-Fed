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
CORS(app)

# --- ENSURE DIRECTORY CONSISTENCY ---
# This ensures data is saved in the same folder as the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_FILE = os.path.join(BASE_DIR, "live_alerts.json")
STREAM_FILE = os.path.join(BASE_DIR, "live_stream.json")

_alerts_lock = threading.Lock()
_stream_lock = threading.Lock()

MOVEMENT_THRESHOLD = float(os.environ.get("SECMED_THRESHOLD", "13.0"))

def _extend_json(path, lock, new_entries, max_items=150):
    if not new_entries: return
    with lock:
        records = []
        if os.path.exists(path):
            try:
                with open(path, "r") as f: records = json.load(f)
            except: records = []
        
        records.extend(new_entries)
        records = records[-max_items:] # Keep it lean for speed
        
        with open(path, "w") as f:
            json.dump(records, f, indent=2)

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "online", "threshold": MOVEMENT_THRESHOLD}), 200

@app.route("/", methods=["POST"])
def secure_ingest():
    data = request.get_json(silent=True)
    if not data or "payload" not in data:
        return jsonify({"status": "error"}), 400

    stream_batch = []
    alert_batch = []

    for sensor in data["payload"]:
        # SAFER CHECK: Case-insensitive and covers 'uncalibrated' variations
        s_name = sensor.get("name", "").lower()
        if "accel" not in s_name:
            continue

        v = sensor.get("values", {})
        x, y, z = v.get("x", 0), v.get("y", 0), v.get("z", 0)
        mag = (x**2 + y**2 + z**2) ** 0.5

        now = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(now))

        entry = {
            "time": time_str,
            "timestamp": str(now),
            "x": round(x, 4), "y": round(y, 4), "z": round(z, 4), "mag": round(mag, 4)
        }
        stream_batch.append(entry)

        if mag > MOVEMENT_THRESHOLD:
            safe_mag = apply_privacy_mask(mag)
            proof = generate_zkp_proof(safe_mag, str(now))
            alert_batch.append({
                **entry,
                "masked_mag": round(safe_mag, 4),
                "proof": proof
            })
            print(f"!!! ANOMALY: {mag:.2f} !!!")

    _extend_json(STREAM_FILE, _stream_lock, stream_batch)
    _extend_json(ALERTS_FILE, _alerts_lock, alert_batch)
    return jsonify({"status": "received", "count": len(stream_batch)}), 200

if __name__ == "__main__":
    # Get IP for the demo display
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except: ip = "127.0.0.1"
    finally: s.close()
    
    print(f"\n--- DEMO READY ---\nURL: http://{ip}:5000/\n------------------")
    app.run(host="0.0.0.0", port=5000, debug=False)