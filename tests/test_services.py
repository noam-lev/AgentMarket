import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from agent_market.main import app as fastapi_app
import uuid
import httpx
import inspect
from agent_market.models.mongo import db


@pytest_asyncio.fixture
async def test_client():
    await db.connect()
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await db.close()

@pytest.fixture
def unique_email():
    return f"test_provider_{uuid.uuid4()}@example.com"

@pytest.fixture
def unique_service_name():
    return f"Test Service {uuid.uuid4()}"

@pytest_asyncio.fixture
async def test_provider(test_client, unique_email):
    # Register a new provider
    register_data = {
        "email": unique_email,
        "password": "testpassword123",
        "name": "Test Provider"
    }
    resp = await test_client.post("/api/providers/register", json=register_data)
    if resp.status_code != 201:
        print("Provider registration failed:", resp.status_code, resp.text)
    assert resp.status_code == 201
    provider = resp.json()
    # Login to get JWT
    login_data = {
        "username": unique_email,
        "password": "testpassword123"
    }
    resp = await test_client.post("/api/providers/token", data=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"provider": provider, "token": token}

@pytest_asyncio.fixture
async def test_service(test_client, test_provider, unique_service_name):
    # Create a service for the test provider
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    service_data = {
        "name": unique_service_name,
        "description": "A test service for API testing.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp = await test_client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201
    service = resp.json()
    yield service
    # Cleanup: delete the service
    resp = await test_client.delete(f"/api/services/{service['id']}", headers=headers)
    # Allow 200 or 204 (depending on implementation)
    assert resp.status_code in (200, 204)

@pytest.mark.asyncio
async def test_create_service(test_client, test_provider, unique_service_name):
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    service_data = {
        "name": unique_service_name,
        "description": "A test service for API testing.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp = await test_client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == service_data["name"]
    assert data["provider_id"] == service_data["provider_id"]
    assert "id" in data
    # Cleanup
    resp = await test_client.delete(f"/api/services/{data['id']}", headers=headers)
    assert resp.status_code in (200, 204)

@pytest.mark.asyncio
async def test_get_service_by_id(test_client, test_provider, unique_service_name):
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    # Create service
    service_data = {
        "name": unique_service_name,
        "description": "A test service for get by id.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp = await test_client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    # Get by id
    resp = await test_client.get(f"/api/services/{created['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]
    assert data["name"] == service_data["name"]
    # Cleanup
    resp = await test_client.delete(f"/api/services/{created['id']}", headers=headers)
    assert resp.status_code in (200, 204)

@pytest.mark.asyncio
async def test_update_service(test_client, test_provider, unique_service_name):
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    # Create service
    service_data = {
        "name": unique_service_name,
        "description": "A test service for update.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp = await test_client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    # Update
    update_data = service_data.copy()
    update_data["description"] = "Updated description."
    resp = await test_client.put(f"/api/services/{created['id']}", json=update_data, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["description"] == "Updated description."
    # Cleanup
    resp = await test_client.delete(f"/api/services/{created['id']}", headers=headers)
    assert resp.status_code in (200, 204)

@pytest.mark.asyncio
async def test_delete_service(test_client, test_provider, unique_service_name):
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    # Create service
    service_data = {
        "name": unique_service_name,
        "description": "A test service for delete.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp = await test_client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    # Delete
    resp = await test_client.delete(f"/api/services/{created['id']}", headers=headers)
    assert resp.status_code in (200, 204)
    # Confirm deletion
    resp = await test_client.get(f"/api/services/{created['id']}")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_semantic_search(test_client, test_provider, unique_service_name):
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    # Create two services
    service_data1 = {
        "name": unique_service_name + " 1",
        "description": "A semantic search test service for AI.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    service_data2 = {
        "name": unique_service_name + " 2",
        "description": "Another semantic search test service for ML.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp1 = await test_client.post("/api/services/", json=service_data1, headers=headers)
    resp2 = await test_client.post("/api/services/", json=service_data2, headers=headers)
    assert resp1.status_code == 201 and resp2.status_code == 201
    # Search
    resp = await test_client.get("/api/services/search", params={"query": "AI"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(service["name"] == service_data1["name"] for service in results)
    # Cleanup
    id1 = resp1.json()["id"]
    id2 = resp2.json()["id"]
    await test_client.delete(f"/api/services/{id1}", headers=headers)
    await test_client.delete(f"/api/services/{id2}", headers=headers)

@pytest.mark.asyncio
async def test_report_service_usage(test_client, test_provider, unique_service_name):
    provider = await test_provider
    headers = {"Authorization": f"Bearer {provider['token']}"}
    # Create service
    service_data = {
        "name": unique_service_name,
        "description": "A test service for usage reporting.",
        "provider_id": provider["provider"]["id"],
        "openapi_spec": "{}"
    }
    resp = await test_client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    # Report usage
    resp = await test_client.post(f"/api/services/{created['id']}/usage")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Usage reported successfully."
    # Cleanup
    resp = await test_client.delete(f"/api/services/{created['id']}", headers=headers)
    assert resp.status_code in (200, 204)

def test_print_asgitransport_signature():
    print('ASGITransport.__init__ signature:', inspect.signature(ASGITransport.__init__))
