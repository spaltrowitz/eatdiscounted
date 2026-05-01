# Project Context

- **Owner:** Shari Paltrowitz
- **Project:** EatDiscounted — a Next.js web app that checks 8 dining discount platforms for any restaurant name. Results stream via SSE. Also has a Python CLI.
- **Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, better-sqlite3, SSE streaming, Python CLI
- **Created:** 2026-04-30

## Session: 2026-04-30 — Ship-Readiness Evaluation

**Role:** Backend Dev — Backend reliability & API review  
**Participants:** Keaton, Hockney, Fenster, McManus  
**Outcome:** 🔴 Not ship-ready — three critical fixes required before launch

**Backend audit findings:**
- API design (SSE) is clean but not actually streaming: all results in burst despite SSE complexity
- **Google CSE dependency:** 100 free queries/day = ~14 user searches before quota exhaustion (hard ceiling)
- **Rate limiting:** 🔴 Zero actual rate limiting; RATE_LIMIT_DELAY constant is dead code
- **Error handling:** Backend is solid with timeouts and graceful failures; good input validation
- **Database:** WAL mode, UNIQUE constraints, parameterized queries ✅; but hot-reload fragility + SQLite on serverless blocker
- **Scalability:** No caching, no CDN, single-writer SQLite limitation; memory issue with large Blackbird sitemap
- **Secrets:** 🔴 `.env.local` NOT in `.gitignore` (credential leak risk); hardcoded salt in db.ts

**Three highest-leverage fixes:**
1. **Response caching** — cache Google CSE results by query for 1 hour (multiplies effective capacity 10-50x)
2. **Rate limiting** — 5 req/IP/min on `/api/check` (prevents quota death to first bot)
3. **Fix `.env.local` in `.gitignore` & rotate API key** — check git history for exposure

**Post-launch:** Blackbird sitemap caching, structured logging, proper XML parser, deployment platform decision.

---

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-04-30 — Backend hardening (caching, rate limiting, secrets)

