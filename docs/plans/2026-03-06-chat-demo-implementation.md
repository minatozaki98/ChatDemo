# ChatDemo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python FastAPI + Vite/React chat app using Azure OpenAI, with Ruff+mypy, CodeRabbit CI gate, and single-instance Fly.io deployment.

**Architecture:** FastAPI backend serves a `POST /api/chat` endpoint and mounts the built Vite/React frontend as static files. Conversation history lives entirely in browser memory and is sent with each request. A multi-stage Dockerfile builds the frontend then packages it with the backend.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, openai SDK, pydantic-settings, Ruff, mypy, Vite, React 18, TypeScript, Tailwind CSS, Fly.io, GitHub Actions, CodeRabbit

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.template`
- Create: `backend/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "chatdemo"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "openai>=1.40.0",
    "pydantic-settings>=2.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "mypy>=1.11.0",
    "ruff>=0.6.0",
]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
strict = true
python_version = "3.12"
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 2: Create .gitignore**

```
.env
__pycache__/
*.pyc
.mypy_cache/
.ruff_cache/
dist/
frontend/dist/
node_modules/
.venv/
*.egg-info/
```

**Step 3: Create .env.template**

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-01
```

**Step 4: Create empty init files**

```bash
mkdir -p backend tests
touch backend/__init__.py tests/__init__.py
```

**Step 5: Install Python dependencies**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

**Step 6: Commit**

```bash
git init
git add pyproject.toml .gitignore .env.template backend/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding"
```

---

## Task 2: Backend — Config

**Files:**
- Create: `backend/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import pytest
from backend.config import Settings


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    settings = Settings()
    assert settings.azure_openai_endpoint == "https://test.openai.azure.com/"
    assert settings.azure_openai_api_key == "test-key"
    assert settings.azure_openai_deployment == "gpt-4o"
    assert settings.azure_openai_api_version == "2024-02-01"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```
Expected: FAIL with `ImportError: cannot import name 'Settings'`

**Step 3: Write minimal implementation**

```python
# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str
    azure_openai_api_version: str


def get_settings() -> Settings:
    return Settings()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```
Expected: PASS

**Step 5: Run ruff and mypy**

```bash
ruff check backend/config.py
mypy backend/config.py
```
Expected: no errors

**Step 6: Commit**

```bash
git add backend/config.py tests/test_config.py
git commit -m "feat: backend config with pydantic-settings"
```

---

## Task 3: Backend — Models

**Files:**
- Create: `backend/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# backend/models.py
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ChatResponse(BaseModel):
    reply: str
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```
Expected: PASS

**Step 5: Run ruff and mypy**

```bash
ruff check backend/models.py
mypy backend/models.py
```
Expected: no errors

**Step 6: Commit**

```bash
git add backend/models.py tests/test_models.py
git commit -m "feat: backend Pydantic models"
```

---

## Task 4: Backend — Chat Logic

**Files:**
- Create: `backend/chat.py`
- Create: `tests/test_chat.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_chat.py -v
```
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# backend/chat.py
from openai import AzureOpenAI

from backend.config import get_settings
from backend.models import Message

_settings = get_settings()

client = AzureOpenAI(
    azure_endpoint=_settings.azure_openai_endpoint,
    api_key=_settings.azure_openai_api_key,
    api_version=_settings.azure_openai_api_version,
)


def get_reply(messages: list[Message]) -> str:
    response = client.chat.completions.create(
        model=_settings.azure_openai_deployment,
        messages=[{"role": m.role, "content": m.content} for m in messages],
    )
    content = response.choices[0].message.content
    return content if content is not None else ""
```

Note: Tests mock `backend.chat.client` at module level, so the AzureOpenAI client is never actually called during tests. You'll need a `.env` file with dummy values so `get_settings()` doesn't fail at import time.

Create a `.env` file for local testing (not committed):
```
AZURE_OPENAI_ENDPOINT=https://dummy.openai.azure.com/
AZURE_OPENAI_API_KEY=dummy
AZURE_OPENAI_DEPLOYMENT=dummy
AZURE_OPENAI_API_VERSION=2024-02-01
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_chat.py -v
```
Expected: PASS

