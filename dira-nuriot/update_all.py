#!/usr/bin/env python3
"""Run the complete update pipeline and persist machine-readable status/history."""
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES = os.path.join(HERE, "updates")
STATUS_PATH = os.path.join(UPDATES, "update-status.json")
HISTORY_PATH = os.path.join(UPDATES, "update-history.json")
# Committed (not git-ignored) so CI checkouts can rebuild and the page can show real freshness.
MARKET_LATEST_PATH = os.path.join(HERE, "market_latest.json")
MARKET_STATUS_PATH = os.path.join(HERE, "market_status.json")


def run_stage(name, command):
    started = time.monotonic()
    completed = subprocess.run(command, cwd=HERE, text=True, capture_output=True, encoding="utf-8", errors="replace")
    return {
        "name": name,
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 2),
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def snapshot(stamp):
    target = os.path.join(UPDATES, "snapshots", stamp)
    os.makedirs(target, exist_ok=True)
    copied = []
    for name in ("apartment.json", "renovation.json", "management.json"):
        source = os.path.join(HERE, name)
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(target, name))
            copied.append(name)
    deals = os.path.join(UPDATES, f"deals-{datetime.date.today().isoformat()}.json")
    if os.path.exists(deals):
        shutil.copy2(deals, os.path.join(target, os.path.basename(deals)))
        copied.append(os.path.basename(deals))
    return {"ok": True, "path": os.path.relpath(target, HERE), "files": copied}


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def merge_market(new, previous):
    """Latest fetch, but a source that failed this run keeps its last-good entry (tagged stale).

    Madlan/Nadlan block some runs (403); without this a single blocked run would blank the
    dashboard's market section until the next lucky run.
    """
    merged = dict(new)
    prev_sources = {s.get("comparison_area"): s for s in (previous or {}).get("supplemental_sources", [])
                    if s.get("ok", True)}
    sources = []
    for item in new.get("supplemental_sources", []):
        old = prev_sources.get(item.get("comparison_area"))
        if not item.get("ok", True) and old:
            kept = dict(old)
            kept["stale"] = True
            kept["stale_reason"] = item.get("error", "fetch failed")
            sources.append(kept)
        else:
            sources.append(item)
    merged["supplemental_sources"] = sources
    return merged


def write_market_files(fetch_stage, now):
    """Persist market_latest.json (on success) + market_status.json (always)."""
    status = _load(MARKET_STATUS_PATH, {})
    status["last_attempt"] = now.isoformat()
    status["last_attempt_ok"] = bool(fetch_stage.get("ok"))
    deals = os.path.join(UPDATES, f"deals-{datetime.date.today().isoformat()}.json")
    if fetch_stage.get("ok") and os.path.exists(deals):
        merged = merge_market(_load(deals, {}), _load(MARKET_LATEST_PATH, {}))
        with open(MARKET_LATEST_PATH, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, ensure_ascii=False, indent=2)
        status["last_success"] = now.isoformat()
        status["sources_ok"] = {k: bool(v.get("ok")) for k, v in (merged.get("source_health") or {}).items()}
        status.pop("last_error", None)
    else:
        # Keep the most informative line (e.g. "HTTP Error 403") for the dashboard banner.
        output = fetch_stage.get("stdout", "") + "\n" + fetch_stage.get("stderr", "")
        lines = [line for line in output.splitlines() if "⚠" in line or "Error" in line]
        status["last_error"] = (lines[0] if lines else f"exit {fetch_stage.get('exit_code')}").strip()[:300]
    with open(MARKET_STATUS_PATH, "w", encoding="utf-8") as handle:
        json.dump(status, handle, ensure_ascii=False, indent=2)
    return status


def market_only(now):
    """--market-only: fetch + persist market_latest/market_status, nothing else.

    Run from an Israeli residential IP (refresh_market.cmd on the home PC): Nadlan answers 403
    to GitHub runners, so CI no longer fetches market data and only commits these two files'
    consumers (index.html). Exit 1 when the fetch failed so the caller skips the commit.
    """
    fetch_stage = run_stage("fetch", [sys.executable, "fetch_deals.py"])
    write_market_files(fetch_stage, now)
    print(("✅" if fetch_stage.get("ok") else "❌") + f" fetch ({fetch_stage.get('duration_seconds', 0)}s)")
    if not fetch_stage.get("ok"):
        print((fetch_stage.get("stderr") or fetch_stage.get("stdout"))[-500:])
    return 0 if fetch_stage.get("ok") else 1


