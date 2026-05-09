import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import time
from streamlit_autorefresh import st_autorefresh
from core.security import verify_zkp_proof

# --- Page Config & Auto-Refresh ---
st.set_page_config(page_title="SecureMed Monitor", layout="wide", page_icon="🛡️")
st_autorefresh(interval=1000, key="datarefresh")

# --- Path Consistency ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STREAM_FILE = os.path.join(BASE_DIR, "live_stream.json")
ALERTS_FILE = os.path.join(BASE_DIR, "live_alerts.json")

def load_data(path):
    if not os.path.exists(path): return []
    try:
        with open(path, "r") as f: return json.load(f)
    except: return []

# Load data
stream_data = load_data(STREAM_FILE)
alerts = load_data(ALERTS_FILE)

# --- Header ---
st.title("SecureMed-Fed Clinical Dashboard")
st.markdown("---")

# --- Metrics Section ---
c1, c2, c3 = st.columns(3)
c1.metric("Live Pulses", len(stream_data))
c2.metric("Security Alerts", len(alerts))

# Live Connection Check
is_online = False
if stream_data:
    last_ts = float(stream_data[-1].get('timestamp', 0))
    if (time.time() - last_ts) < 5:
        is_online = True

status_text = "🟢 System Online" if is_online else "🔴 Waiting for Sensor..."
c3.subheader(status_text)

# --- Real-Time Graph ---
if stream_data:
    df_stream = pd.DataFrame(stream_data).tail(100)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_stream['time'], y=df_stream['mag'], mode='lines', name="Magnitude", line=dict(color='#58a6ff')))
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Start Sensor Logger to visualize data.")

# --- Row-by-Row Security Audit ---
st.markdown("### Security Audit (ZKP Verified)")

if alerts:
    df_alerts = pd.DataFrame(alerts).tail(10)
    
    # 1. Perform Integrity Check for each row
    integrity_list = []
    status_icons = []
    
    for _, row in df_alerts.iterrows():
        # Verify ZKP: binds masked_mag and timestamp
        is_valid = verify_zkp_proof(
            float(row.get('masked_mag', 0)), 
            str(row.get('timestamp', '')), 
            row.get('proof', '')
        )
        integrity_list.append(is_valid)
        status_icons.append("Verified" if is_valid else "Tampered")

    # Add the status column to the dataframe for display
    df_alerts['Integrity_Status'] = status_icons

    # 2. Styling Logic: Highlight entire row if Tampered
    def style_rows(row_data):
        # Calculate local index relative to the displayed tail
        local_idx = row_data.name - df_alerts.index[0]
        if not integrity_list[local_idx]:
            return ['background-color: #8B0000; color: white'] * len(row_data)
        return [''] * len(row_data)

    # 3. Render the Styled Table
    styled_df = df_alerts.style.apply(style_rows, axis=1)
    st.table(styled_df) # st.table handles the styling well for a static log view

    # 4. Global Alert Banner
    if not all(integrity_list):
        st.error("CRITICAL: DATA TAMPERING DETECTED IN MEDICAL LOGS")
    else:
        st.success("All cryptographic proofs verified successfully.")
else:
    st.write("No anomalies detected yet.")