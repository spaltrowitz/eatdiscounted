# Project Context

- **Owner:** Shari Paltrowitz
- **Project:** EatDiscounted — a Next.js web app that checks 8 dining discount platforms for any restaurant name. SSE streaming results. Aggregating deals across Blackbird, inKind, Bilt, Rakuten Dining, Too Good To Go, and more.
- **Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, better-sqlite3, SSE streaming
- **Created:** 2026-04-30

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-04-30 — Product Strategy Review (Beli lens)
- Completed product-market fit, retention, growth, and monetization analysis.
- Biggest risk: Single-use retention problem. Users search once and leave.
- P0 recommendation: Restaurant permalink pages for SEO + shareability.
- P1: Saved restaurants + alerts (converts lookup tool to monitoring tool).
- Bold bet: Deals-Near-Me location-based discovery (10x product potential).
- Monetization: Affiliate links first (Blackbird, inKind, Bilt referral programs). Passive, validates signal.
- Audience: ~30-50K NYC power users on 3+ platforms. Growth via food Twitter/Reddit, not paid ads.

### 2026-04-30 — Partnership Outreach Strategy (App-Only Platforms)
- **Problem:** 3 app-only platforms (Nea, Seated, Upside) inaccessible via web search—no public listings APIs.
- **Solution:** B2B partnership pitch: offer free user acquisition + discovery channel in exchange for read-only API or data feed access.
- **Value prop:** Each platform gets incremental bookings from diner discovery. We get complete platform coverage. Win-win.
- **Contact strategy:** LinkedIn-first for app-stage companies (Nea, Seated). Formal BD outreach for Series B+ (Upside).
- **Integration options:** REST API (preferred), daily JSON feed, or webhook. 2-3 week implementation timeline.
- **Positioning:** EatDiscounted as meta-search engine for dining discounts—free distribution channel, not competitor.

## 2026-05-01: Partnership Outreach Strategy — Completed

### Deliverable
Drafted comprehensive partnership pitch for Nea, Seated, and Upside platforms. Document: `./partnership-pitch.md`

### Pitch Components
1. **One-pager:** Value proposition (user traffic, discovery potential, affiliate revenue sharing)
2. **Platform-specific notes:** 
   - Nea: B2B restaurant SaaS angle; offer co-marketing
   - Seated: Existing web presence; offer feature integration
   - Upside: Direct API already public; offer official partnership + higher priority support
3. **Email templates:** Personalized outreach for BD/partnerships team
4. **Next steps:** Follow-up sequencing, FAQ responses, pilot program framework

### Business Case
- **For EatDiscounted:** Access to app-only platforms (Nea, Seated) enables full coverage
- **For platforms:** Qualified restaurant traffic, user behavior signals, potential affiliate revenue
- **Win-win:** Seated/Nea gain web discoverability; EatDiscounted gains authoritative data

### Action Items
- [ ] Prioritize outreach: Nea (highest value per Redfoot audit) → Seated → Upside (confirmatory)
- [ ] Assign outreach lead (likely PM with platform contacts)
- [ ] Prepare for common objections (privacy, API load, attribution)
- [ ] Design affiliate revenue model (if accepted)

### Status
Ready for partnership outreach. Pending PM decision on priority sequencing.
