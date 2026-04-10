import json, urllib.parse, os, sys
import urllib.request
from datetime import date

# ── FETCH FROM AIRTABLE ───────────────────────────────────────────────────────
API_KEY = os.environ.get("AIRTABLE_API_KEY")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
TABLE   = "Events"

if not API_KEY or not BASE_ID:
    print("ERROR: Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID", file=sys.stderr)
    sys.exit(1)

def fetch_airtable():
    events = []
    offset = None
    while True:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{urllib.parse.quote(TABLE)}?pageSize=100"
        if offset:
            url += f"&offset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        for record in data.get("records", []):
            f = record.get("fields", {})
            if not f.get("Published"):
                continue
            events.append({
                "title":    f.get("Title", ""),
                "org":      f.get("Org", ""),
                "type":     f.get("Type", "Show"),
                "date":     f.get("Date") or None,
                "date_str": f.get("Date String", ""),
                "location": f.get("Location", ""),
                "url":      f.get("Event link", ""),
            })
        offset = data.get("offset")
        if not offset:
            break
    return events

events = fetch_airtable()
print(f"Fetched {len(events)} published events from Airtable")

# ── SORT ──────────────────────────────────────────────────────────────────────
today = date.today()

def sort_key(e):
    if e["type"] == "Incubator": return (0, "0000")
    if not e["date"]: return (3, "9999")
    if e["date"] < str(today): return (2, e["date"])
    return (1, e["date"])

events.sort(key=sort_key)

# ── HELPERS ───────────────────────────────────────────────────────────────────
TYPE_META = {
    "Show":      ("#FFD700","#111","Show"),
    "Jam":       ("#00A878","#fff","Jam"),
    "Workshop":  ("#0055BF","#fff","Workshop"),
    "Class":     ("#FF6B00","#fff","Class"),
    "Audition":  ("#E8001C","#fff","Audition"),
    "Incubator": ("#9B2DE8","#fff","Incubator"),
    "Festival":  ("#FF1493","#fff","Festival"),
    "Other":     ("#888888","#fff","Other"),
}

MAP = {
  "Off Cabot Comedy & Events, Beverly, MA": "Off Cabot Comedy Events 286 Cabot St Beverly MA",
  "UU Manchester, Manchester, NH": "First Unitarian Universalist Society 669 Union St Manchester NH",
  "Stark Brewing Company, Manchester, NH": "Stark Brewing Company 500 Commercial St Manchester NH",
  "Portland Media Center, Portland, ME": "Portland Media Center 516 Congress St Portland ME",
  "South Church UU, Portsmouth, NH": "South Church Unitarian Universalist 292 State St Portsmouth NH",
  "Beverly, MA": "Beverly MA",
  "Portsmouth, NH": "Portsmouth NH",
  "Manchester, NH": "Manchester NH",
}

DAYS = ["MON","TUE","WED","THU","FRI","SAT","SUN"]

def fmt_date(d_str):
    if not d_str: return None, None, None
    try:
        d = date.fromisoformat(d_str)
        return DAYS[d.weekday()], d.strftime("%b").upper(), d.strftime("%-d")
    except: return None, None, None

def is_soon(d_str):
    if not d_str: return False
    try:
        d = date.fromisoformat(d_str)
        return 0 <= (d - today).days <= 7
    except: return False

def is_started(e):
    if e["type"] not in ("Class","Workshop"): return False
    if e["date"] is None: return True
    return e["date"] < str(today)

def map_url(loc):
    q = MAP.get(loc, loc)
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)

def card(e):
    bg, fg, label = TYPE_META.get(e["type"], ("#333","#fff",e["type"]))
    dow, mon, day = fmt_date(e["date"])
    soon = is_soon(e["date"])
    started = is_started(e)

    if dow:
        date_html = f'<div class="cd"><div class="cd-dow">{dow}</div><div class="cd-mon">{mon}</div><div class="cd-day">{day}</div></div>'
    else:
        date_html = '<div class="cd ongoing"><span>ON<br>GOING</span></div>'

    soon_badge   = '<div class="badges"><span class="badge-soon">This Week</span></div>' if soon else ""
    started_note = '<div class="badges"><span class="badge-started">In Progress</span></div>' if started else ""
    murl         = map_url(e["location"])
    started_cls  = " card-started" if started else ""

    return f'''<div class="card{started_cls}" data-href="{e["url"]}" data-type="{e["type"]}" data-org="{e["org"]}" role="link" tabindex="0">
  <div class="card-top" style="background:{bg};color:{fg}">
    <div class="card-type-row"><span class="card-lbl">{label}</span>{soon_badge}</div>
    <p class="card-title">{e["title"]}</p>
    <p class="card-org-name">{e["org"]}</p>
  </div>
  <div class="card-bottom">
    {date_html}
    <p class="card-loc"><a class="map-link" href="{murl}" target="_blank" rel="noopener">{e["location"]} <span class="map-arr">↗</span></a></p>
    <p class="card-when">{e["date_str"]}</p>
    {started_note}
  </div>
</div>'''

