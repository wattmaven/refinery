import pytest
from fastapi.testclient import TestClient

from src.fastapi_template.main import app

client = TestClient(app)


@pytest.mark.integration
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
