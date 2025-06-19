from fastapi.testclient import TestClient
from agent_market.main import app
import pytest

client = TestClient(app)

TEST_PROVIDER = {
    "name": "Test Provider",
    "email": "test_provider@example.com",
    "password": "TestPassword123!"
}

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_provider():
    # Cleanup before and after tests (requires direct DB access if needed)
    yield
    # Optionally, remove test provider from DB after tests


def test_register_provider_success():
    response = client.post("/api/providers/register", json=TEST_PROVIDER)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == TEST_PROVIDER["email"]
    assert data["name"] == TEST_PROVIDER["name"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_register_provider_duplicate_email():
    # Register once
    client.post("/api/providers/register", json=TEST_PROVIDER)
    # Register again with same email
    response = client.post("/api/providers/register", json=TEST_PROVIDER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered."
