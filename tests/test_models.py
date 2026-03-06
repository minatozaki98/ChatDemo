# tests/test_models.py
from backend.models import ChatRequest, ChatResponse, Message


def test_message_model() -> None:
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_chat_request_model() -> None:
    req = ChatRequest(messages=[Message(role="user", content="Hi")])
    assert len(req.messages) == 1
    assert req.messages[0].role == "user"


def test_chat_response_model() -> None:
    resp = ChatResponse(reply="Hello there")
    assert resp.reply == "Hello there"
