#!/usr/bin/env python3
"""Fetch the CBS residential construction-inputs index (מדד תשומות הבנייה למגורים) series.

Writes construction_index.json: {"YYYY-MM": value} on CBS's *current* base (Jul 2025=100),
starting at the contract base month (apartment.json → payments.index_base_period). The dashboard
uses ratios between months, so the base CBS happens to publish on doesn't matter as long as the
whole series is on one base. Stdlib only; exits non-zero on failure but never touches the file
then (last-good series is kept).
"""
import datetime
import json
import os
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "construction_index.json")
SERIES_ID = 200010  # CBS: "מדד מחירי תשומה בבנייה למגורים - כללי"
API = "https://api.cbs.gov.il/index/data/price?id={id}&format=json&download=false&last={last}&lang=he"


def parse_series(payload, since):
    """CBS API JSON → {"YYYY-MM": value} for months >= since, all on the newest base.

    Rows from before a CBS rebase carry an older currBase (e.g. Jul 2011=100); mixing them would
    corrupt ratios, so only rows sharing the newest row's base are kept.
    """
    rows = payload["month"][0]["date"]
    newest_base = rows[0]["currBase"]["baseDesc"]
    out = {}
    for r in rows:
        if r["currBase"]["baseDesc"] != newest_base:
            continue
        key = f'{r["year"]:04d}-{r["month"]:02d}'
        if key >= since:
            out[key] = r["currBase"]["value"]
    return dict(sorted(out.items())), newest_base


def main():
    with open(os.path.join(HERE, "apartment.json"), encoding="utf-8") as f:
        pay = json.load(f).get("payments", {})
    since = pay.get("index_base_period", "2025-10")
    y, m = map(int, since.split("-"))
    today = datetime.date.today()
    last = (today.year - y) * 12 + (today.month - m) + 2
    req = urllib.request.Request(API.format(id=SERIES_ID, last=last), headers={"User-Agent": "dira-nuriot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    series, base_desc = parse_series(payload, since)
    if since not in series:
        # Contract base month must be on the same CBS base, or every ratio would be wrong.
        raise SystemExit(f"❌ חודש הבסיס {since} חסר בסדרה (בסיס CBS: {base_desc})")
    doc = {
        "_comment": "נשאב אוטומטית מ-API של הלמ\"ס (fetch_index.py). ערכים בבסיס הלמ\"ס הנוכחי — הלוח משתמש ביחסים בלבד.",
        "series_id": SERIES_ID,
        "cbs_base": base_desc,
        "fetched": today.isoformat(),
        "source": "https://api.cbs.gov.il/index/data/price?id=200010",
        "series": series,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    latest = list(series)[-1]
    print(f"✅ מדד תשומות הבנייה: {len(series)} חודשים, אחרון {latest} = {series[latest]} (בסיס {base_desc})")


if __name__ == "__main__":
    main()
