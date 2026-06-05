from fastapi.testclient import TestClient

from app import main as app_main


def test_api_root_points_users_to_frontend_and_api_docs():
    response = TestClient(app_main.app).get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["frontend"] == "http://localhost:3001"
    assert body["models"] == "/models"


def test_favicon_request_is_no_content():
    response = TestClient(app_main.app).get("/favicon.ico")

    assert response.status_code == 204
    assert response.content == b""
