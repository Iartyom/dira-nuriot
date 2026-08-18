#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch public Nadlan market data for a neighborhood.

The former ``Nadlan.REST/Main`` endpoints were retired when nadlan.gov.il
moved to its current SPA.  The current site resolves locations with GovMap,
maps current neighborhood IDs to Nadlan's legacy statistical IDs, and serves
public summary JSON from data.nadlan.gov.il.

Individual transaction rows are intentionally not fetched here: the current
``/deal-data`` endpoint requires reCAPTCHA and a signed browser payload.  This
script uses only public, unattended endpoints and records that limitation in
its output rather than silently substituting unverified listing data.
"""
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES_DIR = os.path.join(HERE, "updates")
DEFAULT_QUERY = "נוריות ראשון לציון"
APT_AREA = 145

GOVMAP_DETAILS = "https://es.govmap.gov.il/TldSearch/api/DetailsByQuery"
NADLAN_CONFIG = "https://www.nadlan.gov.il/config.json"
DEFAULT_DATA_BASE = "https://data.nadlan.gov.il/api"

# GovMap's ``es.govmap.gov.il`` TLS configuration is incompatible with some
# Python/OpenSSL builds.  Keep only project-owned, manually verified seeds
# here; the ID is still translated and validated against Nadlan's live index.
KNOWN_LOCATIONS = {
    "נוריות ראשון לציון": {
        "requested_label": "נוריות, ראשון לציון",
        "current_id": "67689667",
        "statistical_area_id": "65209940",
        "x": 184121.2095,
        "y": 652607.6766,
        "resolution": "verified_seed",
    },
    "נרקיסים ראשון לציון": {
        "requested_label": "נרקיסים, ראשון לציון",
        "current_id": "67689477",
        "x": 184122.3824,
        "y": 651820.2008,
        "resolution": "verified_seed",
    },
}


def _safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "response"


def _save_raw(name, body):
    os.makedirs(UPDATES_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(UPDATES_DIR, f"raw-{_safe_name(name)}-{stamp}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(body, handle, ensure_ascii=False, indent=2)
    return path


def _get_json(url, raw_name=None, timeout=30):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (dira-nuriot public-data updater)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8-sig", "replace").lstrip()
    if text.startswith("<"):
        raise ValueError(f"Expected JSON but received HTML from {url}")
    data = json.loads(text)
    if raw_name:
        _save_raw(raw_name, data)
    return data


def _pick_neighborhood(search_response):
    candidates = (search_response.get("data") or {}).get("NEIGHBORHOOD") or []
    if not candidates:
        raise ValueError("GovMap did not return a neighborhood for the query")
    item = candidates[0]
    return {
        "requested_label": item.get("ResultLable"),
        "current_id": str(item.get("ObjectID")),
        "x": item.get("X"),
        "y": item.get("Y"),
    }


# Any of the public endpoints can intermittently answer with an HTML challenge/SPA
# page instead of JSON (raising ValueError) or be unreachable (URLError). Treat all of
# these as "endpoint unavailable" so we can fall back to the verified project seed.
FETCH_ERRORS = (
    urllib.error.URLError,
    urllib.error.HTTPError,
    TimeoutError,
    ValueError,
    json.JSONDecodeError,
)


def resolve_neighborhood(query, data_base=DEFAULT_DATA_BASE):
    params = urllib.parse.urlencode({"query": query, "lyrs": 4, "gid": "nadlan"})
    seed = KNOWN_LOCATIONS.get(" ".join(query.split()))
    try:
        search = _get_json(f"{GOVMAP_DETAILS}?{params}", "govmap-neighborhood")
        location = _pick_neighborhood(search)
        location["resolution"] = "govmap_live"
    except FETCH_ERRORS:
        if not seed:
            raise
        location = dict(seed)

    # Map the current neighborhood id to Nadlan's legacy statistical-area id.
    mapping = None
    try:
        index = _get_json(f"{data_base}/index/neigh.json")
        mapping = index.get(location["current_id"])
    except FETCH_ERRORS:
        mapping = None
    if isinstance(mapping, dict) and mapping.get("UNIQ_ID_OLD"):
        location["statistical_area_id"] = str(mapping["UNIQ_ID_OLD"])
    elif seed and seed.get("statistical_area_id"):
        # Live index unavailable — use the verified seed's known mapping as a last resort.
        location["statistical_area_id"] = str(seed["statistical_area_id"])
        location["resolution"] = "seed_statistical_area"
    else:
        raise ValueError(
            f"Nadlan has no legacy statistical-area mapping for neighborhood "
            f"{location['current_id']}"
        )
    return location


def _room_summary(page, room_count):
    rooms = ((page.get("trends") or {}).get("rooms") or [])
    return next((row for row in rooms if str(row.get("numRooms")) == str(room_count)), None)


def extract_public_summary(page):
    """Extract transparent market signals from Nadlan's neighborhood page."""
    all_rooms = _room_summary(page, "all") or {}
    five_rooms = _room_summary(page, 5) or {}
    all_summary = all_rooms.get("summary") or {}
    five_summary = five_rooms.get("summary") or {}
    graph = all_rooms.get("graphData") or []
    latest_neighborhood = next(
        (point for point in graph if point.get("neighborhoodPrice") is not None), None
    )
    return {
        "dataset_version": page.get("version"),
        "statistical_area_name": page.get("neighborhoodName"),
        "settlement_name": page.get("settlementName"),
        "settlement_id": page.get("settlementID"),
        "all_rooms_last_year_avg_price_nis": all_summary.get("lastYearAvgPrice"),
        "all_rooms_price_change_pct": all_summary.get("priceDifferencePercentage"),
        "five_rooms_last_year_avg_price_nis": five_summary.get("lastYearAvgPrice"),
        "latest_neighborhood_period": (
            {"year": latest_neighborhood.get("year"), "month": latest_neighborhood.get("month")}
            if latest_neighborhood else None
        ),
        "latest_neighborhood_price_nis": (
            latest_neighborhood.get("neighborhoodPrice") if latest_neighborhood else None
        ),
    }


