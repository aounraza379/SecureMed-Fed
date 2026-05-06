"""
dashboard.py — SecureMed-Fed Clinical Monitor
Real-time Streamlit dashboard for the doctor.

Data sources:
  live_stream.json  — every accelerometer reading (drives the live graph)
  live_alerts.json  — ZKP-verified anomaly events (overlaid as markers)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import time
from streamlit_autorefresh import st_autorefresh
from core.security import verify_zkp_proof

# ─── Auto-refresh must be called FIRST (before any rendering) ─────────────────
st_autorefresh(interval=1000, key="audit_refresh")

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecureMed-Fed | Clinical Monitor",
    page_icon="🛡️",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background-color: #0d1117; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* Alert badges */
    .badge-verified {
        background: linear-gradient(90deg, #1a7f3c, #2ea44f);
        color: white; padding: 3px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 600;
    }
    .badge-invalid {
        background: linear-gradient(90deg, #a32c2c, #cf3535);
        color: white; padding: 3px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 600;
    }

    /* Section dividers */
    hr { border-color: #21262d; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("## SecureMed-Fed — Clinical Audit Dashboard")
st.caption("Real-time accelerometer monitoring with ZKP-verified anomaly detection")

# ─── File paths ───────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ALERTS_FILE  = os.path.join(BASE_DIR, "live_alerts.json")
STREAM_FILE  = os.path.join(BASE_DIR, "live_stream.json")
THRESHOLD    = float(os.environ.get("SECMED_THRESHOLD", "3.0"))
EPSILON      = float(os.environ.get("SECMED_EPSILON",    "0.5"))


# ─── Load data ────────────────────────────────────────────────────────────────
def load_json(path, retries=3):
    """Read a JSON list file safely. Retries on transient errors (e.g. mid-write)."""
    for _ in range(retries):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                content = f.read()
            if content.strip():
                return json.loads(content)
            return []
        except (json.JSONDecodeError, OSError):
            time.sleep(0.05)
    return []

stream_data = load_json(STREAM_FILE)
alerts      = load_json(ALERTS_FILE)

# --- Connection Status Check ---
is_live = False
if stream_data:
    last_ts_str = stream_data[-1].get("timestamp", "0")
    try:
        last_ts = float(last_ts_str)
        if (time.time() - last_ts) < 2.5:
            is_live = True
    except ValueError:
        pass


# ─── Sidebar — Security Status ────────────────────────────────────────────────
with st.sidebar:
    st.header("Cybersecurity Status")

    st.metric("Stream Readings",    len(stream_data), help="Total accelerometer samples received")
    st.metric("Anomaly Alerts",     len(alerts),      help="ZKP-verified movement anomalies")
    st.metric("Privacy Budget (ε)", EPSILON,           help="Lower = stronger privacy (Laplace DP)")
    st.metric("Threshold (m/s²)",  THRESHOLD,         help="Magnitude above this triggers an alert")

    st.divider()
    if is_live:
        st.success("SENSOR CONNECTED")
    else:
        st.error("DISCONNECTED")
        # Clear data from display if stale
        stream_data = []

    st.divider()

    # Attack simulation
    if st.button("Simulate Unauthorized Attack", key="sim_attack"):
        st.warning("INJECTION DETECTED: Unauthorized data push attempt…")
        time.sleep(0.8)
        st.error("ZKP VERIFICATION FAILED: HMAC commitment mismatch")

    st.divider()
    st.caption("Flask server: `python app.py`")
    st.caption("Configure Sensor Logger → POST to `:5000/`")


# ─── Main Monitor: Real-Time Graph ────────────────────────────────────────────
st.subheader("Live Accelerometer Stream")

fig = go.Figure()

if stream_data:
    df_stream = pd.DataFrame(stream_data)

    # Keep last 150 points for a much faster, more reactive window
    df_stream = df_stream.tail(150)

    # Primary trace — live magnitude
    fig.add_trace(go.Scatter(
        x=df_stream["time"],
        y=df_stream["mag"],
        name="Accel Magnitude (m/s²)",
        mode="lines",
        line=dict(color="#58a6ff", width=2),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.07)",
    ))

    # X/Y/Z component traces (subtle, toggleable)
    for axis, color in [("x", "#3fb950"), ("y", "#d29922"), ("z", "#f78166")]:
        if axis in df_stream.columns:
            fig.add_trace(go.Scatter(
                x=df_stream["time"],
                y=df_stream[axis],
                name=f"{axis.upper()}-axis",
                mode="lines",
                line=dict(color=color, width=1, dash="dot"),
                visible="legendonly",   # hidden by default, clickable in legend
            ))

else:
    # Placeholder trace while waiting for data
    fig.add_annotation(
        text="Waiting for sensor data…<br><span style='font-size:13px'>Start the Flask server and connect Sensor Logger</span>",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=18, color="#8b949e"),
        align="center",
    )

# Threshold line
fig.add_hline(
    y=THRESHOLD,
    line=dict(color="#f85149", width=1.5, dash="dash"),
    annotation_text=f"  Anomaly threshold ({THRESHOLD} m/s²)",
    annotation_font_color="#f85149",
)

# Overlay anomaly markers from live_alerts.json
if alerts and stream_data:
    alert_times = [a["time"] for a in alerts[-50:]]   # last 50
    alert_mags  = [a["mag"]  for a in alerts[-50:]]
    fig.add_trace(go.Scatter(
        x=alert_times,
        y=alert_mags,
        name="Verified Anomaly",
        mode="markers",
        marker=dict(color="#f85149", size=10, symbol="star-diamond",
                    line=dict(color="#ff7b72", width=1)),
    ))

fig.update_layout(
    template="plotly_dark",
    height=440,
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_title="Time",
    yaxis_title="Magnitude (m/s²)",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    xaxis=dict(showgrid=True, gridcolor="#21262d"),
    yaxis=dict(showgrid=True, gridcolor="#21262d"),
)

st.plotly_chart(fig, use_container_width=True)


# ─── Audit Table with ZKP Verification ───────────────────────────────────────
st.divider()
st.subheader("Medical Security Audit Log")

if alerts:
    # Show last 10 alerts
    recent = alerts[-10:][::-1]   # newest first

    rows = []
    for a in recent:
        # Re-verify the HMAC proof live on the dashboard
        try:
            is_valid = verify_zkp_proof(
                magnitude  = float(a.get("masked_mag", a.get("mag", 0))),
                timestamp  = str(a.get("timestamp", "")),
                proof      = a.get("proof", ""),
            )
        except Exception:
            is_valid = False

        badge = (
            '<span class="badge-verified">VERIFIED</span>'
            if is_valid else
            '<span class="badge-invalid">INVALID</span>'
        )

        rows.append({
            "Time":              a.get("time", "—"),
            "Raw Mag (m/s²)":   a.get("mag", "—"),
            "Masked Mag (DP)":  a.get("masked_mag", "—"),
            "ZKP Proof (first 20 chars)": str(a.get("proof", ""))[:20] + "…",
            "Integrity":        badge,
        })

    df_table = pd.DataFrame(rows)

    # Render table with HTML badges
    st.markdown(
        df_table.to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

else:
    st.info("System Normal — Waiting for encrypted edge data from Sensor Logger…")


# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
col1, col2, col3 = st.columns(3)
col1.caption("ZKP: HMAC-SHA256")
col2.caption("Privacy: Laplace DP")
col3.caption("Transport: Local WiFi (Flask)")