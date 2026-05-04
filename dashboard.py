import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import time
from streamlit_autorefresh import st_autorefresh

# --- UI CONFIGURATION ---
st.set_page_config(page_title="SecureMed-Fed | Clinical Monitor", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ SecureMed-Fed: Clinical Audit Dashboard")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "live_alerts.json")

# 1. Load Data
data = pd.read_csv('data/patient_data.csv')
alerts = []
if os.path.exists(FILE_PATH):
    with open(FILE_PATH, "r") as f:
        try: alerts = json.load(f)
        except: alerts = []

# 2. Sidebar: Professional Security Stats
st.sidebar.header("🔐 Cybersecurity Status")
st.sidebar.metric("Privacy Budget (ε)", "0.5", help="Lower means higher privacy via Gaussian Noise.")
st.sidebar.metric("Total Verified Alerts", len(alerts))

if st.sidebar.button("🚨 Simulate Unauthorized Attack"):
    st.sidebar.warning("INJECTION DETECTED: Attempting unauthorized data push...")
    time.sleep(1)
    st.sidebar.error("ZKP VERIFICATION FAILED: Invalid Commitment")

# 3. Main Monitor (The Graph)
fig = go.Figure()
fig.add_trace(go.Scatter(x=data['Timestamp'], y=data['Heart_Rate'], name='Baseline HR', line=dict(color='#484f58', width=1, dash='dot')))

if alerts:
    latest = alerts[-1]
    # Red Line for Emergency Event
    fig.add_trace(go.Scatter(
        x=[data['Timestamp'].iloc[-1]], y=[160],
        mode='markers+text', name='CRITICAL EVENT',
        text=["VERIFIED ANOMALY"],
        marker=dict(color='#ff4b4b', size=20, symbol='star-diamond')
    ))

fig.update_layout(template='plotly_dark', height=500, margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig, use_container_width=True)

# 4. Professional Audit Table
st.subheader("📋 Medical Security Audit Log")
if alerts:
    df_alerts = pd.DataFrame(alerts)[['time', 'mag', 'proof']]
    df_alerts.columns = ['Timestamp', 'G-Force Mag', 'ZKP Hash (Audit ID)']
    st.table(df_alerts.tail(5)) # Show last 5 for a clean look
else:
    st.info("System Normal: Waiting for encrypted edge data...")

st_autorefresh(interval=3000, key="audit_refresh")