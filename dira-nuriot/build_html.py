#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מייצר index.html self-contained — אתר ניהול שיפוץ + שווי + תשלומים + שכונה + פליפ (RTL).
נתונים מוטמעים → נפתח בדפדפן בלי שרת, offline, נייד. אינטראקטיבי (localStorage):
בחירת אפשרויות שיפוץ → מחשבת תקציב/לו"ז/אנשי מקצוע/משימות. סימון תשלומים ומשימות.
stdlib בלבד. שימוש: python3 build_html.py
"""
import json
import os
import glob
import datetime
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "index.html")


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def shekel(n):
    try:
        return f"{int(round(float(n))):,} ₪"
    except (ValueError, TypeError):
        return "—"


def find_photo():
    for ext in ("jpg", "jpeg", "png", "webp"):
        for name in (f"photo.{ext}", f"dira.{ext}"):
            if os.path.exists(os.path.join(HERE, name)):
                return name
    return None


CSS = """
:root { --bg:#0b1120; --card:#16213a; --card2:#1b2748; --ink:#e6edf6; --muted:#8da2bd;
        --accent:#38bdf8; --gold:#fbbf24; --green:#22c55e; --red:#f87171; --line:#2a3a5c; }
* { box-sizing:border-box; }
body { margin:0; font-family:-apple-system,"Segoe UI",Rubik,Arial,sans-serif; background:var(--bg); color:var(--ink); line-height:1.65; }
.wrap { max-width:1080px; margin:0 auto; padding:20px 16px 80px; }
header { display:flex; gap:20px; align-items:center; flex-wrap:wrap; padding:18px 0; border-bottom:1px solid var(--line); }
header .info h1 { margin:0; font-size:26px; }
header .info .meta { color:var(--muted); margin-top:4px; font-size:14px; }
.photo { flex:0 0 220px; height:150px; border-radius:14px; overflow:hidden; border:1px solid var(--line); }
.photo img { width:100%; height:100%; object-fit:cover; }
.photo.placeholder { display:flex; align-items:center; justify-content:center; text-align:center; color:var(--muted); background:var(--card); font-size:13px; padding:10px; }
.grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); margin:18px 0; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; }
.card h3 { font-size:12px; color:var(--accent); margin:0 0 8px; text-transform:uppercase; letter-spacing:.5px; }
.big { font-size:24px; font-weight:800; }
.sub { color:var(--muted); font-size:12.5px; margin-top:4px; }
section { margin-top:32px; }
section > h2 { border-right:3px solid var(--accent); padding-right:10px; font-size:20px; }
table { width:100%; border-collapse:collapse; }
td,th { text-align:right; padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:top; }
th { color:var(--accent); font-size:12px; }
.note { color:var(--muted); font-size:12px; font-weight:400; margin-top:2px; }
.num { white-space:nowrap; color:var(--muted); }
input.price { width:110px; background:var(--bg); border:1px solid var(--line); color:var(--ink); border-radius:8px; padding:6px 9px; font-size:14px; }
.foot { display:flex; justify-content:space-between; align-items:center; gap:14px; flex-wrap:wrap; margin-top:14px; padding:14px 18px; background:var(--card2); border-radius:12px; }
.foot .big2 { font-size:20px; font-weight:800; color:var(--gold); }
.week { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:6px 18px 14px; margin-bottom:12px; }
.week-head { display:flex; gap:10px; align-items:center; padding:12px 0 8px; border-bottom:1px dashed var(--line); flex-wrap:wrap; }
.wk { background:var(--accent); color:#04293b; font-weight:800; border-radius:8px; padding:3px 10px; font-size:13px; }
.wk-title { font-weight:700; }
.trade { margin-inline-start:auto; color:var(--muted); font-size:11.5px; border:1px solid var(--line); border-radius:20px; padding:2px 10px; }
ul.tasks { list-style:none; margin:8px 0 0; padding:0; }
ul.tasks li { padding:6px 0; }
ul.tasks label { display:flex; gap:9px; align-items:flex-start; cursor:pointer; }
ul.tasks .days { color:var(--gold); font-size:12px; font-weight:700; white-space:nowrap; margin-top:2px; }
input[type=checkbox] { width:18px; height:18px; margin-top:3px; accent-color:var(--green); flex:0 0 auto; cursor:pointer; }
.done > label, label.done { opacity:.5; text-decoration:line-through; }
ul.flat { list-style:none; margin:0; padding:0; }
ul.flat li { display:flex; gap:10px; align-items:center; padding:10px; border-bottom:1px solid var(--line); }
ul.flat label { display:flex; gap:9px; align-items:center; cursor:pointer; flex:1; }
ul.flat .pri { font-size:12px; color:var(--muted); white-space:nowrap; }
.opt { display:grid; grid-template-columns:24px 1fr auto auto; gap:10px; align-items:start; padding:11px 0; border-bottom:1px solid var(--line); }
.opt .name { font-weight:600; }
.opt .ess { font-size:10.5px; color:#04293b; background:var(--gold); border-radius:6px; padding:1px 6px; margin-inline-start:6px; }
.vb { font-size:10.5px; border-radius:6px; padding:1px 7px; margin-inline-start:6px; font-weight:700; }
.vb-h { background:#16a34a; color:#fff; }
.vb-m { background:#1b2748; color:#7dd3fc; border:1px solid #38bdf8; }
.opt .rng { color:var(--muted); font-size:12px; white-space:nowrap; align-self:center; }
.diyline { margin-top:6px; padding-top:6px; border-top:1px dashed var(--line); display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
.diychk { display:inline-flex; align-items:center; gap:6px; cursor:pointer; background:#06281f; border:1px solid #22c55e; color:#bbf7d0; padding:2px 10px; border-radius:20px; font-size:12.5px; }
.diychk input { margin:0; width:15px; height:15px; }
.prodprice { font-size:12px; color:var(--gold); }
.addbtn { margin-top:10px; background:var(--accent); color:#04293b; border:0; border-radius:8px; padding:8px 16px; font-weight:700; cursor:pointer; font-size:14px; }
.addbtn:hover { opacity:.9; }
table input.cell { width:100%; background:var(--bg); border:1px solid var(--line); color:var(--ink); border-radius:6px; padding:6px 8px; font-size:13px; }
.delbtn { background:none; border:0; color:var(--red); cursor:pointer; font-size:16px; }
.vtrend { font-size:15px; margin-bottom:10px; font-weight:700; }
.vchart { display:flex; align-items:flex-end; gap:16px; height:200px; padding:30px 0 0; }
.vbar { flex:1; display:flex; flex-direction:column; align-items:center; height:100%; justify-content:flex-end; }
.vbar-fill { width:70%; max-width:90px; background:linear-gradient(180deg,#38bdf8,#22d3ee 55%,#34d399); border-radius:8px 8px 0 0; min-height:4px; position:relative; display:flex; justify-content:center; }
.vbar-amt { position:absolute; top:-24px; font-size:15px; font-weight:800; color:var(--gold); white-space:nowrap; }
.vbar-lbl { font-size:12px; color:var(--muted); margin-top:7px; text-align:center; }
.vbar-lbl b { color:var(--ink); display:block; }
.area-cell { color:var(--gold); font-weight:700; white-space:nowrap; }
.szt { font-size:10px; font-weight:700; border-radius:6px; padding:1px 7px; margin-inline-start:5px; }
.szt-s { background:#7f1d1d; color:#fecaca; }
.szt-m { background:#1b2748; color:#7dd3fc; border:1px solid #38bdf8; }
.szt-l { background:#14532d; color:#bbf7d0; }
.tglegend { font-size:12.5px; color:var(--muted); margin-bottom:8px; }
.tg-k { display:inline-block; width:12px; height:12px; border-radius:3px; vertical-align:middle; margin-inline-start:4px; }
.tgwrap { display:flex; align-items:flex-end; gap:10px; height:170px; padding:24px 0 0; border-bottom:1px solid var(--line); }
.tg { flex:1; display:flex; flex-direction:column; align-items:center; height:100%; justify-content:flex-end; }
.tg-bars { display:flex; gap:3px; align-items:flex-end; height:100%; width:100%; justify-content:center; }
.tg-b { width:42%; max-width:26px; border-radius:4px 4px 0 0; min-height:4px; position:relative; }
.tg-b span { position:absolute; top:-17px; left:50%; transform:translateX(-50%); font-size:10px; color:var(--muted); }
.tg-area { background:#38bdf8; }
.tg-nat { background:#64748b; }
.tg-yr { font-size:11px; color:var(--muted); margin-top:6px; }
.toolbar { display:flex; gap:8px; margin:14px 0 0; }
.toolbar { flex-wrap:wrap; }
.badge { display:inline-flex; align-items:center; gap:5px; border-radius:999px; padding:3px 9px; font-size:11px; font-weight:700; border:1px solid var(--line); }
.badge-ok { color:#bbf7d0; background:#06281f; border-color:#166534; }
.badge-warn { color:#fde68a; background:#3b1f06; border-color:#b45309; }
.badge-bad { color:#fecaca; background:#3f1117; border-color:#991b1b; }
.badge-info { color:#bae6fd; background:#082f49; border-color:#0369a1; }
.health-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; }
.health-item { background:var(--card2); border:1px solid var(--line); border-radius:10px; padding:12px; }
.health-item b { display:block; margin-bottom:3px; }
.metric-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:12px; }
.metric { flex:1 1 150px; background:var(--card2); border-radius:10px; padding:12px; }
.metric strong { display:block; font-size:19px; color:var(--gold); }
.scroll { overflow-x:auto; }
.scenario-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; margin-top:12px; }
.scenario { background:var(--card2); border:1px solid var(--line); border-radius:10px; padding:12px; text-align:center; }
.scenario strong { display:block; color:var(--gold); font-size:20px; }
.field-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }
.field-grid label { color:var(--muted); font-size:12px; }
.field-grid input { display:block; width:100%; margin-top:4px; }
.status-line { display:flex; justify-content:space-between; gap:10px; padding:7px 0; border-bottom:1px dashed var(--line); }
.status-line:last-child { border-bottom:0; }
.filebtn { position:relative; overflow:hidden; display:inline-block; }
.filebtn input { position:absolute; inset:0; opacity:0; cursor:pointer; }
.toast { min-height:20px; color:var(--muted); font-size:12px; margin-top:6px; }
@media (max-width:700px){ td,th{padding:7px 6px;font-size:12px} input.price{width:90px}.wrap{padding-inline:10px}.card{padding:13px} }
section > h2 { cursor:pointer; user-select:none; }
section > h2:hover { color:var(--accent); }
.toggle-ind { display:inline-block; width:1.1em; color:var(--accent); font-size:14px; }
.progress { height:8px; background:var(--bg); border-radius:20px; overflow:hidden; margin:6px 0 0; }
.progress > i { display:block; height:100%; background:var(--green); width:0; transition:width .3s; }
.warn { background:#3b1f06; border:1px solid #b45309; color:#fde68a; border-radius:10px; padding:12px 16px; font-size:14px; margin-top:10px; }
.pillrow { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
.pill { font-size:12.5px; background:var(--card2); border:1px solid var(--line); padding:4px 11px; border-radius:20px; }
.restr div, .nb div { padding:6px 0; border-bottom:1px dashed var(--line); font-size:13.5px; }
.restr b, .nb b { color:var(--accent); }
.src { margin-top:10px; display:flex; flex-wrap:wrap; gap:8px; }
.src a { font-size:12px; color:var(--accent); background:var(--card2); padding:4px 10px; border-radius:20px; text-decoration:none; }
.tier { border-inline-start:3px solid var(--gold); padding:4px 14px; margin:12px 0; background:var(--card2); border-radius:0 12px 12px 0; }
.tier h4 { margin:6px 0 4px; }
.tier .price { color:var(--gold); font-weight:700; }
.paid-yes { color:var(--green); }
.paid-no { color:var(--muted); }
.next { background:#06281f; border:1px solid var(--green); border-radius:10px; padding:10px 14px; margin-top:10px; font-size:14px; }
code { background:#04293b; padding:2px 6px; border-radius:6px; }
footer { text-align:center; color:var(--muted); font-size:12px; margin-top:40px; }
/* ניווט סקשנים דביק */
.secnav { position:sticky; top:0; z-index:30; display:flex; gap:6px; overflow-x:auto; padding:9px 4px; margin:10px -4px 0; background:rgba(11,17,32,.94); backdrop-filter:blur(6px); border-bottom:1px solid var(--line); scrollbar-width:thin; }
.secnav a { flex:0 0 auto; font-size:12px; color:var(--muted); text-decoration:none; background:var(--card2); border:1px solid var(--line); border-radius:20px; padding:4px 11px; white-space:nowrap; }
.secnav a:hover { color:var(--accent); border-color:var(--accent); }
.backtop { position:fixed; inset-inline-start:16px; bottom:16px; z-index:40; background:var(--accent); color:#04293b; border:0; border-radius:50%; width:42px; height:42px; font-size:18px; font-weight:800; cursor:pointer; box-shadow:0 4px 14px rgba(0,0,0,.4); display:none; }
/* שורת KPI עליונה */
.hero { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:14px 0 0; }
.kpi { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px; }
.kpi .k-lbl { color:var(--muted); font-size:11.5px; }
.kpi .k-val { font-size:19px; font-weight:800; margin-top:3px; }
.kpi .k-sub { color:var(--muted); font-size:11px; margin-top:2px; }
/* באנר טריות */
.stale { border-radius:10px; padding:9px 14px; font-size:13px; margin-top:10px; border:1px solid; }
.stale-ok { background:#06281f; border-color:#166534; color:#bbf7d0; }
.stale-warn { background:#3b1f06; border-color:#b45309; color:#fde68a; }
.stale-bad { background:#3f1117; border-color:#991b1b; color:#fecaca; }
@media print {
  body { background:#fff; color:#000; }
  .toolbar, .secnav, .backtop, .toast, iframe, .addbtn, .delbtn, .filebtn { display:none !important; }
  .wrap { max-width:100%; padding:0; }
  .card, .week, .metric, .health-item, .kpi, .foot { background:#fff !important; border-color:#bbb !important; }
  section { break-inside:avoid; margin-top:18px; }
  section > h2 { color:#000 !important; }
  a { color:#000; text-decoration:underline; }
  .big, .big2, .metric strong, .kpi .k-val { color:#000 !important; }
}
/* ============ שכבת עיצוב פרימיום — Executive Dark (כיוון A) ============ */
:root {
  --bg:#0a1122; --card:#142033; --card2:#182a45; --ink:#eaf1fb; --muted:#8fa2c0;
  --accent:#38bdf8; --accent2:#22d3ee; --gold:#f5c451; --green:#34d399; --line:#26324e;
}
html { scroll-behavior:smooth; scroll-padding-top:60px; }
body { font-family:"Heebo","Segoe UI",Rubik,Arial,sans-serif;
  background:radial-gradient(1100px 560px at 100% -8%, #14294a 0%, rgba(10,17,34,0) 60%), var(--bg);
  background-attachment:fixed; font-variant-numeric:tabular-nums; }
* { scrollbar-width:thin; scrollbar-color:#33507e transparent; }
::selection { background:rgba(56,189,248,.28); }
.wrap { max-width:1120px; }
header { background:linear-gradient(135deg, rgba(56,189,248,.10), rgba(52,211,153,.05)); border:1px solid var(--line);
  border-radius:18px; padding:20px 24px; margin-top:10px; }
header .info h1 { letter-spacing:-.4px; }
.photo { flex:0 0 230px; height:158px; box-shadow:0 8px 26px rgba(0,0,0,.35); }
section > h2 { font-size:21px; letter-spacing:-.3px; border-right-width:4px; }
.card, .week, .metric, .health-item, .kpi, .tier, .foot, .scenario {
  transition:transform .16s ease, border-color .16s ease, box-shadow .16s ease; }
.card:hover, .kpi:hover, .health-item:hover { border-color:#375888; box-shadow:0 10px 28px rgba(0,0,0,.30); }
.kpi { background:linear-gradient(162deg, var(--card), var(--card2)); }
.kpi .k-val { letter-spacing:-.3px; }
.addbtn { background:linear-gradient(135deg, var(--accent), var(--accent2)); box-shadow:0 5px 16px rgba(56,189,248,.22); }
.addbtn:hover { opacity:1; transform:translateY(-1px); box-shadow:0 8px 22px rgba(56,189,248,.34); }
.secnav { padding:10px 4px; }
.secnav a { transition:color .15s, border-color .15s, background .15s; }
.secnav a:hover { background:rgba(56,189,248,.12); }
.badge { backdrop-filter:blur(2px); }
.metric strong, .foot .big2, .scenario strong { letter-spacing:-.3px; }
.warn { border-radius:12px; }
footer { border-top:1px solid var(--line); padding-top:18px; }
#comparables-table tr.notcomp { opacity:.45; }
#comparables-table tr.notcomp:hover { opacity:.8; }
/* טאבים ראשיים */
.tabs { position:sticky; top:0; z-index:30; display:flex; gap:7px; overflow-x:auto; padding:11px 4px; margin:12px -4px 6px;
        background:rgba(10,17,34,.95); backdrop-filter:blur(8px); border-bottom:1px solid var(--line); scrollbar-width:thin; }
.tab { flex:0 0 auto; font-family:inherit; font-size:14.5px; font-weight:700; color:var(--muted); background:var(--card2);
       border:1px solid var(--line); border-radius:11px; padding:9px 17px; white-space:nowrap; cursor:pointer; transition:all .15s; }
.tab:hover { color:var(--ink); border-color:#375888; }
.tab.active { color:#04263a; background:linear-gradient(135deg, var(--accent), var(--accent2)); border-color:transparent; box-shadow:0 5px 16px rgba(56,189,248,.28); }
.tab .cnt { font-size:11px; opacity:.65; margin-inline-start:5px; font-variant-numeric:tabular-nums; }
.tabpanel { display:none; }
.tabpanel.active { display:block; }
.tabpanel > section:first-child { margin-top:20px; }
@media print { .tabs { display:none !important; } .tabpanel { display:block !important; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior:auto; } *{ transition:none !important; } }
/* גלריית השראה חיה (Openverse) + שמורים לפי חדר */
.saved-filter { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:4px 0 2px; }
.chip-toggle { font-family:inherit; font-size:12.5px; font-weight:700; cursor:pointer; color:var(--muted);
  background:var(--card2); border:1px solid var(--line); border-radius:999px; padding:5px 12px; }
.chip-toggle.on { color:#04263a; background:linear-gradient(135deg,#f5c451,#f59e0b); border-color:transparent; }
.cc-search { display:flex; gap:6px; margin:12px 0 8px; }
.cc-q { flex:1; min-width:0; background:var(--bg); border:1px solid var(--line); color:var(--ink);
  border-radius:8px; padding:7px 10px; font-family:inherit; font-size:13px; }
.cc-go { flex:0 0 auto; font-family:inherit; font-size:13px; font-weight:700; cursor:pointer; color:#04263a;
  background:linear-gradient(135deg,var(--accent),var(--accent2)); border:none; border-radius:8px; padding:7px 12px; }
/* כרטיסי רעיונות רחבים יותר + גלריה גדולה יותר */
.room-ideas-grid { grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); }
.cc-results, .room-saved { display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:8px; margin:6px 0; }
.cctile { position:relative; margin:0; border-radius:8px; overflow:hidden; border:1px solid var(--line); background:var(--bg); }
.cctile.saved { border-color:#f5c451; box-shadow:0 0 0 2px rgba(245,196,81,.35); }
.cctile img { width:100%; height:150px; object-fit:cover; display:block; cursor:zoom-in; }
.cctile.zoom { grid-column:1 / -1; }
.cctile.zoom img { height:auto; max-height:420px; object-fit:contain; cursor:zoom-out; background:#000; }
.cc-bar { position:absolute; top:3px; inset-inline-start:3px; display:flex; gap:3px; }
.cc-like, .cc-del { font-size:13px; line-height:1; cursor:pointer; border:none; border-radius:6px; padding:3px 6px;
  background:rgba(4,20,34,.74); color:#e6edf6; }
.cc-like:hover { background:rgba(245,196,81,.92); color:#04263a; }
.cc-del:hover { background:rgba(220,38,38,.92); }
.cc-cred { position:absolute; inset-inline:0; bottom:0; font-size:9px; line-height:1.2; padding:2px 4px;
  color:#dbe4ef; text-decoration:none; background:linear-gradient(transparent, rgba(4,12,22,.82));
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; opacity:0; transition:opacity .15s; }
.cctile:hover .cc-cred, .cctile.zoom .cc-cred { opacity:1; }
.cc-msg { grid-column:1 / -1; font-size:12px; color:var(--muted); padding:8px 4px; }
.cc-msg.dim { opacity:.7; }
/* כרטיס עם לשוניות (עיצוב ג') */
.rc-head { display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap; }
.savecount { font-size:12px; font-weight:700; color:#f5c451; white-space:nowrap; }
.rc-seg { display:flex; gap:3px; background:var(--bg); border:1px solid var(--line); border-radius:10px;
  padding:3px; margin:11px 0 6px; }
.rc-seg button { flex:1 1 0; font-family:inherit; font-size:12px; font-weight:700; cursor:pointer; color:var(--muted);
  background:transparent; border:none; border-radius:7px; padding:6px 6px; white-space:nowrap; }
.rc-seg button:hover { color:var(--ink); }
.rc-seg button.on { color:#04263a; background:linear-gradient(135deg,var(--accent),var(--accent2)); }
.rc-panel { display:none; }
.rc-panel.on { display:block; }
/* מצב "שמורים בלבד" — כל הכרטיסים עוברים ללשונית שמורים */
section.saved-only .rc-seg { display:none; }
section.saved-only .rc-panel { display:none !important; }
section.saved-only .rc-panel[data-panel="saved"] { display:block !important; }
@media print { .cc-search, .room-img-input, .filebtn, .saved-filter, .cc-bar, .rc-seg { display:none !important; }
  .rc-panel { display:block !important; } }
"""

JS = r"""
const LS = "dira-nuriot-state-v3";
const LEGACY_LS = "dira-nuriot-state-v2";
const state = JSON.parse(localStorage.getItem(LS) || localStorage.getItem(LEGACY_LS) || "{}");
function save(){ localStorage.setItem(LS, JSON.stringify(state)); }
function nis(n){ return Math.round(n).toLocaleString("he-IL") + " ₪"; }
function esc(s){ return (s==null?"":(""+s)).replace(/&/g,"&amp;").replace(/"/g,"&quot;"); }
function sizeTag(a){ if(!a) return ""; if(a<6) return '<span class="szt szt-s">קטן</span>'; if(a<=12) return '<span class="szt szt-m">בינוני</span>'; return '<span class="szt szt-l">גדול</span>'; }
function getSel(k, def){ const v = state["sel_"+k]; return v===undefined ? def : v; }

// ---------- גיבוי וייבוא ----------
function exportBackup(){
  const payload={schema_version:1,app:"dira-nuriot",exported_at:new Date().toISOString(),generated_at:DATA.generated_at,state};
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob);
  a.download="dira-nuriot-backup-"+new Date().toISOString().slice(0,10)+".json"; a.click(); URL.revokeObjectURL(a.href);
  document.getElementById("backup-msg").textContent="הגיבוי נוצר עם חותמת זמן "+payload.exported_at;
}
function importBackup(file){
  const reader=new FileReader(); reader.onload=()=>{ try{
    const payload=JSON.parse(reader.result); if(payload.app!=="dira-nuriot"||payload.schema_version!==1||!payload.state) throw new Error("קובץ לא תואם");
    Object.keys(state).forEach(k=>delete state[k]); Object.assign(state,payload.state); save(); location.reload();
  }catch(e){ document.getElementById("backup-msg").textContent="ייבוא נכשל: "+e.message; }}; reader.readAsText(file);
}
document.getElementById("export-state").addEventListener("click",exportBackup);
document.getElementById("import-state").addEventListener("change",e=>{if(e.target.files[0]) importBackup(e.target.files[0]);});

// ---------- אפשרויות שיפוץ ----------
function renderOptions(){
  const host = document.getElementById("options-list");
  host.innerHTML = "";
  DATA.options.forEach(o => {
    const sel = getSel(o.key, o.default);
    const diyOn = !!state["diy_"+o.key];
    const row = document.createElement("div");
    row.className = "opt";
    let diyLine = "";
    if(o.diy){
      diyLine = '<div class="diyline"><label class="diychk"><input type="checkbox" class="diy" data-key="'+o.key+'" '
        + (diyOn?"checked":"") + '> לבד 🔧</label>'
        + '<span class="prodprice">🛒 שוק: '+nis(o.prod_market_min)+'–'+nis(o.prod_market_max)
        + ' · 📦 עלי: '+nis(o.prod_ali_min)+'–'+nis(o.prod_ali_max)+'</span>'
        + (o.diy_note?'<div class="note">'+o.diy_note+'</div>':'') + '</div>';
    }
    let vb = "";
    if(o.value==="high") vb='<span class="vb vb-h">📈 מעלה ערך</span>';
    else if(o.value==="med") vb='<span class="vb vb-m">📈 ערך בינוני</span>';
    row.innerHTML =
      '<input type="checkbox" class="optchk" data-key="'+o.key+'" '+(sel?"checked":"")+'>'
      + '<div><div class="name">'+o.he+(o.essential?'<span class="ess">חובה</span>':'')+vb
        + '</div><div class="note">'+(o.note||"")+' <span style="color:#64748b">['+o.category+']</span></div>'
        + diyLine + '</div>'
      + '<div class="rng">'+nis(o.cost_min)+'–'+nis(o.cost_max)+'</div>'
      + '<input type="number" class="price" data-key="'+o.key+'" placeholder="'+Math.round((o.cost_min+o.cost_max)/2)+'">';
    host.appendChild(row);
  });
  host.querySelectorAll(".optchk").forEach(c => {
    c.addEventListener("change", () => { state["sel_"+c.dataset.key]=c.checked; save(); recompute(); });
  });
  host.querySelectorAll("input.diy").forEach(c => {
    c.addEventListener("change", () => { state["diy_"+c.dataset.key]=c.checked; save(); recompute(); });
  });
  host.querySelectorAll("input.price").forEach(inp => {
    const k="price_"+inp.dataset.key;
    if(state[k]!=null) inp.value=state[k];
    inp.addEventListener("input", () => { state[k]=inp.value; save(); recompute(); });
  });
}

function recompute(){
  let lo=0, hi=0, planned=0, days=0, savings=0;
  const pros=new Set(), selected=[];
  DATA.options.forEach(o => {
    if(!getSel(o.key, o.default)) return;
    selected.push(o);
    lo+=o.cost_min; hi+=o.cost_max; days+=o.days||0;
    const proMid = Math.round((o.cost_min+o.cost_max)/2);
    const diyOn = o.diy && !!state["diy_"+o.key];
    const ov=parseFloat(state["price_"+o.key]);
    if(diyOn){
      const aliMid = Math.round((o.prod_ali_min+o.prod_ali_max)/2);
      const cost = isNaN(ov) ? aliMid : ov;
      planned += cost;
      savings += Math.max(0, proMid - cost);
      // לבד → לא צריך את אנשי המקצוע של הפריט
    } else {
      planned += isNaN(ov) ? proMid : ov;
      (o.pros||[]).forEach(p=>pros.add(p));
    }
  });
  const credit = DATA.kitchen_credit||0;
  const netPlanned = Math.max(0, planned - credit);
  document.getElementById("budget-range").textContent = nis(lo)+"–"+nis(hi);
  document.getElementById("budget-planned").textContent = nis(netPlanned);
  document.getElementById("budget-savings").textContent = savings>0 ? "−"+nis(savings) : "—";
  document.getElementById("timeline-days").textContent = days + " ימי עבודה (≈ "+Math.max(1,Math.ceil(days/5))+" שבועות בחפיפה)";

  // אנשי מקצוע נדרשים
  const ph=document.getElementById("pros-needed"); ph.innerHTML="";
  if(pros.size===0) ph.innerHTML='<span class="muted">—</span>';
  pros.forEach(p => { const s=document.createElement("span"); s.className="pill"; s.textContent=DATA.pros[p]||p; ph.appendChild(s); });

  // משימות מצטברות מהאפשרויות שנבחרו
  const tl=document.getElementById("task-list"); tl.innerHTML="";
  let total=0, done=0;
  selected.forEach(o => {
    (o.tasks||[]).forEach((t,i) => {
      total++;
      const id="task_"+o.key+"_"+i;
      const isDone=!!state[id]; if(isDone) done++;
      const li=document.createElement("li");
      li.innerHTML='<label class="'+(isDone?"done":"")+'"><input type="checkbox" '+(isDone?"checked":"")
        +' data-id="'+id+'"><span class="days">'+o.he.split("—")[0].trim()+'</span> '+t+'</label>';
      li.querySelector("input").addEventListener("change", e=>{
        state[id]=e.target.checked; save();
        e.target.closest("label").classList.toggle("done", e.target.checked);
        recompute();
      });
      tl.appendChild(li);
    });
  });
  const pct = total ? Math.round(done/total*100) : 0;
  document.getElementById("task-pct").textContent = pct+"% ("+done+"/"+total+")";
  document.getElementById("task-bar").style.width = pct+"%";
}

// ---------- תשלומים ----------
function recalcPayments(){
  const base=DATA.index_base||0;
  let cur=parseFloat(state.index_cur); if(isNaN(cur)||!base) cur=base;
  const factor = base ? cur/base : 1;
  let paid=0, remaining=0, extra=0; let nextEl=null;
  document.querySelectorAll(".paychk").forEach(c => {
    const amt=parseFloat(c.dataset.amt)||0;
    const indexed = c.dataset.indexed==="1";
    const eff = indexed ? amt*factor : amt;
    if(indexed) extra += eff-amt;
    const cell=c.closest("tr").querySelector(".amt-cell");
    if(cell) cell.textContent = nis(eff) + (indexed?" 🔗":"");
    if(c.checked){ paid+=eff; c.closest("tr").querySelector(".paid-cell").innerHTML='<span class="paid-yes">✓ שולם</span>'; }
    else { remaining+=eff; c.closest("tr").querySelector(".paid-cell").innerHTML='<span class="paid-no">ממתין</span>';
           if(!nextEl) nextEl=c; }
  });
  document.getElementById("paid-total").textContent=nis(paid);
  document.getElementById("remaining-total").textContent=nis(remaining);
  const ie=document.getElementById("index-extra"); if(ie) ie.textContent=(extra>0?"+":"")+nis(extra);
  const nb=document.getElementById("next-payment");
  const hnp=document.getElementById("hero-nextpay"), hnps=document.getElementById("hero-nextpay-sub");
  if(nextEl){ const amt=parseFloat(nextEl.dataset.amt)||0; const eff=nextEl.dataset.indexed==="1"?amt*factor:amt;
    nb.style.display="block";
    nb.innerHTML='⏭️ התשלום הבא: <b>'+nextEl.dataset.date+'</b> · '+nis(eff);
    if(hnp) hnp.textContent=nis(eff); if(hnps) hnps.textContent=nextEl.dataset.date; }
  else { nb.style.display="none"; if(hnp) hnp.textContent="הושלם"; if(hnps) hnps.textContent="כל התשלומים שולמו"; }
}
document.querySelectorAll(".paychk").forEach(c=>{
  const k="paid_"+c.dataset.date;
  if(state[k]!==undefined) c.checked=state[k];
  c.addEventListener("change",()=>{ state[k]=c.checked; save(); recalcPayments(); });
});
(function(){ const ii=document.getElementById("index-input");
  if(ii){ if(state.index_cur!=null) ii.value=state.index_cur;
    ii.addEventListener("input",()=>{ state.index_cur=ii.value; save(); recalcPayments(); }); } })();

// ---------- גאנט-רפרנס ----------
document.querySelectorAll("input.gtask").forEach(c=>{
  const k="g_"+c.dataset.id;
  if(state[k]){ c.checked=true; c.closest("li").classList.add("done"); }
  c.addEventListener("change",()=>{ state[k]=c.checked; save(); c.closest("li").classList.toggle("done",c.checked); });
});

// ---------- דברים לביצוע ----------
document.querySelectorAll("input.action").forEach(c=>{
  const k="a_"+c.dataset.id;
  if(state[k]){ c.checked=true; c.closest("li").classList.add("done"); }
  c.addEventListener("change",()=>{ state[k]=c.checked; save(); c.closest("li").classList.toggle("done",c.checked); });
});

// ---------- בדק בית צ'קליסט ----------
function recalcHand(){
  const all=document.querySelectorAll("input.handcheck");
  const done=[...all].filter(c=>c.checked).length;
  const pct=all.length?Math.round(done/all.length*100):0;
  const p=document.getElementById("hand-pct"), b=document.getElementById("hand-bar");
  if(p) p.textContent=pct+"% ("+done+"/"+all.length+")";
  if(b) b.style.width=pct+"%";
}
document.querySelectorAll("input.handcheck").forEach(c=>{
  const k="hand_"+c.dataset.id;
  if(state[k]){ c.checked=true; c.closest("li").classList.add("done"); }
  c.addEventListener("change",()=>{ state[k]=c.checked; save();
    c.closest("li").classList.toggle("done",c.checked); recalcHand(); });
});
recalcHand();

// ---------- ספקים (טבלה נערכת) ----------
function saveRows(key, table){
  const rows=[...table.querySelectorAll("tr.datarow")].map(tr=>{
    const o={};
    tr.querySelectorAll("[data-f]").forEach(el=>{ o[el.dataset.f]= el.type==="checkbox"?el.checked:el.value; });
    return o;
  });
  state[key]=rows; save();
}
function addSupplierRow(table, d){
  d=d||{};
  const tr=document.createElement("tr"); tr.className="datarow";
  tr.innerHTML='<td><input class="cell" data-f="name" value="'+esc(d.name)+'"></td>'
    +'<td><input class="cell" data-f="trade" value="'+esc(d.trade)+'" list="trades"></td>'
    +'<td><input class="cell" data-f="phone" value="'+esc(d.phone)+'"></td>'
    +'<td><input class="cell" data-f="quote" type="number" value="'+esc(d.quote)+'"></td>'
    +'<td><input class="cell" data-f="status" value="'+esc(d.status)+'" placeholder="הצעה/נבחר"></td>'
    +'<td><button class="delbtn">✕</button></td>';
  table.appendChild(tr);
  tr.querySelectorAll("input").forEach(i=>i.addEventListener("input",()=>saveRows("suppliers",table)));
  tr.querySelector(".delbtn").addEventListener("click",()=>{ tr.remove(); saveRows("suppliers",table); });
}
(function(){ const t=document.getElementById("suppliers-table");
  let dl=document.createElement("datalist"); dl.id="trades";
  (DATA.pros_seed||[]).forEach(p=>{ const o=document.createElement("option"); o.value=p; dl.appendChild(o); });
  document.body.appendChild(dl);
  const saved=state.suppliers||[];
  if(saved.length) saved.forEach(d=>addSupplierRow(t,d)); else addSupplierRow(t,{});
  document.getElementById("add-supplier").addEventListener("click",()=>addSupplierRow(t,{}));
})();

// ---------- רשימת קניות ----------
function addShopRow(table, d){
  d=d||{};
  const tr=document.createElement("tr"); tr.className="datarow";
  tr.innerHTML='<td><input class="cell" data-f="item" value="'+esc(d.item)+'"></td>'
    +'<td><input class="cell" data-f="link" value="'+esc(d.link)+'" placeholder="https://"></td>'
    +'<td><input class="cell" data-f="price" type="number" value="'+esc(d.price)+'"></td>'
    +'<td style="text-align:center"><input type="checkbox" data-f="ordered" '+(d.ordered?"checked":"")+'></td>'
    +'<td><button class="delbtn">✕</button></td>';
  table.appendChild(tr);
  tr.querySelectorAll("input").forEach(i=>i.addEventListener(i.type==="checkbox"?"change":"input",()=>saveRows("shop",table)));
  tr.querySelector(".delbtn").addEventListener("click",()=>{ tr.remove(); saveRows("shop",table); });
}
(function(){ const t=document.getElementById("shop-table");
  const saved=state.shop;
  if(saved && saved.length) saved.forEach(d=>addShopRow(t,d));
  else (DATA.shopping_seed||[]).forEach(it=>addShopRow(t,{item:it}));
  document.getElementById("add-shop").addEventListener("click",()=>addShopRow(t,{}));
})();

// ---------- גלריית השראה חיה (Openverse) + שמירה לפי חדר ----------
// תמונות Creative-Commons (API מפתח-חינם, CORS). 🔖 שומר מקומית (נכנס לגיבוי).
// הגלריה דורשת אינטרנט; שאר הדף אופליין. אין הטמעת תמונות מוגנות-זכויות בריפו הפומבי —
// שומרים רק הפניה (thumbnail/מקור) + קרדיט רישיון.
(function(){
  // מיגרציה מהמבנה הישן (room_images ← העלאות) → room_saved
  if (state.room_images && !state.room_saved){
    state.room_saved = {};
    for (const k in state.room_images)
      state.room_saved[k] = (state.room_images[k]||[]).map(it => ({ t:"up", src:it.src }));
    delete state.room_images; save();
  }
  state.room_saved = state.room_saved || {};
  const savedFor = k => (state.room_saved[k] = state.room_saved[k] || []);
  const same = (a,b) => (a.t==="cc"&&b.t==="cc"&&a.full===b.full) || (a.t==="up"&&b.t==="up"&&a.src===b.src);
  const isSaved = (k,it) => savedFor(k).some(s => same(s,it));
  function persist(){ try { save(); return true; }
    catch(e){ alert("האחסון המקומי מלא — הסר תמונות שמורות או ייצא גיבוי."); return false; } }
  function updateCount(){
    // מונה כללי + מונה לכל חדר (לשונית + תגית בכותרת)
    document.querySelectorAll(".rc-savedn").forEach(s => s.textContent = (state.room_saved[s.dataset.room]||[]).length);
    document.querySelectorAll(".savecount").forEach(s => { const b = s.querySelector("b");
      if (b) b.textContent = (state.room_saved[s.dataset.count]||[]).length; });
    const n = Object.values(state.room_saved).reduce((a,arr)=>a+arr.length,0);
    const el = document.getElementById("saved-img-count"); if (el) el.textContent = n;
  }

  function credLink(item){
    const a = document.createElement("a"); a.className = "cc-cred"; a.target = "_blank"; a.rel = "noopener nofollow";
    a.href = item.srcurl || item.licurl || "#";
    a.textContent = (item.by ? item.by + " · " : "") + "CC " + (item.lic||"") + " ↗"; return a;
  }
  // ----- גלריה חיה -----
  function tileCC(k, res){
    const item = { t:"cc", thumb:res.thumbnail, full:res.url||res.thumbnail, title:res.title||"",
      by:res.creator||"", lic:(res.license||"").toUpperCase(), licurl:res.license_url||"",
      src:res.source||"", srcurl:res.foreign_landing_url||"" };
    const fig = document.createElement("figure"); fig.className = "cctile";
    const im = document.createElement("img"); im.src = item.thumb; im.loading = "lazy"; im.alt = esc(item.title);
    im.addEventListener("click", () => fig.classList.toggle("zoom"));
    const bar = document.createElement("div"); bar.className = "cc-bar";
    const like = document.createElement("button"); like.className = "cc-like";
    const setLike = () => { const s = isSaved(k,item); like.textContent = s ? "🔖" : "🏷️";
      like.title = s ? "הסר משמורים" : "שמור להשראה"; fig.classList.toggle("saved", s); };
    like.addEventListener("click", () => { const arr = savedFor(k), idx = arr.findIndex(s => same(s,item));
      if (idx>=0) arr.splice(idx,1); else arr.push(item);
      if (persist()){ setLike(); renderSaved(k); updateCount(); } });
    setLike(); bar.appendChild(like);
    fig.appendChild(im); fig.appendChild(bar); fig.appendChild(credLink(item));
    return fig;
  }
  async function search(k, q){
    const box = document.querySelector('.cc-results[data-room="'+k+'"]'); if (!box) return;
    box.dataset.loaded = "1"; box.innerHTML = '<div class="cc-msg">טוען תמונות…</div>';
    try {
      const url = "https://api.openverse.org/v1/images/?q=" + encodeURIComponent(q) + "&page_size=12&mature=false";
      const r = await fetch(url, {headers:{Accept:"application/json"}});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const results = (await r.json()).results || [];
      box.innerHTML = "";
      if (!results.length){ box.innerHTML = '<div class="cc-msg">לא נמצאו תמונות — נסו שאילתה אחרת או Pinterest/Google.</div>'; return; }
      results.forEach(res => { if (res.thumbnail) box.appendChild(tileCC(k,res)); });
    } catch(e){
      box.innerHTML = '<div class="cc-msg">הגלריה החיה לא זמינה כרגע (' + esc(e.message) + '). נסו שוב, או Pinterest/Google למעלה. (דורש אינטרנט)</div>';
    }
  }
  // ----- שמורים (CC + העלאות) -----
  function renderSaved(k){
    const box = document.querySelector('.room-saved[data-room="'+k+'"]'); if (!box) return;
    const arr = savedFor(k); box.innerHTML = "";
    if (!arr.length){ box.innerHTML = '<div class="cc-msg dim">— אין שמורים —</div>'; return; }
    arr.forEach(item => {
      const fig = document.createElement("figure"); fig.className = "cctile saved";
      const im = document.createElement("img"); im.src = item.t==="cc" ? item.thumb : item.src; im.loading = "lazy"; im.alt = "שמור";
      im.addEventListener("click", () => fig.classList.toggle("zoom"));
      const bar = document.createElement("div"); bar.className = "cc-bar";
      const del = document.createElement("button"); del.className = "cc-del"; del.textContent = "✕"; del.title = "הסר";
      del.addEventListener("click", () => { const i = arr.indexOf(item); if (i>=0) arr.splice(i,1);
        if (persist()){ renderSaved(k); updateCount(); const lb = document.querySelector('.cc-results[data-room="'+k+'"]');
          if (lb && lb.dataset.loaded) search(k, document.querySelector('.cc-q[data-room="'+k+'"]').value.trim()); } });
      bar.appendChild(del); fig.appendChild(im); fig.appendChild(bar);
      if (item.t==="cc") fig.appendChild(credLink(item));
      box.appendChild(fig);
    });
  }
  // ----- העלאה עצמית (מוקטנת ל-dataURL) -----
  function downscale(file, cb){
    const url = URL.createObjectURL(file), img = new Image();
    img.onload = function(){ const max=900; let w=img.width,h=img.height;
      if (w>max||h>max){ const rr=Math.min(max/w,max/h); w=Math.round(w*rr); h=Math.round(h*rr); }
      const c=document.createElement("canvas"); c.width=w; c.height=h; c.getContext("2d").drawImage(img,0,0,w,h);
      URL.revokeObjectURL(url); cb(c.toDataURL("image/jpeg",0.72)); };
    img.onerror = function(){ URL.revokeObjectURL(url); alert("קובץ תמונה לא תקין."); };
    img.src = url;
  }
  // ----- חיווט -----
  document.querySelectorAll(".cc-go").forEach(btn => btn.addEventListener("click", () => {
    const k = btn.dataset.room, q = document.querySelector('.cc-q[data-room="'+k+'"]').value.trim(); if (q) search(k,q);
  }));
  document.querySelectorAll(".cc-q").forEach(inp => inp.addEventListener("keydown", e => {
    if (e.key==="Enter"){ e.preventDefault(); const q = inp.value.trim(); if (q) search(inp.dataset.room, q); }
  }));
  document.querySelectorAll(".room-img-input").forEach(inp => inp.addEventListener("change", () => {
    const k = inp.dataset.room, files = [...inp.files].filter(f => f.type.startsWith("image/")); let pending = files.length;
    if (!pending){ inp.value=""; return; }
    files.forEach(f => downscale(f, src => { savedFor(k).push({ t:"up", src:src });
      if (--pending<=0 && persist()){ renderSaved(k); updateCount(); } }));
    inp.value = "";
  }));
  const chip = document.getElementById("saved-only-toggle"), section = chip ? chip.closest("section") : null;
  let savedOnly = false;
  if (chip) chip.addEventListener("click", () => { savedOnly = !savedOnly; chip.classList.toggle("on", savedOnly);
    chip.setAttribute("aria-pressed", savedOnly); if (section) section.classList.toggle("saved-only", savedOnly); });
  // לשוניות הכרטיס (עיצוב ג'): רעיונות · גלריה · שמורים.
  // הגלריה החיה נטענת רק בפתיחה ראשונה של לשונית "גלריה" — חוסך קריאות API.
  document.querySelectorAll(".rc-seg").forEach(seg => {
    const k = seg.dataset.room, card = seg.closest(".card");
    seg.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
      seg.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === btn));
      card.querySelectorAll(".rc-panel").forEach(p => p.classList.toggle("on", p.dataset.panel === btn.dataset.tab));
      if (btn.dataset.tab === "gal"){ const box = card.querySelector(".cc-results");
        if (box && !box.dataset.loaded) search(k, box.dataset.search); }
    }));
  });
  // render saved on load
  document.querySelectorAll(".room-saved").forEach(b => renderSaved(b.dataset.room));
  updateCount();
})();

// ---------- מעקב שווי ----------
function fmtM(v){ return (v/1000000).toFixed(2)+"M ₪"; }
function renderValueChart(){
  const rows=[...document.querySelectorAll("#value-table tr.datarow")].map(tr=>({
    date: tr.querySelector("[data-f=date]").value,
    value: parseFloat(tr.querySelector("[data-f=value]").value)||0,
    note: tr.querySelector("[data-f=note]").value
  })).filter(r=>r.value>0);
  const host=document.getElementById("value-chart"); if(!host) return; host.innerHTML="";
  const tr=document.getElementById("value-trend"); if(tr) tr.innerHTML="";
  if(!rows.length) return;
  const max=Math.max(...rows.map(r=>r.value)), min=Math.min(...rows.map(r=>r.value));
  // קנה מידה: בסיס מעט מתחת למינימום כדי שההבדלים יבלטו
  const base=Math.max(0, min-(max-min)*0.4||min*0.9);
  let h='<div class="vchart">';
  rows.forEach(r=>{ const ht=Math.round((r.value-base)/(max-base||1)*100);
    h+='<div class="vbar"><div class="vbar-fill" style="height:'+Math.max(6,ht)+'%"><span class="vbar-amt">'+fmtM(r.value)+'</span></div>'
      +'<div class="vbar-lbl"><b>'+(r.date||"")+'</b>'+(r.note||"")+'</div></div>'; });
  h+='</div>'; host.innerHTML=h;
  if(tr && rows.length>=2){
    const first=rows[0].value, last=rows[rows.length-1].value;
    const diff=last-first, pct=Math.round(diff/first*100);
    const up=diff>=0; const col=up?"#22c55e":"#f87171"; const arr=up?"▲":"▼";
    tr.innerHTML='מגמה: <span style="color:'+col+'">'+arr+' '+(up?"+":"")+fmtM(diff)+' ('+(up?"+":"")+pct+'%)</span> '
      +'<span style="color:var(--muted);font-weight:400">מאז '+(rows[0].date||"")+'</span>';
  }
}
function addValueRow(table,d){ d=d||{};
  const tr=document.createElement("tr"); tr.className="datarow";
  tr.innerHTML='<td><input class="cell" data-f="date" value="'+esc(d.date)+'" placeholder="2026-06"></td>'
    +'<td><input class="cell" data-f="value" type="number" value="'+esc(d.value)+'"></td>'
    +'<td><input class="cell" data-f="note" value="'+esc(d.note)+'"></td>'
    +'<td><button class="delbtn">✕</button></td>';
  table.appendChild(tr);
  tr.querySelectorAll("input").forEach(i=>i.addEventListener("input",()=>{saveRows("valuations",table);renderValueChart();}));
  tr.querySelector(".delbtn").addEventListener("click",()=>{tr.remove();saveRows("valuations",table);renderValueChart();});
}
(function(){ const t=document.getElementById("value-table");
  const saved=state.valuations;
  if(saved && saved.length) saved.forEach(d=>addValueRow(t,d));
  else (DATA.value_seed||[]).forEach(d=>addValueRow(t,d));
  document.getElementById("add-value").addEventListener("click",()=>{addValueRow(t,{});});
  renderValueChart();
})();

// ---------- מודל שווי + נכסים להשוואה ----------
function renderValuationModel(){
  const cfg=DATA.management.valuation_model||{};
  const baseInput=document.getElementById("valuation-base");
  if(state.valuation_base==null) state.valuation_base=cfg.base_value_nis||0;
  baseInput.value=state.valuation_base;
  const host=document.getElementById("valuation-adjustments"); host.innerHTML="";
  let totalPct=0;
  (cfg.adjustments||[]).forEach(a=>{
    const key="valuation_adj_"+a.key; if(state[key]==null) state[key]=a.pct; const pct=parseFloat(state[key])||0; totalPct+=pct;
    const row=document.createElement("div"); row.className="status-line";
    row.innerHTML='<span><b>'+esc(a.label)+'</b><span class="note">'+esc(a.reason||"")+'</span></span><input class="price" type="number" step="0.1" value="'+pct+'" aria-label="'+esc(a.label)+'">';
    row.querySelector("input").addEventListener("input",e=>{state[key]=e.target.value;save();renderValuationModel();}); host.appendChild(row);
  });
  const adjusted=(parseFloat(state.valuation_base)||0)*(1+totalPct/100);
  document.getElementById("valuation-adjusted").textContent=nis(adjusted);
  document.getElementById("valuation-total-pct").textContent=(totalPct>=0?"+":"")+totalPct.toFixed(1)+"%";
  const scenarios=document.getElementById("valuation-scenarios"); scenarios.innerHTML="";
  (cfg.scenarios||[]).forEach(s=>{const el=document.createElement("div");el.className="scenario";el.innerHTML='<span>'+esc(s.label)+'</span><strong>'+nis(adjusted*s.multiplier)+'</strong><span class="note">×'+s.multiplier+'</span>';scenarios.appendChild(el);});
  save();
}
document.getElementById("valuation-base").addEventListener("input",e=>{state.valuation_base=e.target.value;save();renderValuationModel();});

function addCompRow(table,d){ d=d||{}; const tr=document.createElement("tr");tr.className="datarow";
  const cmp = d.comparable===false ? "" : "checked";  // ברירת מחדל: בר-השוואה, אלא אם סומן במפורש false
  tr.innerHTML='<td><input class="cell" data-f="date" value="'+esc(d.date)+'"></td><td><input class="cell" data-f="address" value="'+esc(d.address)+'"></td>'
    +'<td><input class="cell" data-f="rooms" type="number" value="'+esc(d.rooms)+'"></td><td><input class="cell" data-f="area_sqm" type="number" value="'+esc(d.area_sqm)+'"></td>'
    +'<td><input class="cell" data-f="price_nis" type="number" value="'+esc(d.price_nis)+'"></td><td class="num ppsqm">—</td>'
    +'<td><input class="cell" data-f="kind" value="'+esc(d.kind)+'"></td><td><input class="cell" data-f="confidence" value="'+esc(d.confidence)+'"></td>'
    +'<td style="text-align:center"><input type="checkbox" data-f="comparable" '+cmp+'></td>'
    +'<td><input class="cell" data-f="source_url" value="'+esc(d.source_url)+'" placeholder="https://"></td><td><button class="delbtn">✕</button></td>';
  table.appendChild(tr); const update=()=>{const p=parseFloat(tr.querySelector('[data-f=price_nis]').value),a=parseFloat(tr.querySelector('[data-f=area_sqm]').value);tr.querySelector('.ppsqm').textContent=p&&a?nis(p/a):"—";tr.classList.toggle("notcomp",!tr.querySelector('[data-f=comparable]').checked);saveRows("comparables",table);renderCompStats();};
  tr.querySelectorAll("input").forEach(i=>i.addEventListener(i.type==="checkbox"?"change":"input",update));tr.querySelector(".delbtn").addEventListener("click",()=>{tr.remove();saveRows("comparables",table);renderCompStats();});update();
}
function renderCompStats(){
  const rows=[...document.querySelectorAll('#comparables-table tr.datarow')]
    .filter(tr=>tr.querySelector('[data-f=comparable]').checked)
    .map(tr=>({p:parseFloat(tr.querySelector('[data-f=price_nis]').value),a:parseFloat(tr.querySelector('[data-f=area_sqm]').value)}));
  const priced=rows.filter(r=>r.p>0);
  const perSqm=rows.filter(r=>r.p>0&&r.a>0).map(r=>r.p/r.a);
  const priceAvg=priced.length?priced.reduce((s,r)=>s+r.p,0)/priced.length:0;
  const ppsqmAvg=perSqm.length?perSqm.reduce((s,x)=>s+x,0)/perSqm.length:0;
  document.getElementById('comp-count').textContent=rows.length;
  document.getElementById('comp-price-avg').textContent=priceAvg?nis(priceAvg):"—";
  document.getElementById('comp-avg').textContent=ppsqmAvg?nis(ppsqmAvg)+"/מ״ר":"—";
}
(function(){const t=document.getElementById("comparables-table"),seed=state.comparables||DATA.management.comparables||[];seed.forEach(d=>addCompRow(t,d));document.getElementById("add-comp").addEventListener("click",()=>addCompRow(t,{}));renderValuationModel();renderCompStats();})();

// ---------- תחזית תזרים ----------
function renderCashFlow(){
  const cfg=DATA.management.cash_flow||{}; ["available_cash_nis","monthly_contribution_nis","contingency_pct","renovation_target_nis"].forEach(k=>{if(state["cash_"+k]==null)state["cash_"+k]=cfg[k]||0;const el=document.getElementById("cash-"+k);el.value=state["cash_"+k];});
  const base=DATA.index_base||0,cur=parseFloat(state.index_cur)||base,factor=base?cur/base:1;
  let remaining=0; (DATA.payments||[]).forEach(p=>{const paid=state["paid_"+p.date]===undefined?p.paid:state["paid_"+p.date];if(!paid)remaining+=p.amount_incl_vat*(p.indexed?factor:1);});
  const reno=parseFloat(state.cash_renovation_target_nis)||0,cont=parseFloat(state.cash_contingency_pct)||0,available=parseFloat(state.cash_available_cash_nis)||0,monthly=parseFloat(state.cash_monthly_contribution_nis)||0;
  const required=remaining+reno*(1+cont/100),gap=Math.max(0,required-available);const last=DATA.payments.length?new Date(DATA.payments[DATA.payments.length-1].date):new Date();const months=Math.max(1,Math.ceil((last-new Date())/(1000*60*60*24*30.44)));const projected=available+monthly*months;
  document.getElementById("cash-remaining").textContent=nis(remaining);document.getElementById("cash-required").textContent=nis(required);document.getElementById("cash-gap").textContent=nis(gap);document.getElementById("cash-months").textContent=months;document.getElementById("cash-projected").textContent=nis(projected);document.getElementById("cash-monthly-needed").textContent=nis(gap/months);document.getElementById("cash-status").innerHTML=projected>=required?'<span class="badge badge-ok">ממומן לפי ההנחות</span>':'<span class="badge badge-warn">פער מימון '+nis(required-projected)+'</span>';save();
}
["available_cash_nis","monthly_contribution_nis","contingency_pct","renovation_target_nis"].forEach(k=>document.getElementById("cash-"+k).addEventListener("input",e=>{state["cash_"+k]=e.target.value;renderCashFlow();}));

// ---------- מעקב שיפוץ בפועל ----------
function addRenoRow(table,d){d=d||{};const tr=document.createElement("tr");tr.className="datarow";tr.innerHTML='<td><input class="cell" data-f="item" value="'+esc(d.item)+'"></td><td><input class="cell" data-f="budget" type="number" value="'+esc(d.budget)+'"></td><td><input class="cell" data-f="quote" type="number" value="'+esc(d.quote)+'"></td><td><input class="cell" data-f="supplier" value="'+esc(d.supplier)+'"></td><td><input class="cell" data-f="deposit" type="number" value="'+esc(d.deposit)+'"></td><td><input class="cell" data-f="paid" type="number" value="'+esc(d.paid)+'"></td><td><input class="cell" data-f="status" value="'+esc(d.status)+'" placeholder="מתוכנן/הוזמן/הושלם"></td><td class="num variance">—</td><td><button class="delbtn">✕</button></td>';table.appendChild(tr);const update=()=>{const b=parseFloat(tr.querySelector('[data-f=budget]').value)||0,q=parseFloat(tr.querySelector('[data-f=quote]').value)||0;tr.querySelector('.variance').textContent=(q?nis(q-b):"—");saveRows("renovation_tracking",table);renderRenoTotals();};tr.querySelectorAll("input").forEach(i=>i.addEventListener("input",update));tr.querySelector('.delbtn').addEventListener('click',()=>{tr.remove();saveRows("renovation_tracking",table);renderRenoTotals();});update();}
function renderRenoTotals(){let budget=0,committed=0,paid=0;document.querySelectorAll('#reno-track-table tr.datarow').forEach(tr=>{budget+=parseFloat(tr.querySelector('[data-f=budget]').value)||0;committed+=parseFloat(tr.querySelector('[data-f=quote]').value)||0;paid+=parseFloat(tr.querySelector('[data-f=paid]').value)||0;});document.getElementById('reno-budget-total').textContent=nis(budget);document.getElementById('reno-committed-total').textContent=nis(committed);document.getElementById('reno-paid-total').textContent=nis(paid);document.getElementById('reno-variance-total').textContent=nis(committed-budget);}
(function(){const t=document.getElementById('reno-track-table');let rows=state.renovation_tracking||DATA.management.renovation_tracking||[];if(!rows.length)rows=(DATA.options||[]).filter(o=>o.default).map(o=>({item:o.he,budget:Math.round((o.cost_min+o.cost_max)/2),status:'מתוכנן'}));rows.forEach(d=>addRenoRow(t,d));document.getElementById('add-reno-track').addEventListener('click',()=>addRenoRow(t,{}));})();

// ---------- ליקויי מסירה ----------
function addDefectRow(table,d){d=d||{};const tr=document.createElement('tr');tr.className='datarow';tr.innerHTML='<td><input class="cell" data-f="date" value="'+esc(d.date)+'"></td><td><input class="cell" data-f="area" value="'+esc(d.area)+'"></td><td><input class="cell" data-f="description" value="'+esc(d.description)+'"></td><td><input class="cell" data-f="severity" value="'+esc(d.severity)+'" placeholder="נמוכה/בינונית/קריטית"></td><td><input class="cell" data-f="responsible" value="'+esc(d.responsible)+'"></td><td><input class="cell" data-f="due" value="'+esc(d.due)+'"></td><td><input class="cell" data-f="status" value="'+esc(d.status)+'" placeholder="פתוח/בטיפול/נסגר"></td><td><input class="cell" data-f="photo" value="'+esc(d.photo)+'" placeholder="קישור/שם קובץ"></td><td><button class="delbtn">✕</button></td>';table.appendChild(tr);tr.querySelectorAll('input').forEach(i=>i.addEventListener('input',()=>{saveRows('defects',table);renderDefectStats();}));tr.querySelector('.delbtn').addEventListener('click',()=>{tr.remove();saveRows('defects',table);renderDefectStats();});}
function renderDefectStats(){const rows=[...document.querySelectorAll('#defects-table tr.datarow')],open=rows.filter(tr=>!['נסגר','סגור'].includes(tr.querySelector('[data-f=status]').value.trim())).length,critical=rows.filter(tr=>tr.querySelector('[data-f=severity]').value.includes('קריט')).length;document.getElementById('defect-open').textContent=open;document.getElementById('defect-critical').textContent=critical;}
(function(){const t=document.getElementById('defects-table'),rows=state.defects||DATA.management.defects||[];rows.forEach(d=>addDefectRow(t,d));document.getElementById('add-defect').addEventListener('click',()=>addDefectRow(t,{date:new Date().toISOString().slice(0,10),status:'פתוח'}));renderDefectStats();})();

// ---------- מידות חדרים ----------
function addRoomRow(table,d){ d=d||{};
  const tr=document.createElement("tr"); tr.className="datarow";
  const a=(parseFloat(d.len)*parseFloat(d.wid));
  tr.innerHTML='<td><input class="cell" data-f="room" value="'+esc(d.room)+'"></td>'
    +'<td><input class="cell" data-f="len" type="number" step="0.01" value="'+esc(d.len)+'"></td>'
    +'<td><input class="cell" data-f="wid" type="number" step="0.01" value="'+esc(d.wid)+'"></td>'
    +'<td class="area-cell">'+(a?a.toFixed(1)+" "+sizeTag(a):"—")+'</td>'
    +'<td><button class="delbtn">✕</button></td>';
  table.appendChild(tr);
  function upd(){ const l=parseFloat(tr.querySelector("[data-f=len]").value), w=parseFloat(tr.querySelector("[data-f=wid]").value);
    const ar=(l&&w)?l*w:0; tr.querySelector(".area-cell").innerHTML=ar?ar.toFixed(1)+" "+sizeTag(ar):"—"; saveRows("rooms",table); }
  tr.querySelectorAll("input").forEach(i=>i.addEventListener("input",upd));
  tr.querySelector(".delbtn").addEventListener("click",()=>{tr.remove();saveRows("rooms",table);});
}
(function(){ const t=document.getElementById("rooms-table");
  const saved=state.rooms;
  if(saved && saved.length) saved.forEach(d=>addRoomRow(t,d));
  else (DATA.rooms_seed||[]).forEach(d=>addRoomRow(t, typeof d==="string"?{room:d}:d));
  document.getElementById("add-room").addEventListener("click",()=>{addRoomRow(t,{});});
})();

// ---------- קיפול נושאים + ניווט ----------
const sections=[...document.querySelectorAll("section")];
const applers=[];
const navItems=[];
sections.forEach((sec,i)=>{
  const h2=sec.querySelector("h2"); if(!h2) return;
  const title=h2.textContent.trim();
  sec.id="sec-"+i;
  navItems.push({i,title});
  const rest=[...sec.children].filter(el=>el!==h2);
  const ind=document.createElement("span"); ind.className="toggle-ind"; h2.prepend(ind);
  const key="collapsed_"+i;
  function apply(){ const c=!!state[key]; rest.forEach(el=>el.style.display=c?"none":""); ind.textContent=c?"▸":"▾"; }
  apply(); applers[i]=apply;
  h2.addEventListener("click",()=>{ state[key]=!state[key]; save(); apply(); });
});
function setAll(c){ sections.forEach((sec,i)=>{ if(sec.querySelector("h2")) state["collapsed_"+i]=c; }); save();
  applers.forEach(a=>a&&a()); }
const ea=document.getElementById("expand-all"); if(ea) ea.addEventListener("click",()=>setAll(false));
const ca=document.getElementById("collapse-all"); if(ca) ca.addEventListener("click",()=>setAll(true));
// ---------- טאבים ראשיים (6 תחומים) ----------
// כל סקשן משויך לתחום לפי כותרת; הסקשנים מועברים לפאנל התחום בסדר הרצוי.
const DOMAINS=[
  {key:"overview", label:"סקירה", match:["#value-summary","דברים לביצוע","משימות לביצוע"]},
  {key:"finance", label:"כספים", match:["נתוני שוק","לוח תשלומים","תחזית תזרים","הערכת שווי"]},
  {key:"renovation", label:"שיפוץ", match:["מה כלול מהקבלן","אפשרויות שיפוץ","רעיונות עיצוב לפי חדר","תקציב שיפוץ בפועל","תוכנית ביצוע מהירה","לו\"ז ביצוע","מדריך אנשי מקצוע","ספקים והצעות","רשימת קניות"]},
  {key:"handover", label:"מסירה", match:["מסירה ובדק בית"]},
  {key:"property", label:"נכס וסביבה", match:["מיקום, תוכניות","מידות חדרים","סקירת שכונה","פלופ","מגבלות מחיר"]},
  {key:"system", label:"מערכת", match:["מצב מערכת"]},
];
(function(){
  const wrap=document.querySelector(".wrap"), footer=wrap.querySelector("footer");
  const valueGrid=document.getElementById("value-summary");
  function findEl(token){
    if(token[0]==="#") return document.getElementById(token.slice(1));
    return sections.find(s=>{ const h=s.querySelector("h2"); return h && h.textContent.includes(token); });
  }
  const tabbar=document.createElement("nav"); tabbar.className="tabs";
  const panels={};
  DOMAINS.forEach(d=>{
    const panel=document.createElement("div"); panel.className="tabpanel"; panel.id="tab-"+d.key; panel.dataset.tab=d.key;
    let count=0;
    d.match.forEach(tok=>{ const el=findEl(tok); if(el){ panel.appendChild(el); count++; } });
    if(!panel.children.length) return;
    panels[d.key]=panel; wrap.insertBefore(panel, footer);
    const btn=document.createElement("button"); btn.className="tab"; btn.dataset.tab=d.key;
    btn.innerHTML=d.label+'<span class="cnt">'+count+'</span>';
    btn.addEventListener("click",()=>activate(d.key));
    tabbar.appendChild(btn);
  });
  wrap.insertBefore(tabbar, wrap.querySelector(".tabpanel"));
  function activate(key){
    if(!panels[key]) key=DOMAINS.find(d=>panels[d.key]).key;
    Object.entries(panels).forEach(([k,p])=>p.classList.toggle("active",k===key));
    [...tabbar.children].forEach(b=>b.classList.toggle("active",b.dataset.tab===key));
    state.active_tab=key; save();
    if(location.hash!=="#"+key) history.replaceState(null,"","#"+key);
  }
  const fromHash=location.hash.slice(1);
  activate(panels[fromHash]?fromHash:(panels[state.active_tab]?state.active_tab:"overview"));
})();
// כפתור חזרה למעלה
(function(){ const b=document.createElement("button"); b.className="backtop"; b.textContent="↑"; b.title="למעלה";
  document.body.appendChild(b);
  b.addEventListener("click",()=>window.scrollTo({top:0,behavior:"smooth"}));
  window.addEventListener("scroll",()=>{ b.style.display=window.scrollY>500?"block":"none"; });
})();
// הרחבת כל הסקשנים להדפסה (ללא שמירה)
window.addEventListener("beforeprint",()=>{ sections.forEach(sec=>{ const h2=sec.querySelector("h2"); if(!h2) return;
  [...sec.children].forEach(el=>{ if(el!==h2) el.style.display=""; }); }); });
window.addEventListener("afterprint",()=>{ applers.forEach(a=>a&&a()); });
// עד מסירה (KPI)
(function(){ const el=document.getElementById("hero-handover"); if(!el||!DATA.payments||!DATA.payments.length) return;
  const last=new Date(DATA.payments[DATA.payments.length-1].date);
  const days=Math.ceil((last-new Date())/(1000*60*60*24));
  el.textContent = days>0 ? days.toLocaleString("he-IL")+" ימים" : "הגיע/עבר"; })();

renderOptions();
recompute();
recalcPayments();
renderCashFlow();
"""


def main():
    # Validate data files (permissive by default). Use validate_data.py --strict to enforce.
    try:
        from validate_data import validate_all
    except Exception:
        validate_all = None
    if validate_all:
        try:
            validate_all(base_dir=HERE, strict=False)
        except Exception as e:
            print(f"⚠️  Data validation raised an exception: {e}")
    apt = load_json(os.path.join(HERE, "apartment.json"), {}) or {}
    reno = load_json(os.path.join(HERE, "renovation.json"), {}) or {}
    management = load_json(os.path.join(HERE, "management.json"), {}) or {}
    status = load_json(os.path.join(HERE, "updates", "update-status.json"), {}) or {}
    update_history = load_json(os.path.join(HERE, "updates", "update-history.json"), []) or []
    deal_files = sorted(glob.glob(os.path.join(HERE, "updates", "deals-*.json")))
    market = load_json(deal_files[-1], {}) if deal_files else {}
    market = market or {}
    today = datetime.date.today().isoformat()

    p = apt.get("project", {})
    u = apt.get("unit", {})
    pur = apt.get("purchase", {})
    val = apt.get("valuation", {})
    restr = apt.get("restrictions", {})
    pay = apt.get("payments", {})
    nb = apt.get("neighborhood_review", {})
    up = apt.get("upgrade_paths", {})
    cons = apt.get("constraints", {})
    docs = apt.get("documents", {})
    photo = find_photo()
    wet = "".join(f'<span class="pill">🚿 {w}</span>' for w in u.get("wet_areas", []))

    paid_price = pur.get("price_nis")
    est = val.get("estimated_market_value_nis")
    equity = val.get("on_paper_equity_nis")
    equity_pct = val.get("on_paper_equity_pct")
    equity_color = "#22c55e" if (equity or 0) >= 0 else "#f87171"

    # ----- טווח שווי/רווח + טריות הערכה -----
    val_low = val.get("estimated_value_low_nis")
    val_high = val.get("estimated_value_high_nis")
    equity_low = (val_low - paid_price) if (val_low and paid_price) else None
    equity_high = (val_high - paid_price) if (val_high and paid_price) else None
    equity_range_txt = (
        f"{shekel(equity_low)} – {shekel(equity_high)}"
        if (equity_low is not None and equity_high is not None) else shekel(equity)
    )
    val_age_days = None
    try:
        val_age_days = (datetime.date.today()
                        - datetime.datetime.strptime(val.get("last_updated", ""), "%Y-%m-%d").date()).days
    except (TypeError, ValueError):
        pass
    if val_age_days is None:
        stale_class, stale_txt = "stale-warn", "לא ידוע מתי עודכנה ההערכה — מומלץ רענון מחקר (מצב agent)."
    elif val_age_days <= 30:
        stale_class, stale_txt = "stale-ok", f"הערכת השווי עודכנה לפני {val_age_days} ימים — עדכנית."
    elif val_age_days <= 60:
        stale_class, stale_txt = "stale-warn", f"הערכת השווי בת {val_age_days} ימים — כדאי רענון מחקר (מצב agent) בקרוב."
    else:
        stale_class, stale_txt = "stale-bad", f"הערכת השווי בת {val_age_days} ימים — נדרש רענון מחקר חודשי (הרץ מצב agent לפי PROMPT.md)."
    confidence_badge_class = {"גבוהה": "badge-ok", "בינונית": "badge-warn"}.get(val.get("confidence", ""), "badge-bad")

    public_market = market.get("public_market_summary", {})
    market_location = market.get("location", {})
    source_health = market.get("source_health", {})
    madlan_market = next(
        (item for item in market.get("supplemental_sources", [])
         if item.get("source") == "madlan" and item.get("comparison_area") == "נוריות" and item.get("ok", True)),
        {},
    )
    madlan_six = (madlan_market.get("prices_by_rooms") or {}).get("6", {})
    narkisim_market = next(
        (item for item in market.get("supplemental_sources", [])
         if item.get("source") == "madlan" and item.get("comparison_area") == "נרקיסים" and item.get("ok", True)),
        {},
    )
    narkisim_six = (narkisim_market.get("prices_by_rooms") or {}).get("6", {})
    government_narkisim = next(
        (item for item in market.get("government_comparisons", []) if item.get("area") == "נרקיסים"),
        {},
    )
    government_narkisim_summary = government_narkisim.get("summary") or {}
    government_narkisim_location = government_narkisim.get("location") or {}
    nuriot_six_price = madlan_six.get("new_build_price_nis") or 0
    narkisim_six_price = narkisim_six.get("new_build_price_nis") or 0
    narkisim_premium_pct = (
        round((narkisim_six_price / nuriot_six_price - 1) * 100, 1)
        if nuriot_six_price and narkisim_six_price else None
    )
    dataset_version = public_market.get("dataset_version")
    dataset_age_days = None
    try:
        dataset_date = datetime.datetime.strptime(dataset_version, "%d-%m-%Y").date()
        dataset_age_days = (datetime.date.today() - dataset_date).days
    except (TypeError, ValueError):
        dataset_date = None
    freshness_class = "badge-ok" if dataset_age_days is not None and dataset_age_days <= 120 else "badge-warn"
    freshness_text = f"{dataset_age_days} ימים" if dataset_age_days is not None else "לא ידוע"
    source_badge = "badge-ok" if market else "badge-bad"
    boundary_badge = "badge-warn" if market_location.get("boundary_name_mismatch") else "badge-ok"

    stage_html = "".join(
        f'<div class="status-line"><span>{s.get("name", "")}</span>'
        f'<span class="badge {"badge-ok" if s.get("ok") else "badge-bad"}">'
        f'{"תקין" if s.get("ok") else "נכשל"} · {s.get("duration_seconds", 0)}s</span></div>'
        for s in status.get("stages", [])
    ) or '<div class="note">טרם נרשמה ריצת עדכון מלאה.</div>'
    history_rows = "".join(
        f'<tr><td>{h.get("completed_at", "")[:19].replace("T", " ")}</td>'
        f'<td><span class="badge {"badge-ok" if h.get("ok") else "badge-bad"}">{"תקין" if h.get("ok") else "נכשל"}</span></td>'
        f'<td>{", ".join(s.get("name", "") for s in h.get("stages", []))}</td></tr>'
        for h in update_history[-5:][::-1]
    ) or '<tr><td colspan="3">אין היסטוריה עדיין</td></tr>'

    photo_html = (f'<div class="photo"><img src="{photo}" alt="הדירה"></div>' if photo
                  else '<div class="photo placeholder">📷 שמור תמונה בשם <code>photo.jpg</code> בתיקייה</div>')

    # ----- תשלומים -----
    pay_rows = ""
    for s in pay.get("schedule", []):
        idx = "🔗" if s.get("indexed") else ""
        pay_rows += (
            f'<tr><td>{s["date"]}</td>'
            f'<td class="num amt-cell" data-base="{s["amount_incl_vat"]}">{shekel(s["amount_incl_vat"])} {idx}</td>'
            f'<td class="paid-cell"></td>'
            f'<td><input type="checkbox" class="paychk" data-date="{s["date"]}" '
            f'data-amt="{s["amount_incl_vat"]}" data-indexed="{1 if s.get("indexed") else 0}" '
            f'{"checked" if s.get("paid") else ""}></td></tr>'
        )

    # ----- מקורות -----
    def srcs(items):
        return "".join(f'<a href="{s["url"]}" target="_blank">{s["label"]} ↗</a>' for s in items or [])

    # ----- גאנט -----
    gantt_html = ""
    for w in reno.get("gantt", []):
        tasks = ""
        for i, t in enumerate(w.get("tasks", [])):
            tasks += (f'<li><label><input type="checkbox" class="gtask" data-id="w{w["week"]}t{i}">'
                      f'<span class="days">ימים {t["days"]}</span> {t["desc"]}</label></li>')
        gantt_html += (f'<div class="week"><div class="week-head"><span class="wk">שבוע {w["week"]}</span>'
                       f'<span class="wk-title">{w["title"]}</span><span class="trade">{w.get("trade","")}</span></div>'
                       f'<ul class="tasks">{tasks}</ul></div>')

    # ----- אנשי מקצוע (רפרנס) -----
    pros_ref = ""
    for pr in reno.get("professionals", []):
        pros_ref += (f'<tr><td><b>{pr["he"]}</b></td><td>{pr["role"]}</td>'
                     f'<td class="num">{pr.get("when","")}</td></tr>')

    # ----- דברים לביצוע (נגזר מ-constraints + valuation) -----
    actions = [
        ("spec", "לקרוא תוכנית מכר + מפרט ולסמן מה כלול בגימור", "🔴 דחוף"),
        ("wall", "לבדוק בתוכנית אם הקיר להזזה מחיצה / נושא / ממ\"ד", "🔴 דחוף"),
        ("next_pay", f"תשלום הבא 07/06/26 (~{shekel(242568.70)})", "🔴 דחוף"),
        ("kitchen_quote", "לקבל 2–3 הצעות מחיר למטבח (אספקה+התקנה)", "🟡 בינוני"),
        ("pros_quotes", "לאתר אנשי מקצוע ולקבל הצעות (אינסטלטור/חשמלאי/רצף/גבסן/צבעי)", "🟡 בינוני"),
        ("budget", "לקבע תקציב שיפוץ סופי לפי האפשרויות שנבחרו", "🟡 בינוני"),
        ("handover", "לעקוב אחר מועד מסירה (~Q3 2028) ולתעד עיכובים", "🟢 רגיל"),
    ]
    action_html = "".join(
        f'<li><label><input type="checkbox" class="action" data-id="{k}">{txt}</label>'
        f'<span class="pri">{pri}</span></li>' for k, txt, pri in actions
    )

    # ----- שכונה -----
    nb_pros = "".join(f'<span class="pill">✓ {x}</span>' for x in nb.get("pros", []))
    nb_cons = "".join(f'<span class="pill">⚠ {x}</span>' for x in nb.get("cons", []))

    # ----- פליפ / שדרוג -----
    tiers_html = ""
    for t in up.get("tiers", []):
        tiers_html += (f'<div class="tier"><h4>{t["tier"]} — <span class="price">{t["price_range"]}</span></h4>'
                       f'<div class="sub">📍 {", ".join(t.get("areas", []))} · {t.get("type","")}</div>'
                       f'<div style="margin-top:4px">{t.get("fit","")}</div></div>')

    hand = apt.get("handover", {})
    # ----- גרף מגמת שוק (ראשל"צ מול ארצי) -----
    mt = apt.get("market_trend", {})
    trend_chart_html = ""
    mseries = mt.get("series", [])
    if mseries:
        mx = max(max(s["national"], s["area"]) for s in mseries)
        mn = min(min(s["national"], s["area"]) for s in mseries)
        base = max(0, mn - (mx - mn) * 0.6)
        bars = ""
        for s in mseries:
            ha = round((s["area"] - base) / (mx - base or 1) * 100)
            hn = round((s["national"] - base) / (mx - base or 1) * 100)
            bars += (f'<div class="tg"><div class="tg-bars">'
                     f'<div class="tg-b tg-area" style="height:{max(4,ha)}%"><span>{s["area"]}</span></div>'
                     f'<div class="tg-b tg-nat" style="height:{max(4,hn)}%"><span>{s["national"]}</span></div>'
                     f'</div><div class="tg-yr">{s["year"]}</div></div>')
        trend_chart_html = (
            '<div class="tglegend"><span class="tg-k tg-area"></span> ראשל"צ/נוריות '
            '<span class="tg-k tg-nat"></span> ארצי <span class="sub">(מדד 2021=100)</span></div>'
            f'<div class="tgwrap">{bars}</div>'
            f'<div class="sub" style="margin-top:8px">{mt.get("summary","")}</div>'
            f'<div class="src"><a href="{mt.get("source",{}).get("url","#")}" target="_blank">{mt.get("source",{}).get("label","")} ↗</a></div>'
        )

    # ----- בדק בית / מסירה -----
    hand = apt.get("handover", {})
    warranty_rows = "".join(
        f'<tr><td>{w["item"]}</td><td class="num">{w["bedek"]}</td><td class="num">{w["achrayut"]}</td></tr>'
        for w in hand.get("warranty", [])
    )
    checklist_html = ""
    for ci, c in enumerate(hand.get("checklist", [])):
        items = "".join(
            f'<li><label><input type="checkbox" class="handcheck" data-id="h{ci}_{ii}"> {it}</label></li>'
            for ii, it in enumerate(c.get("items", []))
        )
        checklist_html += (f'<div class="week"><div class="week-head"><span class="wk">{c["cat"]}</span></div>'
                           f'<ul class="tasks">{items}</ul></div>')

    payload = {"options": reno.get("options", []),
               "pros": {pr["key"]: pr["he"] for pr in reno.get("professionals", [])},
               "kitchen_credit": reno.get("kitchen_credit_nis", 0),
               "index_base": pay.get("index_base", 0),
               "shopping_seed": [o["he"] for o in reno.get("options", []) if o.get("diy")],
               "pros_seed": [pr["he"] for pr in reno.get("professionals", [])],
               "value_seed": apt.get("valuation_history") or [
                   {"date": (pur.get("contract_signed", "") or "")[:7], "value": paid_price, "note": "מחיר רכישה"},
                   {"date": val.get("last_updated", ""), "value": est, "note": "הערכת שוק"},
               ],
               "rooms_seed": apt.get("rooms_dimensions") or ["כניסה", "סלון + פינת אוכל", "מטבח"],
               "payments": pay.get("schedule", []),
               "management": management,
               "market": market,
               "update_status": {
                   "ok": status.get("ok"),
                   "completed_at": status.get("completed_at"),
                   "stages": [
                       {
                           "name": stage.get("name"),
                           "ok": stage.get("ok"),
                           "duration_seconds": stage.get("duration_seconds", 0),
                       }
                       for stage in status.get("stages", [])
                   ],
               },
               "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    # ----- סקשנים שעוברים לסוף / נוספים -----
    prep_html = "".join(
        f'<li><label><input type="checkbox" class="action" data-id="prep{i}">{t}</label></li>'
        for i, t in enumerate(reno.get("prep_before_key", []))
    )
    shortest_section = f"""
  <section>
    <h2>🚀 תוכנית ביצוע מהירה + מה לפני מפתח</h2>
    <div class="warn" style="background:#06281f;border-color:#22c55e;color:#bbf7d0">⚡ {reno.get('shortest_path','')}</div>
    <div class="card" style="margin-top:10px">
      <h3>✅ משימות שאפשר להשלים לפני קבלת המפתח</h3>
      <ul class="flat">{prep_html}</ul>
    </div>
  </section>"""
    action_section = f"""
  <section>
    <h2>📋 דברים לביצוע</h2>
    <div class="card"><ul class="flat">{action_html}</ul></div>
  </section>"""
    restr_section = f"""
  <section>
    <h2>⚖️ מגבלות מחיר למשתכן</h2>
    <div class="card restr">
      <div><b>נעילת מכירה:</b> {restr.get('sale_lock','')}</div>
      <div><b>קנס מכירה מוקדמת:</b> {restr.get('early_sale_penalty_nis','')}</div>
      <div><b>השכרה:</b> {restr.get('rent','')}</div>
      <div><b>מס שבח אחרי ההגבלה:</b> {restr.get('tax_after_lock','')}</div>
      <div class="src"><a href="{restr.get('source',{}).get('url','#')}" target="_blank">{restr.get('source',{}).get('label','')} ↗</a></div>
    </div>
  </section>"""

    # ----- מיקום, תוכניות ומסמכים רשמיים -----
    documents_section = ""
    if docs:
        gis_url = docs.get("city_gis_url", "#")
        map_lat = docs.get("map_lat")
        map_lon = docs.get("map_lon")
        map_zoom = docs.get("map_zoom", 18)
        if map_lat is not None and map_lon is not None:
            # תצ״א/לוויין עדכני (Google hybrid). gis-net העירוני חוסם iframe, ו-OSM embed הוא מפת רחובות בלבד.
            ortho_src = (
                f"https://maps.google.com/maps?q={map_lat},{map_lon}"
                f"&t=h&z={map_zoom}&hl=he&output=embed"
            )
            map_visual = (
                f'<iframe src="{ortho_src}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" '
                f'title="תצ״א עדכנית — הבניין" '
                f'style="width:100%;height:320px;border:1px solid var(--line);border-radius:10px"></iframe>'
            )
        else:
            map_img = docs.get("location_map_image")
            map_visual = (
                f'<div class="photo placeholder" style="margin:0">🗺️ שמור צילום מפה בשם '
                f'<code>{map_img or "assets/location-map.png"}</code></div>'
            )
        plan_local = docs.get("apartment_plan_pdf_local")
        plan_url = docs.get("apartment_plan_pdf_url", "#")
        plan_embed = (
            f'<object data="{plan_local}" type="application/pdf" '
            f'style="width:100%;height:360px;border-radius:10px;border:1px solid var(--line)">'
            f'<div class="note">לא ניתן להטמיע כאן (למשל באתר הפומבי — הקובץ פרטי). '
            f'<a href="{plan_url}" target="_blank">פתח את תוכנית הדירה ↗</a></div></object>'
            if plan_local else ""
        )
        building_url = docs.get("building_plan_pdf_url", "#")
        cityhall_url = docs.get("cityhall_building_url", "#")
        documents_section = f"""
  <section>
    <h2>📍 מיקום, תוכניות ומסמכים רשמיים</h2>
    <div class="grid">
      <div class="card">
        <h3>🗺️ מפת מיקום</h3>
        {map_visual}
        <div class="note">תצ״א/לוויין עדכני לאוריינטציה. גושים/חלקות, תצ״א רשמית ותוכניות בניין נמצאים ב-GIS העירוני.</div>
        <a class="addbtn" href="{gis_url}" target="_blank" rel="noopener" style="display:inline-block;text-decoration:none">🗺️ פתח GIS עירוני (עם כל השכבות) ↗</a>
      </div>
      <div class="card">
        <h3>📐 תוכנית הדירה ({u.get('unit_code','')})</h3>
        {plan_embed}
        <div class="src"><a href="{plan_url}" target="_blank">פתח / הורד PDF ↗</a></div>
        <div class="note">מוטמע מקומית; באתר הפומבי הקובץ פרטי — נפתח בקישור.</div>
      </div>
      <div class="card">
        <h3>🏢 תוכנית / תיק הבניין</h3>
        <div class="src"><a href="{building_url}" target="_blank">פתח סריקת תיק בניין ↗</a></div>
        <div class="note">{docs.get('building_plan_note','')}</div>
      </div>
      <div class="card">
        <h3>🏛️ תיק הבניין בעירייה</h3>
        <div class="src"><a href="{cityhall_url}" target="_blank">פתח בקשה {docs.get('cityhall_request_id','')} ↗</a></div>
        <div class="note">מערכת הרישוי של עיריית ראשון לציון (נפתח בכרטיסייה חדשה).</div>
      </div>
    </div>
  </section>"""

    # ----- שורת KPI עליונה -----
    hero_html = f"""
  <div class="hero">
    <div class="kpi"><div class="k-lbl">מחיר ששולם</div><div class="k-val">{shekel(paid_price)}</div><div class="k-sub">חוזה {pur.get('contract_signed','')}</div></div>
    <div class="kpi"><div class="k-lbl">שווי מוערך (טווח)</div><div class="k-val">{shekel(val_low)}–{shekel(val_high)}</div><div class="k-sub"><span class="badge {confidence_badge_class}">ביטחון {val.get('confidence','—')}</span></div></div>
    <div class="kpi"><div class="k-lbl">רווח על הנייר (טווח)</div><div class="k-val" style="color:{equity_color}">{equity_range_txt}</div><div class="k-sub">≈ +{equity_pct}% · מימוש ממכירה מ-{restr.get('sale_allowed_from','~2030')}</div></div>
    <div class="kpi"><div class="k-lbl">התשלום הבא</div><div class="k-val" id="hero-nextpay">—</div><div class="k-sub" id="hero-nextpay-sub">לוח החוזה</div></div>
    <div class="kpi"><div class="k-lbl">עד מסירה משוערת</div><div class="k-val" id="hero-handover">—</div><div class="k-sub">תשלום אחרון 30/09/28</div></div>
  </div>"""

    # ----- תוכנית הדירה האמיתית (render מה-PDF) + מהלכי השבחה -----
    plan_img = "assets/plan-128A5.png"
    plan_exists = os.path.exists(os.path.join(HERE, plan_img))
    plan_visual = (
        f'<img src="{plan_img}" alt="תוכנית מכר 128A5" loading="lazy" '
        'style="width:100%;border-radius:10px;border:1px solid var(--line);background:#fff">'
        if plan_exists else
        '<div class="note">התוכנית המלאה מוצגת בסקשן "מיקום, תוכניות ומסמכים רשמיים". הקובץ פרטי ואינו מתפרסם.</div>'
    )
    floorplan_html = (
        '<div class="card" style="margin-top:12px">'
        '<h3>🗺️ תוכנית הדירה (128A5) + מהלכי השבחה</h3>'
        + plan_visual +
        '<div class="pillrow" style="margin-top:10px">'
        '<span class="pill" style="border-color:#f5c451;color:#fde9b8">🏆 מטבח → לפתוח לסלון/פינת אוכל (השבחה מקסימלית)</span>'
        '<span class="pill" style="border-color:#22d3ee;color:#bae6fd">🚽 שירותי 113/173 (אסלה) — לרוב עדיף להשאיר כ-WC אורחים</span>'
        '<span class="pill" style="border-color:#f87171;color:#fecaca">⛔ ממ"ד — קירות בטון, אסור לגעת</span>'
        '</div>'
        '<div class="note">התוכנית האמיתית (מהדורה 7, 04.11.25) מוצגת מקומית — הקובץ פרטי (מסונן ב-git). לביצוע — לאמת מול התוכנית המקורית ומהנדס.</div>'
        '</div>'
    )

    # ----- אסטרטגיית השבחת ערך (מבוסס תוכנית) -----
    vstrat = reno.get("value_strategy", {})
    value_strategy_html = ""
    if vstrat.get("items"):
        vitems = "".join(f"<li>{it}</li>" for it in vstrat["items"])
        value_strategy_html = (
            '<div class="card" style="border-color:#16a34a;background:#06281f;margin-top:12px">'
            f'<h3 style="color:#bbf7d0">{vstrat.get("title","")}</h3>'
            f'<ul class="flat" style="margin:0">{vitems}</ul></div>'
        )

    # ----- רעיונות עיצוב לפי חדר -----
    # קישורי השראה בלבד (Pinterest + Google Images בעברית) ולא תמונות מוטמעות —
    # שומר על index.html עצמאי/אופליין ומונע קישורים שבורים לספקים ספציפיים.
    ridea = reno.get("room_ideas", {})
    room_ideas_section = ""
    if ridea.get("rooms"):
        cards = []
        # מפתח חדר = אינדקס מספרי (יציב, ונמנע מבעיות ציטוט בשמות עם " כמו ממ"ד)
        for i, r in enumerate(ridea["rooms"]):
            ideas = "".join(f"<li>{it}</li>" for it in r.get("ideas", []))
            links = "".join(
                f'<a class="addbtn" href="{lk.get("url","#")}" target="_blank" rel="noopener" '
                f'style="display:inline-block;text-decoration:none;margin:4px 4px 0 0">{lk.get("label","")} ↗</a>'
                for lk in r.get("links", [])
            )
            note = (f'<div class="note" style="margin-bottom:8px">{r.get("note","")}</div>'
                    if r.get("note") else "")
            q = (r.get("search_en", "") or "").replace('"', '&quot;')
            # כרטיס עם לשוניות (עיצוב ג'): רעיונות · גלריה · שמורים.
            # הגלריה החיה נטענת רק כשפותחים את לשונית "גלריה" (חוסך קריאות API).
            cards.append(
                '<div class="card">'
                '<div class="rc-head">'
                f'<div><h3 style="margin:0">{r.get("emoji","")} {r.get("name","")}</h3>'
                f'<div class="sub" style="margin-top:3px">📐 {r.get("dims","")}</div></div>'
                f'<span class="savecount" data-count="{i}">🔖 <b>0</b></span>'
                '</div>'
                f'{note}'
                f'<div class="rc-seg" data-room="{i}">'
                f'<button class="on" data-tab="ideas">🎨 רעיונות</button>'
                f'<button data-tab="gal">🖼️ גלריה</button>'
                f'<button data-tab="saved">🔖 שמורים (<span class="rc-savedn" data-room="{i}">0</span>)</button>'
                '</div>'
                # לשונית רעיונות
                '<div class="rc-panel on" data-panel="ideas">'
                f'<ul class="flat" style="margin:0 0 10px">{ideas}</ul>'
                f'<div class="pillrow">{links}</div>'
                '</div>'
                # לשונית גלריה (Openverse)
                '<div class="rc-panel" data-panel="gal">'
                '<div class="cc-search">'
                f'<input class="cc-q" data-room="{i}" value="{q}" placeholder="חיפוש תמונות השראה…">'
                f'<button class="cc-go" data-room="{i}">🔎 חפש</button>'
                '</div>'
                f'<div class="cc-results" data-room="{i}" data-search="{q}"></div>'
                '<div class="pillrow" style="margin-top:8px">' + links + '</div>'
                '</div>'
                # לשונית שמורים
                '<div class="rc-panel" data-panel="saved">'
                f'<div class="room-saved" data-room="{i}"></div>'
                '<label class="addbtn filebtn" style="background:var(--card2);color:var(--ink);'
                'display:inline-block;margin-top:8px">➕ העלה תמונה משלך'
                f'<input type="file" accept="image/*" multiple class="room-img-input" data-room="{i}"></label>'
                '</div>'
                '</div>'
            )
        room_ideas_section = f"""
  <section>
    <h2>💡 רעיונות עיצוב לפי חדר</h2>
    <div class="sub">{ridea.get('intro','')}</div>
    <div class="saved-filter">
      <button class="chip-toggle" id="saved-only-toggle" aria-pressed="false">🔖 הצג שמורים בלבד (<span id="saved-img-count">0</span>)</button>
      <span class="note" style="margin:0">גלריה חיה מ-Openverse (תמונות Creative-Commons, עם קרדיט וקישור למקור) — דורשת אינטרנט. 🔖 = שמור להשראה (נשמר מקומית + בגיבוי). אפשר גם להעלות תמונה משלך.</span>
    </div>
    <div class="grid room-ideas-grid" style="margin-top:10px">{''.join(cards)}</div>
  </section>"""

    body = f"""
  <header>
    {photo_html}
    <div class="info">
      <h1>🏠 ניהול שיפוץ — דירת נוריות</h1>
      <div class="meta">{u.get('rooms','')} חדרים · {u.get('area_sqm','')} מ"ר + מרפסת {u.get('balcony_sqm','')} מ"ר · {p.get('neighborhood','')}, {p.get('city','')} · פרויקט {p.get('developer','')} · מחיר למשתכן · מסירה {pur.get('expected_handover','')}</div>
    </div>
  </header>
{hero_html}

  <div class="toolbar">
    <button class="addbtn" id="expand-all">⊕ פתח הכל</button>
    <button class="addbtn" id="collapse-all" style="background:var(--card2);color:var(--ink)">⊖ כווץ הכל</button>
    <button class="addbtn" id="export-state" style="background:var(--green);color:#052e1a">⬇ גיבוי נתונים</button>
    <label class="addbtn filebtn" style="background:var(--card2);color:var(--ink)">⬆ שחזור גיבוי<input type="file" id="import-state" accept="application/json"></label>
  </div>
  <div class="toast" id="backup-msg">עריכות נשמרות מקומית. מומלץ לייצא גיבוי לאחר שינוי משמעותי.</div>
{documents_section}

  <section>
    <h2>🩺 מצב מערכת ונתונים</h2>
    <div class="health-grid">
      <div class="health-item"><b>מקור שוק</b><span class="badge {source_badge}">{'זמין' if market else 'חסר'}</span><div class="note">Nadlan + GovMap</div></div>
      <div class="health-item"><b>גרסת נתונים</b><span class="badge {freshness_class}">{dataset_version or 'לא ידועה'}</span><div class="note">גיל: {freshness_text}</div></div>
      <div class="health-item"><b>התאמת גבול</b><span class="badge {boundary_badge}">{'פער — נוריות/מרום ראשון' if market_location.get('boundary_name_mismatch') else 'תואם'}</span><div class="note">אזור {market_location.get('statistical_area_id','—')}</div></div>
      <div class="health-item"><b>עדכון אחרון</b><span class="badge {'badge-ok' if status.get('ok') else 'badge-warn'}">{'תקין' if status.get('ok') else 'לא אומת'}</span><div class="note">{status.get('completed_at', market.get('fetched_at','—'))[:19].replace('T',' ')}</div></div>
      <div class="health-item"><b>Madlan</b><span class="badge {'badge-ok' if (source_health.get('madlan') or {}).get('ok') else 'badge-bad'}">{'נסרק' if (source_health.get('madlan') or {}).get('ok') else 'נכשל'}</span><div class="note">אינדיקציות שוק, לא עסקאות ממשלתיות</div></div>
      <div class="health-item"><b>Yad2</b><span class="badge badge-warn">לא זמין לאוטומציה</span><div class="note">הגנת anti-bot; החבילה שנבדקה ממוקדת רכב</div></div>
    </div>
    <div class="grid">
      <div class="card"><h3>שלבי הריצה האחרונה</h3>{stage_html}</div>
      <div class="card scroll"><h3>היסטוריית עדכונים</h3><table><tr><th>מועד</th><th>מצב</th><th>שלבים</th></tr>{history_rows}</table></div>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>🔄 רענון נתונים</h3>
      <div class="sub">הצינור המלא (משיכת שוק → אימות → snapshot → בניית HTML) רץ ב-GitHub Actions — הקישור פותח את המסך שבו לוחצים <b>"Run workflow"</b>. רץ גם אוטומטית כל יום שני.</div>
      <a class="addbtn" href="{p.get('refresh_workflow_url','#')}" target="_blank" rel="noopener" style="display:inline-block;text-decoration:none">🔄 הרץ עדכון נתונים (GitHub Actions) ↗</a>
      <div class="note" style="margin-top:8px">מקומית (מריצים את כל הסקריפטים): <code>python dira-nuriot/update_all.py</code></div>
    </div>
  </section>

  <section>
    <h2>🏙️ נתוני שוק רשמיים</h2>
    <div class="warn">הנתון הרשמי הוא סיכום לכל גדלי הדירות באזור הסטטיסטי הישן “{public_market.get('statistical_area_name','—')}”. התצפית האחרונה היא מ־03/2025 ואין בקובץ מחיר שכונתי מאוחר יותר; לכן היא היסטורית בלבד ואינה שווי נוכחי לדירת 6 חדרים בנוריות.</div>
    <div class="metric-row">
        <div class="metric"><span>תצפית ממשלתית אחרונה — ישנה</span><strong>{shekel(public_market.get('latest_neighborhood_price_nis'))}</strong><span class="note">{(public_market.get('latest_neighborhood_period') or {}).get('month','—')}/{(public_market.get('latest_neighborhood_period') or {}).get('year','—')} · כל החדרים · אין תצפית מאוחרת יותר</span></div>
      <div class="metric"><span>ממוצע שנה — כל החדרים</span><strong>{shekel(public_market.get('all_rooms_last_year_avg_price_nis'))}</strong><span class="note">שינוי {public_market.get('all_rooms_price_change_pct','—')}%</span></div>
      <div class="metric"><span>ממוצע שנה — 5 חדרים</span><strong>{shekel(public_market.get('five_rooms_last_year_avg_price_nis'))}</strong><span class="note">קטגוריה קרובה, לא זהה</span></div>
    </div>
    <div class="src"><a href="{market.get('source_url','#')}" target="_blank">מקור ממשלתי ↗</a></div>
    <div class="card" style="margin-top:12px">
      <h3>Madlan — אינדיקציות עדכניות לנוריות (מקור עיקרי לעדכניות)</h3>
      <div class="metric-row">
        <div class="metric"><span>6 חדרים — בנייה חדשה</span><strong>{shekel(madlan_six.get('new_build_price_nis'))}</strong><span class="note">סיכום קטגוריה, לא עסקה בודדת</span></div>
        <div class="metric"><span>6 חדרים — יד שנייה</span><strong>{shekel(madlan_six.get('second_hand_price_nis'))}</strong><span class="note">סיכום קטגוריה</span></div>
        <div class="metric"><span>ממוצע עסקאות למ״ר</span><strong>{shekel(madlan_market.get('average_price_per_sqm_nis'))}</strong><span class="note">{madlan_market.get('total_deals_count','—')} עסקאות בסיכום</span></div>
        <div class="metric"><span>עסקאות בשנה</span><strong>{madlan_market.get('year_deals_count','—')}</strong><span class="note">מודעות פעילות למכירה: {madlan_market.get('active_for_sale_count','—')}</span></div>
      </div>
      <div class="sub">עודכן במקור: {madlan_market.get('source_updated_at','—')} · מקור משלים מסחרי; אין לערבב עם עסקאות ממשלתיות ללא תיוג.</div>
      <div class="src"><a href="{madlan_market.get('source_url','#')}" target="_blank">Madlan נוריות ↗</a></div>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>השוואת שכונה חדשה סמוכה — נרקיסים</h3>
      <div class="metric-row">
        <div class="metric"><span>6 חדרים — בנייה חדשה</span><strong>{shekel(narkisim_six.get('new_build_price_nis'))}</strong><span class="note">פער מול נוריות: {('+' + str(narkisim_premium_pct) + '%') if narkisim_premium_pct is not None else '—'}</span></div>
        <div class="metric"><span>ממוצע עסקאות למ״ר</span><strong>{shekel(narkisim_market.get('average_price_per_sqm_nis'))}</strong><span class="note">מקור Madlan</span></div>
        <div class="metric"><span>עסקאות בשנה</span><strong>{narkisim_market.get('year_deals_count','—')}</strong><span class="note">מול {madlan_market.get('year_deals_count','—')} בנוריות</span></div>
        <div class="metric"><span>מודעות פעילות למכירה</span><strong>{narkisim_market.get('active_for_sale_count','—')}</strong><span class="note">מדד עומק היצע</span></div>
      </div>
      <div class="warn">נרקיסים מתאימה כבנצ׳מרק לשכונה חדשה סמוכה, אך אינה נכס זהה: יש הבדלים בבשלות השכונה, מלאי, מיקום פנימי, קומה, מפרט ומועד מסירה.</div>
      <div class="warn" style="background:#3b1f06;border-color:#b45309">מקור ממשלתי: נרקיסים ממופה לאזור הישן “{government_narkisim_summary.get('statistical_area_name','—')}” ({government_narkisim_location.get('statistical_area_id','—')}), גרסה {government_narkisim_summary.get('dataset_version','—')}. קיימת אינדיקציית עסקאות, אך מחירי השכונה הפומביים ריקים—לכן הם אינם נכנסים לחישוב.</div>
      <div class="src"><a href="{narkisim_market.get('source_url','#')}" target="_blank">Madlan נרקיסים ↗</a></div>
      <div class="src"><a href="{government_narkisim.get('source_url','#')}" target="_blank">Nadlan ממשלתי — מיפוי נרקיסים ↗</a></div>
    </div>
  </section>

  <div class="grid" id="value-summary">
    <div class="card"><h3>מחיר רכישה</h3><div class="big">{shekel(paid_price)}</div><div class="sub">חוזה {pur.get('contract_signed','')} · ~{pur.get('price_per_sqm_paid','—'):,} ₪/מ"ר · מטבח לא כלול</div></div>
    <div class="card"><h3>שווי שוק מוערך</h3><div class="big">{shekel(est)}</div><div class="sub">טווח {shekel(val.get('estimated_value_low_nis'))}–{shekel(val.get('estimated_value_high_nis'))} · ביטחון {val.get('confidence','—')}</div></div>
    <div class="card"><h3>רווח על הנייר</h3><div class="big" style="color:{equity_color}">+{shekel(equity)} <span style="font-size:15px">(+{equity_pct}%)</span></div><div class="sub">מול המחיר ששולם · עודכן {val.get('last_updated','')}</div></div>
  </div>

  <section>
    <h2>💳 לוח תשלומים (חוזה)</h2>
    <div class="next" id="next-payment"></div>
    <div class="card" style="margin-top:10px">
      <table>
        <tr><th>תאריך</th><th>סכום (כולל מע"מ)</th><th>סטטוס</th><th>שולם?</th></tr>
        {pay_rows}
      </table>
      <div class="sub" style="margin-top:8px">🔗 = צמוד למדד תשומות הבנייה. {pay.get('index_note','')}</div>
      <div class="diyline" style="margin-top:10px">
        <label class="diychk" style="background:#1b2748;border-color:#38bdf8;color:#bae6fd">📊 מדד תשומות נוכחי
          <input type="number" step="0.01" id="index-input" style="width:90px;background:var(--bg);border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:3px 6px" placeholder="{pay.get('index_base','')}"></label>
        <span class="prodprice" style="color:#bae6fd">מדד בסיס: {pay.get('index_base','')} · תוספת מדד על הצמודים: <b id="index-extra">0 ₪</b></span>
      </div>
    </div>
    <div class="foot">
      <div>שולם עד כה: <b id="paid-total">—</b></div>
      <div>נותר לשלם (לפי מדד): <b id="remaining-total">—</b></div>
    </div>
  </section>

  <section>
    <h2>💰 תחזית תזרים ומימון עד מסירה</h2>
    <div class="card">
      <div class="field-grid">
        <label>מזומן זמין<input class="cell" id="cash-available_cash_nis" type="number"></label>
        <label>הפקדה חודשית<input class="cell" id="cash-monthly_contribution_nis" type="number"></label>
        <label>יעד שיפוץ<input class="cell" id="cash-renovation_target_nis" type="number"></label>
        <label>רזרבה (%)<input class="cell" id="cash-contingency_pct" type="number" step="0.1"></label>
      </div>
      <div class="metric-row">
        <div class="metric"><span>תשלומי חוזה שנותרו</span><strong id="cash-remaining">—</strong></div>
        <div class="metric"><span>צורך כולל + רזרבה</span><strong id="cash-required">—</strong></div>
        <div class="metric"><span>חודשים עד תשלום אחרון</span><strong id="cash-months">—</strong></div>
        <div class="metric"><span>חיסכון צפוי</span><strong id="cash-projected">—</strong></div>
        <div class="metric"><span>חיסכון חודשי נדרש</span><strong id="cash-monthly-needed">—</strong></div>
        <div class="metric"><span>פער נוכחי</span><strong id="cash-gap">—</strong><div id="cash-status"></div></div>
      </div>
    </div>
  </section>

  <section>
    <h2>📈 הערכת שווי, מגמה ומעקב</h2>
    <div class="stale {stale_class}">🕒 {stale_txt}</div>
    <div class="card">
      <h3>מודל שווי שקוף</h3>
      <div class="field-grid"><label>שווי בסיס<input class="cell" id="valuation-base" type="number"></label></div>
      <div id="valuation-adjustments" style="margin-top:10px"></div>
      <div class="foot"><div>סך התאמות: <b id="valuation-total-pct">—</b></div><div>שווי מתואם: <span class="big2" id="valuation-adjusted">—</span></div></div>
      <div class="scenario-grid" id="valuation-scenarios"></div>
    </div>
    <div class="card scroll" style="margin-top:12px">
      <h3>נכסים להשוואה — סוג המקור תמיד גלוי</h3>
      <div class="sub" style="margin-bottom:8px">רק שורות מסומנות <b>בר-השוואה</b> נכנסות לממוצע. נתונים מצרפיים/שכונות סמוכות מוצגים כרקע ומוחשכים. ₪/מ״ר מחושב כשמוזן שטח.</div>
      <div class="metric-row"><div class="metric"><span>בני-השוואה</span><strong id="comp-count">0</strong></div><div class="metric"><span>ממוצע מחיר (בני-השוואה)</span><strong id="comp-price-avg">—</strong></div><div class="metric"><span>ממוצע ₪/מ״ר (בני-השוואה)</span><strong id="comp-avg">—</strong></div></div>
      <table id="comparables-table"><tr><th>תאריך</th><th>כתובת</th><th>חדרים</th><th>מ״ר</th><th>מחיר</th><th>₪/מ״ר</th><th>סוג</th><th>ביטחון</th><th>בר-השוואה</th><th>מקור</th><th></th></tr></table>
      <button class="addbtn" id="add-comp">+ הוסף השוואה</button>
    </div>
    <div class="card">
      <div id="value-trend" class="vtrend"></div>
      <div id="value-chart"></div>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>📉 מגמת מחירים — ראשל"צ/נוריות מול ארצי</h3>
      {trend_chart_html}
    </div>
    <div class="card" style="margin-top:12px">
      <p style="margin-top:0">{val.get('trend','')}</p>
      <div class="sub"><b>השוואות:</b> {' · '.join(val.get('comps', []))}</div>
      <div class="src">{srcs(val.get('sources'))}</div>
    </div>
    <div class="card" style="margin-top:12px">
      <div class="sub" style="margin-bottom:6px">הערכות שווי לאורך זמן (נשמר בדפדפן):</div>
      <table id="value-table">
        <tr><th>תאריך</th><th>שווי (₪)</th><th>הערה</th><th></th></tr>
      </table>
      <button class="addbtn" id="add-value">+ הוסף הערכה</button>
    </div>
  </section>

  <section>
    <h2>📐 מידות חדרים</h2>
    <div class="sub">אורך×רוחב לכל חדר (שטח מחושב). שלח תוכנית מכר ואמלא אוטומטית. נשמר בדפדפן.</div>
    <div class="card" style="margin-top:10px">
      <table id="rooms-table">
        <tr><th>חדר</th><th>אורך (מ')</th><th>רוחב (מ')</th><th>שטח (מ"ר)</th><th></th></tr>
      </table>
      <button class="addbtn" id="add-room">+ הוסף חדר</button>
    </div>
  </section>

  <section>
    <h2>📐 מה כלול מהקבלן (מתוך המפרט)</h2>
    <div class="card nb">
      <div><b>פריסה:</b> {u.get('layout','')}</div>
      <div><b>קומה:</b> {u.get('floor','')} (מתוך {u.get('building_floors','')}) · בניין {u.get('building','')} · דירה {u.get('apartment_no','')} · גובה תקרה {u.get('ceiling_height_m','')} מ'</div>
      <div class="pillrow" style="margin:8px 0">{wet}</div>
      <div><b>🍳 מטבח:</b> {u.get('kitchen_note','')}</div>
      <div><b>❄️ מיזוג:</b> {u.get('ac_note','')}</div>
      <div><b>🚽 סניטריה:</b> {u.get('sanitary_note','')}</div>
      <div><b>🧱 ריצוף/דלתות:</b> {u.get('finishes_note','')}</div>
      <div class="warn" style="margin-top:10px">🛡️ <b>ממ"ד:</b> {cons.get('mamad_wall','')}</div>
      <div class="sub" style="margin-top:8px">🧩 {cons.get('wall_types','')}</div>
    </div>
  </section>

  <section>
    <h2>🛠️ אפשרויות שיפוץ — בחר מה לבצע</h2>
    <div class="sub">{reno.get('scope_note','')}</div>
    {floorplan_html}
    {value_strategy_html}
    <div class="warn">⚠️ הזזת קיר מותנית: רק אם הקיר אינו נושא/ממ"ד. הקבלן לא מבצע דבר — כל איש מקצוע עצמאי.</div>
    <div class="warn" style="background:#06281f;border-color:#22c55e;color:#bbf7d0">🔧 פריט עם <b>לבד</b> = ניתן להתקנה עצמית (יש לך ידיים טובות). סמן "לבד" כדי לשלם רק על המוצר. 🛒 = מחיר בארץ · 📦 = עלי אקספרס (זול בהרבה; מכס: עד $75 פטור, $75–500 — מע"מ 18% בלבד).</div>
    <div class="warn" style="background:#052e1a;border-color:#16a34a;color:#bbf7d0"><span class="vb vb-h">📈 מעלה ערך</span> = משדרג משמעותית את שווי הדירה למכירה (מטבח, אמבטיות, מיזוג). <span class="vb vb-m">📈 ערך בינוני</span> = תורם. ללא תגית = בעיקר נוחות/אסתטיקה, החזר נמוך במכירה. 💡 בדירה חדשה כדאי למקד תקציב בפריטי "מעלה ערך" ולא להגזים בהתאמה אישית (לא תמיד מחזירה את עלותה).</div>
    <div class="card" style="margin-top:12px">
      <div id="options-list"></div>
      <div class="src">{srcs(reno.get('sources'))}</div>
    </div>
    <div class="foot">
      <div>טווח שוק (נבחרו): <b id="budget-range">—</b></div>
      <div>זיכוי קבלן (מטבח): <b style="color:#22c55e">−{shekel(reno.get('kitchen_credit_nis',0))}</b></div>
      <div>תקציב מתוכנן (נטו): <span class="big2" id="budget-planned">—</span></div>
      <div>💰 חיסכון DIY: <b id="budget-savings" style="color:#22c55e">—</b></div>
      <div>לו"ז מוערך: <b id="timeline-days">—</b></div>
    </div>
    <div class="card" style="margin-top:12px">
      <h3>👷 אנשי מקצוע נדרשים (לפי הבחירה)</h3>
      <div class="pillrow" id="pros-needed"></div>
    </div>
  </section>
{room_ideas_section}

  <section>
    <h2>✅ משימות לביצוע (מתעדכן לפי האפשרויות)</h2>
    <div class="card" style="margin-bottom:12px">
      <div>התקדמות: <span id="task-pct">0%</span></div>
      <div class="progress"><i id="task-bar"></i></div>
    </div>
    <div class="card"><ul class="tasks" id="task-list"></ul></div>
  </section>

  <section>
    <h2>📊 תקציב שיפוץ בפועל</h2>
    <div class="metric-row"><div class="metric"><span>תקציב</span><strong id="reno-budget-total">—</strong></div><div class="metric"><span>התחייבויות/הצעות</span><strong id="reno-committed-total">—</strong></div><div class="metric"><span>שולם</span><strong id="reno-paid-total">—</strong></div><div class="metric"><span>סטייה</span><strong id="reno-variance-total">—</strong></div></div>
    <div class="card scroll"><table id="reno-track-table"><tr><th>פריט</th><th>תקציב</th><th>הצעה/סופי</th><th>ספק</th><th>מקדמה</th><th>שולם</th><th>סטטוס</th><th>סטייה</th><th></th></tr></table><button class="addbtn" id="add-reno-track">+ הוסף פריט</button></div>
  </section>

  {shortest_section}

  <section>
    <h2>🗓️ לו"ז ביצוע מפורט (רפרנס — מניח scope מלא, 5 שבועות)</h2>
    {gantt_html}
  </section>

  <section>
    <h2>👷 מדריך אנשי מקצוע</h2>
    <div class="card"><table>
      <tr><th>בעל מקצוע</th><th>תפקיד</th><th>מתי</th></tr>
      {pros_ref}
    </table></div>
  </section>

  <section>
    <h2>🔑 מסירה ובדק בית (לקראת ~2028)</h2>
    <div class="warn">🔍 {hand.get('inspection_tip','')}</div>
    <div class="warn" style="background:#3b1f06;border-color:#b45309">⏱️ {hand.get('delay_note','')}</div>
    <div class="card" style="margin-top:12px">
      <h3>תקופות בדק ואחריות (חוק המכר)</h3>
      <table>
        <tr><th>רכיב</th><th>תקופת בדק</th><th>אחריות</th></tr>
        {warranty_rows}
      </table>
      <div class="src"><a href="{hand.get('warranty_source',{}).get('url','#')}" target="_blank">{hand.get('warranty_source',{}).get('label','')} ↗</a></div>
    </div>
    <h3 style="margin-top:18px">✅ צ'קליסט בדיקה ביום המסירה</h3>
    <div class="card" style="margin-bottom:12px">
      <div>התקדמות בדיקה: <span id="hand-pct">0%</span></div>
      <div class="progress"><i id="hand-bar"></i></div>
    </div>
    {checklist_html}
    <div class="card scroll" style="margin-top:14px">
      <h3>ליקויים, אחריות ותיקון</h3>
      <div class="metric-row"><div class="metric"><span>פתוחים</span><strong id="defect-open">0</strong></div><div class="metric"><span>קריטיים</span><strong id="defect-critical">0</strong></div></div>
      <table id="defects-table"><tr><th>תאריך</th><th>אזור</th><th>תיאור</th><th>חומרה</th><th>אחראי</th><th>יעד</th><th>סטטוס</th><th>תמונה</th><th></th></tr></table>
      <button class="addbtn" id="add-defect">+ הוסף ליקוי</button>
    </div>
  </section>

  <section>
    <h2>📇 ספקים והצעות מחיר</h2>
    <div class="sub">הוסף בעלי מקצוע/ספקים, טלפון, הצעת מחיר וסטטוס. נשמר בדפדפן.</div>
    <div class="card" style="margin-top:10px">
      <table id="suppliers-table">
        <tr><th>שם</th><th>תחום</th><th>טלפון</th><th>הצעה (₪)</th><th>סטטוס</th><th></th></tr>
      </table>
      <button class="addbtn" id="add-supplier">+ הוסף ספק</button>
    </div>
  </section>

  <section>
    <h2>🛒 רשימת קניות / Wishlist עלי אקספרס</h2>
    <div class="sub">מוצרי DIY לקנייה: פריט, לינק, מחיר, והאם הוזמן. נשמר בדפדפן.</div>
    <div class="card" style="margin-top:10px">
      <table id="shop-table">
        <tr><th>פריט</th><th>לינק</th><th>מחיר (₪)</th><th>הוזמן?</th><th></th></tr>
      </table>
      <button class="addbtn" id="add-shop">+ הוסף פריט</button>
    </div>
  </section>

  <section>
    <h2>🏘️ סקירת שכונה — נוריות, ראשון לציון</h2>
    <div class="card nb">
      <p style="margin-top:0">{nb.get('summary','')}</p>
      <div><b>אוכלוסייה:</b> {nb.get('population','')}</div>
      <div><b>חינוך:</b> {nb.get('education','')}</div>
      <div><b>תחבורה:</b> {nb.get('transport','')}</div>
      <div><b>פיתוח:</b> {nb.get('development','')}</div>
      <div><b>מחירים:</b> {nb.get('prices','')}</div>
      <div class="pillrow">{nb_pros}</div>
      <div class="pillrow">{nb_cons}</div>
      <div class="src">{srcs(nb.get('sources'))}</div>
    </div>
  </section>

  <section>
    <h2>🔁 פלופ — מסלולי שדרוג עתידיים</h2>
    <div class="sub">{up.get('preferences','')}</div>
    <div class="warn">💡 {up.get('current_equity_note','')}</div>
    <div class="stale stale-warn">🔒 מימוש הרווח והשדרוג מותנה ב<b>תום נעילת המכירה: 18 חודשים אחרי קבלת המפתח → חלון מכירה חופשי מ-{restr.get('sale_allowed_from','~2030')}</b> (ראו "מגבלות מחיר למשתכן"). מומלץ לאמת ניסוח/קנס בחוזה.</div>
    {tiers_html}
    <div class="src">{srcs(up.get('sources'))}</div>
  </section>
{action_section}
{restr_section}

  <footer>עודכן {today} · index.html self-contained · עריכות מקומיות עם גיבוי/שחזור · מקור-אמת: apartment.json + renovation.json + management.json</footer>
"""

    html = (
        '<!DOCTYPE html>\n<html lang="he" dir="rtl">\n<head>\n'
        '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="לוח הדירה — נוריות, ראשון לציון: שווי, תשלומים, שיפוץ, שכונה ומסמכים רשמיים.">\n'
        '<meta name="theme-color" content="#0a0e1a">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800;900&display=swap">\n'
        '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'%3E%3Ctext y=\'.9em\' font-size=\'90\'%3E%F0%9F%8F%A0%3C/text%3E%3C/svg%3E">\n'
        '<title>לוח הדירה — נוריות</title>\n<style>' + CSS + '</style>\n</head>\n<body>\n'
        '<div class="wrap">' + body + '</div>\n'
        '<script>\nconst DATA = ' + json.dumps(payload, ensure_ascii=False) + ';\n' + JS + '\n</script>\n'
        '</body>\n</html>'
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ נוצר {OUT}")


if __name__ == "__main__":
    main()