def fetch_public_market_data(query):
    # config.json only supplies the S3 base URLs; it is periodically served as an HTML
    # challenge/SPA fallback instead of JSON. Treat it as optional and fall back to the
    # known public bases so a flaky config endpoint does not sink the whole fetch.
    try:
        config = _get_json(NADLAN_CONFIG, "nadlan-config")
    except FETCH_ERRORS as error:
        print(f"ℹ️  config.json לא זמין כ-JSON ({error}); ממשיך עם כתובות ברירת המחדל של Nadlan.", file=sys.stderr)
        config = {}
    data_base = config.get("s3_url_base") or DEFAULT_DATA_BASE
    page_base = config.get("s3_page_base") or f"{data_base}/pages"
    location = resolve_neighborhood(query, data_base)
    page_url = (
        f"{page_base}/neighborhood/buy/"
        f"{urllib.parse.quote(location['statistical_area_id'])}.json"
    )
    page = _get_json(page_url, "nadlan-neighborhood-summary")
    summary = extract_public_summary(page)
    location["statistical_area_name"] = summary["statistical_area_name"]
    location["boundary_name_mismatch"] = bool(
        location.get("requested_label")
        and summary.get("statistical_area_name")
        and summary["statistical_area_name"] not in location["requested_label"]
    )
    return location, summary, page_url


def fetch_deals(query):
    """Backward-compatible API: return metadata and no protected deal rows."""
    location, summary, page_url = fetch_public_market_data(query)
    return {
        "location": location,
        "public_summary": summary,
        "source_url": page_url,
    }, []


def _extract_area(deal):
    for key in ("_area_sqm", "DEALNATURE", "ASSETAREA", "AREA", "DEALAREA", "ASSETAREAM2", "AREA_SQM"):
        value = deal.get(key)
        if value in (None, ""):
            continue
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            pass
    return None


