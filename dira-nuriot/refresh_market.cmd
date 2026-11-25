@echo off
rem Weekly market-data refresh from the home PC (scheduled task "DiraMarketRefresh").
rem Why here and not CI: Nadlan answers 403 to GitHub runners but not to an Israeli home IP.
rem Commits only market_latest/market_status (CI never touches them -> no merge conflicts),
rem then triggers the GitHub workflow, which rebuilds index.html from them.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
git pull --rebase --autostash -q
.venv\Scripts\python.exe dira-nuriot\update_all.py --market-only
if errorlevel 1 (
  rem Failed fetch: drop the "failed" status locally; the last good data stays published.
  git checkout -- dira-nuriot/market_status.json
  exit /b 1
)
git add dira-nuriot/market_latest.json dira-nuriot/market_status.json
git diff --cached --quiet && exit /b 0
git commit -q -m "רענון נתוני שוק (מחשב הבית)"
git push -q && gh workflow run refresh-data.yml
