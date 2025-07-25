import pytest
import json
from fastapi.testclient import TestClient
from core.app import app
from core.config import DATA_DIR, Path
import uuid
from datetime import datetime
import requests
import json
import uuid
from datetime import datetime
from core.config import DATA_DIR, Path, os

API_ENDPOINT = "http://localhost:8080"
SAMPLE_ENTRY_FOLDER = Path(DATA_DIR, "sample_entries.json")
ROUTERS = "/api/v1"
AUTHEN_ROUTER = f"{API_ENDPOINT}{ROUTERS}/authen"
LOG_ROUTER = f"{API_ENDPOINT}{ROUTERS}/logs"
EXPIRE_MIN: int = 10080
TOKEN_FILE = Path(DATA_DIR, f"{EXPIRE_MIN}m_access.json")
ONE_WEEK_TOKEN = os.environ.get("ONE_WEEK_TOKEN")
ONE_WEEK_SESSION = os.environ.get("ONE_WEEK_SESSION")
UUID = str(uuid.uuid4())


@pytest.fixture(scope="module")
def sample_entries():
    with open(SAMPLE_ENTRY_FOLDER, "r") as f:
        return json.load(f)


@pytest.fixture
def token_package():
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)


def test_create_log(sample_entries, token_package):
    entry = sample_entries[0]
    entry.update(
        {
            "id": UUID,
            "session_id": ONE_WEEK_SESSION,
            "timestamp": datetime.fromisoformat(
                entry.get("timestamp", "2025-07-19T08:15:53.870+00:00")
            ).isoformat(),
        }
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/logs/",
            json=entry,
            headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Create Log Successfully!"
        assert response_data["log"]["id"] == entry["id"]


def test_get_logs(token_package):
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/logs/",
            headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert (
            response_data["message"] == "Retrieve logs successfully!"
        )
        assert isinstance(response_data["logs"], list)

def test_export_logs(token_package):
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/logs/export",
            headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
        )

        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=logs.csv"
        )

def test_get_logs_stats(token_package):
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/logs/stats",
            headers={"Authorization": f"Bearer {ONE_WEEK_TOKEN}"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert (
            response_data["message"]
            == "Log statistics retrieved successfully!"
        )

# def test_cleanup_old_logs(token_package):
#     access_token = token_package.get("access_token", "")
#     with TestClient(app) as client:
#         response = client.delete(
#             "/api/v1/logs/cleanup",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 200
#         assert "Cleanup completed successfully!" in response.json()["message"]
