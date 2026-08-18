# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-apartment "living document" and dashboard for a specific מחיר-למשתכן apartment
(code `128A5`) in the נוריות neighborhood, ראשון לציון. It fetches public Israeli real-estate
market data, tracks a renovation budget/valuation, and renders a self-contained
`dira-nuriot/index.html` dashboard published via GitHub Pages. The primary audience and UI
language is **Hebrew (RTL)**; write user-facing strings, commit-relevant docs, and dashboard
copy in Hebrew, code/comments in English.

## Layout note (important)

The repo root and the Python package share the name `dira-nuriot`, so the actual project code
lives in `dira-nuriot/dira-nuriot/`. All Python scripts, JSON data, and schemas are in that
inner directory; `tests/` and `.github/` are at the repo root.

## Commands

Run from the repo root. There is no pytest config file — `pytest` discovers `tests/` by default.

```bash
pytest -q                                  # full suite (offline; uses tests/fixtures/)
pytest tests/test_fetch_deals.py -q        # one file
pytest tests/test_fetch_deals.py::test_summarize_basic   # one test
flake8                                      # lint (dev dependency)
pip install -r requirements-dev.txt         # pytest, jsonschema, requests, flake8

python dira-nuriot/build_html.py            # rebuild index.html from the JSON data (stdlib only)
python dira-nuriot/update_all.py            # full pipeline: fetch → validate → snapshot → build
python dira-nuriot/fetch_deals.py [query]   # fetch public market data (network; default query = נוריות)
python dira-nuriot/validate_data.py --strict  # schema-validate the JSON (exit 2 on failure)
```

`dira-nuriot/update.sh [data|agent|html]` is the portable bash entry point (bash + python3
stdlib only). On this Windows box, invoke the Python scripts directly instead.

## Architecture

**Data-driven, no runtime server.** Four JSON files in `dira-nuriot/` are the source of truth;
`build_html.py` embeds them into a fully self-contained `index.html` (inline CSS/JS, no external
requests) that runs offline and persists user edits to `localStorage`. Do not hand-edit
`index.html` — regenerate it from the data.

- `apartment.json` — fixed facts + `valuation` + `valuation_history` + selling restrictions + to-dos. Source of truth for value.
- `renovation.json` — renovation budget (2026 ranges) + Gantt schedule.
- `management.json` — valuation model, comparables, cash flow, defect tracking.
- `*.schema.json` — Draft-7 schemas; `validate_data.py` is **permissive by default, strict with `--strict`**.

**Two update modes** (see `dira-nuriot/PROMPT.md`, `dira-nuriot/README.md`):
- *data mode* — automated fetch of public market summaries.
- *agent mode* — a research agent reads `PROMPT.md` and manually refreshes valuation/renovation
  figures with **sourced, dated numbers**, appends an `updates/YYYY-MM-DD.md` snapshot, and
  never overwrites history.

**Fetch layer** (`fetch_deals.py` + `adapters/`):
- Only public, unattended endpoints are used. Individual nadlan.gov.il transaction rows are
  reCAPTCHA-protected and deliberately **not** scraped — the code records that limitation
  rather than substituting unverified data.
- `resolve_neighborhood` uses GovMap to map a neighborhood to Nadlan's legacy statistical-area
  ID, with hardcoded verified location seeds (`KNOWN_LOCATIONS`) as a TLS-failure fallback.
- `adapters/` auto-discovers any module exposing `fetch(query)`; adapter failures are caught and
  never abort the pipeline. `madlan.py` parses SSR-hydrated JSON (market indicator, kept separate
  from government data); `yad2.py` is intentionally not wired in (anti-bot).
- Raw responses and snapshots are written under `updates/` for provenance and are **git-ignored**
  (only `index.html`, dated `updates/*.md`, and the JSON data are committed).

## Conventions

- **Never invent numbers.** Every market/renovation figure needs a source + date; mark estimates
  as such with a confidence level. Append new `updates/` snapshots — do not overwrite old ones.
- Tests are **offline**: they load the hyphen-named modules via `SourceFileLoader`/importlib
  (the package name isn't a valid import) and use `tests/fixtures/` HTML rather than live network.
  Keep new tests network-free.
- Runtime scripts use **Python stdlib only** (`urllib`, not `requests`); `requests`/`jsonschema`
  are dev/validation dependencies. Scripts `reconfigure` stdout/stderr to UTF-8 for Hebrew output.
- Pipelines target **Python 3.11** (CI and the scheduled workflow); a local `.venv` may be older.

## CI / publishing

- `.github/workflows/ci.yml` runs `pytest -q` on push/PR to main/master.
- `.github/workflows/refresh-data.yml` runs `update_all.py` weekly (Mon 06:15 IL) and on manual
  dispatch, committing a refreshed `index.html`.
- GitHub Pages deploys from `main` at repo root; root `index.html` redirects to `dira-nuriot/`.