**Step 5: Run ruff and mypy**

```bash
ruff check backend/chat.py
mypy backend/chat.py
```
Expected: no errors

**Step 6: Commit**

```bash
git add backend/chat.py tests/test_chat.py
git commit -m "feat: Azure OpenAI chat logic"
```

---

## Task 5: Backend — FastAPI App

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# backend/main.py
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_main.py -v
```
Expected: PASS

**Step 5: Run all backend tests**

```bash
pytest tests/ -v
```
Expected: all PASS

**Step 6: Run ruff and mypy on entire backend**

```bash
ruff check backend/
mypy backend/
```
Expected: no errors

**Step 7: Commit**

```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: FastAPI app with /api/chat endpoint"
```

---

## Task 6: Frontend Scaffold

**Files:**
- Create: `frontend/` (Vite project)
- Modify: `frontend/vite.config.ts`

**Step 1: Scaffold Vite + React + TypeScript project**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**Step 2: Install Tailwind CSS**

```bash
npm install -D tailwindcss @tailwindcss/vite
```

**Step 3: Configure Tailwind in vite.config.ts**

Replace the contents of `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

**Step 4: Add Tailwind import to frontend/src/index.css**

Replace the entire contents of `frontend/src/index.css`:

```css
@import "tailwindcss";
```

**Step 5: Verify frontend builds**

```bash
cd frontend && npm run build
```
Expected: `dist/` folder created with `index.html`, `assets/`

**Step 6: Commit**

```bash
cd ..
git add frontend/
git commit -m "chore: scaffold Vite + React + TypeScript + Tailwind"
```

---

## Task 7: Frontend — Types and API Client

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`

**Step 1: Create types**

```typescript
// frontend/src/types.ts
export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
}
```

**Step 2: Create API client**

```typescript
// frontend/src/api.ts
import type { ChatResponse, Message } from "./types";

export async function sendMessage(messages: Message[]): Promise<string> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data: ChatResponse = await response.json() as ChatResponse;
  return data.reply;
}
```

**Step 3: Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts
git commit -m "feat: frontend types and API client"
```

---

## Task 8: Frontend — Components

**Files:**
- Create: `frontend/src/components/MessageBubble.tsx`
- Create: `frontend/src/components/ChatWindow.tsx`
- Create: `frontend/src/components/InputBar.tsx`

**Step 1: Create MessageBubble**

```tsx
// frontend/src/components/MessageBubble.tsx
import type { Message } from "../types";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 text-sm ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
```

**Step 2: Create ChatWindow**

```tsx
// frontend/src/components/ChatWindow.tsx
import { useEffect, useRef } from "react";
import type { Message } from "../types";
import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: Message[];
}

export function ChatWindow({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.length === 0 && (
        <p className="text-center text-gray-400 mt-8">Start a conversation...</p>
      )}
      {messages.map((msg, i) => (
        <MessageBubble key={i} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
```

**Step 3: Create InputBar**

```tsx
// frontend/src/components/InputBar.tsx
import { useState } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function InputBar({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t p-4 flex gap-2">
      <textarea
        className="flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={2}
        placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button
        className="self-end rounded-xl bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
      >
        Send
      </button>
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: chat UI components"
```

---

