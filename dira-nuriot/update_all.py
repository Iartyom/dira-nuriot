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


def main():
    os.makedirs(UPDATES, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    stages = [
        run_stage("fetch", [sys.executable, "fetch_deals.py"]),
        run_stage("validate", [sys.executable, "validate_data.py", "--strict"]),
    ]
    stages.append({"name": "snapshot", "duration_seconds": 0, **snapshot(stamp)})
    stages.append(run_stage("build", [sys.executable, "build_html.py"]))
    status = {
        "run_id": stamp,
        "started_at": now.isoformat(),
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ok": all(stage.get("ok") for stage in stages),
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
    raise SystemExit(0 if status["ok"] else 2)


if __name__ == "__main__":
    main()
