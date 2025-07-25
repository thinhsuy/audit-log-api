import streamlit as st
import requests
import random
import uuid
import pandas as pd
import json
import threading
import time
from websockets.sync.client import connect
from datetime import datetime
from core.config import ONE_WEEK_SESSION, VIETNAM_TZ

# Configuration
API_URL = "http://localhost:8080/api/v1/logs"
BULK_API_URL = f"{API_URL}/bulk"
STATS_API_URL = f"{API_URL}/stats"
WS_URL = "ws://localhost:8080/api/v1/logs/stream"

st.set_page_config(page_title="Audit Logs Dashboard", layout="wide")
st.title("🔍 Audit Logs Dashboard")

# Sidebar
st.sidebar.title("Settings")
token = st.sidebar.text_input("Bearer Token", type="password")
use_ws = st.sidebar.checkbox("Use WebSocket to fetch logs", value=False)
skip = st.sidebar.number_input("Skip", min_value=0, value=0, step=1)
limit = st.sidebar.slider("Limit", min_value=1, max_value=1000, value=10)
bulk_count = st.sidebar.number_input("Bulk Count", min_value=1, max_value=100, value=5, step=1)

# Shared session state
if "logs" not in st.session_state:
    st.session_state.logs = []

ws_thread_started = False

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

def start_ws_client(token: str):
    def run():
        headers = {"Authorization": f"Bearer {token}"}
        try:
            ws = connect(WS_URL, additional_headers=headers)
            while True:
                message = ws.recv()
                data = json.loads(message)
                if data.get("type") == "log.view":
                    st.session_state.logs.insert(0, data.get("log", {}))
                    if len(st.session_state.logs) > limit:
                        st.session_state.logs = st.session_state.logs[:limit]
        except Exception as e:
            st.error(f"WebSocket error: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def fetch_stats(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(STATS_API_URL, headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json().get('response', {}).get("stats", {})
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}

# Generate logs
if token:
    headers = {"Authorization": f"Bearer {token}"}

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Random Log"):
            try:
                resp = requests.post(API_URL, headers=headers, json={**generate_random_log()}, timeout=5)
                resp.raise_for_status()
                st.success("Random log created successfully!")
            except Exception as e:
                st.error(f"Failed to create random log: {e}")
    with col2:
        if st.button("Generate Bulk Logs"):
            bulk_payload = [generate_random_log() for _ in range(bulk_count)]
            try:
                resp = requests.post(BULK_API_URL, headers=headers, json=bulk_payload, timeout=5)
                resp.raise_for_status()
                st.success(f"Bulk logs ({bulk_count}) created successfully!")
            except Exception as e:
                st.error(f"Failed to create bulk logs: {e}")

    # Start WS thread
    if use_ws and not ws_thread_started:
        start_ws_client(token)
        ws_thread_started = True
    elif not use_ws:
        st.session_state.logs = fetch_logs(token, skip, limit)

    stats = fetch_stats(token)

    if stats:
        st.subheader("Log Statistics")
        df_stats = pd.DataFrame(list(stats.items()), columns=["Category", "Count"])
        st.bar_chart(df_stats.set_index("Category"))

    if st.session_state.logs:
        fields_order = [
            "action_type", "resource_type", "severity",
            "ip_address", "user_agent", "meta_data",
            "before_state", "after_state", "timestamp",
            "id", "session_id", "resource_id"
        ]
        cleaned = []
        for log in st.session_state.logs:
            entry = {k: v for k, v in log.items()}
            ordered_entry = {field: entry.get(field) for field in fields_order}
            cleaned.append(ordered_entry)
        st.subheader("Recent Logs")
        st.dataframe(cleaned)
    else:
        st.info("No logs available or invalid token.")
else:
    st.warning("Please enter your access token in the sidebar to fetch or generate logs.")

def generate_random_log():
    return {
        "action_type": random.choice(["CREATE", "UPDATE", "DELETE", "VIEW"]),
        "resource_type": random.choice(["user", "order", "product", "report"]),
        "resource_id": str(uuid.uuid4()),
        "session_id": ONE_WEEK_SESSION,
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
        "timestamp": datetime.now(VIETNAM_TZ).isoformat(),
    }