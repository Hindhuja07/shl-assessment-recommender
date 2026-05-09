from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_vague_query_clarifies():
    response = client.post("/chat", json={"messages": [{"role": "user", "content": "I need an assessment"}]})
    body = response.json()
    assert response.status_code == 200
    assert body["recommendations"] == []
    assert body["end_of_conversation"] is False


def test_recommendation_schema():
    response = client.post("/chat", json={"messages": [{"role": "user", "content": "Hiring a mid-level Java developer with stakeholder communication needs"}]})
    body = response.json()
    assert response.status_code == 200
    assert isinstance(body["reply"], str)
    assert isinstance(body["recommendations"], list)
    assert "end_of_conversation" in body
