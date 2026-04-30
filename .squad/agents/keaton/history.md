# Project Context

- **Owner:** Shari Paltrowitz
- **Project:** EatDiscounted — a Next.js web app that checks 8 dining discount platforms for any restaurant name. Results stream via SSE. Also has a Python CLI.
- **Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, better-sqlite3, SSE streaming, Python CLI
- **Created:** 2026-04-30

## Session: 2026-04-30 — Ship-Readiness Evaluation

**Role:** Lead — Architecture & ship-readiness assessment  
**Participants:** Keaton, Hockney, Fenster, McManus  
**Outcome:** 🟡 Ship with caveats — not ready for broad shipping, ready in 2-3 sprint days

**Key findings:**
- Architecture is clean, well-typed, good separation of concerns ✅
- Dependencies are minimal (3 runtime), current, no bloat ✅
- **Security gap:** No rate limiting on `/api/check` endpoint (critical blocker)
- **Build:** Compiles cleanly but has 6 lint errors; no deployment config exists
- **Must-fix:** Rate limiting, Google CSE quota strategy, lint errors
- **Deployment decision required:** Vercel (complex) vs. VPS (simpler)

**Cross-team observations:**
- Frontend needs accessibility fixes (no ARIA attributes found)
- Backend needs response caching (multiplies capacity 10-50x)
- No tests exist; critical logic verified only by manual clicking
- Unicode normalization bug produces false positives/negatives
- Google CSE quota (100/day = ~14 searches) is hard ceiling

**Estimated ship timeline:** 2-3 focused days after critical fixes.

---

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->
