import { Platform, CheckResult, PLATFORMS } from "./platforms";
import { matchesRestaurant, slugVariants } from "./matching";

// --- In-memory cache ---
type CacheEntry<T> = { data: T; expiresAt: number };

const searchCache = new Map<string, CacheEntry<SearchResult[]>>();
const SEARCH_CACHE_TTL = 3_600_000; // 1 hour

let blackbirdSitemapCache: CacheEntry<string[]> | null = null;
const SITEMAP_CACHE_TTL = 300_000; // 5 minutes

function normalizeKey(restaurant: string, platform: string): string {
  return `${restaurant.toLowerCase().trim()}::${platform.toLowerCase().trim()}`;
}

function getSearchCache(key: string): SearchResult[] | null {
  const entry = searchCache.get(key);
  if (!entry) return null;
  if (Date.now() >= entry.expiresAt) {
    searchCache.delete(key);
    return null;
  }
  console.log(`[cache] HIT search: ${key}`);
  return entry.data;
}

function setSearchCache(key: string, data: SearchResult[]): void {
  searchCache.set(key, { data, expiresAt: Date.now() + SEARCH_CACHE_TTL });
}

async function getBlackbirdSpots(): Promise<string[]> {
  if (blackbirdSitemapCache && Date.now() < blackbirdSitemapCache.expiresAt) {
    console.log("[cache] HIT blackbird sitemap");
    return blackbirdSitemapCache.data;
  }
  console.log("[cache] MISS blackbird sitemap — fetching");
  const resp = await fetch("https://www.blackbird.xyz/sm.xml", {
    signal: AbortSignal.timeout(15000),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const xml = await resp.text();
  const spots = [
    ...xml.matchAll(
      /<loc>(https:\/\/www\.blackbird\.xyz\/spots\/[^<]+)<\/loc>/g
    ),
  ].map((m) => m[1]);
  blackbirdSitemapCache = { data: spots, expiresAt: Date.now() + SITEMAP_CACHE_TTL };
  return spots;
}

export async function checkBlackbird(name: string): Promise<CheckResult> {
  const platform = PLATFORMS.find((p) => p.name === "Blackbird")!;
  try {
    const spots = await getBlackbirdSpots();

    const found = spots.filter((url) => {
      const slug = url.split("/spots/")[1] ?? "";
      const slugText = slug.replace(/-/g, " ");
      if (matchesRestaurant(slugText, name)) return true;
      // Also check slug variants of the restaurant name against the raw URL slug
      const variants = slugVariants(name);
      return variants.some((v) => slug === v);
    });

    if (found.length > 0) {
      return {
        platform: "Blackbird",
        found: true,
        details: `Found ${found.length} match(es) in sitemap`,
        method: "sitemap",
        url: found[0],
        matches: found,
      };
    }
    return {
      platform: "Blackbird",
      found: false,
      details: `Not in sitemap (${spots.length} restaurants checked)`,
      method: "sitemap",
      url: platform.url,
      matches: [],
    };
  } catch (e) {
    console.error('[blackbird]', e);
    return {
      platform: "Blackbird",
      found: false,
      details: `Sitemap error: ${e instanceof Error ? e.message : "unknown"}`,
      method: "error",
      url: platform.url,
      matches: [],
    };
  }
}

type SearchResult = { title: string; href: string; snippet: string };
type SearchResponse = {
  results: SearchResult[];
  blocked: boolean;
};

// Search via Google Custom Search JSON API (100 free queries/day)
async function googleCSESearch(query: string): Promise<SearchResult[]> {
  const apiKey = process.env.GOOGLE_CSE_API_KEY;
  const cx = process.env.GOOGLE_CSE_ID;

  if (!apiKey || apiKey === "your_api_key_here") {
    throw new Error("GOOGLE_CSE_API_KEY not configured");
  }
  if (!cx || cx === "your_cse_id_here") {
    throw new Error("GOOGLE_CSE_ID not configured");
  }

  const params = new URLSearchParams({
    key: apiKey,
    cx,
    q: query,
    num: "10",
  });

  const resp = await fetch(
    `https://www.googleapis.com/customsearch/v1?${params}`,
    { signal: AbortSignal.timeout(10000) }
  );

  if (!resp.ok) {
    // Parse error body for actionable diagnostics
    let reason = "";
    try {
      const errBody = await resp.json();
      reason = errBody?.error?.message || errBody?.error?.status || "";
    } catch { /* ignore parse failure */ }

    if (resp.status === 403) {
      if (reason.toLowerCase().includes("quota") || reason.toLowerCase().includes("limit")) {
        console.error(`[google-cse] QUOTA EXHAUSTED (403): ${reason} | query: ${query}`);
        throw new Error("Google CSE quota exhausted");
      }
      console.error(`[google-cse] PERMISSION DENIED (403): ${reason} | query: ${query}`);
      throw new Error(`Google CSE permission denied: ${reason}`);
    }
    if (resp.status === 429) {
      console.error(`[google-cse] RATE LIMITED (429): ${reason} | query: ${query}`);
      throw new Error("Google CSE rate limited");
    }
    console.error(`[google-cse] HTTP ${resp.status}: ${reason} | query: ${query}`);
    throw new Error(`Google CSE HTTP ${resp.status}: ${reason}`);
  }

  const data = await resp.json();
  const items: Array<{ title?: string; link?: string; snippet?: string }> =
    data.items || [];

  return items.map((r) => ({
    title: r.title ?? "",
    href: r.link ?? "",
    snippet: r.snippet ?? "",
  }));
}

// Batch search: runs all non-Blackbird queries via Google CSE in parallel
export async function batchSearch(
  name: string
): Promise<Map<string, SearchResponse>> {
  const nonBlackbird = PLATFORMS.filter((p) => p.name !== "Blackbird");
  const resultMap = new Map<string, SearchResponse>();

  // Initialize all as blocked (fallback)
  for (const p of nonBlackbird) {
    resultMap.set(p.name, { results: [], blocked: true });
  }

  // Run all searches in parallel, using cache when available
  // Fallback strategy: if site:-scoped query fails, retry with the original format
  const searchPromises = nonBlackbird.map(async (platform) => {
    const cacheKey = normalizeKey(name, platform.name);
    const cached = getSearchCache(cacheKey);
    if (cached !== null) {
      return { platform: platform.name, results: cached, blocked: false };
    }

    console.log(`[cache] MISS search: ${cacheKey}`);
    const siteOp = platform.domainFilter ? ` site:${platform.domainFilter}` : "";
    const baseQuery = platform.searchQuery
      ? `"${name}" ${platform.searchQuery}`
      : `"${name}"`;
    const query = `${baseQuery}${siteOp}`;

    try {
      const results = await googleCSESearch(query);
      setSearchCache(cacheKey, results);
      return { platform: platform.name, results, blocked: false };
    } catch (error) {
      // Fallback: retry without site: operator if one was used
      if (siteOp) {
        console.warn(`[google-cse] Retrying ${platform.name} without site: operator`);
        try {
          const fallbackResults = await googleCSESearch(baseQuery);
          setSearchCache(cacheKey, fallbackResults);
          return { platform: platform.name, results: fallbackResults, blocked: false };
        } catch (fallbackError) {
          console.error('[google-cse]', platform.name, 'fallback also failed:', fallbackError);
          return { platform: platform.name, results: [] as SearchResult[], blocked: true };
        }
      }
      console.error('[google-cse]', platform.name, error);
      return { platform: platform.name, results: [] as SearchResult[], blocked: true };
    }
  });

  const searchResults = await Promise.all(searchPromises);

  for (const sr of searchResults) {
    resultMap.set(sr.platform, {
      results: sr.results,
      blocked: sr.blocked,
    });
  }

  return resultMap;
}

// Convert raw search results into a CheckResult for a platform
export function evaluateSearchResults(
  platform: Platform,
  name: string,
  search: SearchResponse
): CheckResult {
  if (search.blocked) {
    return {
      platform: platform.name,
      found: false,
      details: platform.appOnly
        ? "Search unavailable — check the app directly"
        : "Search unavailable — check the platform directly",
      method: "error",
      url: platform.url,
      matches: [],
      searchUnavailable: true,
    };
  }

  for (const r of search.results) {
    if (
      platform.domainFilter &&
      !r.href.toLowerCase().includes(platform.domainFilter)
    ) {
      continue;
    }
    // Skip generic blog/help pages that mention restaurant names incidentally
    const lowerHref = r.href.toLowerCase();
    if (
      lowerHref.includes("/blog/") ||
      lowerHref.includes("/retailer-blog/") ||
      lowerHref.includes("/help/") ||
      lowerHref.includes("/faq/") ||
      lowerHref.includes("/hc/en-us/")
    ) {
      continue;
    }
    if (matchesRestaurant(`${r.title} ${r.snippet} ${r.href}`, name)) {
      return {
        platform: platform.name,
        found: true,
        details: r.title || `Found on ${platform.name}`,
        method: "web_search",
        url: r.href.startsWith("http") ? r.href : `https://${r.href}`,
        matches: [],
      };
    }
  }

  if (platform.appOnly) {
    return {
      platform: platform.name,
      found: false,
      details: "Not indexed on the web — check the app to verify",
      method: "web_search",
      url: platform.url,
      matches: [],
      searchUnavailable: true,
    };
  }

  return {
    platform: platform.name,
    found: false,
    details: "Not found via web search",
    method: "web_search",
    url: platform.url,
    matches: [],
  };
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
