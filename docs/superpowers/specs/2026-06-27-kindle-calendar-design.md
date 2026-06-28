# Kindle Calendar — Design Spec
**Date:** 2026-06-27

## Overview

A single-page web dashboard optimized for landscape-mode old Kindle browsers (Kindle 3/4, WebKit-based). Displays a live digital clock, today's date, WDAY stock price, and a 7-day weather forecast for Burnaby, BC. Hosted on GitHub Pages. Data refreshed once daily via GitHub Actions.

---

## Architecture

```
kindle-calendar/
├── index.html          # Single HTML file — all CSS and JS inline
├── data.json           # Written daily by GitHub Actions (stock + weather)
└── .github/
    └── workflows/
        └── fetch-data.yml   # Scheduled workflow: runs daily at 6am PST
```

- **No build step, no framework, no external dependencies at runtime**
- `index.html` fetches `data.json` (same-origin, no CORS issues) on page load
- GitHub Actions fetches WDAY from Yahoo Finance (unofficial JSON endpoint, no key needed) and weather from Open-Meteo (free, no key needed), then writes `data.json` and commits it

---

## Layout

Fixed landscape layout, table-based for old WebKit compatibility.

```
┌─────────────────────────────────────────────────────────┐
│  Friday, June 27, 2025          08:42:17 AM             │  ← top bar (black bg)
├──────────────────┬──────────────────────────────────────┤
│  WDAY            │  7-Day Forecast — Burnaby, BC         │
│  $234.56         │  Fri   Sat   Sun   Mon   Tue   Wed   Thu │
│  ▲ +3.21 (+1.4%) │  ⛅    ☀    ☁    🌧    🌧    ⛅    ☀  │
│  Open: $231.80   │  22°  25°  19°  16°  17°  20°  24°  │
│  Prev: $231.35   │  13°  14°  12°  11°  12°  13°  14°  │
│  Updated 6am PST │                    Burnaby, BC | °C  │
└──────────────────┴──────────────────────────────────────┘
```

**Top bar:** Full-width, black background, white text. Date left-aligned, clock right-aligned.

**Bottom-left (stock panel, ~220px wide):** Light grey background. Ticker, price (large), change with up/down arrow, open price, previous close, last-updated note.

**Bottom-right (weather panel, remaining width):** 7 columns (one per day). Today's column highlighted with black background. Each column: day name, date, emoji weather icon, description, high temp, low temp.

---

## Kindle Browser Compatibility

- **Layout:** HTML `<table>` elements only — no CSS flex or grid (unreliable on old WebKit)
- **CSS:** Inline styles and a single `<style>` block — no external stylesheets
- **JS:** ES3-compatible vanilla JS (`var`, no arrow functions, no template literals, no `fetch` — use `XMLHttpRequest`)
- **Fonts:** System serif only (`Georgia, "Times New Roman", serif`) and monospace (`"Courier New", monospace`) — no web fonts
- **Icons:** Unicode emoji characters — no SVG, no `<img>` tags for icons
- **Viewport:** `<meta name="viewport" content="width=800, initial-scale=1.0">`
- **Address bar hiding:** `window.scrollTo(0, 1)` on page load to nudge bar away
- **Dynamic height:** `window.innerHeight` used in JS to size the bottom content area so it fills exactly the visible viewport, compensating for browser chrome

---

## Clock

- Rendered in the top bar, right side
- Updated every second via `setInterval(tick, 1000)`
- Format: `HH:MM:SS AM/PM`
- Uses `new Date()` — shows local device time (Kindle's local time)
- ES3-safe: `var`, `function`, string concatenation, no template literals

---

## Data: `data.json`

Schema written by GitHub Actions daily:

```json
{
  "stock": {
    "ticker": "WDAY",
    "price": 234.56,
    "change": 3.21,
    "change_pct": 1.39,
    "open": 231.80,
    "prev_close": 231.35,
    "updated": "2026-06-27T14:00:00Z"
  },
  "weather": {
    "location": "Burnaby, BC",
    "days": [
      {
        "date": "2026-06-27",
        "day_name": "Fri",
        "icon": "⛅",
        "description": "Partly Cloudy",
        "high_c": 22,
        "low_c": 13
      }
      // ... 6 more days
    ]
  },
  "generated_at": "2026-06-27T14:00:00Z"
}
```

---

## GitHub Actions Workflow

**File:** `.github/workflows/fetch-data.yml`

**Schedule:** Daily at 14:00 UTC (6:00 AM PST / 7:00 AM PDT)

**Steps:**
1. Checkout repo
2. Run Python script (`scripts/fetch_data.py`) that:
   - Fetches WDAY quote from Yahoo Finance unofficial endpoint
   - Fetches 7-day forecast for Burnaby (lat 49.2488, lon -122.9805) from Open-Meteo API
   - Maps WMO weather codes to emoji icons and descriptions
   - Writes `data.json` to repo root
3. Commit and push `data.json` if changed

**Fallback:** If fetch fails, existing `data.json` is left unchanged — page shows stale data with the `updated` timestamp so user knows it's old.

---

## GitHub Pages Setup

- Repository: public GitHub repo (e.g. `kindle-calendar`)
- Pages source: `main` branch, root `/`
- `index.html` + `data.json` served directly — no Jekyll, no build

---

## Error Handling

- **`data.json` missing:** Page shows "Data unavailable" in stock/weather panels — no JS crash
- **Stale data:** `updated` timestamp shown in stock panel so user can see age of data
- **Clock failure:** Extremely unlikely — just `new Date()` and DOM write

---

## Out of Scope

- Multiple stock tickers
- Push notifications or auto-refresh (Kindle browser is not left open like a phone)
- User settings / configuration UI
- Mobile portrait mode
- Dark mode toggle
