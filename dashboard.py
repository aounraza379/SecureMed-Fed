import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

st.set_page_config(page_title="SecureMed-Fed Live", layout="wide")
st.title("SecureMed-Fed: Live Medical Monitoring")

# 1. Load Baseline Data
data = pd.read_csv('data/patient_data.csv')

# 2. Check for LIVE Alerts
live_alert = None
if os.path.exists("live_alerts.json"):
    with open("live_alerts.json", "r") as f:
        live_alert = json.load(f)

# 3. Visualization
fig = go.Figure()

# Background Patient Data
fig.add_trace(go.Scatter(x=data['Timestamp'], y=data['Heart_Rate'], name='Baseline HR', line=dict(color='gray', width=1, dash='dot')))

# If a live shake is detected, overlay it!
if live_alert:
    st.error(f"🚨 LIVE EMERGENCY DETECTED at {live_alert['time']}")
    st.sidebar.success("ZKP PROOF VERIFIED")
    st.sidebar.code(live_alert['proof'][:20] + "...", language="text")
    
    # Add a big red marker for the live alert
    fig.add_trace(go.Scatter(
        x=[data['Timestamp'].iloc[-1]], # Plot at the most recent time
        y=[live_alert['mag'] * 5],      # Scaling mag to look like a HR spike
        mode='markers+text',
        name='LIVE ALERT',
        text=["EMERGENCY"],
        marker=dict(color='red', size=15, symbol='star')
    ))

fig.update_layout(template='plotly_dark', height=600)
st.plotly_chart(fig, use_container_width=True)

# Auto-refresh the page every 3 seconds to check for new shakes
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=3000, key="datarefresh")