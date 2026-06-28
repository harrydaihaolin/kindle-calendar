# Kindle Calendar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-page Kindle dashboard on GitHub Pages showing a live clock, WDAY stock, and 7-day Burnaby BC weather, refreshed daily by GitHub Actions.

**Architecture:** A single `index.html` with all CSS/JS inline fetches `data.json` via XHR on page load. Table-based layout and ES3-safe JS ensure old Kindle WebKit compatibility. GitHub Actions runs a Python script daily at 14:00 UTC to fetch stock (Yahoo Finance) and weather (Open-Meteo), then commits updated `data.json` to main.

**Tech Stack:** HTML/CSS/ES3 JS (no framework), Python 3 + requests, GitHub Actions, GitHub Pages.

## Global Constraints

- ES3-safe JS only: `var`, no arrow functions, no template literals, no `const`/`let`, no `fetch()` — use `XMLHttpRequest`
- Table-based HTML layout only — no CSS flex or grid
- System fonts only: `Georgia, "Times New Roman", serif` and `"Courier New", monospace`
- Unicode emoji for weather icons — no SVG, no `<img>` tags for icons
- Viewport meta: `content="width=800, initial-scale=1.0"`
- Address bar hide: `window.scrollTo(0, 1)` fired 300ms after `window.onload`
- Dynamic height: `window.innerHeight` used to size `#bottom-table`, `#stock-td`, `#weather-td`
- `data.json` written with `ensure_ascii=False` to preserve emoji
- GitHub Actions commits use `[skip ci]` in message to prevent workflow loops
- GitHub Pages: main branch, root `/`
- Python script writes `data.json` relative to repo root, not script directory

---

## File Map

| File | Role |
|------|------|
| `index.html` | Dashboard — all CSS and JS inline |
| `data.json` | Seed + daily-updated stock and weather |
| `scripts/fetch_data.py` | Fetches stock + weather, writes `data.json` |
| `scripts/__init__.py` | Empty — makes `scripts` importable for tests |
| `tests/test_fetch_data.py` | Pytest unit tests for helper functions |
| `.github/workflows/fetch-data.yml` | Scheduled daily fetch workflow |
| `.gitignore` | Ignores `__pycache__`, `.pytest_cache`, `.DS_Store` |

---

### Task 1: Initialize repo and push to GitHub

**Files:**
- Create: `.gitignore`

**Interfaces:**
- Produces: git repo with `origin` remote pointing at GitHub, design spec committed

- [ ] **Step 1: Initialize git repo**

```bash
cd /Users/adminaccount/Documents/kindle-calendar
git init
git branch -M main
```

Expected: `Initialized empty Git repository in .../kindle-calendar/.git/`

- [ ] **Step 2: Create .gitignore**

Create `.gitignore`:

```
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
```

- [ ] **Step 3: Create GitHub repo and push**

```bash
gh repo create kindle-calendar --public --source=. --remote=origin --push
```

If the repo already exists on GitHub:
```bash
OWNER=$(gh api user --jq .login)
git remote add origin https://github.com/${OWNER}/kindle-calendar.git
git add .gitignore docs/
git commit -m "chore: init repo with design spec"
git push -u origin main
```

Expected: repo visible at `https://github.com/<owner>/kindle-calendar`

- [ ] **Step 4: Enable GitHub Pages**

```bash
OWNER=$(gh api user --jq .login)
gh api "repos/${OWNER}/kindle-calendar/pages" \
  --method POST \
  --input - <<'EOF'
{"source":{"branch":"main","path":"/"}}
EOF
```

If that fails (e.g. Pages already enabled or API error), go to:
`https://github.com/<owner>/kindle-calendar/settings/pages` → Source: Deploy from branch → Branch: main → Folder: / (root) → Save.

---

### Task 2: Build index.html

**Files:**
- Create: `index.html`

**Interfaces:**
- Consumes: `data.json` via same-origin XHR (`GET data.json`)
- Produces: rendered dashboard — live clock in top bar, stock panel bottom-left, weather panel bottom-right

- [ ] **Step 1: Create index.html**

