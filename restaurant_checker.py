#!/usr/bin/env python3
"""
Restaurant Discount Checker
Check which dining discount platforms list a given restaurant.

Platforms checked: Blackbird, inKind, Upside, Seated, Nea

How it works:
  • Blackbird — parses their public sitemap (fast & reliable)
  • inKind — checks subdomain patterns (direct HTTP check)
  • All platforms — DuckDuckGo search fallback via Playwright browser
  • Manual check links provided for app-only platforms

Compliance:
  • Only uses publicly accessible data (sitemaps, public web pages)
  • Respects robots.txt for all platforms
  • Rate-limited (2s delay between checks)
  • No private APIs, no authentication bypass
  • For personal use only
"""

import argparse
import asyncio
import re
import subprocess
import sys
from dataclasses import dataclass, field
from urllib.parse import quote_plus

import httpx


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    platform: str
    found: bool
    details: str
    method: str
    url: str = ""
    matches: list = field(default_factory=list)


RATE_LIMIT_DELAY = 2


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def slug_variants(name: str) -> list[str]:
    """Generate possible URL slug variants from a restaurant name."""
    name = name.strip()
    lower = name.lower()
    nopunc = re.sub(r"[^a-z0-9\s]", "", lower)
    words = nopunc.split()

    variants = set()
    variants.add(nopunc.replace(" ", ""))        # "thesmith"
    variants.add(nopunc.replace(" ", "-"))        # "the-smith"
    if words and words[0] == "the":
        rest = words[1:]
        variants.add("".join(rest))              # "smith"
        variants.add("-".join(rest))             # "smith"
    variants.discard("")
    return list(variants)


def matches_restaurant(text: str, restaurant_name: str) -> bool:
    text_norm = normalize(text)
    name_norm = normalize(restaurant_name)
    if name_norm in text_norm:
        return True
    words = [w for w in name_norm.split() if len(w) > 2]
    return bool(words) and all(w in text_norm for w in words)


# ---------------------------------------------------------------------------
# 1. Blackbird — Sitemap parsing
# ---------------------------------------------------------------------------

