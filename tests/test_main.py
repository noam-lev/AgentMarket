from fastapi.testclient import TestClient
import importlib.util
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow import of 'agent market.main'
sys.path.append(str(Path(__file__).parent.parent / "agent market"))

main_path = Path(__file__).parent.parent / "agent market" / "main.py"
spec = importlib.util.spec_from_file_location("main", main_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for {main_path}")
main = importlib.util.module_from_spec(spec)
sys.modules["main"] = main
spec.loader.exec_module(main)
app = main.app

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AgentMarket API"}
