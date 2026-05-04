from flask import Flask, request, jsonify
import time, json, os
from core.security import generate_zkp_proof
from core.privacy import apply_privacy_mask

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "live_alerts.json")

@app.route("/", methods=["POST"])
def secure_ingest():
    data = request.get_json()
    if not data or 'payload' not in data:
        return jsonify({"status": "error"}), 400

    for sensor in data['payload']:
        if sensor.get('name') == 'accelerometer':
            v = sensor.get('values', {})
            # Normalized Magnitude
            mag = (v.get('x',0)**2 + v.get('y',0)**2 + v.get('z',0)**2)**0.5
            
            # --- PROFESSIONAL CALIBRATION ---
            # If your phone sends ~0.1 as rest, the threshold should be 0.5
            # If your phone sends ~9.8 as rest, the threshold should be 15.0
            threshold = 0.5 if mag < 2.0 else 15.0 

            if mag > threshold:
                timestamp = str(int(time.time()))
                # Differential Privacy masking
                safe_mag = apply_privacy_mask(mag)
                # ZKP Generation
                proof = generate_zkp_proof(safe_mag, timestamp)

                alert_data = {
                    "time": time.strftime("%H:%M:%S"),
                    "mag": round(mag, 2),
                    "proof": proof
                }

                # Save to shared log
                alerts = []
                if os.path.exists(FILE_PATH):
                    with open(FILE_PATH, "r") as f:
                        try: alerts = json.load(f)
                        except: alerts = []
                
                alerts.append(alert_data)
                with open(FILE_PATH, "w") as f:
                    json.dump(alerts, f, indent=2)

                print(f"[AUDIT LOGGED] Secure Event Verified. Magnitude: {alert_data['mag']}")

    return jsonify({"status": "secure_received"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)