import os
import sys
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(__file__)
module_path = os.path.abspath(os.path.join(HERE, '..', 'dira-nuriot', 'fetch_deals.py'))
fetch_mod = SourceFileLoader('fetch_deals', module_path).load_module()


def test_summarize_basic():
    # create fake raw results similar to nadlan response
    results = [
        {"DEALAMOUNT": "1,000,000", "DEALNATURE": "100", "DEALDATETIME": "2026-01-01", "FULLADRESS": "A"},
        {"DEALAMOUNT": "1,500,000", "DEALNATURE": "150", "DEALDATETIME": "2026-02-01", "FULLADRESS": "B"},
        {"DEALAMOUNT": "2,000,000", "DEALNATURE": "100", "DEALDATETIME": "2026-03-01", "FULLADRESS": "C"},
    ]
    rows, summary = fetch_mod.summarize(results)
    assert summary is not None
    assert summary["deals_used"] == 3
    assert summary["median_price_per_sqm"] == 10000


def test_pick_neighborhood():
    response = {
        "data": {
            "NEIGHBORHOOD": [{
                "ObjectID": "67689667",
                "ResultLable": "נוריות, ראשון לציון",
                "X": 184121.2,
                "Y": 652607.6,
            }]
        }
    }
    result = fetch_mod._pick_neighborhood(response)
    assert result["current_id"] == "67689667"
    assert result["requested_label"] == "נוריות, ראשון לציון"


def test_extract_public_summary():
    page = {
        "version": "28-07-2025",
        "neighborhoodName": "מרום ראשון",
        "settlementID": 8300,
        "settlementName": "ראשון לציון",
        "trends": {
            "rooms": [
                {
                    "numRooms": 5,
                    "summary": {"lastYearAvgPrice": 3346800},
                    "graphData": [],
                },
                {
                    "numRooms": "all",
                    "summary": {
                        "lastYearAvgPrice": 3911750,
                        "priceDifferencePercentage": 1.55,
                    },
                    "graphData": [
                        {"year": 2025, "month": 6, "neighborhoodPrice": None},
                        {"year": 2025, "month": 3, "neighborhoodPrice": 3997300},
                    ],
                },
            ]
        },
    }
    result = fetch_mod.extract_public_summary(page)
    assert result["dataset_version"] == "28-07-2025"
    assert result["statistical_area_name"] == "מרום ראשון"
    assert result["all_rooms_last_year_avg_price_nis"] == 3911750
    assert result["latest_neighborhood_price_nis"] == 3997300
    assert result["latest_neighborhood_period"] == {"year": 2025, "month": 3}


def test_default_query_has_verified_location_seed():
    seed = fetch_mod.KNOWN_LOCATIONS[fetch_mod.DEFAULT_QUERY]
    assert seed["current_id"] == "67689667"
    assert seed["resolution"] == "verified_seed"