## Task 9: Frontend — App Entry Point

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Replace App.tsx with chat implementation**

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { sendMessage } from "./api";
import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import type { Message } from "./types";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (text: string) => {
    const userMessage: Message = { role: "user", content: text };
    const updated = [...messages, userMessage];
    setMessages(updated);
    setLoading(true);
    setError(null);

    try {
      const reply = await sendMessage(updated);
      setMessages([...updated, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="border-b px-6 py-4">
        <h1 className="text-lg font-semibold text-gray-900">ChatDemo</h1>
      </header>
      <ChatWindow messages={messages} />
      {error && (
        <p className="px-4 pb-2 text-center text-sm text-red-500">{error}</p>
      )}
      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
```

**Step 2: Build and verify no TypeScript errors**

```bash
cd frontend && npm run build
```
Expected: successful build, no TypeScript errors

**Step 3: Commit**

```bash
cd ..
git add frontend/src/App.tsx
git commit -m "feat: App component with full chat flow"
```

---

## Task 10: Dockerfile

**Files:**
- Create: `Dockerfile`

**Step 1: Create multi-stage Dockerfile**

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[" && pip install --no-cache-dir fastapi uvicorn openai pydantic-settings

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Wait — pip install from pyproject.toml requires the source. Use this instead:

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.12-slim AS runner
WORKDIR /app

COPY pyproject.toml ./
COPY backend/ ./backend/
RUN pip install --no-cache-dir .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Step 2: Verify Docker build locally (requires Docker Desktop)**

```bash
docker build -t chatdemo .
```
Expected: successful build

**Step 3: Commit**

```bash
git add Dockerfile
git commit -m "chore: multi-stage Dockerfile"
```

---

## Task 11: Fly.io Config

**Files:**
- Create: `fly.toml`

**Step 1: Install flyctl if not already installed**

```bash
# Windows (PowerShell):
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
# Or: winget install Fly.io.flyctl
```

**Step 2: Initialize Fly.io app**

```bash
fly launch --no-deploy
```

This generates a `fly.toml`. If it doesn't match, replace with:

```toml
app = "chatdemo"
primary_region = "iad"

[build]

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

**Step 3: Set Fly.io secrets**

```bash
fly secrets set \
  AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
  AZURE_OPENAI_API_KEY="your-key" \
  AZURE_OPENAI_DEPLOYMENT="your-deployment" \
  AZURE_OPENAI_API_VERSION="2024-02-01"
```

**Step 4: Commit**

```bash
git add fly.toml
git commit -m "chore: Fly.io config"
```

---

## Task 12: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`

**Step 1: Create ci.yml**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  lint-and-type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Python dependencies
        run: pip install -e ".[dev]"

      - name: Ruff lint
        run: ruff check backend/

      - name: Mypy type check
        run: mypy backend/

      - name: Run tests
        run: pytest tests/ -v
        env:
          AZURE_OPENAI_ENDPOINT: https://dummy.openai.azure.com/
          AZURE_OPENAI_API_KEY: dummy
          AZURE_OPENAI_DEPLOYMENT: dummy
          AZURE_OPENAI_API_VERSION: 2024-02-01

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: npm ci
        working-directory: frontend

      - name: Build frontend (TypeScript check + bundle)
        run: npm run build
        working-directory: frontend
```

**Step 2: Create deploy.yml**

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up flyctl
        uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Deploy to Fly.io
        run: fly deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Step 3: Commit**

```bash
git add .github/
git commit -m "ci: GitHub Actions CI and deploy workflows"
```

---

## Task 13: CodeRabbit Config

**Files:**
- Create: `.coderabbit.yaml`

**Step 1: Create .coderabbit.yaml**

```yaml
# .coderabbit.yaml
language: en-US

reviews:
  auto_review:
    enabled: true
    drafts: false
  path_filters:
    - "!docs/**"
    - "!*.md"
    - "!.env.template"
    - "!fly.toml"

chat:
  auto_reply: true
```

**Step 2: Configure branch protection in GitHub**

In GitHub → repo Settings → Branches → Add rule for `main`:
- Check "Require a pull request before merging"
- Check "Require status checks to pass before merging" → add `lint-and-type-check` and `frontend-build`
- Check "Require approvals" → add CodeRabbit as a required reviewer (after installing CodeRabbit GitHub App)

Install CodeRabbit GitHub App at: https://github.com/apps/coderabbitai

**Step 3: Commit**

```bash
git add .coderabbit.yaml
git commit -m "ci: CodeRabbit config"
```

---

## Task 14: Documentation Files

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `DEVLOG.md`
- Create: `CONTRIBUTING.md`

**Step 1: Create README.md**

```markdown
# ChatDemo

A chat application powered by Azure OpenAI, built with FastAPI and React.

## Prerequisites

- Python 3.12+
- Node.js 20+
- An Azure OpenAI resource with a deployed model

## Local Development

### 1. Clone and set up environment

```bash
git clone <repo-url>
cd ChatDemo
cp .env.template .env
# Edit .env with your Azure OpenAI credentials
```

### 2. Start the backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn backend.main:app --reload --port 8000
```

### 3. Start the frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Run tests and linting

```bash
pytest tests/ -v
ruff check backend/
mypy backend/
```

## Deployment

### First-time setup

```bash
fly auth login
fly launch --no-deploy
fly secrets set AZURE_OPENAI_ENDPOINT=... AZURE_OPENAI_API_KEY=... AZURE_OPENAI_DEPLOYMENT=... AZURE_OPENAI_API_VERSION=...
```

### Deploy

```bash
fly deploy
```

Or push to `main` — GitHub Actions deploys automatically after CI passes.

## CI/CD

- Every PR runs: ruff, mypy, pytest, frontend build, CodeRabbit review
- CodeRabbit approval is required before merging to `main`
- Merging to `main` triggers automatic Fly.io deployment

## Environment Variables

See `.env.template` for all required variables.
```

**Step 2: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-03-06

### Added
- FastAPI backend with `/api/chat` endpoint
- Azure OpenAI integration via `openai` SDK
- Vite + React + TypeScript frontend
- Tailwind CSS styling
- In-browser conversation history
- Multi-stage Dockerfile for single-instance deployment
- Fly.io deployment config
- GitHub Actions CI (ruff, mypy, pytest, frontend build)
- CodeRabbit AI review gate
- Automated deploy on merge to main
```

**Step 3: Create DEVLOG.md**

```markdown
# Development Log

## 2026-03-06 — Initial Build

### Architecture Decisions

**Monorepo over split repos:** FastAPI serves the built React frontend as static files. Single `fly deploy` ships everything. No CORS config needed.

**FastAPI over Flask:** Async-native, excellent Pydantic integration, automatic OpenAPI docs. Better fit for AI workloads.

**No streaming:** Full response delivery keeps the backend stateless and the frontend simple. Streaming can be added later with SSE if needed.

**In-browser history:** No database required. Full conversation history is maintained in React state and sent with every request. Simple, zero infrastructure.

**Tailwind CSS:** Utility-first, no separate CSS files to maintain, ships tiny in production with Vite's tree-shaking.

**pydantic-settings:** Type-safe environment variable loading with validation. Fails fast at startup if any required var is missing.
```

**Step 4: Create CONTRIBUTING.md**

```markdown
# Contributing

## Setup

```bash
git clone <repo-url>
cd ChatDemo
cp .env.template .env  # fill in your Azure credentials
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd frontend && npm install && cd ..
```

## Branch Naming

- `feat/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `chore/<short-description>` — tooling, config, docs

## Before Pushing

All of these must pass:

```bash
ruff check backend/
mypy backend/
pytest tests/ -v
cd frontend && npm run build
```

## Pull Request Process

1. Open a PR against `main`
2. CI runs automatically (ruff, mypy, pytest, frontend build)
3. CodeRabbit AI reviews your PR — address any blocking feedback
4. CodeRabbit approval is required before merge
5. Merging to `main` triggers automatic deployment to Fly.io

## Code Style

- Python: ruff enforces style, mypy enforces strict types
- TypeScript: strict mode enabled in `tsconfig.json`
- Commits: use conventional commits (`feat:`, `fix:`, `chore:`, `ci:`, `docs:`)
```

**Step 5: Commit**

```bash
git add README.md CHANGELOG.md DEVLOG.md CONTRIBUTING.md
git commit -m "docs: add README, CHANGELOG, DEVLOG, CONTRIBUTING"
```

---

## Task 15: First Deploy

**Step 1: Push to GitHub**

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```

**Step 2: Add FLY_API_TOKEN to GitHub secrets**

```bash
fly tokens create deploy -x 999999h
```

Copy the token → GitHub repo → Settings → Secrets → Actions → New secret → `FLY_API_TOKEN`

**Step 3: Deploy manually to verify**

```bash
fly deploy
```

Expected: app live at `https://chatdemo.fly.dev` (or your app name)

**Step 4: Smoke test**

```bash
curl -X POST https://chatdemo.fly.dev/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

Expected: `{"reply": "..."}` with a real AI response

**Step 5: Open the app**

Visit `https://chatdemo.fly.dev` in a browser and send a message.