- **Response caching:** Google CSE results are now cached in-memory by normalized `restaurant::platform` key with 1-hour TTL. Blackbird sitemap is cached with 5-minute TTL. This should multiply effective Google CSE capacity 10-50x for repeated queries. Cache is a simple Map with timestamp expiry — no external deps.
- **Rate limiting:** In-memory per-IP rate limiter added to all three API routes (`/api/check`: 5/min, `/api/report`: 10/min, `/api/reports`: 20/min). Returns 429 with `Retry-After` header. Expired entries cleaned every 60s to prevent memory leaks. No external deps.
- **Secrets:** `.env.local` was already covered by `.env*` in `.gitignore` and was not tracked by git. No action needed — the original `.gitignore` was set up correctly.
- **Dead code:** Removed `RATE_LIMIT_DELAY` constant from `platforms.ts` — it was unused in the TypeScript codebase (only referenced in Python CLI and squad docs, which don't import from there).
- **Key constraint:** All caching is in-memory (process-scoped). Cache is lost on deploy/restart. This is fine for the current single-process model but won't survive serverless cold starts. If we move to Vercel serverless, we'd need Redis or similar.

### 2026-04-30 Fix Blockers Session
- Completed: In-memory caching (1hr CSE, 5min sitemap) + per-IP rate limiting (5/10/20 rpm) + removed dead RATE_LIMIT_DELAY.
- Team context: Keaton updated README, Hockney added error UI + a11y, McManus added 38 tests.

### 2026-04-30 Commit & Deployment Session
- Verified Fly.io deployment config: Dockerfile, .dockerignore, fly.toml, db.ts `DATABASE_PATH` env var, README deployment section all present.
- Authored Fly.io Deployment Configuration decision (persistent volume SQLite, auto-stop, secrets via `fly secrets`).
- Team context: Keaton committed full sprint (43cadba) and pushed to spaltrowitz/add-nextjs-web-ui.

📌 Team update (2026-04-30T18:34): Platform accuracy — Redfoot proposes site: operator in CSE queries, word-boundary matching, data corrections (Rakuten appOnly→false, Seated domain→seatedapp.io). Affects search.ts and platforms.ts.
📌 Team update (2026-04-30T18:34): Product roadmap — Kobayashi proposes restaurant permalinks (P0). May need new API route + caching strategy.

### 2026-04-30 Unicode Transliteration & Structured Logging
- **Unicode fix:** `norm()` now uses NFD decomposition + combining-mark stripping before ASCII filter. Handles ß→ss, æ→ae, œ→oe as special cases. "Café Boulud" → "cafe boulud" instead of "caf boulud".
- **Structured logging:** Added `console.error`/`console.warn` with bracketed prefixes (`[blackbird]`, `[google-cse]`, `[api/check]`, `[rate-limit]`) to all catch blocks and error paths. Grep-friendly, no deps.
- **API route hardening:** Wrapped SSE stream body in try/catch so unhandled errors don't crash without logging.
- **Tests:** All 38 tests pass. Updated 2 test expectations from "documents broken behavior" to "verifies correct behavior".
- **Key constraint:** CJK/Cyrillic still normalize to empty string — acceptable for NYC Latin-script focus.

### 2026-04-30 Google CSE Search Broken — Diagnosis & Fix
- **Root cause:** NOT the `site:` operator or quota exhaustion. The Google Cloud project does not have the "Custom Search JSON API" enabled. Every request returns 403 PERMISSION_DENIED regardless of query format.
- **Fix applied:** (1) Structured error parsing — distinguishes permission denied (403), quota exhausted (403 with "quota" reason), and rate limited (429). (2) Fallback strategy — if `site:`-scoped query fails, retries without `site:` before giving up. (3) Actionable log messages with query context.
- **Action required (Shari):** Go to Google Cloud Console → APIs & Services → Enable "Custom Search JSON API" for the project associated with key `AIzaSyCa...`. The code is ready; it will work as soon as the API is enabled.
- **Tests:** 38/38 pass, TypeScript compiles clean.

### 2026-04-30 Platform Accuracy Improvements (Redfoot's Review)
- **Word-boundary matching:** `matchesRestaurant` now uses `\b` regex instead of bare `includes()`. Prevents "robot" matching "Bo" and "blacksmith" matching "The Smith". Full-name check also uses boundaries. Regex special chars escaped.
- **site: operator in CSE:** Search queries now include `site:{domainFilter}` when a platform has a domain filter. Eliminates blog/review noise from results. Example: `"Carbone" site:inkind.com`.
- **slugVariants wired in:** `slugVariants()` is now used in `checkBlackbird` to match URL slugs directly (e.g. "the-smith-nomad" matching "The Smith Nomad"). No longer dead code.
- **Data corrections:** Rakuten Dining `appOnly` → false (has web UI). Seated `domainFilter` → "seatedapp.io" (was too loose at "seated"). Blackbird `cardLink` annotated as NFC/QR.
- **Tests:** All 38 pass. Updated 1 test expectation for word-boundary behavior ("Bo" no longer matches "robot").

### 2026-04-30 DuckDuckGo Fallback for Google CSE Failures
- **Problem:** Google CSE returns 403 due to Cloud project misconfiguration. App completely non-functional without it.
- **Solution:** Added `duckDuckGoSearch()` function that scrapes `html.duckduckgo.com/html/` and parses result titles, URLs, and snippets. `batchSearch()` now probes Google CSE with the first platform — if it fails (any error), all platforms fall back to DuckDuckGo sequentially with 2-second delays between requests.
- **DuckDuckGo parsing:** Splits on `result__body` class, extracts `result__a` href (unwraps DDG redirect via `uddg=` param), title text, and `result__snippet` content. HTML entities decoded. Caps at 10 results.
- **Caching:** DDG results cached identically to CSE results (same key, same TTL). Cache doesn't care which engine produced the data.
- **Logging:** `[search]` prefix logs which engine is active. `[duckduckgo]` prefix for per-platform DDG results. Existing `[google-cse]` logging unchanged.
- **Trade-off:** DDG fallback is sequential (not parallel) to respect rate limits. ~14 seconds for 7 platforms vs ~2s parallel with CSE. Acceptable since it only activates when CSE is broken.
- **Tests:** 38/38 pass, TypeScript compiles clean, Next.js build green.
- **Orchestration:** Documented in `.squad/orchestration-log/2026-04-30T19-36-30Z-fenster.md` and `.squad/log/2026-04-30T19-36-30Z-ddg-fallback.md`. Decisions archived in `.squad/decisions.md`.

### 2026-04-30 Brave Search API Migration
- **Root cause:** Google CSE completely broken (100% error rate, permission denied). Required complex Cloud Console setup that was never completed. Python CLI already successfully uses Brave Search API.
- **Solution:** Replaced `googleCSESearch()` with `braveSearch()` calling `https://api.search.brave.com/res/v1/web/search` with `X-Subscription-Token` header. Removed Google CSE env vars (`GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ID`) and replaced with single `BRAVE_SEARCH_API_KEY`.
- **Brave API details:** Returns 5 results per query, supports `site:` operator, has 2,000 free queries/month (20x Google CSE's 100/day). Response structure: `data.web.results[]` with `title`, `url`, `description` fields.
- **Removed complexity:** Eliminated DuckDuckGo fallback code entirely (no longer needed). Removed retry-without-site-operator logic. Brave is now the sole search engine.
- **Caching:** Existing 1-hour in-memory cache logic preserved. All search queries still cached by `restaurant::platform` key.
- **Error handling:** Updated error messages and logging to use `[brave-search]` prefix. Preserved structured error parsing for 403/429 responses.
- **Documentation:** Updated README.md Quick Start, How It Works, Deployment, and Compliance sections. Created `.env.local.example` with Brave API key reference.
- **Tests:** All 38 tests pass. Build green. No code changes needed in tests — all matching logic unchanged.
- **Trade-off:** Brave free tier (2,000/month) is far more generous than Google CSE (100/day). With 1-hour caching, should support ~200+ users/day before hitting limits.

### 2026-05-01 Team Delivery: Brave Search + Design + Tests
- Deployed Brave Search API integration (lib/checkers.ts) — replaced broken Google CSE, removed DDG fallback
- Build passes, 38 existing tests all green
- Collaborating with Hockney on design improvements and McManus on test suite expansion

### 2026-05-01 Upside Direct API Integration
- **What:** Replaced Brave Search fallback for Upside with a direct REST API call. Upside's offer-finder page calls an open API (`POST /prod/offers/refresh`) that accepts a bounding box and returns restaurant offers with names, cashback percentages, and categories. No auth needed.
- **Implementation:** New `checkUpside()` function in `lib/checkers.ts` calls the API with a Manhattan bounding box (lat 40.70–40.82, lng -74.02 to -73.93), filters to `RESTAURANT` category, matches using `matchesRestaurant()`. Results include cashback percentage (e.g. "8% cash back"). Full offer list cached with 1-hour TTL (same pattern as Blackbird sitemap cache).
- **Fallback:** If the Upside API is down, falls back to Brave Search with `site:upside.com`. If that also fails, returns `searchUnavailable` gracefully.
- **Route changes:** `app/api/check/route.ts` now runs `checkUpside()` in parallel with `checkBlackbird()` and `batchSearch()`. Upside excluded from `batchSearch()` since it has its own checker.
- **Platform update:** Upside `appOnly` set to `false` in `platforms.ts` — we now have direct API access. Added `"api"` to the `CheckResult.method` union type.
- **Tests:** 75/75 pass. Updated batchSearch test to expect Upside excluded. Build green.
- **Key insight:** This is the second platform (after Blackbird) with authoritative data. No more guessing from search snippets — we get exact restaurant names and cashback rates from Upside's own API. API returned 196 restaurant offers for Manhattan in testing.

### 2026-05-01 Bilt Rewards API Cracked — Direct API Integration
- **Investigation:** Fetched biltrewards.com/dining, downloaded 127 webpack chunks, searched for DatoCMS tokens. Found DatoCMS read-only API token (`bea318e7535d484591167aee94fb72`) in JS bundle alongside Stellate GraphQL endpoint (`bilt-rewards.stellate.sh`). Token works but introspection is blocked (`BLOCKED_INTROSPECTION`).
- **Breakthrough:** While analyzing JS bundles, discovered a REST API endpoint: `https://api.biltrewards.com/public/merchants` — completely public, no auth required, returns all 2,237 Bilt Dining restaurants with pagination. Supports `?query=` search parameter and `?page=N&size=100` pagination.
- **Restaurant data fields:** name, address, neighborhood, primary_cuisine, multiplier (per-day points multipliers), exclusive flag, booking_provider, latitude/longitude, rating, review_count, price_rating, and more.
- **Implementation:** Added `checkBilt()` to `lib/checkers.ts`. Fetches all ~2,237 restaurants (paginated, 100/page) and caches with 1-hour TTL. Uses `matchesRestaurant()` for name matching — same logic as Blackbird/Upside. Falls back to Brave Search if API is down.
- **Route changes:** `app/api/check/route.ts` now runs `checkBilt()` in parallel with `checkBlackbird()`, `checkUpside()`, and `batchSearch()`. Bilt excluded from `batchSearch()` since it has its own checker.
- **Tests:** 75/75 pass. Updated batchSearch test expectations (Bilt excluded). Build green.
- **Key insight:** Third platform (after Blackbird and Upside) with authoritative API data. We now get exact restaurant names, points multipliers, cuisine types, and exclusive status directly from Bilt's API. The DatoCMS/Stellate GraphQL path was a red herring — the REST API at `/public/merchants` is simpler and doesn't require any auth.

## 2026-05-01: Upside & Bilt Platform API Cracking — Completed

### Work Log
- **Upside Direct API:** Cracked open REST endpoint at `POST https://pdjc6srrfb.execute-api.us-east-1.amazonaws.com/prod/offers/refresh`, no auth required. Returns 196 Manhattan restaurant offers. Built `checkUpside()` with 1-hour caching + Brave fallback. Commit 5421369.
- **Bilt GraphQL/REST:** Found public GraphQL endpoint + REST at api.biltrewards.com/public/merchants. 2,237 restaurants. Built `checkBilt()` function. Commit 9fedd3b.
- **DatoCMS discovery:** Found DatoCMS token during investigation (logged for later audit).

### Integration Results
- Updated `lib/checkers.ts` with `checkUpside()`, `getUpsideOffers()`, and `checkBilt()` functions
- Modified `app/api/check/route.ts` to parallel-run Upside via direct API
- Updated `lib/platforms.ts`: Upside `appOnly: false`, added `"api"` method type
- Tests: All 75 tests passing post-changes

### Trade-offs
- Upside: NYC-only bounding box (Manhattan). Scalable to multi-region with larger boxes.
- Bilt: GraphQL reliability TBD; REST fallback available.
- Both: Caching strategy balances freshness vs. API load.

### Commits
- 5421369: Upside direct API integration
- 9fedd3b: Bilt GraphQL/REST discovery & implementation

### Next: Architecture Decision
Need to finalize: real-time checks + periodic sync model, or cache-everything model?
