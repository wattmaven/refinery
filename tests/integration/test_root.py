import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.refinery.main import app


@pytest.mark.integration
@pytest.mark.anyio
async def test_read_main():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
