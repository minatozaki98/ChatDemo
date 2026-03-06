# tests/test_chat.py
from unittest.mock import MagicMock, patch

import pytest

from backend.chat import get_reply
from backend.models import Message


@pytest.fixture
def messages() -> list[Message]:
    return [Message(role="user", content="Say hello")]


def test_get_reply_returns_string(messages: list[Message]) -> None:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello!"

    with patch("backend.chat.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        result = get_reply(messages)

    assert result == "Hello!"


def test_get_reply_passes_messages(messages: list[Message]) -> None:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hi"

    with patch("backend.chat.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        get_reply(messages)
        call_kwargs = mock_client.chat.completions.create.call_args[1]

    assert call_kwargs["messages"][0]["role"] == "user"
    assert call_kwargs["messages"][0]["content"] == "Say hello"
