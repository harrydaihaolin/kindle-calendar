import json
import os
import sys
from datetime import datetime, timezone

import requests

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
    prev_close = float(meta.get('previousClose') or meta.get('chartPreviousClose') or 0)
    open_price = float(meta.get('regularMarketOpen') or prev_close)
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
