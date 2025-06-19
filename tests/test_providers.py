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


def test_login_success():
    response = client.post(
        "/api/providers/token",
        data={"username": TEST_PROVIDER["email"], "password": TEST_PROVIDER["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]


def test_login_failure():
    response = client.post(
        "/api/providers/token",
        data={"username": TEST_PROVIDER["email"], "password": "WrongPassword!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_with_valid_jwt():
    # Get a valid token first
    token = test_login_success()
    response = client.get(
        "/api/providers/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_PROVIDER["email"]
    assert data["name"] == TEST_PROVIDER["name"]
    assert "id" in data


def test_me_with_invalid_jwt():
    response = client.get(
        "/api/providers/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_me_with_no_jwt():
    response = client.get("/api/providers/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
