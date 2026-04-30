# Squad Decisions

## Active Decisions

### In-Memory Caching & Rate Limiting Strategy
**Author:** Fenster | **Date:** 2026-04-30 | **Status:** Implemented

- Caching: In-memory Map with TTL (1hr search results, 5min sitemap). Process-scoped.
- Rate limiting: Per-IP sliding window. `/api/check`: 5/min, `/api/report`: 10/min, `/api/reports`: 20/min. Returns 429 + Retry-After.
- Trade-off: No cross-instance sharing. Needs Redis/Upstash if moving to serverless at scale.

### README: Google CSE Documentation
**Author:** Keaton | **Date:** 2026-04-30 | **Status:** Implemented

- README now accurately reflects Google CSE (not DuckDuckGo) as the search method.
- Added Quick Start API setup note (`.env.local.example` → `.env.local`).
- Documented 100 queries/day free tier limit.
- Compliance section clarifies Google CSE is an official API.

### Vitest as Test Framework
**Author:** McManus | **Date:** 2026-04-30 | **Status:** Implemented

- Adopted Vitest: `npm test` → `vitest run`, `npm run test:watch` → `vitest`.
- Config: `vitest.config.ts` with `globals: true`. Tests at `lib/__tests__/`.
- 38 tests cover core matching logic. 3 known Unicode bugs documented.
- All team members should run `npm test` before pushing.

### Unicode Normalization Strategy
**Author:** Fenster | **Date:** 2026-04-30 | **Status:** Implemented

- `norm()` uses NFD decomposition + combining mark removal for Unicode transliteration. Special cases (ß, æ, œ) handled before NFD. No external dependencies.
- CJK/Cyrillic names still normalize to empty string → false-positive matches. Acceptable for NYC Latin-script focus.
- If we expand internationally, we'd need ICU transliteration or a lookup table for non-Latin scripts.
- All restaurant names with common accents (Café, Señor, Lïllïes) now match correctly in search and Blackbird sitemap checks.

### Fly.io Deployment Configuration
**Author:** Fenster | **Date:** 2026-04-30 | **Status:** Implemented

- Deploy to Fly.io with persistent volumes for SQLite (shared-cpu-1x, 512MB, Newark).
- DB path via `DATABASE_PATH` env var; defaults to `process.cwd()/eatdiscounted.db` locally.
- Auto-stop machines when idle ($0 cost at rest), auto-start on request (~2-3s cold start).
- Secrets (`GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ID`) via `fly secrets`, not in fly.toml.
- Single machine = single-writer SQLite works perfectly; no Redis needed for caching/rate limiting.
- Trade-off: In-memory cache lost on deploy. If multi-instance needed later, move to LiteFS or hosted DB.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
