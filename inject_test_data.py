import requests, json, math, time, random

BASE = "http://127.0.0.1:5000/"

def send(x, y, z):
    payload = {"payload": [{"name": "accelerometer", "values": {"x": x, "y": y, "z": z}}]}
    r = requests.post(BASE, json=payload, timeout=3)
    mag = round((x**2 + y**2 + z**2) ** 0.5, 2)
    status = r.json()["status"]
    print(f"  mag={mag:6.2f}  -> {status}")

print("Sending 20 normal readings (rest ~9.8 m/s2)...")
for i in range(20):
    noise = random.uniform(-0.3, 0.3)
    send(0.1 + noise, 0.1 + noise, 9.8 + noise)

print()
print("Sending 6 anomaly readings (shake ~17 m/s2)...")
for i in range(6):
    v = 10.0 + random.uniform(-1, 1)
    send(v, v, v)

print()
stream = json.load(open("live_stream.json"))
alerts = json.load(open("live_alerts.json"))
print(f"Stream entries : {len(stream)}")
print(f"Alert entries  : {len(alerts)}")
print("DONE")
