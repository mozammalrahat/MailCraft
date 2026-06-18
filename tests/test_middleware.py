from fastapi.testclient import TestClient


def test_request_id_header_returned(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_request_id_header_preserved(client: TestClient) -> None:
    custom_id = "test-request-id-12345"
    response = client.get(
        "/api/health",
        headers={"X-Request-ID": custom_id},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
