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

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
