import asyncio
import websockets
import json
import time
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import random
import uuid
from zoneinfo import ZoneInfo

# SERVER_ENDPOINT = "https://travist-audit-log-api.orangecoast-1a9ad26f.southeastasia.azurecontainerapps.io/api/v1"
SERVER_ENDPOINT = "http://localhost:8080/api/v1"

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
WS_SERVER_URL = SERVER_ENDPOINT.replace("https", "wss").replace("http", "ws") + "/logs/stream"
print(WS_SERVER_URL)
BULK_API_URL = f"{SERVER_ENDPOINT}/logs/bulk"
CLEANUP_API_URL = f"{SERVER_ENDPOINT}/logs/cleanup"
CHATBOT_API_URL = f"{SERVER_ENDPOINT}/chat"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "logs" not in st.session_state:
    st.session_state.logs = []

st.set_page_config(page_title="Audit Logs Dashboard", layout="wide")
st.title("🔍 Audit Logs Dashboard")
st.sidebar.title("Settings")
token = st.sidebar.text_input("Bearer Token", type="password")
# skip = st.sidebar.number_input("Skip", min_value=0, value=0, step=1)
# limit = st.sidebar.slider("Limit", min_value=1, max_value=1000, value=10)
bulk_count = st.sidebar.number_input("Bulk Count", min_value=1, max_value=100, value=5, step=1)

stats_placeholder = st.empty()
log_placeholder = st.empty()

def generate_random_log():
    return {
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
        "timestamp": datetime.now(VIETNAM_TZ).isoformat(),
    }

async def run_server(access_token: str):
    async with websockets.connect(
        WS_SERVER_URL,
        additional_headers={"Authorization": f"Bearer {access_token}"}
    ) as websocket:
        await run_audio_loop(websocket)
        await wait_for_response(websocket)

async def run_audio_loop(websocket):
    session_update_msg = {
        'type': 'session.update'
    }
    await websocket.send(json.dumps(session_update_msg))

def draw_stats_chart(stats: dict):
    stats.pop("total_logs", None)
    df_stats = pd.DataFrame(list(stats.items()), columns=["Category", "Count"])
    stats_placeholder.subheader("Log Statistics")
    stats_placeholder.bar_chart(df_stats.set_index("Category"))

def draw_logs_table(logs: list):
    fields_order = [
        "action_type", "resource_type", "severity",
        "ip_address", "user_agent", "meta_data",
        "before_state", "after_state", "timestamp",
        "id", "session_id", "resource_id"
    ]
    cleaned = []
    for log in logs:
        entry = {k: v for k, v in log.items()}
        ordered_entry = {field: entry.get(field) for field in fields_order}
        cleaned.append(ordered_entry)
    log_placeholder.dataframe(cleaned)

async def wait_for_response(websocket):
    try:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            message_type = data.get("type", None)
            if message_type == "logs.view":
                new_logs = data.get("logs", [])

                for log in new_logs:
                    if log not in st.session_state.logs:
                        st.session_state.logs.append(log)
                draw_logs_table(st.session_state.logs)
            
            if message_type == "logs.stats":
                draw_stats_chart(data.get("stats", {}))

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket closed.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Disconnected. Code: {e.code}, Reason: {e.reason}")


def generate_bot_response(prompt):
    try:
        payload = {"query": prompt}
        resp = requests.post(CHATBOT_API_URL, headers=headers, json=payload, timeout=30)
        response = json.loads(resp.text)
        content_response = response.get("response", {}).get("content", "There is no content in response")
        return content_response
    except Exception as e:
        st.error(f"Failed to get chatbot response: {e}")
        return "Failed to get chatbot response"

if __name__ == "__main__":
    if token:
        col1, col2, col3 = st.columns(3)
        headers = {"Authorization": f"Bearer {token}"}
        with col1:
            if st.button("Generate Random Log"):
                try:
                    resp = requests.post(SERVER_ENDPOINT, headers=headers, json={**generate_random_log()}, timeout=5)
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
        with col3:
            if st.button("Clean up 24h logs"):
                try:
                    resp = requests.get(CLEANUP_API_URL, headers=headers, timeout=5)
                    response = json.loads(resp.text)
                    delete_count = response.get("deleted_count", 0)
                    st.success(f"Clean up total {delete_count} logs")
                except Exception as e:
                    st.error(f"Failed to cleanup logs: {e}")
            
        # st.markdown("---")
        # st.subheader("💬 Audit Log Assistant")
        

        # user_input = st.chat_input("Ask something about the logs...")
        # if user_input:
        #     # Display user's message
        #     st.chat_message("user").write(user_input)
        #     st.session_state.chat_history.append({"role": "user", "message": user_input})

        #     # Display placeholder assistant message
        #     with st.chat_message("assistant"):
        #         wait_placeholder = st.empty()
        #         wait_placeholder.markdown("⏳ Wait for me a little bit ...")

        #         # Fetch real response
        #         bot_reply = generate_bot_response(user_input)

        #         # Replace waiting message
        #         wait_placeholder.markdown(bot_reply)

        #     # Save to history (but no need to re-render now)
        #     st.session_state.chat_history.append({"role": "assistant", "message": bot_reply})

        # if not user_input:
        #     for chat in st.session_state.chat_history:
        #         st.chat_message(chat["role"]).write(chat["message"])

        asyncio.run(run_server(token))