Create `index.html` — this is the complete file, no changes needed after this step:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=800, initial-scale=1.0">
<title>Kindle Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #fff;
  color: #000;
  font-family: Georgia, "Times New Roman", serif;
  width: 800px;
  overflow: hidden;
}
#top-bar {
  width: 100%;
  background: #000;
  color: #fff;
  padding: 8px 16px;
}
#top-table { width: 100%; border-collapse: collapse; }
#date-cell { font-size: 22px; font-weight: bold; letter-spacing: 1px; }
#clock-cell {
  text-align: right;
  font-size: 36px;
  font-family: "Courier New", monospace;
  font-weight: bold;
  letter-spacing: 3px;
}
#divider { height: 3px; background: #000; }
#bottom-table { width: 100%; border-collapse: collapse; }
#stock-td {
  width: 220px;
  vertical-align: top;
  border-right: 3px solid #000;
  padding: 16px 14px;
  background: #f5f5f5;
}
.s-label {
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #555;
  margin-bottom: 6px;
}
#s-ticker { font-size: 28px; font-weight: bold; font-family: "Courier New", monospace; }
#s-price {
  font-size: 42px;
  font-weight: bold;
  font-family: "Courier New", monospace;
  line-height: 1.1;
  margin-top: 4px;
}
#s-change { font-size: 18px; font-family: "Courier New", monospace; margin-top: 6px; }
.s-row { margin-top: 8px; }
.s-row-label { font-size: 11px; color: #555; }
.s-row-val { font-size: 14px; font-family: "Courier New", monospace; }
#s-updated {
  font-size: 10px;
  color: #888;
  margin-top: 16px;
  border-top: 1px solid #ccc;
  padding-top: 8px;
}
#s-error { color: #cc0000; font-size: 12px; display: none; }
#weather-td { vertical-align: top; padding: 12px 10px; }
#w-title {
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #555;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 2px solid #000;
}
#weather-days-table { width: 100%; table-layout: fixed; border-collapse: collapse; }
.wd { text-align: center; vertical-align: top; padding: 6px 2px; border-right: 1px solid #ccc; }
.wd:last-child { border-right: none; }
.wd-name { font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
.wd-date { font-size: 10px; color: #666; margin-bottom: 6px; }
.wd-icon { font-size: 30px; display: block; margin: 4px 0; }
.wd-desc { font-size: 10px; color: #444; margin-bottom: 6px; min-height: 28px; }
.wd-hi { font-size: 18px; font-weight: bold; font-family: "Courier New", monospace; }
.wd-lo { font-size: 13px; color: #666; font-family: "Courier New", monospace; }
.wd-today { background: #000; color: #fff; border-radius: 4px; }
.wd-today .wd-date,
.wd-today .wd-desc,
.wd-today .wd-lo { color: #ccc; }
#w-location { font-size: 11px; color: #666; margin-top: 10px; text-align: right; padding-right: 4px; }
#w-error { color: #cc0000; font-size: 12px; display: none; }
</style>
</head>
<body>

<div id="top-bar">
  <table id="top-table"><tr>
    <td id="date-cell">Loading...</td>
    <td id="clock-cell">--:--:-- --</td>
  </tr></table>
</div>
<div id="divider"></div>

<table id="bottom-table"><tr>
  <td id="stock-td">
    <div class="s-label">Nasdaq: Stock</div>
    <div id="s-ticker">WDAY</div>
    <div id="s-price">--</div>
    <div id="s-change">--</div>
    <div class="s-row">
      <div class="s-row-label">Open</div>
      <div class="s-row-val" id="s-open">--</div>
    </div>
    <div class="s-row">
      <div class="s-row-label">Prev Close</div>
      <div class="s-row-val" id="s-prev">--</div>
    </div>
    <div id="s-updated">Loading...</div>
    <div id="s-error"></div>
  </td>
  <td id="weather-td">
    <div id="w-title">7-Day Forecast &#8212; Burnaby, BC</div>
    <table id="weather-days-table"><tr id="weather-row"></tr></table>
    <div id="w-location">&#128205; Burnaby, BC &nbsp;|&nbsp; Temps in &deg;C</div>
    <div id="w-error"></div>
  </td>
</tr></table>

<script>
var DAY_NAMES = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
var MONTH_NAMES = ['January','February','March','April','May','June',
  'July','August','September','October','November','December'];

function pad(n) { return n < 10 ? '0' + n : '' + n; }

function tick() {
  var now = new Date();
  var h = now.getHours();
  var m = now.getMinutes();
  var s = now.getSeconds();
  var ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12;
  if (h === 0) { h = 12; }
  document.getElementById('clock-cell').innerHTML =
    pad(h) + ':' + pad(m) + ':' + pad(s) + ' ' + ampm;
  if (s === 0 || document.getElementById('date-cell').innerHTML === 'Loading...') {
    document.getElementById('date-cell').innerHTML =
      DAY_NAMES[now.getDay()] + ', ' +
      MONTH_NAMES[now.getMonth()] + ' ' +
      now.getDate() + ', ' + now.getFullYear();
  }
}

function sizeLayout() {
  var h = window.innerHeight || 600;
  var topBar = document.getElementById('top-bar');
  var topH = topBar ? (topBar.offsetHeight + 3) : 73;
  var ids = ['bottom-table', 'stock-td', 'weather-td'];
  for (var i = 0; i < ids.length; i++) {
    var el = document.getElementById(ids[i]);
    if (el) { el.style.height = (h - topH) + 'px'; }
  }
}

function renderStock(s) {
  if (!s || typeof s.price !== 'number') {
    document.getElementById('s-error').style.display = 'block';
    document.getElementById('s-error').innerHTML = 'Data unavailable';
    document.getElementById('s-updated').style.display = 'none';
    return;
  }
  document.getElementById('s-price').innerHTML = '$' + s.price.toFixed(2);
  var up = s.change >= 0;
  var arrow = up ? '&#9650;' : '&#9660;';
  var sign = up ? '+' : '';
  var clr = up ? '#006600' : '#cc0000';
  document.getElementById('s-change').innerHTML =
    '<span style="color:' + clr + '">' + arrow + ' ' + sign +
    s.change.toFixed(2) + ' (' + sign + s.change_pct.toFixed(2) + '%)</span>';
  document.getElementById('s-open').innerHTML = '$' + s.open.toFixed(2);
  document.getElementById('s-prev').innerHTML = '$' + s.prev_close.toFixed(2);
  var upd = s.updated ? s.updated.replace('T', ' ').replace('Z', ' UTC') : '';
  document.getElementById('s-updated').innerHTML = 'Updated: ' + upd;
}

function renderWeather(w) {
  if (!w || !w.days || !w.days.length) {
    document.getElementById('w-error').style.display = 'block';
    document.getElementById('w-error').innerHTML = 'Weather data unavailable';
    return;
  }
  var now = new Date();
  var todayStr = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate());
  var row = document.getElementById('weather-row');
  row.innerHTML = '';
  for (var i = 0; i < w.days.length; i++) {
    var d = w.days[i];
    var isToday = (d.date === todayStr);
    var td = document.createElement('td');
    td.className = 'wd' + (isToday ? ' wd-today' : '');
    var parts = d.date.split('-');
    var dispDate = parseInt(parts[1], 10) + '/' + parseInt(parts[2], 10);
    td.innerHTML =
      '<div class="wd-name">' + d.day_name + '</div>' +
      '<div class="wd-date">' + dispDate + '</div>' +
      '<span class="wd-icon">' + d.icon + '</span>' +
      '<div class="wd-desc">' + d.description + '</div>' +
      '<div class="wd-hi">' + d.high_c + '&deg;</div>' +
      '<div class="wd-lo">' + d.low_c + '&deg;</div>';
    row.appendChild(td);
  }
}

function showDataError() {
  var se = document.getElementById('s-error');
  if (se) { se.style.display = 'block'; se.innerHTML = 'Data unavailable'; }
  var we = document.getElementById('w-error');
  if (we) { we.style.display = 'block'; we.innerHTML = 'Data unavailable'; }
}

function loadData() {
  var xhr;
  try {
    xhr = window.XMLHttpRequest
      ? new XMLHttpRequest()
      : new ActiveXObject('Microsoft.XMLHTTP');
    xhr.open('GET', 'data.json', true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4) {
        if (xhr.status === 200 || xhr.status === 0) {
          try {
            var data = JSON.parse(xhr.responseText);
            renderStock(data.stock);
            renderWeather(data.weather);
          } catch(e) { showDataError(); }
        } else { showDataError(); }
      }
    };
    xhr.send(null);
  } catch(e) { showDataError(); }
}

window.onload = function() {
  sizeLayout();
  tick();
  setInterval(tick, 1000);
  loadData();
  setTimeout(function() { window.scrollTo(0, 1); }, 300);
};

window.onresize = sizeLayout;
</script>
</body>
</html>
```

- [ ] **Step 2: Verify locally in browser**

```bash
open /Users/adminaccount/Documents/kindle-calendar/index.html
```

Expected: clock ticks live, date shows correctly, stock/weather panels show `--` placeholders (no `data.json` yet). No JS errors in browser console.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add index.html with clock, stock, and weather panels"
```

---

### Task 3: Create seed data.json

**Files:**
- Create: `data.json`

**Interfaces:**
- Produces: valid `data.json` that `renderStock()` and `renderWeather()` in `index.html` can parse without errors

- [ ] **Step 1: Create data.json**

Create `data.json` — placeholder values; GitHub Actions will overwrite with real data:

```json
{
  "stock": {
    "ticker": "WDAY",
    "price": 0.0,
    "change": 0.0,
    "change_pct": 0.0,
    "open": 0.0,
    "prev_close": 0.0,
    "updated": "2026-06-27T14:00:00Z"
  },
  "weather": {
    "location": "Burnaby, BC",
    "days": [
      {"date": "2026-06-27", "day_name": "Fri", "icon": "⛅", "description": "Partly Cloudy", "high_c": 22, "low_c": 13},
      {"date": "2026-06-28", "day_name": "Sat", "icon": "☀", "description": "Sunny", "high_c": 25, "low_c": 14},
      {"date": "2026-06-29", "day_name": "Sun", "icon": "☁", "description": "Cloudy", "high_c": 19, "low_c": 12},
      {"date": "2026-06-30", "day_name": "Mon", "icon": "🌧", "description": "Rain", "high_c": 16, "low_c": 11},
      {"date": "2026-07-01", "day_name": "Tue", "icon": "🌧", "description": "Showers", "high_c": 17, "low_c": 12},
      {"date": "2026-07-02", "day_name": "Wed", "icon": "⛅", "description": "Partly Cloudy", "high_c": 20, "low_c": 13},
      {"date": "2026-07-03", "day_name": "Thu", "icon": "☀", "description": "Sunny", "high_c": 24, "low_c": 14}
    ]
  },
  "generated_at": "2026-06-27T14:00:00Z"
}
```

- [ ] **Step 2: Verify page renders data**

```bash
open /Users/adminaccount/Documents/kindle-calendar/index.html
```

Expected: stock panel shows `$0.00`, weather panel shows all 7 days with today (Fri Jun 27) highlighted in black background.

- [ ] **Step 3: Commit**

```bash
git add data.json
git commit -m "feat: add seed data.json"
```

---

### Task 4: Create Python fetch script with tests

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/fetch_data.py`
- Create: `tests/test_fetch_data.py`

**Interfaces:**
- Consumes: `https://query1.finance.yahoo.com/v8/finance/chart/WDAY?interval=1d&range=1d` (Yahoo Finance), `https://api.open-meteo.com/v1/forecast?...` (Open-Meteo)
- Produces: `data.json` at repo root matching the schema: `{stock: {ticker, price, change, change_pct, open, prev_close, updated}, weather: {location, days: [{date, day_name, icon, description, high_c, low_c}×7]}, generated_at}`
- Exports (for tests): `wmo_to_icon_desc(code: int) -> (str, str)`, `build_day_name(date_str: str) -> str`, `validate_data_schema(data: dict) -> bool`

- [ ] **Step 1: Create scripts/__init__.py**

```bash
mkdir -p /Users/adminaccount/Documents/kindle-calendar/scripts
mkdir -p /Users/adminaccount/Documents/kindle-calendar/tests
touch /Users/adminaccount/Documents/kindle-calendar/scripts/__init__.py
```

- [ ] **Step 2: Write failing tests first**

Create `tests/test_fetch_data.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from fetch_data import wmo_to_icon_desc, build_day_name, validate_data_schema


def test_wmo_clear():
    icon, desc = wmo_to_icon_desc(0)
    assert icon == '☀'
    assert desc == 'Clear'


def test_wmo_partly_cloudy():
    icon, desc = wmo_to_icon_desc(2)
    assert icon == '⛅'
    assert desc == 'Partly Cloudy'


def test_wmo_rain():
    icon, desc = wmo_to_icon_desc(63)
    assert icon == '\U0001f327'
    assert desc == 'Rain'


def test_wmo_thunderstorm():
    icon, desc = wmo_to_icon_desc(95)
    assert icon == '⛈'
    assert desc == 'Thunderstorm'


def test_wmo_unknown_returns_fallback():
    icon, desc = wmo_to_icon_desc(999)
    assert icon == '?'
    assert desc == 'Unknown'


def test_build_day_name_friday():
    assert build_day_name('2026-06-27') == 'Fri'


def test_build_day_name_saturday():
    assert build_day_name('2026-06-28') == 'Sat'


def _make_valid_data():
    return {
        'stock': {
            'ticker': 'WDAY', 'price': 234.56, 'change': 3.21,
            'change_pct': 1.39, 'open': 231.80, 'prev_close': 231.35,
            'updated': '2026-06-27T14:00:00Z',
        },
        'weather': {
            'location': 'Burnaby, BC',
            'days': [
                {'date': '2026-06-27', 'day_name': 'Fri', 'icon': '⛅',
                 'description': 'Partly Cloudy', 'high_c': 22, 'low_c': 13},
                {'date': '2026-06-28', 'day_name': 'Sat', 'icon': '☀',
                 'description': 'Sunny', 'high_c': 25, 'low_c': 14},
                {'date': '2026-06-29', 'day_name': 'Sun', 'icon': '☁',
                 'description': 'Overcast', 'high_c': 18, 'low_c': 11},
                {'date': '2026-06-30', 'day_name': 'Mon', 'icon': '\U0001f327',
                 'description': 'Rain', 'high_c': 15, 'low_c': 10},
                {'date': '2026-07-01', 'day_name': 'Tue', 'icon': '\U0001f327',
                 'description': 'Showers', 'high_c': 16, 'low_c': 11},
                {'date': '2026-07-02', 'day_name': 'Wed', 'icon': '⛅',
                 'description': 'Partly Cloudy', 'high_c': 19, 'low_c': 12},
                {'date': '2026-07-03', 'day_name': 'Thu', 'icon': '☀',
                 'description': 'Sunny', 'high_c': 22, 'low_c': 13},
            ],
        },
        'generated_at': '2026-06-27T14:00:00Z',
    }


def test_validate_data_schema_valid():
    assert validate_data_schema(_make_valid_data()) is True


def test_validate_data_schema_missing_stock():
    data = _make_valid_data()
    del data['stock']
    assert validate_data_schema(data) is False


def test_validate_data_schema_wrong_day_count():
    data = _make_valid_data()
    data['weather']['days'] = data['weather']['days'][:3]
    assert validate_data_schema(data) is False


def test_validate_data_schema_missing_day_field():
    data = _make_valid_data()
    del data['weather']['days'][0]['high_c']
    assert validate_data_schema(data) is False
```

- [ ] **Step 3: Run tests — expect ImportError**

```bash
cd /Users/adminaccount/Documents/kindle-calendar
python -m pytest tests/test_fetch_data.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'fetch_data'`

- [ ] **Step 4: Create scripts/fetch_data.py**

Create `scripts/fetch_data.py`:

```python
import json
import os
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    requests = None

WMO_MAP = {
    0:  ('☀',    'Clear'),
    1:  ('\U0001f324','Mainly Clear'),
    2:  ('⛅',    'Partly Cloudy'),
    3:  ('☁',    'Overcast'),
    45: ('\U0001f32b','Fog'),
    48: ('\U0001f32b','Icy Fog'),
    51: ('\U0001f326','Light Drizzle'),
    53: ('\U0001f326','Drizzle'),
    55: ('\U0001f326','Heavy Drizzle'),
    61: ('\U0001f327','Light Rain'),
    63: ('\U0001f327','Rain'),
    65: ('\U0001f327','Heavy Rain'),
    71: ('\U0001f328','Light Snow'),
    73: ('\U0001f328','Snow'),
    75: ('\U0001f328','Heavy Snow'),
    77: ('\U0001f328','Snow Grains'),
    80: ('\U0001f327','Showers'),
    81: ('\U0001f327','Showers'),
    82: ('\U0001f327','Heavy Showers'),
    85: ('\U0001f328','Snow Showers'),
    86: ('\U0001f328','Heavy Snow Showers'),
    95: ('⛈',    'Thunderstorm'),
    96: ('⛈',    'Thunderstorm+Hail'),
    99: ('⛈',    'Thunderstorm+Hail'),
}


def wmo_to_icon_desc(code):
    return WMO_MAP.get(code, ('?', 'Unknown'))


def build_day_name(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return dt.strftime('%a')


def validate_data_schema(data):
    try:
        stock = data['stock']
        for key in ('ticker', 'price', 'change', 'change_pct', 'open', 'prev_close', 'updated'):
            assert key in stock
        days = data['weather']['days']
        assert len(days) == 7
        for d in days:
            for k in ('date', 'day_name', 'icon', 'description', 'high_c', 'low_c'):
                assert k in d
        return True
    except (AssertionError, KeyError, TypeError):
        return False


def fetch_stock():
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/WDAY?interval=1d&range=1d'
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; kindle-calendar/1.0)'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    meta = resp.json()['chart']['result'][0]['meta']
    price = float(meta['regularMarketPrice'])
    prev_close = float(meta['previousClose'])
    open_price = float(meta.get('regularMarketOpen', prev_close))
    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0.0
    return {
        'ticker': 'WDAY',
        'price': round(price, 2),
        'change': round(change, 2),
        'change_pct': round(change_pct, 2),
        'open': round(open_price, 2),
        'prev_close': round(prev_close, 2),
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }


def fetch_weather():
    url = (
        'https://api.open-meteo.com/v1/forecast'
        '?latitude=49.2488&longitude=-122.9805'
        '&daily=weather_code,temperature_2m_max,temperature_2m_min'
        '&timezone=America%2FVancouver'
        '&forecast_days=7'
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    daily = resp.json()['daily']
    days = []
    for i in range(7):
        date_str = daily['time'][i]
        icon, desc = wmo_to_icon_desc(daily['weather_code'][i])
        days.append({
            'date': date_str,
            'day_name': build_day_name(date_str),
            'icon': icon,
            'description': desc,
            'high_c': round(daily['temperature_2m_max'][i]),
            'low_c': round(daily['temperature_2m_min'][i]),
        })
    return {'location': 'Burnaby, BC', 'days': days}


def main():
    print('Fetching WDAY stock...')
    stock = fetch_stock()
    print('  price: $' + str(stock['price']))

    print('Fetching weather for Burnaby, BC...')
    weather = fetch_weather()
    print('  days fetched: ' + str(len(weather['days'])))

    data = {
        'stock': stock,
        'weather': weather,
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }

    if not validate_data_schema(data):
        print('ERROR: data schema validation failed', file=sys.stderr)
        sys.exit(1)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(repo_root, 'data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Written to ' + out_path)


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: Run tests — expect all pass**

```bash
cd /Users/adminaccount/Documents/kindle-calendar
python -m pytest tests/test_fetch_data.py -v
```

Expected output:
```
PASSED tests/test_fetch_data.py::test_wmo_clear
PASSED tests/test_fetch_data.py::test_wmo_partly_cloudy
PASSED tests/test_fetch_data.py::test_wmo_rain
PASSED tests/test_fetch_data.py::test_wmo_thunderstorm
PASSED tests/test_fetch_data.py::test_wmo_unknown_returns_fallback
PASSED tests/test_fetch_data.py::test_build_day_name_friday
PASSED tests/test_fetch_data.py::test_build_day_name_saturday
PASSED tests/test_fetch_data.py::test_validate_data_schema_valid
PASSED tests/test_fetch_data.py::test_validate_data_schema_missing_stock
PASSED tests/test_fetch_data.py::test_validate_data_schema_wrong_day_count
PASSED tests/test_fetch_data.py::test_validate_data_schema_missing_day_field
11 passed
```

- [ ] **Step 6: Run live fetch to verify real data (requires internet)**

```bash
pip install requests
python /Users/adminaccount/Documents/kindle-calendar/scripts/fetch_data.py
```

Expected: prints stock price and `Written to .../data.json`, then open `index.html` in browser to see real WDAY price and real Burnaby weather.

- [ ] **Step 7: Commit**

```bash
git add scripts/ tests/
git commit -m "feat: add fetch_data.py with unit tests"
```

---

### Task 5: Create GitHub Actions workflow

**Files:**
- Create: `.github/workflows/fetch-data.yml`

**Interfaces:**
- Consumes: `scripts/fetch_data.py`, GitHub repo write permission
- Produces: `data.json` committed to `main` daily at 14:00 UTC with `[skip ci]` tag

- [ ] **Step 1: Create workflow file**

```bash
mkdir -p /Users/adminaccount/Documents/kindle-calendar/.github/workflows
```

Create `.github/workflows/fetch-data.yml`:

```yaml
name: Fetch Data

on:
  schedule:
    - cron: '0 14 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Fetch data
        run: python scripts/fetch_data.py

      - name: Commit and push data.json
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email 'github-actions[bot]@users.noreply.github.com'
          git add data.json
          git diff --staged --quiet || git commit -m "chore: update data.json [skip ci]"
          git push
```

- [ ] **Step 2: Commit and push**

```bash
git add .github/
git commit -m "feat: add GitHub Actions workflow for daily data fetch"
git push
```

---

### Task 6: Deploy, trigger first fetch, verify live site

**Files:** none (deployment verification)

**Interfaces:**
- Consumes: all pushed commits on `main`
- Produces: live GitHub Pages site with real stock and weather data

- [ ] **Step 1: Push all commits (if not already pushed)**

```bash
git push origin main
```

- [ ] **Step 2: Get the live Pages URL**

```bash
OWNER=$(gh api user --jq .login)
echo "Live URL: https://${OWNER}.github.io/kindle-calendar/"
```

Wait 1-2 minutes for GitHub Pages to deploy, then open the URL in a browser.

- [ ] **Step 3: Manually trigger the data fetch workflow**

```bash
gh workflow run fetch-data.yml
```

Wait ~30 seconds then check status:

```bash
gh run list --workflow=fetch-data.yml --limit=1
```

Expected: `completed  success`

- [ ] **Step 4: Pull updated data.json and verify schema**

```bash
git pull
python -c "
import json
with open('data.json') as f:
    d = json.load(f)
print('WDAY price: \$' + str(d['stock']['price']))
print('Weather days:', len(d['weather']['days']))
print('First day:', d['weather']['days'][0])
"
```

Expected: real WDAY price (non-zero), 7 weather days with real temperatures.

- [ ] **Step 5: Final browser verification of live site**

Open `https://<owner>.github.io/kindle-calendar/` in a browser.

Verify:
- Clock ticks live every second
- Date shows today's full name and date
- WDAY stock shows real price with green/red change indicator
- 7 weather days for Burnaby show with today highlighted in black
- Page fits within 800px width, no horizontal scroll