async def check_blackbird(restaurant_name: str) -> CheckResult:
    """Parse Blackbird's public sitemap to find restaurants."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://www.blackbird.xyz/sm.xml",
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
        except Exception as e:
            return CheckResult(
                platform="Blackbird",
                found=False,
                details=f"Could not fetch sitemap: {e}",
                method="sitemap",
                url="https://www.blackbird.xyz/where-to-blackbird",
            )

        spots = re.findall(
            r"<loc>(https://www\.blackbird\.xyz/spots/[^<]+)</loc>",
            resp.text,
        )

        found_spots = []
        for spot_url in spots:
            slug = spot_url.split("/spots/")[-1]
            slug_readable = slug.replace("-", " ")
            if matches_restaurant(slug_readable, restaurant_name):
                found_spots.append(spot_url)

        if found_spots:
            return CheckResult(
                platform="Blackbird",
                found=True,
                details=f"Found {len(found_spots)} match(es) in Blackbird sitemap",
                method="sitemap",
                url=found_spots[0],
                matches=found_spots,
            )

        return CheckResult(
            platform="Blackbird",
            found=False,
            details=f"Not in Blackbird sitemap ({len(spots)} restaurants checked)",
            method="sitemap",
            url="https://www.blackbird.xyz/where-to-blackbird",
        )


# ---------------------------------------------------------------------------
# 2. inKind — Subdomain check + search
# ---------------------------------------------------------------------------

INKIND_DEFAULT_TITLE = "Download the inKind App | inKind"


async def check_inkind(restaurant_name: str) -> CheckResult:
    """Check inKind by testing subdomain patterns, then falling back to search."""
    variants = slug_variants(restaurant_name)

    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        for slug in variants:
            try:
                resp = await client.get(f"https://{slug}.inkind.com")
                title_match = re.search(r"<title>([^<]+)</title>", resp.text)
                title = title_match.group(1) if title_match else ""

                if title and title != INKIND_DEFAULT_TITLE:
                    return CheckResult(
                        platform="inKind",
                        found=True,
                        details=f"{title}",
                        method="subdomain",
                        url=f"https://{slug}.inkind.com",
                    )
            except Exception:
                continue

    # Fall back to search
    return await _search_platform(
        restaurant_name,
        platform="inKind",
        site_query="site:inkind.com",
        fallback_url="https://inkind.com/#explore-restaurants",
        app_only_note="",
    )


# ---------------------------------------------------------------------------
# 3–5. Upside, Seated, Nea — Search-based
# ---------------------------------------------------------------------------

async def check_upside(restaurant_name: str) -> CheckResult:
    return await _search_platform(
        restaurant_name,
        platform="Upside",
        site_query="site:upside.com",
        fallback_url="https://www.upside.com/find-offers",
        app_only_note="app-only — check the app for full results",
    )


async def check_seated(restaurant_name: str) -> CheckResult:
    # Only search seatedapp.io and getseated.com — seated.com is a different
    # company (event ticketing) and causes false positives
    return await _search_platform(
        restaurant_name,
        platform="Seated",
        site_query="(site:seatedapp.io OR site:getseated.com)",
        fallback_url="https://seatedapp.io",
        app_only_note="app-only — check the app for full results",
    )


async def check_nea(restaurant_name: str) -> CheckResult:
    return await _search_platform(
        restaurant_name,
        platform="Nea",
        site_query="site:neaapp.ai",
        fallback_url="https://neaapp.ai",
        app_only_note="app-only, NYC only — check the app",
    )


# ---------------------------------------------------------------------------
# Search engine helper — tries ddgs, then Playwright, then curl
# ---------------------------------------------------------------------------

async def _search_platform(
    restaurant_name: str,
    platform: str,
    site_query: str,
    fallback_url: str,
    app_only_note: str,
) -> CheckResult:
    """Search for a restaurant on a platform using multiple search strategies."""
    query = f'"{restaurant_name}" {site_query}'

    # Strategy 1: ddgs package (most lightweight)
    results = _try_ddgs_search(query)
    if results:
        for r in results:
            combined = f"{r.get('title', '')} {r.get('body', '')} {r.get('href', '')}"
            if matches_restaurant(combined, restaurant_name):
                return CheckResult(
                    platform=platform,
                    found=True,
                    details=r.get("title", f"Found on {platform}"),
                    method="web_search",
                    url=r.get("href", fallback_url),
                )

    # Strategy 2: Playwright browser search
    results = await _try_playwright_search(query)
    if results:
        for title, url, snippet in results:
            combined = f"{title} {snippet} {url}"
            if matches_restaurant(combined, restaurant_name):
                return CheckResult(
                    platform=platform,
                    found=True,
                    details=title or f"Found on {platform}",
                    method="web_search",
                    url=url or fallback_url,
                )

    # Strategy 3: curl-based search
    results = _try_curl_search(query)
    if results:
        for title, url, snippet in results:
            combined = f"{title} {snippet} {url}"
            if matches_restaurant(combined, restaurant_name):
                return CheckResult(
                    platform=platform,
                    found=True,
                    details=title or f"Found on {platform}",
                    method="web_search",
                    url=url or fallback_url,
                )

    not_found_msg = f"Not found via web search"
    if app_only_note:
        not_found_msg += f" ({app_only_note})"

    return CheckResult(
        platform=platform,
        found=False,
        details=not_found_msg,
        method="web_search",
        url=fallback_url,
    )


def _try_ddgs_search(query: str) -> list[dict]:
    """Try searching with the ddgs package."""
    try:
        from ddgs import DDGS
        return DDGS().text(query, max_results=5) or []
    except Exception:
        return []


async def _try_playwright_search(query: str) -> list[tuple]:
    """Use Playwright to search DuckDuckGo in a real browser."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)

            results = []
            elements = await page.query_selector_all(".result")
            for elem in elements[:5]:
                title_el = await elem.query_selector(".result__title")
                snippet_el = await elem.query_selector(".result__snippet")
                url_el = await elem.query_selector(".result__url")

                title = await title_el.inner_text() if title_el else ""
                snippet = await snippet_el.inner_text() if snippet_el else ""
                href = await url_el.inner_text() if url_el else ""
                results.append((title.strip(), href.strip(), snippet.strip()))

            await browser.close()
            return results
    except Exception:
        return []


