# Development Log

## 2026-03-06 — Initial Build

### Architecture Decisions

**Monorepo over split repos:** FastAPI serves the built React frontend as static files. Single `fly deploy` ships everything. No CORS config needed.

**FastAPI over Flask:** Async-native, excellent Pydantic integration, automatic OpenAPI docs. Better fit for AI workloads.

**No streaming:** Full response delivery keeps the backend stateless and the frontend simple. Streaming can be added later with SSE if needed.

**In-browser history:** No database required. Full conversation history is maintained in React state and sent with every request. Simple, zero infrastructure.

**Tailwind CSS:** Utility-first, no separate CSS files to maintain, ships tiny in production with Vite's tree-shaking.

**pydantic-settings:** Type-safe environment variable loading with validation. Fails fast at startup if any required var is missing.
