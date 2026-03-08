# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.1] - 2026-03-08

### Fixed
- Startup crash: lazy-load Azure OpenAI settings instead of module-level init
- Deploy workflow restored to auto-deploy on push to main

### Added
- `/healthz` health check endpoint for Fly.io monitoring
- Fly.io health check config in `fly.toml`
- CodeRabbit full-repo review scope with gitignore-aligned exclusions

### Changed
- `backend/chat.py` uses `@lru_cache` for client initialization
- `.coderabbit.yaml` now uses `review_scope: "full"`

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
