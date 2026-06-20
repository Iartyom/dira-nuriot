import os
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(__file__)
madlan_path = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot', 'adapters', 'madlan.py'))
yad2_path = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot', 'adapters', 'yad2.py'))
madlan = SourceFileLoader('madlan', madlan_path).load_module()
yad2 = SourceFileLoader('yad2', yad2_path).load_module()


def test_madlan_parse_structured_summary():
    payload = {
        'reduxInitialState': {
            'insightsContext': {'x': {'updateTime': '2026-06-15T03:00:20.681Z'}},
            'domainData': {
                'localDoc': {'data': {'searchLocal2': {
                    'zoneName': 'נוריות, בראשון לציון',
                    'zoneSummary': {'bulletinsForSaleCount': 3, 'bulletinsForRentCount': 3},
                    'pricesTable': [{'rooms': '6', 'newPrice': 3565909, 'oldPrice': 3637143, 'rent': None}],
                }}},
                'strictLocalDoc': {'data': {'docId2Information': {'yearNumberOfDeals': 48}}},
                'neighborhoodPublicInsights': {'data': {'neighborhoodPublicInsights': {'dealsSummary': {
                    'totalDeals': 198, 'averagePricePerMeter': 21467.99,
                }}}},
            },
        }
    }
    html = '<script>window.__SSR_HYDRATED_CONTEXT__=' + __import__('json').dumps(payload, ensure_ascii=False) + '</script>'
    result = madlan.parse_market_summary(html)
    assert result['prices_by_rooms']['6']['new_build_price_nis'] == 3565909
    assert result['average_price_per_sqm_nis'] == 21467.99
    assert result['year_deals_count'] == 48
    assert result['comparison_area'] == 'נוריות'


def test_madlan_comparison_area_validation():
    payload = {
        'reduxInitialState': {
            'insightsContext': {},
            'domainData': {
                'localDoc': {'data': {'searchLocal2': {
                    'zoneName': 'נרקיסים, בראשון לציון',
                    'zoneSummary': {'bulletinsForSaleCount': 53},
                    'pricesTable': [{'rooms': '6', 'newPrice': 4003333}],
                }}},
                'strictLocalDoc': {'data': {'docId2Information': {'yearNumberOfDeals': 107}}},
                'neighborhoodPublicInsights': {'data': {'neighborhoodPublicInsights': {'dealsSummary': {
                    'totalDeals': 300, 'averagePricePerMeter': 26516.59,
                }}}},
            },
        }
    }
    html = '<script>window.__SSR_HYDRATED_CONTEXT__=' + __import__('json').dumps(payload, ensure_ascii=False) + '</script>'
    result = madlan.parse_market_summary(html, expected_area='נרקיסים')
    assert result['prices_by_rooms']['6']['new_build_price_nis'] == 4003333
    assert result['comparison_area'] == 'נרקיסים'


def test_yad2_parse_fixture():
    with open(os.path.join(HERE, 'fixtures', 'yad2_sample.html'), encoding='utf-8') as f:
        html = f.read()
    items = yad2._parse_html_for_comps(html)
    assert isinstance(items, list)
    assert items and items[0].get('_area_sqm') == 145
    assert '3100000' in items[0].get('DEALAMOUNT')
