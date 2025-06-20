from fastapi.testclient import TestClient
from agent_market.main import app

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
