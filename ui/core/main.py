import streamlit as st
import requests
import random
import uuid
import pandas as pd
import json
from websockets.sync.client import connect
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Configuration
API_URL = "http://localhost:8080/api/v1/logs"
BULK_API_URL = f"{API_URL}/bulk"
STATS_API_URL = f"{API_URL}/stats"
WS_URL = "ws://localhost:8080/api/v1/logs/stream"

# Automatically rerun the script every 20 seconds
st_autorefresh(interval=20000, limit=None, key="logs_refresh")

st.set_page_config(page_title="Audit Logs Dashboard", layout="wide")
st.title("🔍 Audit Logs Dashboard")

# Sidebar for parameters
token = st.sidebar.text_input("Bearer Token", type="password")
use_ws = st.sidebar.checkbox("Use WebSocket to fetch logs", value=False)
skip = st.sidebar.number_input("Skip", min_value=0, value=0, step=1)
limit = st.sidebar.slider("Limit", min_value=1, max_value=1000, value=10)
bulk_count = st.sidebar.number_input("Bulk Count", min_value=1, max_value=100, value=5, step=1)

# Function to fetch logs via REST API
def fetch_logs(token: str, skip: int, limit: int):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"skip": skip, "limit": limit}
    try:
        resp = requests.get(API_URL, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json().get("logs", [])
    except Exception as e:
        st.error(f"Error fetching logs: {e}")
        return []

# Function to fetch logs via WebSocket (using websockets.sync)
def fetch_logs_ws(token: str, max_msgs: int):
    """
    Connects to the WebSocket endpoint using the Authorization header for handshake.
    """
    logs = []
    try:
        # Pass Authorization header via extra_headers only
        ws = connect(WS_URL, additional_headers=headers)
    except Exception as e:
        st.error(f"WebSocket connect error: {e}")
        return []
    try:
        for _ in range(max_msgs):
            msg = ws.recv()
            data = json.loads(msg)
            if data.get("type") == "log.view":
                logs.append(data.get("log", {}))
    except Exception as e:
        st.error(f"WebSocket receive error: {e}")
    finally:
        try:
            ws.close()
        except:
            pass
    return logs

# Function to fetch stats
def fetch_stats(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(STATS_API_URL, headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json().get('response', {}).get("stats", {})
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}

# Only proceed if token is provided
if not token:
    st.warning("Please enter your access token in the sidebar to fetch or generate logs.")
else:
    headers = {"Authorization": f"Bearer {token}"}

    # Log generation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Random Log"):
            payload = {
                "action_type": random.choice(["CREATE", "UPDATE", "DELETE", "VIEW"]),
                "resource_type": random.choice(["user", "order", "product", "report"]),
                "resource_id": str(uuid.uuid4()),
                "severity": random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"]),
                "ip_address": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                "user_agent": random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "Mozilla/5.0 (X11; Linux x86_64)",
                ]),
                "before_state": {},
                "after_state": {},
                "meta_data": {"generated": True},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=5)
                resp.raise_for_status()
                st.success("Random log created successfully!")
            except Exception as e:
                st.error(f"Failed to create random log: {e}")
    with col2:
        if st.button("Generate Bulk Logs"):
            bulk_payload = []
            for _ in range(bulk_count):
                bulk_payload.append({
                    "action_type": random.choice(["CREATE", "UPDATE", "DELETE", "VIEW"]),
                    "resource_type": random.choice(["user", "order", "product", "report"]),
                    "resource_id": str(uuid.uuid4()),
                    "severity": random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"]),
                    "ip_address": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                    "user_agent": random.choice([
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                        "Mozilla/5.0 (X11; Linux x86_64)",
                    ]),
                    "before_state": {},
                    "after_state": {},
                    "meta_data": {"bulk_generated": True},
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            try:
                resp = requests.post(BULK_API_URL, headers=headers, json=bulk_payload, timeout=5)
                resp.raise_for_status()
                st.success(f"Bulk logs ({bulk_count}) created successfully!")
            except Exception as e:
                st.error(f"Failed to create bulk logs: {e}")

    # Fetch logs and stats
    if use_ws:
        logs = fetch_logs_ws(token, limit)
    else:
        logs = fetch_logs(token, skip, limit)
    stats = fetch_stats(token)

    # Display stats as bar chart
    if stats:
        st.subheader("Log Statistics")
        df_stats = pd.DataFrame(list(stats.items()), columns=["Category", "Count"])
        st.bar_chart(df_stats.set_index("Category"))

    # Display logs table
    if logs:
        fields_order = [
            "timestamp", "session_id", "action_type", "resource_type", "resource_id",
            "severity", "ip_address", "user_agent", "before_state", "after_state", "meta_data"
        ]
        cleaned = []
        for log in logs:
            entry = {k: v for k, v in log.items() if k not in ("id", "tenant_id", "user_id")}
            ordered_entry = {field: entry.get(field) for field in fields_order}
            cleaned.append(ordered_entry)
        st.subheader("Recent Logs")
        st.dataframe(cleaned)
    else:
        st.info("No logs available or invalid token.")