def main():
    os.makedirs(UPDATES, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    if "--market-only" in sys.argv:
        raise SystemExit(market_only(now))
    # --skip-market (CI): GitHub runners get 403 from Nadlan, so a CI fetch only ever overwrote
    # market_status.json with "failed" and hid the home PC's good fetch. CI keeps index + rebuild.
    skip_market = "--skip-market" in sys.argv

    # Market fetch is best-effort: Nadlan/Madlan return 403 to datacenter IPs (GitHub runners)
    # and GovMap's TLS is flaky. A failed fetch must not fail the workflow; instead it is recorded
    # in market_status.json and the dashboard is rebuilt from the committed market_latest.json,
    # so the page can say "last good data from X" rather than silently looking fresh.
    # Construction-inputs index (CBS API) is independent and best-effort too.
    index_stage = run_stage("index", [sys.executable, "fetch_index.py"])
    if skip_market:
        fetch_stage = {"name": "fetch", "ok": True, "skipped": True, "duration_seconds": 0}
        stages = [index_stage]
        fetch_ok = False  # no fresh deals file -> no snapshot this run
    else:
        fetch_stage = run_stage("fetch", [sys.executable, "fetch_deals.py"])
        stages = [index_stage, fetch_stage]
        fetch_ok = fetch_stage.get("ok")
        write_market_files(fetch_stage, now)
    market_status = _load(MARKET_STATUS_PATH, {})
    stages.append(run_stage("validate", [sys.executable, "validate_data.py", "--strict"]))
    if fetch_ok:
        stages.append({"name": "snapshot", "duration_seconds": 0, **snapshot(stamp)})
    stages.append(run_stage("build", [sys.executable, "build_html.py"]))

    # Only the ability to rebuild a valid dashboard is critical for the exit code.
    critical_ok = all(s.get("ok", True) for s in stages if s["name"] in ("validate", "build"))
    status = {
        "run_id": stamp,
        "started_at": now.isoformat(),
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ok": all(stage.get("ok") for stage in stages),
        "fetch_ok": bool(fetch_ok),
        "rebuilt": True,
        "stages": stages,
    }
    with open(STATUS_PATH, "w", encoding="utf-8") as handle:
        json.dump(status, handle, ensure_ascii=False, indent=2)
    history = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, encoding="utf-8") as handle:
                history = json.load(handle)
        except (json.JSONDecodeError, OSError):
            history = []
    history.append({"run_id": stamp, "completed_at": status["completed_at"], "ok": status["ok"], "stages": [{"name": s["name"], "ok": s.get("ok"), "duration_seconds": s.get("duration_seconds", 0)} for s in stages]})
    with open(HISTORY_PATH, "w", encoding="utf-8") as handle:
        json.dump(history[-100:], handle, ensure_ascii=False, indent=2)
    # Rebuild once more so the embedded dashboard contains this run's final status.
    subprocess.run([sys.executable, "build_html.py"], cwd=HERE, capture_output=True)
    for stage in stages:
        mark = "✅" if stage.get("ok") else "❌"
        print(f"{mark} {stage['name']} ({stage.get('duration_seconds', 0)}s)")
        if stage.get("stdout"):
            print(stage["stdout"])
        if stage.get("stderr"):
            print(stage["stderr"], file=sys.stderr)
    if skip_market:
        # The home PC is the only fetcher now; warn in CI when it has gone quiet (PC off, task broken).
        last = market_status.get("last_success")
        age = (now - datetime.datetime.fromisoformat(last)).days if last else None
        if age is None or age > 10:
            msg = f"נתוני השוק לא רועננו {age if age is not None else '?'} ימים — בדקו את המשימה המתוזמנת DiraMarketRefresh במחשב הבית."
            print("⚠️  " + msg, file=sys.stderr)
            if os.environ.get("GITHUB_ACTIONS"):
                print(f"::warning title=Market data stale::{msg}")
    elif not fetch_ok:
        msg = (f"שאיבת נתוני השוק נכשלה ({market_status.get('last_error', '')}) — "
               f"הלוח נבנה מנתוני השוק האחרונים שנשמרו ({market_status.get('last_success') or 'אין'}).")
        print("⚠️  " + msg, file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS"):
            # Surfaces as a yellow annotation on the run instead of a silent green check.
            print(f"::warning title=Market data not refreshed::{msg}")
    raise SystemExit(0 if critical_ok else 2)


if __name__ == "__main__":
    main()
