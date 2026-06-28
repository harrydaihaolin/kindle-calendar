from fetch_data import wmo_to_icon_desc, build_day_name, validate_data_schema  # type: ignore[import-untyped]


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
    assert build_day_name('2026-06-26') == 'Fri'


def test_build_day_name_saturday():
    assert build_day_name('2026-06-27') == 'Sat'


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
                {'date': '2026-06-27', 'day_name': 'Sat', 'icon': '⛅',
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
