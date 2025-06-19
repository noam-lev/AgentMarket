from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow import of 'agent market.main'
sys.path.append(str(Path(__file__).parent.parent / "agent market"))
from main import app

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AgentMarket API"}