cards_html   = "\n".join(card(e) for e in events)
last_updated = today.strftime("%B %-d, %Y")

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Seacoast Improv Scene</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bangers&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --red:#E8001C;--blue:#0055BF;--yellow:#FFD700;
  --green:#00A878;--orange:#FF6B00;--purple:#9B2DE8;
  --bg:#F5F2EC;--black:#111;
}}
body{{background:var(--bg);color:var(--black);font-family:'DM Sans',sans-serif}}
header{{background:var(--bg)}}
.h-inner{{max-width:960px;margin:0 auto;padding:3rem 2rem 2.5rem}}
.eyebrow{{font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;color:#666;margin-bottom:.6rem}}
h1{{font-family:'Bangers',cursive;font-size:clamp(4.5rem,14vw,9rem);letter-spacing:.04em;line-height:.88;color:var(--red)}}
.h-sub{{margin-top:.8rem;font-size:.88rem;color:#555;max-width:500px}}
.filter-bar{{max-width:960px;margin:0 auto;padding:.85rem 2rem;display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}}
.f-label{{font-family:'Bangers',cursive;font-size:1.05rem;letter-spacing:.06em;margin-right:.2rem;flex-shrink:0}}
.f-div{{width:1px;height:18px;background:var(--black);margin:0 .15rem;opacity:.2;flex-shrink:0}}
.fbtn{{background:var(--bg);border:2.5px solid var(--black);color:var(--black);padding:.26rem .72rem;font-family:'DM Sans',sans-serif;font-size:.72rem;font-weight:500;cursor:pointer;text-transform:uppercase;letter-spacing:.06em;transition:background .1s,color .1s}}
.fbtn:hover{{background:var(--black);color:#fff}}
.fbtn.active{{background:var(--black);color:#fff}}
.fbtn[data-filter="Show"]{{border-left:5px solid var(--yellow)}}
.fbtn[data-filter="Jam"]{{border-left:5px solid var(--green)}}
.fbtn[data-filter="Workshop"]{{border-left:5px solid var(--blue)}}
.fbtn[data-filter="Class"]{{border-left:5px solid var(--orange)}}
.fbtn[data-filter="Audition"]{{border-left:5px solid var(--red)}}
.fbtn[data-filter="Incubator"]{{border-left:5px solid var(--purple)}}
.fbtn[data-filter="Festival"]{{border-left:5px solid #FF1493}}
.fbtn[data-filter="Other"]{{border-left:5px solid #888}}
.fbtn.active[data-filter="Show"]{{background:var(--yellow);color:#111;border-left-color:var(--black)}}
.fbtn.active[data-filter="Jam"]{{background:var(--green);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Workshop"]{{background:var(--blue);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Class"]{{background:var(--orange);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Audition"]{{background:var(--red);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Incubator"]{{background:var(--purple);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Festival"]{{background:#FF1493;color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Other"]{{background:#888;color:#fff;border-left-color:var(--black)}}

.listings{{max-width:960px;margin:0 auto;padding:1.5rem 2rem 2rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.75rem}}
.card{{display:flex;flex-direction:column;border:3px solid var(--black);cursor:pointer;color:var(--black);background:var(--bg);position:relative;z-index:0;transition:transform .08s;min-height:180px}}
.card:hover{{transform:translate(-3px,-3px);box-shadow:6px 6px 0 var(--black);z-index:10}}
.card:focus-visible{{outline:3px solid var(--blue);outline-offset:2px}}
.card-started{{opacity:.5;filter:saturate(.35)}}
.card-started:hover{{opacity:.7;filter:saturate(.5)}}
.card-top{{padding:.8rem .9rem .6rem;display:flex;flex-direction:column;gap:.25rem;flex:1}}
.card-type-row{{display:flex;align-items:center;justify-content:space-between;gap:.4rem}}
.card-lbl{{font-size:.55rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;opacity:.8;font-family:'DM Sans',sans-serif}}
.card-title{{font-family:'Bangers',cursive;font-size:1.3rem;letter-spacing:.04em;line-height:1.1;margin-top:.1rem}}
.card-org-name{{font-family:'Bangers',cursive;font-size:1rem;letter-spacing:.04em;opacity:.75;margin-top:auto;padding-top:.4rem}}
.card-bottom{{padding:.6rem .9rem .7rem;border-top:2px solid rgba(0,0,0,.15);display:flex;flex-direction:column;gap:.2rem;background:rgba(0,0,0,.04)}}
.cd{{display:flex;align-items:baseline;gap:.3rem;font-family:'Bangers',cursive;line-height:1}}
.cd-dow{{font-size:.7rem;letter-spacing:.1em;opacity:.7}}
.cd-mon{{font-size:.85rem;letter-spacing:.08em}}
.cd-day{{font-size:1.3rem}}
.cd.ongoing span{{font-family:'DM Sans',sans-serif;font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;opacity:.7}}
.card-loc{{font-size:.68rem}}
.map-link{{color:inherit;text-decoration:none;opacity:.7;display:inline-flex;align-items:center;gap:.2rem}}
.map-link:hover{{opacity:1;text-decoration:underline}}
.map-arr{{font-size:.6rem;opacity:.55}}
.card-when{{font-size:.65rem;opacity:.6}}
.badges{{display:flex;gap:.3rem;flex-wrap:wrap}}
.badge-soon{{display:inline-block;font-size:.52rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;background:var(--black);color:#fff;padding:.1rem .38rem}}
.badge-started{{display:inline-block;font-size:.52rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;background:rgba(0,0,0,.25);color:#fff;padding:.1rem .38rem}}
.suggest-bar{{max-width:960px;margin:0 auto;padding:1.25rem 2rem;border-top:4px solid var(--black);border-bottom:4px solid var(--black);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem}}
.suggest-bar p{{font-size:.85rem;color:#444}}
.suggest-bar p strong{{font-family:'Bangers',cursive;font-size:1.1rem;letter-spacing:.04em;color:var(--black)}}
.suggest-link{{font-family:'Bangers',cursive;font-size:1rem;letter-spacing:.06em;text-transform:uppercase;background:var(--black);color:#fff;padding:.4rem 1.1rem;text-decoration:none;border:2.5px solid var(--black);transition:background .1s,color .1s;flex-shrink:0}}
.suggest-link:hover{{background:var(--red);border-color:var(--red)}}
footer{{border-top:2px solid var(--black);max-width:960px;margin:0 auto;padding:1.2rem 2rem;font-size:.68rem;color:#888;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.75rem}}
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:1000;align-items:center;justify-content:center;padding:1rem}}
.modal-overlay.modal-open{{display:flex}}
.modal-box{{background:var(--bg);border:3px solid var(--black);max-width:560px;width:100%;padding:2rem;position:relative;max-height:90vh;overflow-y:auto}}
.modal-close{{position:absolute;top:1rem;right:1rem;background:none;border:none;font-size:1.1rem;cursor:pointer;color:var(--black);padding:.25rem .4rem}}
.modal-close:hover{{background:var(--black);color:#fff}}
.modal-title{{font-family:'Bangers',cursive;font-size:2rem;letter-spacing:.04em;color:var(--red);margin-bottom:1rem;line-height:1}}
.modal-body{{font-size:.88rem;color:#444;line-height:1.6;margin-bottom:.75rem}}
.modal-list{{font-size:.88rem;color:#444;line-height:1.8;margin:0 0 .75rem 1.5rem}}
.modal-list li{{margin-bottom:.25rem}}
.modal-list strong{{color:var(--black)}}
.modal-btn{{display:inline-block;margin-top:.75rem;font-family:'Bangers',cursive;font-size:1rem;letter-spacing:.06em;text-transform:uppercase;background:var(--black);color:#fff;padding:.5rem 1.2rem;text-decoration:none;border:2.5px solid var(--black);transition:background .1s}}
.modal-btn:hover{{background:var(--red);border-color:var(--red)}}
.how-link{{background:none;border:none;padding:0;font-family:'DM Sans',sans-serif;font-size:inherit;color:#aaa;text-decoration:underline;text-underline-offset:2px;cursor:pointer}}
.how-link:hover{{color:#fff}}
.how-link-header{{background:none;border:none;padding:0;margin-top:.6rem;display:inline-block;font-family:'DM Sans',sans-serif;font-size:.82rem;font-weight:500;color:var(--black);text-decoration:underline;text-underline-offset:3px;cursor:pointer;letter-spacing:.01em}}
.how-link-header:hover{{color:var(--red)}}
.footer-left{{display:flex;flex-wrap:wrap;gap:.5rem .75rem;align-items:center}}
.footer-site{{font-family:'Bangers',cursive;font-size:.9rem;letter-spacing:.04em;color:var(--black)}}
footer a{{color:#555;text-decoration:underline;text-underline-offset:2px}}
footer a:hover{{color:var(--black)}}
.kofi-link{{font-size:.72rem;color:#555;text-decoration:underline;text-underline-offset:2px;white-space:nowrap}}
.kofi-link:hover{{color:var(--black)}}
.hidden{{display:none!important}}
@media(max-width:640px){{
  .h-inner,.filter-bar,.listings,footer,.suggest-bar{{padding-left:1rem;padding-right:1rem}}
  h1{{font-size:3.5rem}}
  .card-go{{display:none}}
  .f-div{{display:none}}
}}
</style>
</head>
<body>
<header>
  <div class="h-inner">
    <div class="eyebrow">Portland ME through Portsmouth NH, Manchester NH, and south to Beverly MA</div>
    <h1>SEACOAST IMPROV SCENE</h1>
    <p class="h-sub">Classes, shows, jams &amp; auditions from Portland ME through Portsmouth NH, Manchester NH, and south to Beverly MA.</p>
    <button class="how-link-header" onclick="document.getElementById('how-modal').classList.add('modal-open')">How does this work? →</button>
  </div>
</header>
<div class="filter-bar">
  <span class="f-label">Filter:</span>
  <button class="fbtn active" data-filter="all">All</button>
  <div class="f-div"></div>
  <button class="fbtn" data-filter="Show">Shows</button>
  <button class="fbtn" data-filter="Jam">Jams</button>
  <button class="fbtn" data-filter="Workshop">Workshops</button>
  <button class="fbtn" data-filter="Class">Classes</button>
  <button class="fbtn" data-filter="Audition">Auditions</button>
  <button class="fbtn" data-filter="Festival">Festivals</button>
  <button class="fbtn" data-filter="Incubator">Incubators</button>
  <button class="fbtn" data-filter="Other">Other</button>
</div>
<main class="listings">
{cards_html}
</main>
<div class="suggest-bar">
  <div class="suggest-text">
    <p class="suggest-heading">Got an event to add?</p>
    <p class="suggest-sub">This site is community-maintained. Submit a new listing, update an existing one, or request a removal.</p>
  </div>
  <a class="suggest-link" href="https://tally.so/r/QKJ18p" target="_blank" rel="noopener">Submit or Update a Listing →</a>
</div>

<!-- HOW IT WORKS MODAL -->
<div class="modal-overlay" id="how-modal">
  <div class="modal-box">
    <button class="modal-close" onclick="document.getElementById('how-modal').classList.remove('modal-open')" aria-label="Close">✕</button>
    <h2 class="modal-title">How does this work?</h2>
    <p class="modal-body">Seacoast Improv Scene is a community-maintained calendar of improv shows, jams, classes, workshops, auditions, and more across the New England seacoast region from Portland ME to Beverly MA.</p>
    <p class="modal-body">Anyone can submit a listing using the form on this page. Here's how:</p>
    <ol class="modal-list">
      <li>Click <strong>Submit or Update a Listing</strong></li>
      <li>Fill in the details — event name, org, type, date, time, location, and a link</li>
      <li>Hit Submit</li>
    </ol>
    <p class="modal-body">We review every submission before it goes live — usually within 24 hours. You can also use the form to update an existing listing, report an error, or request a removal.</p>
    <a class="modal-btn" href="https://tally.so/r/QKJ18p" target="_blank" rel="noopener">Submit or Update a Listing →</a>
  </div>
</div>
<footer>
  <div class="footer-left">
    <span class="footer-site">seacoastimprov.lol</span>
    <span>Updated {last_updated}</span>
    <span>Built by <a href="https://chadmoore.net" target="_blank" rel="noopener">Chad Moore</a> with ❤️ &amp; 🤓 on the seacoast of New Hampshire</span>
    <span>Not affiliated with any organization listed.</span>
  </div>
  <div class="footer-right">
    <a class="kofi-link" href="https://ko-fi.com/cgmoore" target="_blank" rel="noopener">☕ Support this site</a>
  </div>
</footer>


<script>
document.querySelectorAll('.card').forEach(card => {{
  card.addEventListener('click', e => {{
    if (e.target.closest('.map-link')) return;
    window.open(card.dataset.href, '_blank', 'noopener');
  }});
  card.addEventListener('keydown', e => {{
    if (e.key === 'Enter' || e.key === ' ') window.open(card.dataset.href, '_blank', 'noopener');
  }});
}});
const btns = document.querySelectorAll('.fbtn');
const cards = document.querySelectorAll('.card');
btns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    btns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    cards.forEach(card => {{
      const type = card.dataset.type;
      const org = card.dataset.org;
      let show = f === 'all' || f === type || f === org;
      card.classList.toggle('hidden', !show);
    }});
  }});
}});

// Close modal on Escape or overlay click
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') document.getElementById('how-modal').classList.remove('modal-open');
}});
document.getElementById('how-modal').addEventListener('click', e => {{
  if (e.target === document.getElementById('how-modal'))
    document.getElementById('how-modal').classList.remove('modal-open');
}});
</script>
</body>
</html>"""

with open("index.html","w") as f:
    f.write(html)
print(f"Done. {len(events)} events → index.html")
