# tests/test_main.py
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_chat_endpoint_returns_reply() -> None:
    with patch("backend.main.get_reply", return_value="Hello from AI"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hi"}]},
            )
    assert response.status_code == 200
    assert response.json() == {"reply": "Hello from AI"}


@pytest.mark.asyncio
async def test_chat_endpoint_empty_messages_fails() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/chat", json={"messages": []})
    assert response.status_code == 422
