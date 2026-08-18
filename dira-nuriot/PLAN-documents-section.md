# 📍 תוכנית: הוספת סקשן "מיקום, תוכניות ומסמכים רשמיים"

מסמך תכנון להוספת מפת מיקום, תוכנית הדירה, תוכנית הבניין ותיק הבניין בעירייה ללוח `index.html`.

---

## מה המערכת עושה (רקע)

לוח חי לדירה **128A5** (6 חד', נוריות, ראשון לציון, מחיר למשתכן, מסירה ~רבעון 3 2028), מתפרסם כאתר סטטי ב-GitHub Pages.

- **מקור-האמת הוא JSON**, לא HTML: `apartment.json`, `renovation.json`, `management.json`.
- `build_html.py` מרנדר את הכול ל-`index.html` (סקשנים מתקפלים, עריכות נשמרות ב-`localStorage`).
- **לכן** מוסיפים דרך המנגנון של הפרויקט: קישורים/נתונים ב-`apartment.json` + רינדור ב-`build_html.py`. **לא** עורכים ידנית את `index.html` (הוא נוצר מחדש).
- קובץ `128A5.pdf` כבר קיים בתיקייה (131KB) אך **אינו מוצג כרגע** בדף.

---

## אילוץ שנבדק (headers) — קובע embed מול link

| פריט | URL | ניתן ל-iframe? | מסקנה |
|---|---|---|---|
| מפת GIS עירונית | `v5.gis-net.co.il/v5/rishonlezion?extent=…` | ❌ `X-Frame-Options: DENY` | **link-out** (deep-link לגזרת הבניין) + תמונת מפה סטטית לויזואל |
| תוכנית הבניין | `archive.gis-net.co.il/.../202108178010.pdf` | ❌ SAMEORIGIN + **38MB** | **link-out** בלבד |
| תיק בניין בעירייה | `rishonlezion.muni.il/.../request2.aspx` | ❌ SAMEORIGIN + CSP | **link-out** בלבד |
| תוכנית הדירה | `128A5.pdf` (מקומי) | מקומית ✅ · ב-Pages ❌ | **הטמעה** ב-`<object>` עם **fallback link** |

> ⚠️ **`128A5.pdf` מסונן ב-`.gitignore`** ("Private apartment source document"), ולכן **אינו מתפרסם ב-GitHub Pages**. ההטמעה עובדת רק כשפותחים את `index.html` מקומית. באתר הפומבי ה-`<object>` נכשל — לכן הכרטיס חייב **תוכן fallback בתוך ה-`<object>`** (קישור "פתח / הורד" ל-`apartment_plan_pdf_url` המרוחק). כך הכרטיס תקין בשני המצבים בלי לחשוף את הקובץ הפרטי.

---

## ההחלטות שנבחרו

- **ויזואל מפה:** **חלון מפה חי מוטמע (OpenStreetMap embed)** ממורכז על הבניין עם marker — כי gis-net חוסם iframe (`X-Frame-Options: DENY`) ולא ניתן להטמיע אותו ישירות. הקואורדינטות (`map_lat/map_lon/map_bbox`) הומרו מ-ITM (EPSG:2039) ל-WGS84 מתוך ה-`extent` של ה-deep-link (מרכז ≈ 31.965129, 34.831139). מתחת לחלון: **כפתור "פתח GIS עירוני (עם כל השכבות)"** ל-`city_gis_url` בכרטיסייה חדשה — שם נמצאים גושים/חלקות, תצ״א ותוכניות. ⚠️ החלון החי דורש אינטרנט (לא offline); אם אין `map_bbox` בנתונים — נופלים חזרה ל-placeholder של `location_map_image`.
- **תוכנית הבניין (38MB):** link-out בלבד — לא מורידים לריפו, שומר על הריפו קל.

---

## מבנה ההוספה

### סקשן חדש אחד — מיקום בדף
מיד אחרי ה-`<div class="toolbar">`/`toast` (כלומר אחרי ה-`<header>`) ולפני הסקשן `🩺 מצב מערכת ונתונים` — הכי גבוה מבין הסקשנים.

כותרת: **`📍 מיקום, תוכניות ומסמכים רשמיים`** — סקשן מתקפל (כמו כל השאר), עם רשת של 4 כרטיסים:

1. **מפת מיקום** — `<iframe>` מפה חיה (OSM embed) עם marker על הבניין + כפתור בולט **"פתח GIS עירוני (עם כל השכבות) ↗"** → `city_gis_url` (tab חדש). fallback ל-placeholder אם חסרות קואורדינטות.
2. **תוכנית הדירה** — הטמעת `128A5.pdf` המקומי ב-`<object>` מתקפל + קישור "פתח / הורד" ל-`apartment_plan_pdf_url`.
3. **תוכנית הבניין** — כרטיס link-out ל-`building_plan_pdf_url` + הערה שהקובץ גדול (~38MB).
4. **תיק הבניין בעירייה** — כרטיס link-out ל-`cityhall_building_url` (בקשה `#request/20210817`).

### מודל נתונים — הוספה ל-`apartment.json`

```json
"documents": {
  "_comment": "מיקום, תוכניות ומסמכים רשמיים. מוצג בסקשן 'מיקום ומסמכים'.",
  "apartment_plan_pdf_local": "128A5.pdf",
  "apartment_plan_pdf_url": "https://nuriot.o-aharon.co.il/data/pdf/128/128A5.pdf",
  "building_plan_pdf_url": "https://archive.gis-net.co.il/Rishon/files/Scan/4237/129/202108178010.pdf",
  "building_plan_note": "סריקת תיק בניין (~38MB) — נפתח באתר gis-net",
  "city_gis_url": "https://v5.gis-net.co.il/v5/rishonlezion?extent=183630,652257,184706,652768&layers=105,101,233&back=ortho&year=2026&overview=0&opacity=0.9",
  "cityhall_building_url": "https://www.rishonlezion.muni.il/Residents/Construction/newengine/Pages/request2.aspx#request/20210817",
  "cityhall_request_id": "20210817",
  "location_map_image": "assets/location-map.png"
}
```

### שינויים ב-`build_html.py`

1. לקרוא `docs = apt.get("documents", {})` ב-`main()` (ליד שאר `apt.get(...)`).
2. לבנות מחרוזת `documents_section` (סקשן + 4 כרטיסים), על בסיס אותם קלאסים קיימים: `section`, `card`, `grid`, `src`, `pill`, `note`.
3. לשלב `{documents_section}` ל-`body` מיד אחרי `</header>`.
4. ה-collapse-all/expand-all עובד אוטומטית (JS רץ על כל `<section>`), אין צורך בשינוי לוגיקה.

### נכסים

- `dira-nuriot/assets/location-map.png` — צילום מסך של מפת gis-net שמראה את הבניין (רצוי באותה גזרה כמו ה-deep-link: `extent=183630,652257,184706,652768`).
- **`.gitignore`:** `assets/` **אינו** מסונן (גם `photo.jpg` אינו מסונן — רק `128A5.pdf`, `updates/raw-*`, `deals-*.json`, `snapshots/` ו-status/history), ולכן התמונה תיכלל ותתפרסם כרגיל.
- אם התמונה עדיין לא הוכנה — `build_html.py` יציג כרטיס placeholder עם הקישור ל-GIS בלבד (בדיוק כמו ה-placeholder של `photo.jpg`), בלי לשבור את הבנייה.

---

## נקודות לאימות לפני/בזמן מימוש

- **gush/helka:** נתיב הבניין `.../Scan/4237/129/...` ובקשת העירייה `20210817`; ב-`apartment.json` יש `plot: 128`. לוודא שהמסמכים הם של אותו בניין/דירה.
- **`.gitignore`:** לוודא ש-`assets/location-map.png` לא מסונן.
- **בדיקה:** להריץ `python3 build_html.py` ולפתוח את `index.html` — לוודא שה-PDF המקומי מוטמע, שהתמונה נטענת, ושכל 4 הקישורים נפתחים ב-tab חדש.

---

## סדר ביצוע

1. שמירת `assets/location-map.png` (צילום מפת gis-net).
2. הוספת בלוק `documents` ל-`apartment.json`.
3. הוספת `documents_section` ורינדורו ב-`build_html.py`.
4. הרצת `build_html.py` ובדיקה ויזואלית.
5. עדכון `README.md` (מבנה תיקייה + שורת index אם רלוונטי) ו-commit.
