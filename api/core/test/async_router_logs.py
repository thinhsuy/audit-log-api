import json
import uuid
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from core.app import app
from core.config import DATA_DIR, Path, os
from asgi_lifespan import LifespanManager
import pytest

UUID = str(uuid.uuid4())
ONE_WEEK_TOKEN = os.environ.get("ONE_WEEK_TOKEN")
ONE_WEEK_SESSION = os.environ.get("ONE_WEEK_SESSION")


@pytest.fixture(scope="module")
def sample_entries():
    with open(Path(DATA_DIR, "sample_entries.json"), "r") as f:
        return json.load(f)


@pytest.fixture
def token_package():
    with open(Path(DATA_DIR, "1140m_access.json"), "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_create_and_get_logs(sample_entries, token_package):
    entry = sample_entries[0].copy()
    entry.update(
        {
            "id": UUID,
            "session_id": ONE_WEEK_SESSION,
            "timestamp": datetime.fromisoformat(
                entry["timestamp"]
            ).isoformat(),
        }
    )
    transport = ASGITransport(app=app)

    async with LifespanManager(app):
        async with AsyncClient(
            transport=transport, base_url="http://localhost:8080"
        ) as client:
            resp1 = await client.post(
                "/api/v1/logs/",
                json=entry,
                headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
            )
            assert resp1.status_code == 200
            data1 = resp1.json()
            assert data1["message"] == "Create Log Successfully!"
            assert data1["log"]["id"] == UUID

            resp2 = await client.get(
                "/api/v1/logs/",
                headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
            )
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert data2["message"] == "Retrieve logs successfully!"
            assert any(log["id"] == UUID for log in data2["logs"])

            resp3 = await client.get(
                f"/api/v1/logs/{UUID}",
                headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
            )
            assert resp3.status_code == 200
            data3 = resp3.json()
            assert data3["message"] == "Retrieve log successfully!"
            assert data3["log"]["id"] == UUID
