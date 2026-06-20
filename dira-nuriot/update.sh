#!/usr/bin/env bash
# נקודת כניסה דו-מצבית לעדכון נתוני הדירה.
# ניידות: bash + python3 stdlib בלבד. מעתיקים את התיקייה לכל מחשב ומריצים.
#
#   ./update.sh data     צינור מלא: נתוני שוק, אימות, snapshot, סטטוס ו-HTML
#   ./update.sh agent     מצב "אייג'נט": מדפיס את פרומפט המחקר (הזן ל-Claude / claude -p)
#   ./update.sh html      בונה מחדש את index.html בלבד
#   ./update.sh           ברירת מחדל: data → html → מציע agent

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PY="$(command -v python3 || command -v python || true)"
if [[ -z "$PY" ]]; then echo "❌ צריך python3 מותקן." >&2; exit 1; fi

mode="${1:-default}"

run_data() {
  echo "═══ עדכון מלא: נתונים → אימות → snapshot → HTML ═══"
  local query="${1:-}"
  if [[ -n "$query" ]]; then
    "$PY" fetch_deals.py "$query"
    "$PY" validate_data.py --strict
    "$PY" build_html.py
  else
    "$PY" update_all.py
  fi
}

run_html() {
  echo "═══ בונה index.html ═══"
  "$PY" build_html.py
}

case "$mode" in
  data)  shift; run_data "${1:-}" ;;
  html)  run_html ;;
  agent)
    echo "═══ מצב אייג'נט — העתק את הפרומפט הבא ל-Claude (או: claude -p \"\$(cat PROMPT.md)\") ═══"
    echo
    cat PROMPT.md
    ;;
  default)
    run_data "$@"
    echo
    echo "💡 לעדכון מחקר עמוק (שווי + שיפוץ עם מקורות) הרץ:  ./update.sh agent"
    ;;
  *)
    echo "שימוש: ./update.sh [data|agent|html]" >&2; exit 1 ;;
esac

echo "✅ סיום. פתח את index.html בדפדפן."