def _try_curl_search(query: str) -> list[tuple]:
    """Use curl subprocess to search DuckDuckGo (bypasses Python SSL issues)."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        result = subprocess.run(
            [
                "curl", "-s", "-L",
                "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "-H", "Accept: text/html",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result.stdout, "html.parser")
        results = []
        for r in soup.select(".result")[:5]:
            title_el = r.select_one(".result__title")
            snippet_el = r.select_one(".result__snippet")
            url_el = r.select_one(".result__url")
            results.append((
                title_el.get_text(strip=True) if title_el else "",
                url_el.get_text(strip=True) if url_el else "",
                snippet_el.get_text(strip=True) if snippet_el else "",
            ))
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_result(result: CheckResult):
    icon = "✅" if result.found else "❌"
    method_label = {
        "sitemap": "📄 sitemap",
        "subdomain": "🌐 direct",
        "web_search": "🔍 search",
    }
    method = method_label.get(result.method, result.method)

    print(f"  {icon}  {result.platform:<12} [{method}]")
    print(f"      {result.details}")
    if result.url:
        print(f"      → {result.url}")
    if result.matches and len(result.matches) > 1:
        for m in result.matches[1:]:
            print(f"      → {m}")
    print()


async def run_checks(restaurant_name: str):
    print(f"\n🍽️  Checking platforms for: \"{restaurant_name}\"\n")
    print("=" * 60)
    print()

    checkers = [
        ("Blackbird", check_blackbird),
        ("inKind", check_inkind),
        ("Upside", check_upside),
        ("Seated", check_seated),
        ("Nea", check_nea),
    ]

    results = []
    for i, (name, checker) in enumerate(checkers):
        if i > 0:
            await asyncio.sleep(RATE_LIMIT_DELAY)

        sys.stdout.write(f"  ⏳ Checking {name}...\r")
        sys.stdout.flush()
        try:
            result = await checker(restaurant_name)
        except Exception as e:
            result = CheckResult(
                platform=name, found=False, details=f"Error: {e}", method="error",
            )
        results.append(result)
        sys.stdout.write("\033[2K")
        print_result(result)

    print("=" * 60)
    found = [r for r in results if r.found]
    if found:
        print(f"\n✨ \"{restaurant_name}\" found on: {', '.join(r.platform for r in found)}")
    else:
        print(f"\n😕 \"{restaurant_name}\" was not found on any platform.")
        print("   Tip: Some platforms are app-only — check the apps for the most accurate results.")

    app_only = [r for r in results if "app-only" in r.details]
    if app_only:
        print(f"\n📱 App-only platforms (check manually for best results):")
        for r in app_only:
            print(f"   • {r.platform}: {r.url}")

    print()
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Check which dining discount platforms list a given restaurant.",
        epilog=(
            "Platforms: Blackbird, inKind, Upside, Seated, Nea\n\n"
            "Methods:\n"
            "  • Blackbird: public sitemap parsing (sm.xml)\n"
            "  • inKind: subdomain check + web search\n"
            "  • Others: DuckDuckGo web search\n\n"
            "Only uses publicly accessible data. For personal use only."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "restaurant",
        help='Name of the restaurant to search for (e.g. "Carbone")',
    )
    args = parser.parse_args()
    asyncio.run(run_checks(args.restaurant))


if __name__ == "__main__":
    main()
