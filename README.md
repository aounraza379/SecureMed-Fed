# SecureMed-Fed: Privacy-Preserving IoT Healthcare Framework

## Project Overview
SecureMed-Fed is a software-defined IoT ecosystem for real-time monitoring of patient movement/activity data. It uses a **smartphone accelerometer** as the IoT sensor and transmits data securely to a doctor's dashboard over local WiFi.

**Privacy-by-Design**: Raw sensor data never leaves the patient's environment unmasked. Every anomaly alert is cryptographically signed with a Zero-Knowledge Proof (HMAC-SHA256) and masked with Laplace Differential Privacy before storage.

---

## Architecture

```
[Sensor Logger App] ──POST──► [Flask Server :5000] ──writes──► [live_stream.json]
      (Phone)                         │                          [live_alerts.json]
                                      │ ZKP + DP                        │
                                      ▼                                  ▼
                               [core/security.py]          [Streamlit Dashboard]
                               [core/privacy.py]            (Doctor's Monitor)
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set the secret key (optional but recommended)
```powershell
# PowerShell
$env:SECMED_SECRET_KEY = "your-strong-secret-key"

# Optional: override anomaly threshold (default 12.0 m/s²)
$env:SECMED_THRESHOLD = "12.0"

# Optional: override privacy budget (default 0.5)
$env:SECMED_EPSILON = "0.5"
```

### 3. Start the Flask ingestion server
```bash
python app.py
```
The server will print your local IP address:
```
==============================================================
  SecureMed-Fed  —  Secure IoT Ingestion Server
==============================================================
  Local endpoint : http://192.168.x.x:5000/
  Status check   : http://192.168.x.x:5000/status
  Movement threshold : 12.0 m/s²

  👉  Configure Sensor Logger:
      URL    → http://192.168.x.x:5000/
      Method → POST
      Sensor → Accelerometer  (interval: 100 ms)
==============================================================
```

### 4. Configure Sensor Logger on your phone

> **Both your PC and phone must be on the same WiFi network.**

1. Open **Sensor Logger** (Android/iOS)
2. Go to **Settings → HTTP Push**
3. Set **URL** to `http://<YOUR_PC_IP>:5000/`
4. Set **Method** to `POST`
5. Enable **Accelerometer** sensor, interval `100ms`
6. Tap **Start** — data begins streaming immediately

To verify connectivity first: open `http://<YOUR_PC_IP>:5000/status` in the phone's browser. You should see `{"status": "online"}`.

### 5. Run the Doctor's Dashboard
```bash
streamlit run dashboard.py
```

---

## Security Features

| Feature | Implementation |
|---------|---------------|
| **Zero-Knowledge Proof** | HMAC-SHA256 keyed with `SECMED_SECRET_KEY` |
| **Differential Privacy** | Laplace mechanism with configurable ε |
| **Live ZKP Verification** | Dashboard re-derives HMAC for each alert — shows ✅/❌ |
| **Thread-safe storage** | `threading.Lock` prevents JSON corruption |
| **CORS** | `flask-cors` allows cross-origin sensor clients |

---

## File Reference

| File | Purpose |
|------|---------|
| `app.py` | Flask ingestion server (receives phone data) |
| `dashboard.py` | Streamlit real-time monitoring dashboard |
| `core/security.py` | HMAC-SHA256 ZKP generation & verification |
| `core/privacy.py` | Laplace differential privacy masking |
| `live_stream.json` | Every accelerometer reading (rolling buffer) |
| `live_alerts.json` | ZKP-verified anomaly events only |
| `data/patient_data.csv` | Synthetic baseline cardiac data |

---

## Threshold Calibration

Sensor Logger sends accelerometer values in **m/s²** (SI units):

| Motion State | Typical Magnitude |
|--------------|------------------|
| Phone at rest (flat) | ≈ 9.8 m/s² (gravity) |
| Held steady, walking | ≈ 10–11 m/s² |
| Brisk walk / movement | ≈ 11–14 m/s² |
| Shake / fall event | > 15 m/s² |

Default threshold: **12.0 m/s²** — override with `SECMED_THRESHOLD` env var.

---

*Developed by Aoun Raza — IoT Healthcare Security Project*
