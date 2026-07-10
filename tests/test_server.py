from fastapi.testclient import TestClient
from app.main import app  # Adjust this import based on your app factory location

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Procura AI" in response.json().get("message", "")

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    