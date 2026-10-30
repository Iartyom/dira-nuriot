import os
from importlib.machinery import SourceFileLoader


HERE = os.path.dirname(__file__)
APP = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot'))
update_all = SourceFileLoader('update_all', os.path.join(APP, 'update_all.py')).load_module()
build = SourceFileLoader('build_html', os.path.join(APP, 'build_html.py')).load_module()


def test_merge_market_keeps_last_good_source_when_blocked():
    previous = {'supplemental_sources': [
        {'source': 'madlan', 'comparison_area': 'נוריות', 'average_price_per_sqm_nis': 21705.66},
    ]}
    new = {'public_market_summary': {'dataset_version': '20-08-2026'}, 'supplemental_sources': [
        {'source': 'madlan', 'comparison_area': 'נוריות', 'ok': False, 'error': 'HTTP Error 403: Forbidden'},
    ]}
    merged = update_all.merge_market(new, previous)
    kept = merged['supplemental_sources'][0]
    assert kept['average_price_per_sqm_nis'] == 21705.66
    assert kept['stale'] is True
    assert '403' in kept['stale_reason']
    assert merged['public_market_summary']['dataset_version'] == '20-08-2026'


def test_merge_market_prefers_fresh_source():
    previous = {'supplemental_sources': [{'comparison_area': 'נוריות', 'average_price_per_sqm_nis': 1}]}
    new = {'supplemental_sources': [{'comparison_area': 'נוריות', 'average_price_per_sqm_nis': 2}]}
    merged = update_all.merge_market(new, previous)
    assert merged['supplemental_sources'][0]['average_price_per_sqm_nis'] == 2
    assert 'stale' not in merged['supplemental_sources'][0]


def test_build_contains_sale_and_upgrade_calculators():
    build.main()
    with open(os.path.join(APP, 'index.html'), encoding='utf-8') as handle:
        html = handle.read()
    for marker in [
        'מכירה ושדרוג',      # new finance section (also in DOMAINS)
        'sm-table',          # sell-at-Form-4 vs wait comparison
        'uf-out',            # next-home mortgage outputs
        'uf-bridge',         # bridge-loan toggle
        'renderSale',
        'sale_ctx',
        'valuation_seed',    # seed-version refresh of saved boards
        'רענון שוק אחרון',   # market freshness health item
    ]:
        assert marker in html, marker