def summarize(results):
    """Summarize actual transaction rows when supplied by a trusted source."""
    rows = []
    for deal in results:
        try:
            price = float(str(deal.get("DEALAMOUNT", "")).replace(",", ""))
        except (TypeError, ValueError):
            price = None
        area = _extract_area(deal)
        if price and area and area > 20:
            rows.append({
                "date": deal.get("DEALDATETIME"),
                "address": deal.get("FULLADRESS") or deal.get("DISPLAYADRESS") or deal.get("address"),
                "rooms": deal.get("ASSETROOMNUM"),
                "area_sqm": area,
                "price_nis": price,
                "price_per_sqm": round(price / area),
                "source": deal.get("_source", "nadlan"),
            })
    if not rows:
        return rows, None
    prices = sorted(row["price_per_sqm"] for row in rows)
    count = len(prices)
    median = prices[count // 2] if count % 2 else (prices[count // 2 - 1] + prices[count // 2]) / 2
    return rows, {
        "deals_used": count,
        "avg_price_per_sqm": round(sum(prices) / count),
        "median_price_per_sqm": round(median),
        "min_price_per_sqm": prices[0],
        "max_price_per_sqm": prices[-1],
        "estimated_value_for_145sqm": round(median * APT_AREA),
    }


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    today = datetime.date.today().isoformat()
    os.makedirs(UPDATES_DIR, exist_ok=True)
    output_path = os.path.join(UPDATES_DIR, f"deals-{today}.json")
    print(f"🔎 מושך נתוני שוק ציבוריים עבור: {query}")
    try:
        location, public_summary, source_url = fetch_public_market_data(query)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        print(f"⚠️  משיכת נתוני Nadlan נכשלה: {error}", file=sys.stderr)
        sys.exit(2)

    supplemental_sources = []
    government_comparisons = []
    source_health = {
        "nadlan": {"ok": True, "kind": "government_summary"},
        "madlan": {"ok": False, "kind": "market_indicator"},
        "yad2": {
            "ok": False,
            "kind": "asking_listings",
            "reason": "Live real-estate access is blocked by anti-bot controls; yad2-scraper 0.5.3 primarily supports vehicles.",
        },
    }
    try:
        from adapters.madlan import fetch as fetch_madlan
        supplemental_sources = fetch_madlan(query)
        healthy_madlan = [item for item in supplemental_sources if item.get("ok", True)]
        source_health["madlan"]["ok"] = bool(healthy_madlan)
        source_health["madlan"]["areas"] = {
            item.get("comparison_area"): item.get("ok", True) for item in supplemental_sources
        }
        if not healthy_madlan:
            source_health["madlan"]["reason"] = "No structured Nuriot summary returned."
    except Exception as error:
        source_health["madlan"]["reason"] = str(error)
    try:
        comparison_location, comparison_summary, comparison_url = fetch_public_market_data(
            "נרקיסים ראשון לציון"
        )
        government_comparisons.append({
            "area": "נרקיסים",
            "location": comparison_location,
            "summary": comparison_summary,
            "source_url": comparison_url,
            "usable_neighborhood_price": bool(comparison_summary.get("latest_neighborhood_price_nis")),
        })
        source_health["nadlan_narkisim"] = {
            "ok": True,
            "kind": "government_summary",
            "usable_neighborhood_price": bool(comparison_summary.get("latest_neighborhood_price_nis")),
        }
    except Exception as error:
        source_health["nadlan_narkisim"] = {
            "ok": False,
            "kind": "government_summary",
            "reason": str(error),
        }

    payload = {
        "query": query,
        "fetched_at": today,
        "source": "nadlan.gov.il + GovMap (public unattended endpoints)",
        "source_url": source_url,
        "location": location,
        "raw_count": 0,
        "deals": [],
        "summary": None,
        "public_market_summary": public_summary,
        "supplemental_sources": supplemental_sources,
        "government_comparisons": government_comparisons,
        "source_health": source_health,
        "limitations": [
            "Individual transaction rows are protected by reCAPTCHA and are not fetched unattended.",
            "The neighborhood is mapped to Nadlan's legacy statistical area; inspect boundary_name_mismatch.",
            "Dataset freshness is reported by public_market_summary.dataset_version.",
            "Public summary prices are not price-per-square-meter estimates and do not automatically overwrite apartment.json valuation.",
        ],
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"✅ נשמר סיכום שוק רשמי → {output_path}")
    print(
        f"   אזור סטטיסטי: {public_summary.get('statistical_area_name')} "
        f"({location.get('statistical_area_id')})"
    )
    print(f"   גרסת נתונים: {public_summary.get('dataset_version') or 'לא צוינה'}")
    latest = public_summary.get("latest_neighborhood_price_nis")
    if latest is not None:
        print(f"   מחיר שכונתי אחרון שפורסם (כל החדרים): {latest:,.0f} ₪")
    if location.get("boundary_name_mismatch"):
        print("⚠️  נוריות ממופה לאזור הסטטיסטי הישן 'מרום ראשון'; אין להסיק שזה גבול שכונה מדויק.")
    healthy_madlan = [item for item in supplemental_sources if item.get("ok", True)]
    if healthy_madlan:
        madlan = next((item for item in healthy_madlan if item.get("comparison_area") == "נוריות"), healthy_madlan[0])
        six_rooms = (madlan.get("prices_by_rooms") or {}).get("6", {})
        print(
            "✅ Madlan נסרק: 6 חד׳ חדש "
            f"{(six_rooms.get('new_build_price_nis') or 0):,.0f} ₪ · "
            f"{madlan.get('year_deals_count', '—')} עסקאות בשנה"
        )
        comparison = next((item for item in healthy_madlan if item.get("comparison_area") == "נרקיסים"), None)
        if comparison:
            comparison_six = (comparison.get("prices_by_rooms") or {}).get("6", {})
            print(
                "✅ Madlan נרקיסים: 6 חד׳ חדש "
                f"{(comparison_six.get('new_build_price_nis') or 0):,.0f} ₪ · "
                f"{comparison.get('year_deals_count', '—')} עסקאות בשנה"
            )
    else:
        print(f"⚠️  Madlan לא זמין: {source_health['madlan'].get('reason', 'unknown error')}")
    print("ℹ️  Yad2 לא שולב: הגנת anti-bot והחבילה שנבדקה אינה מממשת מודל נדל״ן.")


if __name__ == "__main__":
    main()
