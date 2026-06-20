"""Yad2 adapter (best-effort).

Saves raw HTML to updates/ and extracts heuristic comparable listings. Results
must be validated before they are used for valuation.
"""
import urllib.request
import urllib.parse
import datetime
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES_DIR = os.path.join(HERE, "..", "updates")


def _save_raw(prefix, content, ext="html"):
    try:
        os.makedirs(UPDATES_DIR, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(UPDATES_DIR, f"{prefix}-{ts}.{ext}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
    except Exception:
        return None


import re

def _parse_html_for_comps(html):
    items = []
    price_re = re.compile(r"(₪\s*)?(\d[\d,]{3,})")
    area_re = re.compile(r"(\d{2,3}(?:[\.,]\d)?)\s*(מ\"ר|מר|מ\'ר|sqm|m2)", re.IGNORECASE)
    prices = [m for m in price_re.finditer(html)]
    areas = [m for m in area_re.finditer(html)]
    n = min(len(prices), len(areas))
    for i in range(n):
        pr = prices[i].group(2)
        ar = areas[i].group(1)
        try:
            price = int(str(pr).replace(',', ''))
            area = float(str(ar).replace(',', '.'))
        except Exception:
            continue
        # grab nearby text for address
        span_start = max(0, min(prices[i].start(), areas[i].start()) - 120)
        span_end = min(len(html), max(prices[i].end(), areas[i].end()) + 120)
        ctx = html[span_start:span_end]
        addr_match = re.search(r"([\u0590-\u05FF\w\s\-\d\.,]{5,80})", ctx)
        addr = addr_match.group(1).strip() if addr_match else ""
        items.append({"DEALAMOUNT": str(price), "_area_sqm": area, "FULLADRESS": addr})
    return items


def fetch(query):
    try:
        q = urllib.parse.quote(query)
        url = f"https://www.yad2.co.il/search?text={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (dira-nuriot)"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
            _save_raw("yad2-search", body, ext="html")
            return _parse_html_for_comps(body)
    except Exception:
        return []
