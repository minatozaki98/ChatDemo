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
