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
