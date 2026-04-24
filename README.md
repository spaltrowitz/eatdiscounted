# Restaurant Discount Checker 🍽️

Check which dining discount platforms list a given restaurant — from the command line.

## Platforms Checked

| Platform | Method | Coverage |
|----------|--------|----------|
| **Blackbird** | Sitemap parsing | ✅ Complete — checks all listed restaurants |
| **inKind** | Subdomain check + web search | ⚠️ Partial — subdomain format varies |
| **Upside** | Web search | ⚠️ Limited — app-only, search may miss listings |
| **Seated** | Web search | ⚠️ Limited — app-only, search may miss listings |
| **Nea** | Web search | ⚠️ Limited — app-only, NYC only |

## Setup

```bash
# Clone the repo
git clone https://github.com/spaltrowitz/restaurant-checker.git
cd restaurant-checker

# Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Playwright browser (one-time, used for search fallback)
playwright install chromium
```

## Usage

```bash
python restaurant_checker.py "Carbone"
python restaurant_checker.py "Oxomoco"
python restaurant_checker.py "The Smith"
```

### Example Output

```
🍽️  Checking platforms for: "Oxomoco"

============================================================

  ✅  Blackbird    [📄 sitemap]
      Found 1 match(es) in Blackbird sitemap
      → https://www.blackbird.xyz/spots/oxomoco-greenpoint

  ❌  inKind       [🔍 search]
      Not found via web search
      → https://inkind.com/#explore-restaurants

  ❌  Upside       [🔍 search]
      Not found via web search (app-only — check the app for full results)
      → https://www.upside.com/find-offers

  ❌  Seated       [🔍 search]
      Not found via web search (app-only — check the app for full results)
      → https://seatedapp.io

  ❌  Nea          [🔍 search]
      Not found via web search (app-only, NYC only — check the app)
      → https://neaapp.ai

============================================================

✨ "Oxomoco" found on: Blackbird

📱 App-only platforms (check manually for best results):
   • Upside: https://www.upside.com/find-offers
   • Seated: https://seatedapp.io
   • Nea: https://neaapp.ai
```

## How It Works

### Blackbird (most reliable)
Parses Blackbird's **public sitemap** (`sm.xml`) which lists all partner restaurants as `/spots/{name}` URLs. This is fast, reliable, and gives 100% coverage of their listed restaurants.

### inKind
Checks if the restaurant has a subdomain on `inkind.com` (e.g., `restaurantname.inkind.com`). Falls back to DuckDuckGo web search.

### Upside, Seated, Nea
These platforms are **app-only** with no public restaurant directory. The tool searches DuckDuckGo for indexed mentions, but results are limited. For the most accurate results, check these apps directly:
- **Upside**: [upside.com/find-offers](https://www.upside.com/find-offers)
- **Seated**: [seatedapp.io](https://seatedapp.io)
- **Nea**: [neaapp.ai](https://neaapp.ai) (NYC only)

## Compliance & Safety

This tool is designed to be **completely safe** and **ToS-compliant**:

- ✅ **Blackbird**: Uses their published sitemap — explicitly provided for crawlers
- ✅ **inKind**: Checks publicly accessible subdomains (standard HTTP requests)
- ✅ **Search**: Uses DuckDuckGo, a public search engine
- ✅ **Rate limiting**: 2-second delay between platform checks
- ✅ **robots.txt**: All platforms allow access to the pages we check
- ❌ No private or undocumented APIs
- ❌ No mobile app traffic interception
- ❌ No authentication bypass
- ❌ No scraping of protected content

**For personal use only.** Do not use for commercial data aggregation.

## Limitations

- **App-only platforms** (Upside, Seated, Nea): Web search coverage is limited. Many restaurants listed in these apps won't be found via web search because the data lives only inside the mobile app.
- **inKind subdomains**: The URL slug format is unpredictable (e.g., "Carbone" might be at `carbonevino.inkind.com`), so direct subdomain checks may miss valid restaurants.
- **Search rate limiting**: DuckDuckGo may rate-limit requests if you run many searches in quick succession.

## Future Improvements

- Add more platforms (Resy, OpenTable rewards, etc.)
- Cache sitemap data to avoid re-fetching
- Add batch mode for checking multiple restaurants
- Build a simple web UI
