"""Structured Madlan neighborhood-summary adapter.

Madlan's public area page embeds a large ``window.__SSR_HYDRATED_CONTEXT__``
object.  We parse named fields from that object; no global price/area regex
pairing is used.  Values are market indicators and remain separate from
government-recorded transactions.
"""
import datetime
import json
import os
import re
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES_DIR = os.path.join(HERE, "..", "updates")
AREA_URLS = {
    "נוריות": (
        "https://www.madlan.co.il/area-info/"
        "%D7%A9%D7%9B%D7%95%D7%A0%D7%94-%D7%A0%D7%95%D7%A8%D7%99%D7%95%D7%AA-"
        "%D7%A8%D7%90%D7%A9%D7%95%D7%9F-%D7%9C%D7%A6%D7%99%D7%95%D7%9F-"
        "%D7%99%D7%A9%D7%A8%D7%90%D7%9C"
    ),
    "נרקיסים": (
        "https://www.madlan.co.il/area-info/"
        "%D7%A9%D7%9B%D7%95%D7%A0%D7%94-%D7%A0%D7%A8%D7%A7%D7%99%D7%A1%D7%99%D7%9D-"
        "%D7%A8%D7%90%D7%A9%D7%95%D7%9F-%D7%9C%D7%A6%D7%99%D7%95%D7%9F-"
        "%D7%99%D7%A9%D7%A8%D7%90%D7%9C"
    ),
}
SSR_PREFIX = "<script>window.__SSR_HYDRATED_CONTEXT__="


def _save_raw(area_name, content):
    os.makedirs(UPDATES_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = "nuriyot" if area_name == "נוריות" else "narkisim"
    path = os.path.join(UPDATES_DIR, f"raw-madlan-{safe_name}-{stamp}.html")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def _parse_ssr_context(html):
    start = html.find(SSR_PREFIX)
    if start < 0:
        raise ValueError("Madlan SSR hydration context was not found")
    start += len(SSR_PREFIX)
    end = html.find("</script>", start)
    if end < 0:
        raise ValueError("Madlan SSR hydration script was not terminated")
    raw = html[start:end]
    # The payload is a JavaScript object that uses undefined in router state.
    # Normalize only unquoted value positions needed for strict JSON parsing.
    raw = re.sub(r"(?<=[,:\[])undefined(?=[,}\]])", "null", raw)
    return json.loads(raw)


def _collect_update_times(value, output):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "updateTime" and isinstance(child, str):
                output.append(child)
            else:
                _collect_update_times(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_update_times(child, output)


def parse_market_summary(html, expected_area="נוריות"):
    context = _parse_ssr_context(html)
    root = context.get("reduxInitialState") or {}
    domain = root.get("domainData") or {}
    local = (((domain.get("localDoc") or {}).get("data") or {}).get("searchLocal2") or {})
    strict = (((domain.get("strictLocalDoc") or {}).get("data") or {}).get("docId2Information") or {})
    public = (((domain.get("neighborhoodPublicInsights") or {}).get("data") or {}).get("neighborhoodPublicInsights") or {})
    deal_summary = public.get("dealsSummary") or {}
    prices = {}
    for row in local.get("pricesTable") or []:
        rooms = row.get("rooms")
        if rooms:
            prices[str(rooms)] = {
                "new_build_price_nis": row.get("newPrice"),
                "second_hand_price_nis": row.get("oldPrice"),
                "rent_nis": row.get("rent"),
            }
    update_times = []
    _collect_update_times(root.get("insightsContext") or {}, update_times)
    latest_update = max(update_times) if update_times else None
    zone = local.get("zoneName")
    if not zone or expected_area not in zone:
        raise ValueError(f"Madlan response does not describe {expected_area}")
    return {
        "source": "madlan",
        "source_type": "market_indicator",
        "comparison_area": expected_area,
        "zone_name": zone,
        "source_updated_at": latest_update,
        "active_for_sale_count": (local.get("zoneSummary") or {}).get("bulletinsForSaleCount"),
        "active_for_rent_count": (local.get("zoneSummary") or {}).get("bulletinsForRentCount"),
        "year_deals_count": strict.get("yearNumberOfDeals"),
        "total_deals_count": deal_summary.get("totalDeals"),
        "average_price_per_sqm_nis": deal_summary.get("averagePricePerMeter"),
        "prices_by_rooms": prices,
    }


def fetch(query="נוריות ראשון לציון", timeout=30):
    normalized = " ".join(query.split())
    if "נוריות" not in normalized or "ראשון" not in normalized:
        return []
    results = []
    for area_name, url in AREA_URLS.items():
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                html = response.read().decode("utf-8", "replace")
            _save_raw(area_name, html)
            summary = parse_market_summary(html, expected_area=area_name)
            summary["source_url"] = url
            summary["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            results.append(summary)
        except Exception as error:
            results.append({
                "source": "madlan",
                "source_type": "market_indicator",
                "comparison_area": area_name,
                "source_url": url,
                "ok": False,
                "error": str(error),
            })
    return results


def _parse_html_for_comps(html):
    """Deprecated compatibility hook; heuristic comps are intentionally disabled."""
    return []
