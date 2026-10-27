from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "brickwise"}


def test_graphql_playground_disponible():
    client = TestClient(app)
    response = client.get("/graphql", headers={"accept": "text/html"})
    assert response.status_code == 200
