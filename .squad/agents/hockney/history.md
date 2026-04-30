# Project Context

- **Owner:** Shari Paltrowitz
- **Project:** EatDiscounted — a Next.js web app that checks 8 dining discount platforms for any restaurant name. Results stream via SSE. Also has a Python CLI.
- **Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, better-sqlite3, SSE streaming, Python CLI
- **Created:** 2026-04-30

## Session: 2026-04-30 — Ship-Readiness Evaluation

**Role:** Frontend Dev — Frontend/UI quality & UX review  
**Participants:** Keaton, Hockney, Fenster, McManus  
**Outcome:** 🟡 Ship with caveats — bones are great, fix accessibility & error handling

**Frontend audit findings:**
- Component quality is excellent: clean decomposition, proper TypeScript, smart Suspense ✅
- **Accessibility is 🔴 critical gap:** Zero ARIA attributes across codebase
  - Search input has no aria-label (screen reader announces "unlabeled text field")
  - Results region has no aria-live (screen readers don't know content is updating)
  - Status icons are emoji-only with no text alternatives
  - No skip-to-content link
- **Error handling is broken:** Frontend has `catch {}` empty blocks; errors silently swallowed
- **SSE consumer bug:** No AbortController; concurrent searches leak connections
- **UX flow:** Intuitive and thoughtful (zero-friction popular searches, conflict warnings, community reporting)
- **Responsive design:** Works to 768px; phone-like on large screens; no explicit breakpoints

**Must-fix before shipping:**
1. aria-label on search input (5 min, massive a11y impact)
2. aria-live="polite" on results region + error state UI
3. AbortController on SSE fetch (real bug: connection leaks)
4. Error message when search fails (users currently see nothing)

**Nice-to-have:** OG/Twitter meta tags (critical for sharing), focus styles, viewport meta export.

---

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->
