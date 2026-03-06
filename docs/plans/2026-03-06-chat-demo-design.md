# ChatDemo Design

**Date:** 2026-03-06
**Status:** Approved

## Overview

A chat web application using Azure OpenAI, with a FastAPI Python backend and a Vite + React TypeScript frontend. Deployed as a single instance on Fly.io.

## Requirements

- Python backend with FastAPI
- React + Vite + TypeScript frontend
- Azure OpenAI integration (full conversation history in browser memory)
- Full response delivery (no streaming)
- Ruff + mypy for Python code quality
- CodeRabbit AI review gate via GitHub Actions (must pass before merge to main)
- Fly.io deployment (single machine, single Dockerfile)
- No database
- Documentation: README, DEVLOG, CHANGELOG, CONTRIBUTING, .env.template

## Architecture

### Project Structure

```
ChatDemo/
├── backend/
│   ├── main.py               # FastAPI app, routes, static file mounting
│   ├── chat.py               # AzureOpenAI client + chat logic
│   ├── models.py             # Pydantic request/response models
│   └── config.py             # pydantic-settings env var config
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── InputBar.tsx
│   │   └── api.ts
│   └── dist/                 # built output (gitignored)
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── docs/
│   └── plans/
│       └── 2026-03-06-chat-demo-design.md
├── Dockerfile
├── fly.toml
├── pyproject.toml
├── .env.template
├── .env                      # gitignored
├── .coderabbit.yaml
├── README.md
├── CHANGELOG.md
├── DEVLOG.md
└── CONTRIBUTING.md
```

### Data Flow

1. Browser loads React SPA served by FastAPI's StaticFiles mount
2. User types message → React appends to in-memory `messages` array
3. `POST /api/chat` with full `{messages: [...]}` history
4. FastAPI calls Azure OpenAI, returns `{reply: "..."}`
5. React appends reply to history, re-renders

## Backend

**Framework:** FastAPI + uvicorn
**Dependencies:** `fastapi`, `uvicorn`, `openai`, `pydantic-settings`

### Modules

- `config.py` — `Settings` class via `pydantic-settings`, reads env vars:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_DEPLOYMENT`
  - `AZURE_OPENAI_API_VERSION`
- `models.py` — `Message(role, content)`, `ChatRequest(messages)`, `ChatResponse(reply)`
- `chat.py` — `AzureOpenAI` client, `get_reply(messages) -> str`
- `main.py` — `POST /api/chat`, mounts `frontend/dist` as StaticFiles, SPA fallback

### Code Quality

- `mypy` with `strict = true`
- `ruff` with `select = ["E", "F", "I", "UP", "B"]`

## Frontend

**Stack:** Vite + React + TypeScript + Tailwind CSS

### Components

- `App.tsx` — owns `messages: Message[]` state
- `ChatWindow.tsx` — scrollable message list
- `MessageBubble.tsx` — styled per role (user/assistant)
- `InputBar.tsx` — textarea + send button, disabled while loading
- `api.ts` — `sendMessage(messages)` → `POST /api/chat`

**Dev proxy:** `vite.config.ts` proxies `/api/*` to `http://localhost:8000`

## Deployment

### Dockerfile (multi-stage)

1. **Stage 1 (node):** `npm ci && vite build` → `frontend/dist/`
2. **Stage 2 (python):** copy dist + backend, `pip install`, run `uvicorn`

### Fly.io

- Single machine, port 8080
- Secrets: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`
- Deploy: `fly deploy --remote-only`

## CI/CD

### `ci.yml` (on PR)

1. `ruff check backend/`
2. `mypy backend/`
3. `npm run build` (TypeScript compile check)
4. CodeRabbit auto-review (configured via `.coderabbit.yaml`)

### `deploy.yml` (on push to main)

1. `fly deploy --remote-only`

### Branch Protection

- `main` requires CodeRabbit approval before merge
- Configured in GitHub repo settings (not in workflow)

### GitHub Secrets

- `FLY_API_TOKEN`

## Environment Variables

See `.env.template` for all required variables.

## Documentation Files

- `README.md` — setup, local dev, deployment guide
- `CHANGELOG.md` — Keep a Changelog format
- `DEVLOG.md` — architectural decisions and development narrative
- `CONTRIBUTING.md` — dev setup, branch conventions, PR process, code quality requirements
- `.env.template` — template for all required env vars
