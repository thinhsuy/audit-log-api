def fetch_stats(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(STATS_API_URL, headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json().get('response', {}).get("stats", {})
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}