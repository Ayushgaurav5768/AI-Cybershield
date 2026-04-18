# AI CyberShield Startup Architecture (MVP)

## Current implementation shape
- FastAPI backend in `app/`
- URL phishing model in `ml/`
- LangChain FAISS RAG in `app/rag/`
- Static frontend in `frontend/`
- New Chrome MV3 extension in `apps/chrome-extension/`

## Startup target structure
- `apps/api` (incremental migration target from `app/`)
- `apps/web-dashboard` (future Next.js migration target)
- `apps/chrome-extension` (now implemented)
- `packages/detector-core` (future shared detection lib)
- `packages/rag-engine` (future shared RAG/retrieval)
- `database/` (migrations + seed scripts)
- `docs/` (product, security, architecture docs)

## Hybrid detection pipeline
1. URL normalization and sanitization
2. Threat intel quick checks (known-bad, suspicious TLD, shorteners)
3. Heuristic scoring (URL obfuscation and phishing patterns)
4. ML model scoring (current sklearn model)
5. Weighted risk score composition and explainability output
6. Optional RAG plain-language explanation enhancement

## Data entities (implemented)
- `scans` (legacy core table)
- `scan_details` (signals, confidence, explanations)
- `user_reports` (reporting queue)
- `scan_feedback` (accuracy feedback)
- `allowlist_entries` (trusted domains)
- `extension_events` (browser telemetry)

## Security controls (MVP)
- URL sanitization and strict scheme/host checks
- Basic in-memory rate limiting middleware
- Env-driven config for secrets and limits
- Minimal data collection principle in extension

## Next phase migrations
- Move to Alembic migrations + PostgreSQL
- Add authentication and role-based analyst/admin access
- Add queue for async enrichment and retraining workflow
- Replace in-memory limiter with Redis-backed limiter
