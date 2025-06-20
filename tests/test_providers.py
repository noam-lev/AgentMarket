import pytest
from fastapi.testclient import TestClient
from agent_market.main import app
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from agent_market.core.config import settings

TEST_PROVIDER = {
    "name": "Test Provider",
    "email": "test_provider@example.com",
    "password": "TestPassword123!"
}

MONGO_URI = settings.MONGO_URI
DB_NAME = MONGO_URI.split('/')[-1].split('?')[0] if MONGO_URI else "agentmarket_db"

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_provider():
    # Cleanup before and after tests using Motor
    async def remove_test_provider():
        mongo = AsyncIOMotorClient(MONGO_URI)
        db = mongo[DB_NAME]
        await db.providers.delete_many({"email": TEST_PROVIDER["email"]})
        mongo.close()
    asyncio.run(remove_test_provider())
    yield
    asyncio.run(remove_test_provider())


def test_register_provider_success(client):
    response = client.post("/api/providers/register", json=TEST_PROVIDER)
    print("register_provider_success:", response.status_code, response.text)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == TEST_PROVIDER["email"]
    assert data["name"] == TEST_PROVIDER["name"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_register_provider_duplicate_email(client):
    client.post("/api/providers/register", json=TEST_PROVIDER)
    response = client.post("/api/providers/register", json=TEST_PROVIDER)
    print("register_provider_duplicate_email:", response.status_code, response.text)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered."


def test_login_success(client):
    response = client.post(
        "/api/providers/token",
        data={"username": TEST_PROVIDER["email"], "password": TEST_PROVIDER["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("login_success:", response.status_code, response.text)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]


def test_login_failure(client):
    response = client.post(
        "/api/providers/token",
        data={"username": TEST_PROVIDER["email"], "password": "WrongPassword!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("login_failure:", response.status_code, response.text)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_with_valid_jwt(client):
    token = test_login_success(client)
    response = client.get(
        "/api/providers/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print("me_with_valid_jwt:", response.status_code, response.text)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_PROVIDER["email"]
    assert data["name"] == TEST_PROVIDER["name"]
    assert "id" in data


def test_me_with_invalid_jwt(client):
    response = client.get(
        "/api/providers/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    print("me_with_invalid_jwt:", response.status_code, response.text)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_me_with_no_jwt(client):
    response = client.get("/api/providers/me")
    print("me_with_no_jwt:", response.status_code, response.text)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
