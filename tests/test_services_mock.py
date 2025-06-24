import pytest
from fastapi.testclient import TestClient
from agent_market.main import app
from agent_market.api.deps import get_database
import mongomock
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# --- Async wrappers for mongomock ---
def _to_bson_safe(obj):
    if isinstance(obj, dict):
        return {k: _to_bson_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_to_bson_safe(v) for v in obj]
    elif hasattr(obj, '__str__') and type(obj).__name__ == 'HttpUrl':
        return str(obj)
    else:
        return obj

class AsyncCursor:
    def __init__(self, items):
        self._items = items
        self._index = 0
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item

class AsyncMockCollection:
    def __init__(self, collection):
        self._collection = collection
    async def find_one(self, *args, **kwargs):
        return self._collection.find_one(*args, **kwargs)
    async def insert_one(self, *args, **kwargs):
        # Convert Pydantic/HttpUrl to BSON-safe types
        if args:
            args = (_to_bson_safe(args[0]),) + args[1:]
        if 'document' in kwargs:
            kwargs['document'] = _to_bson_safe(kwargs['document'])
        return self._collection.insert_one(*args, **kwargs)
    async def update_one(self, *args, **kwargs):
        # Recursively convert all update values to BSON-safe types
        if args:
            # If the update is a dict with '$set', ensure its values are BSON-safe
            if len(args) > 1 and isinstance(args[1], dict) and '$set' in args[1]:
                args = (args[0], {'$set': _to_bson_safe(args[1]['$set'])}) + args[2:]
            else:
                args = (_to_bson_safe(args[0]),) + args[1:]
        if 'update' in kwargs:
            kwargs['update'] = _to_bson_safe(kwargs['update'])
        return self._collection.update_one(*args, **kwargs)
    async def delete_one(self, *args, **kwargs):
        return self._collection.delete_one(*args, **kwargs)
    async def find(self, *args, **kwargs):
        logging.debug(f"find called with args: {args}, kwargs: {kwargs}")
        items = list(self._collection.find(*args, **kwargs))
        logging.debug(f"find returning {len(items)} items")
        return AsyncCursor(items)

class AsyncMockDB:
    def __init__(self, db):
        self.providers = AsyncMockCollection(db['providers'])
        self.services = AsyncMockCollection(db['services'])

# Dependency override for a mock MongoDB
@pytest.fixture(autouse=True)
def override_get_database():
    client = mongomock.MongoClient()
    db = client['test_db']
    async_db = AsyncMockDB(db)
    async def _get_db():
        return async_db
    app.dependency_overrides[get_database] = _get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def unique_email():
    return f"test_provider_{uuid.uuid4()}@example.com"

@pytest.fixture
def unique_service_name():
    return f"Test Service {uuid.uuid4()}"

def register_and_login_provider(client, email):
    # Register provider
    register_data = {
        "email": email,
        "password": "testpassword123",
        "name": "Test Provider"
    }
    resp = client.post("/api/providers/register", json=register_data)
    assert resp.status_code == 201, resp.text
    provider = resp.json()
    # Login to get JWT
    login_data = {
        "username": email,
        "password": "testpassword123"
    }
    resp = client.post("/api/providers/token", data=login_data)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"provider": provider, "token": token}

def create_service(client, token, provider_id, name, description, openapi_spec="{}"):
    headers = {"Authorization": f"Bearer {token}"}
    # Ensure description is at least 50 characters
    if len(description) < 50:
        description = description + " " + ("lorem ipsum " * ((50 - len(description)) // 12 + 1))
        description = description[:51]
    service_data = {
        "name": name,
        "description": description,
        "provider_id": provider_id,
        "openapi_spec": openapi_spec,
        "categories": ["Test"],
        "api": {
            "base_url": "http://example.com",
            "auth_type": "none",
            "endpoint": "http://example.com/test",
            "method": "GET"
        }
    }
    resp = client.post("/api/services/", json=service_data, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()

def delete_service(client, token, service_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.delete(f"/api/services/{service_id}", headers=headers)
    assert resp.status_code in (200, 204), resp.text

def test_create_service(client, unique_email, unique_service_name):
    user = register_and_login_provider(client, unique_email)
    provider = user["provider"]
    token = user["token"]
    service = create_service(client, token, provider["id"], unique_service_name, "A test service for API testing. This description is long enough.")
    assert service["name"] == unique_service_name
    assert service["provider_id"] == provider["id"]
    assert "id" in service
    delete_service(client, token, service["id"])

def test_get_service_by_id(client, unique_email, unique_service_name):
    user = register_and_login_provider(client, unique_email)
    provider = user["provider"]
    token = user["token"]
    service = create_service(client, token, provider["id"], unique_service_name, "A test service for get by id. This description is long enough.")
    resp = client.get(f"/api/services/{service['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == service["id"]
    assert data["name"] == unique_service_name
    delete_service(client, token, service["id"])

def test_update_service(client, unique_email, unique_service_name):
    user = register_and_login_provider(client, unique_email)
    provider = user["provider"]
    token = user["token"]
    service = create_service(client, token, provider["id"], unique_service_name, "A test service for update. This description is long enough.")
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "name": unique_service_name,
        "description": "Updated description for service. This is long enough to pass validation.",
        "provider_id": provider["id"],
        "openapi_spec": "{}",
        "categories": ["Test"],
        "api": {
            "base_url": "http://example.com",
            "auth_type": "none",
            "endpoint": "http://example.com/test",
            "method": "GET"
        }
    }
    resp = client.put(f"/api/services/{service['id']}", json=update_data, headers=headers)
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["description"] == update_data["description"]
    delete_service(client, token, service["id"])

def test_delete_service(client, unique_email, unique_service_name):
    user = register_and_login_provider(client, unique_email)
    provider = user["provider"]
    token = user["token"]
    service = create_service(client, token, provider["id"], unique_service_name, "A test service for delete. This description is long enough.")
    delete_service(client, token, service["id"])
    resp = client.get(f"/api/services/{service['id']}")
    assert resp.status_code == 404

def test_semantic_search(client, unique_email, unique_service_name):
    user = register_and_login_provider(client, unique_email)
    provider = user["provider"]
    token = user["token"]
    name1 = unique_service_name + " 1"
    name2 = unique_service_name + " 2"
    service1 = create_service(client, token, provider["id"], name1, "A semantic search test service for AI. This description is long enough.")
    service2 = create_service(client, token, provider["id"], name2, "Another semantic search test service for ML. This description is long enough.")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/services/search", params={"query": "AIs"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(service["name"] == name1 for service in results)
    delete_service(client, token, service1["id"])
    delete_service(client, token, service2["id"])

def test_report_service_usage(client, unique_email, unique_service_name):
    user = register_and_login_provider(client, unique_email)
    provider = user["provider"]
    token = user["token"]
    service = create_service(client, token, provider["id"], unique_service_name, "A test service for usage reporting. This description is long enough.")
    resp = client.post(f"/api/services/{service['id']}/usage")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Usage reported successfully."
    delete_service(client, token, service["id"]) 