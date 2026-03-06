# backend/main.py
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from backend.chat import get_reply
from backend.models import ChatRequest, ChatResponse

app = FastAPI(title="ChatDemo")

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=422, detail="messages must not be empty")
    reply = get_reply(request.messages)
    return ChatResponse(reply=reply)


# Mount static files only if frontend is built
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
