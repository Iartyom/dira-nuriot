import os
from importlib.machinery import SourceFileLoader


HERE = os.path.dirname(__file__)
APP = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot'))
build = SourceFileLoader('build_html', os.path.join(APP, 'build_html.py')).load_module()


def test_build_contains_management_modules():
    build.main()
    with open(os.path.join(APP, 'index.html'), encoding='utf-8') as handle:
        html = handle.read()
    required = [
        'מצב מערכת ונתונים',
        'נתוני שוק רשמיים',
        'comparables-table',
        'cash-monthly-needed',
        'reno-track-table',
        'defects-table',
        'export-state',
        'update_status',
    ]
    for marker in required:
        assert marker in html


def test_build_contains_new_features():
    build.main()
    with open(os.path.join(APP, 'index.html'), encoding='utf-8') as handle:
        html = handle.read()
    # KPI hero, section nav, staleness banner, documents section, refresh + map
    required = [
        'class="hero"',
        'hero-handover',
        'secnav',                # sticky section nav (CSS + JS)
        'class="stale ',         # valuation freshness banner
        'מיקום, תוכניות ומסמכים רשמיים',
        'maps.google.com',       # embedded ortho window
        'actions/workflows/refresh-data.yml',  # update button
        '@media print',
        'comp-price-avg',        # D3: comparable-only average
        'בר-השוואה',             # D3: comparability column
        'tabular-nums',          # direction A: aligned numerals
        'tabpanel',              # IA: domain tabs
        'DOMAINS',               # IA: tab domain map
        '18 חודשים',             # verified sale-lock window
    ]
    for marker in required:
        assert marker in html, marker
