# Fix CI/CD Pipeline & Fly.io Deploy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the Fly.io deployment crash, enable auto-deploy on push to main, and configure CodeRabbit to review all files.

**Architecture:** The app crashes because `backend/chat.py` initializes Azure OpenAI settings at module import time — if env vars are missing, the process dies before serving. We'll make settings lazy-loaded, add a health check for Fly.io, fix the deploy trigger, and commit the CodeRabbit config change.

**Tech Stack:** Python/FastAPI, GitHub Actions, Fly.io, CodeRabbit

---

### Task 1: Add health check endpoint

**Files:**
- Modify: `backend/main.py`
- Test: `tests/test_main.py`

**Step 1: Write the failing test**

Add to `tests/test_main.py`:

```python
@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_health_endpoint_returns_ok -v`
Expected: FAIL with 404

**Step 3: Write minimal implementation**

Add to `backend/main.py` before the static files mount:

```python
@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_health_endpoint_returns_ok -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: add /healthz endpoint for Fly.io health checks"
```

---

### Task 2: Fix module-level settings crash — lazy-load settings

The root cause of the Fly.io restart loop: `backend/chat.py` calls `get_settings()` at import time (line 7). If Azure env vars are missing, pydantic-settings raises `ValidationError` and the process crashes before uvicorn starts.

**Files:**
- Modify: `backend/chat.py`
- Modify: `tests/test_chat.py`

**Step 1: Write the failing test**

Add to `tests/test_chat.py`:

```python
def test_get_reply_calls_azure_with_settings(messages: list[Message]) -> None:
    """Verify get_reply uses lazily-loaded settings, not module-level globals."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hi"

    with (
        patch("backend.chat.get_settings") as mock_settings,
        patch("backend.chat.AzureOpenAI") as mock_azure,
    ):
        mock_azure.return_value.chat.completions.create.return_value = mock_response
        get_reply(messages)
        mock_settings.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat.py::test_get_reply_calls_azure_with_settings -v`
Expected: FAIL — currently `get_settings()` is called at import, not inside `get_reply()`

**Step 3: Refactor chat.py to lazy-load settings**

Replace entire `backend/chat.py`:

```python
# backend/chat.py
from functools import lru_cache

from openai import AzureOpenAI

from backend.config import get_settings
from backend.models import Message


@lru_cache(maxsize=1)
def _get_client() -> AzureOpenAI:
    settings = get_settings()
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def get_reply(messages: list[Message]) -> str:
    client = _get_client()
    settings = get_settings()
    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[misc]
    )
    content = response.choices[0].message.content
    return content if content is not None else ""
```

**Step 4: Update existing tests for new structure**

Replace `tests/test_chat.py` entirely:

```python
# tests/test_chat.py
from unittest.mock import MagicMock, patch

import pytest

from backend.models import Message


@pytest.fixture
def messages() -> list[Message]:
    return [Message(role="user", content="Say hello")]


@pytest.fixture(autouse=True)
def _clear_client_cache() -> None:
    """Clear lru_cache between tests."""
    from backend.chat import _get_client
    _get_client.cache_clear()


def test_get_reply_returns_string(messages: list[Message]) -> None:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello!"

    with (
        patch("backend.chat.get_settings"),
        patch("backend.chat.AzureOpenAI") as mock_azure,
    ):
        mock_azure.return_value.chat.completions.create.return_value = mock_response
        from backend.chat import get_reply
        result = get_reply(messages)

    assert result == "Hello!"


def test_get_reply_passes_messages(messages: list[Message]) -> None:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hi"

    with (
        patch("backend.chat.get_settings"),
        patch("backend.chat.AzureOpenAI") as mock_azure,
    ):
        mock_azure.return_value.chat.completions.create.return_value = mock_response
        from backend.chat import get_reply
        get_reply(messages)
        call_kwargs = mock_azure.return_value.chat.completions.create.call_args[1]

    assert call_kwargs["messages"][0]["role"] == "user"
    assert call_kwargs["messages"][0]["content"] == "Say hello"


def test_get_reply_calls_azure_with_settings(messages: list[Message]) -> None:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hi"

    with (
        patch("backend.chat.get_settings") as mock_settings,
        patch("backend.chat.AzureOpenAI") as mock_azure,
    ):
        mock_azure.return_value.chat.completions.create.return_value = mock_response
        from backend.chat import get_reply
        get_reply(messages)
        mock_settings.assert_called()
```

**Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 6: Run linting and type check**

Run: `ruff check backend/ && mypy backend/`
Expected: No errors

**Step 7: Commit**

```bash
git add backend/chat.py tests/test_chat.py
git commit -m "fix: lazy-load Azure settings to prevent startup crash"
```

---

### Task 3: Add Fly.io health check config

**Files:**
- Modify: `fly.toml`

**Step 1: Add health check to fly.toml**

Add after `[http_service]` section:

```toml
[http_service.checks]
  [http_service.checks.health]
    interval = "10s"
    timeout = "2s"
    grace_period = "5s"
    method = "GET"
    path = "/healthz"
```

**Step 2: Commit**

```bash
git add fly.toml
git commit -m "chore: add Fly.io health check on /healthz"
```

---

### Task 4: Fix deploy workflow — auto-deploy on push to main

**Files:**
- Modify: `.github/workflows/deploy.yml`

**Step 1: Update deploy trigger**

Change the `on:` section from `workflow_dispatch` to:

```yaml
on:
  push:
    branches: [main]
```

**Step 2: Verify the full file looks correct**

```yaml
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

      - name: Set Fly.io secrets
        run: |
          fly secrets set \
            AZURE_OPENAI_ENDPOINT="${{ secrets.AZURE_OPENAI_ENDPOINT }}" \
            AZURE_OPENAI_API_KEY="${{ secrets.AZURE_OPENAI_API_KEY }}" \
            AZURE_OPENAI_DEPLOYMENT="${{ secrets.AZURE_OPENAI_DEPLOYMENT }}" \
            AZURE_OPENAI_API_VERSION="${{ secrets.AZURE_OPENAI_API_VERSION }}" \
            --stage
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

      - name: Deploy to Fly.io
        run: fly deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: auto-deploy to Fly.io on push to main"
```

---

### Task 5: Commit CodeRabbit config

The `.coderabbit.yaml` has already been updated with `review_scope: "full"` and gitignore-aligned path filters.

**Step 1: Verify the file**

Confirm `.coderabbit.yaml` contains `review_scope: "full"` and all path exclusions.

**Step 2: Commit**

```bash
git add .coderabbit.yaml
git commit -m "chore: CodeRabbit full-repo review with gitignore exclusions"
```

---

### Task 6: Verify GitHub secrets are set

**This is a manual step — cannot be automated.**

In your GitHub repo, go to **Settings → Secrets and variables → Actions** and confirm these secrets exist and have correct values:

- `FLY_API_TOKEN`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`

If any are missing, the deploy will fail because `fly secrets set` sends empty values and pydantic-settings rejects them at startup.

---

### Task 7: Push and verify deployment

**Step 1: Push all commits**

```bash
git push origin main
```

**Step 2: Monitor GitHub Actions**

Go to: `https://github.com/<your-repo>/actions` — verify the Deploy workflow triggers.

**Step 3: Monitor Fly.io**

```bash
fly logs --app chatdemo
fly status --app chatdemo
```

Expected: App starts, health check passes, no restart loop.

**Step 4: If machine is stuck from previous crash**

```bash
fly machine list --app chatdemo
fly machine destroy <machine-id> --force
fly deploy --remote-only
```
