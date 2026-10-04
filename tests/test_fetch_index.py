import os
from importlib.machinery import SourceFileLoader


HERE = os.path.dirname(__file__)
APP = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot'))
fi = SourceFileLoader('fetch_index', os.path.join(APP, 'fetch_index.py')).load_module()


def _row(y, m, value, base):
    return {"year": y, "month": m, "currBase": {"baseDesc": base, "value": value}}


def test_parse_series_drops_old_base_and_months_before_since():
    payload = {"month": [{"date": [
        _row(2026, 8, 103.9, "2025 יולי"),
        _row(2025, 10, 100.5, "2025 יולי"),
        _row(2025, 9, 100.4, "2025 יולי"),
        _row(2025, 7, 138.7, "2011 יולי"),  # pre-rebase row must not mix into ratios
    ]}]}
    series, base = fi.parse_series(payload, "2025-10")
    assert base == "2025 יולי"
    assert series == {"2025-10": 100.5, "2026-08": 103.9}


def test_build_embeds_linkage_model():
    build = SourceFileLoader('build_html', os.path.join(APP, 'build_html.py')).load_module()
    build.main()
    with open(os.path.join(APP, 'index.html'), encoding='utf-8') as handle:
        html = handle.read()
    for marker in ('payIndexInfo', '"share": 0.4', 'idx-cell', 'api.cbs.gov.il'):
        assert marker in html, marker
