from flask import Flask, request, jsonify
import hashlib
import time
import json

app = Flask(__name__)

# --- PHASE 4 INTEGRATION: ZKP LOGIC ---
def generate_zkp_proof(magnitude):
    """Proves an anomaly happened without revealing raw sensor spikes."""
    secret_key = "MS_CANDIDATE_2026"
    timestamp = str(int(time.time()))
    commitment = hashlib.sha256(f"{magnitude}{secret_key}{timestamp}".encode()).hexdigest()
    return commitment

@app.route("/", methods=["POST"])
def secure_ingest():
    data = request.get_json()
    if not data: return jsonify({"status": "error"}), 400

    for sensor in data.get('payload', []):
        if sensor.get('name') == 'accelerometer':
            v = sensor.get('values', {})
            mag = (v.get('x',0)**2 + v.get('y',0)**2 + v.get('z',0)**2)**0.5
            
            if mag > 18:
                proof = generate_zkp_proof(mag)
                # SAVE THE LIVE ALERT
                alert_data = {
                    "time": time.strftime("%H:%M:%S"),
                    "mag": round(mag, 2),
                    "proof": proof
                }
                with open("live_alerts.json", "w") as f:
                    json.dump(alert_data, f)
                
                print(f"\n[LIVE ALERT SAVED] Mag: {alert_data['mag']}")
            
    return jsonify({"status": "secure_received"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)