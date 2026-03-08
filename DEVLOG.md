# Development Log

## 2026-03-06 — Initial Build

### Architecture Decisions

**Monorepo over split repos:** FastAPI serves the built React frontend as static files. Single `fly deploy` ships everything. No CORS config needed.

**FastAPI over Flask:** Async-native, excellent Pydantic integration, automatic OpenAPI docs. Better fit for AI workloads.

**No streaming:** Full response delivery keeps the backend stateless and the frontend simple. Streaming can be added later with SSE if needed.

**In-browser history:** No database required. Full conversation history is maintained in React state and sent with every request. Simple, zero infrastructure.

**Tailwind CSS:** Utility-first, no separate CSS files to maintain, ships tiny in production with Vite's tree-shaking.

**pydantic-settings:** Type-safe environment variable loading with validation. Fails fast at startup if any required var is missing.

## 2026-03-08 — Fix CI/CD Pipeline & Fly.io Deploy

### Problem

Fly.io deployment entered a crash loop (10 restarts, then failure). GitHub Actions deploy workflow was set to manual trigger only. CodeRabbit was reviewing only changed files instead of the full codebase.

### Root Cause Analysis

**Startup crash:** `backend/chat.py` called `get_settings()` at module import time (line 7). When uvicorn imported `backend.main`, it triggered `backend.chat` import, which immediately validated Azure OpenAI env vars via pydantic-settings. If any var was missing or invalid, the process crashed before serving a single request. Fly.io retried 10 times, then gave up — the machine got stuck in an "active but dead" state, blocking load balancer attempts.

**Deploy trigger:** Commit `e1f2b8b` changed deploy.yml from `push` to `workflow_dispatch` (manual only). Auto-deploy on push to main was lost.

**CodeRabbit scope:** Missing `review_scope: "full"` in `.coderabbit.yaml` — default behavior is diff-only review.

### Decisions

**Lazy-load settings:** Moved `get_settings()` and `AzureOpenAI` client initialization into a `@lru_cache` function called at first request, not at import. App starts cleanly even if env vars aren't set yet — fails on first API call instead of on boot.

**Health check endpoint:** Added `/healthz` GET endpoint so Fly.io can distinguish between "app is up" and "app is stuck." Configured in `fly.toml` with 10s interval, 5s grace period.

**Auto-deploy restored:** Changed deploy trigger back to `push: branches: [main]`.

**CodeRabbit full review:** Added `review_scope: "full"` and aligned `path_filters` with `.gitignore` exclusions.
