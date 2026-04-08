import json, urllib.parse
from datetime import date

with open("events.json") as f:
    raw = json.load(f)

mist = [
  {"title":"Storytelling w/ Micaela Blei","date":None,"date_str":"Sundays 5–7pm, spring session","type":"Class","org":"Maine Improv Studio","location":"Portland Media Center, Portland, ME","url":"https://crowdwork.com/e/storytelling-w-micaela-blei-sundays-5-7pm"},
  {"title":"Level 1: Scenework","date":None,"date_str":"Thursdays 7–9pm, spring session","type":"Class","org":"Maine Improv Studio","location":"Portland Media Center, Portland, ME","url":"https://crowdwork.com/e/mist-level-1-scenework-thursdays-spring-7-9pm-no-class-march-26th"},
  {"title":"Level 2: Groupwork","date":None,"date_str":"Tuesdays 6–8pm, spring session","type":"Class","org":"Maine Improv Studio","location":"Portland Media Center, Portland, ME","url":"https://crowdwork.com/e/mist-level-2-groupwork-tuesdays-spring-6-8pm-no-class-march-31st"},
]

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

events = list(raw) + mist
def sort_key(e): return (0, e["date"]) if e["date"] else (1, "9999")
events.sort(key=sort_key)
today = date.today()

TYPE_META = {
    "Show":      ("#FFD700","#111","Show"),
    "Jam":       ("#00A878","#fff","Jam"),
    "Workshop":  ("#0055BF","#fff","Workshop"),
    "Class":     ("#FF6B00","#fff","Class"),
    "Audition":  ("#E8001C","#fff","Audition"),
    "Incubator": ("#9B2DE8","#fff","Incubator"),
}
INCUBATOR_ORGS = {"Seacoast Improv Incubator","Portland Maine Improv Incubator"}
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

def is_past(d_str):
    # Only applies to undated (ongoing) classes — if they have no date they may have started
    return False  # Dated events already filtered; ongoing = already started

def is_ongoing_started(e):
    # Cards with no date and type Class or Workshop are ongoing/already started
    return e["date"] is None and e["type"] in ("Class", "Workshop")

def map_url(loc):
    q = MAP.get(loc, loc)
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)

def card(e):
    is_incubator = e["org"] in INCUBATOR_ORGS
    etype = "Incubator" if is_incubator else e["type"]
    bg, fg, label = TYPE_META.get(etype, ("#333","#fff",etype))
    dow, mon, day = fmt_date(e["date"])
    soon = is_soon(e["date"])
    started = is_ongoing_started(e)

    if dow:
        date_html = f'<div class="cd"><div class="cd-dow">{dow}</div><div class="cd-mon">{mon}</div><div class="cd-day">{day}</div></div>'
    else:
        date_html = '<div class="cd ongoing"><span>ON<br>GOING</span></div>'

    soon_badge = '<div class="badges"><span class="badge-soon">This Week</span></div>' if soon else ""
    started_note = '<div class="badges"><span class="badge-started">In Progress</span></div>' if started else ""
    murl = map_url(e["location"])
    started_class = " card-started" if started else ""

    # Card is a div, not an anchor — click handled via JS data attribute
    return f'''<div class="card{started_class}" data-href="{e["url"]}" data-type="{etype}" data-org="{e["org"]}" role="link" tabindex="0">
  <div class="card-left" style="background:{bg};color:{fg}">{date_html}<div class="card-lbl">{label}</div></div>
  <div class="card-body">
    <p class="card-title">{e["title"]}</p>
    <p class="card-org">{e["org"]}</p>
    <p class="card-loc"><a class="map-link" href="{murl}" target="_blank" rel="noopener">{e["location"]} <span class="map-arr">↗</span></a></p>
    <p class="card-when">{e["date_str"]}</p>
    {soon_badge}{started_note}
  </div>
  <div class="card-go">→</div>
</div>'''

cards_html = "\n".join(card(e) for e in events)
last_updated = today.strftime("%B %-d, %Y")

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

/* HEADER */
header{{border-bottom:4px solid var(--black);position:relative;overflow:hidden;background:var(--bg)}}
.h-inner{{max-width:960px;margin:0 auto;padding:2.5rem 2rem 2rem;position:relative;z-index:1}}
.h-deco{{position:absolute;top:0;right:0;height:100%;width:200px;display:flex;flex-direction:column;border-left:4px solid var(--black);overflow:hidden}}
.d-r{{flex:2;background:var(--red);border-bottom:4px solid var(--black)}}
.d-b{{flex:3;background:var(--blue);border-bottom:4px solid var(--black);display:flex}}
.d-b1{{flex:1;border-right:4px solid var(--black)}}
.d-b2{{flex:2}}
.d-y{{flex:1;background:var(--yellow);border-bottom:4px solid var(--black)}}
.d-p{{flex:1.5;background:var(--purple)}}
.eyebrow{{font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;color:#666;margin-bottom:.6rem}}
h1{{font-family:'Bangers',cursive;font-size:clamp(3rem,9vw,5.5rem);letter-spacing:.04em;line-height:.92;color:var(--red)}}
.h-sub{{margin-top:.8rem;font-size:.88rem;color:#555;max-width:500px}}

/* FILTER BAR */
.filter-bar{{max-width:960px;margin:0 auto;padding:.85rem 2rem;display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;border-bottom:3px solid var(--black)}}
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
.fbtn.active[data-filter="Show"]{{background:var(--yellow);color:#111;border-left-color:var(--black)}}
.fbtn.active[data-filter="Jam"]{{background:var(--green);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Workshop"]{{background:var(--blue);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Class"]{{background:var(--orange);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Audition"]{{background:var(--red);color:#fff;border-left-color:var(--black)}}
.fbtn.active[data-filter="Incubator"]{{background:var(--purple);color:#fff;border-left-color:var(--black)}}

/* LISTINGS */
.listings{{max-width:960px;margin:0 auto;padding:1.5rem 2rem 4rem;display:flex;flex-direction:column}}

/* CARD — div, not anchor */
.card{{
  display:flex;
  align-items:stretch;
  border:3px solid var(--black);
  margin-bottom:-3px;
  cursor:pointer;
  color:var(--black);
  background:var(--bg);
  position:relative;
  z-index:0;
  transition:transform .08s;
  text-decoration:none;
}}
.card:hover{{transform:translate(-3px,-3px);box-shadow:6px 6px 0 var(--black);z-index:10}}
.card:focus-visible{{outline:3px solid var(--blue);outline-offset:2px}}

/* Grayed-out state for in-progress classes */
.card-started{{opacity:.55;filter:saturate(.4)}}
.card-started:hover{{opacity:.75;filter:saturate(.6)}}

.card-left{{
  width:72px;min-width:72px;flex-shrink:0;
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  padding:.6rem .3rem;
  border-right:3px solid var(--black);
  gap:.05rem;
}}
.cd{{text-align:center;font-family:'Bangers',cursive;line-height:1}}
.cd-dow{{font-size:.6rem;letter-spacing:.12em;opacity:.8;margin-bottom:.1rem}}
.cd-mon{{font-size:.75rem;letter-spacing:.08em}}
.cd-day{{font-size:1.85rem;line-height:1}}
.cd.ongoing span{{font-family:'DM Sans',sans-serif;font-size:.5rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;line-height:1.3;opacity:.75}}
.card-lbl{{font-size:.44rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;opacity:.65;margin-top:.25rem;font-family:'DM Sans',sans-serif}}

.card-body{{
  flex:1;min-width:0;
  padding:.7rem 1rem;
  display:flex;flex-direction:column;
  justify-content:center;gap:.12rem;
}}
.card-title{{font-family:'Bangers',cursive;font-size:1.2rem;letter-spacing:.04em;line-height:1.1;color:var(--black);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-org{{font-size:.75rem;font-weight:500;color:#333}}
.card-loc{{font-size:.7rem}}
.map-link{{color:#555;text-decoration:none;display:inline-flex;align-items:center;gap:.2rem}}
.map-link:hover{{color:var(--blue);text-decoration:underline}}
.map-arr{{font-size:.6rem;opacity:.55}}
.card-when{{font-size:.67rem;color:#999}}
.badges{{margin-top:.25rem;display:flex;gap:.3rem;flex-wrap:wrap}}
.badge-soon{{display:inline-block;font-size:.55rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;background:var(--red);color:#fff;padding:.1rem .38rem;border:1.5px solid var(--black)}}
.badge-started{{display:inline-block;font-size:.55rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;background:#aaa;color:#fff;padding:.1rem .38rem;border:1.5px solid #888}}

.card-go{{display:flex;align-items:center;padding:0 .9rem;font-size:1rem;color:#ccc;border-left:2px solid #ddd;flex-shrink:0;transition:color .1s}}
.card:hover .card-go{{color:var(--black);border-left-color:var(--black)}}

footer{{border-top:4px solid var(--black);max-width:960px;margin:0 auto;padding:1.2rem 2rem;font-size:.68rem;color:#888;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.4rem}}

.hidden{{display:none!important}}

@media(max-width:640px){{
  .h-deco{{width:80px}}
  .d-b1,.d-b2{{display:none}}
  .h-inner,.filter-bar,.listings,footer{{padding-left:1rem;padding-right:1rem}}
  h1{{font-size:2.8rem}}
  .card-go{{display:none}}
  .f-div{{display:none}}
}}
</style>
</head>
<body>

<header>
  <div class="h-deco" aria-hidden="true">
    <div class="d-r"></div>
    <div class="d-b"><div class="d-b1"></div><div class="d-b2"></div></div>
    <div class="d-y"></div>
    <div class="d-p"></div>
  </div>
  <div class="h-inner">
    <div class="eyebrow">Portland ME · Portsmouth NH · Manchester NH · Beverly MA</div>
    <h1>SEACOAST<br>IMPROV<br>SCENE</h1>
    <p class="h-sub">Classes, shows, jams &amp; auditions across the region — all in one place.</p>
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
  <button class="fbtn" data-filter="Incubator">Incubator</button>
  <div class="f-div"></div>
  <button class="fbtn" data-filter="Essex Improv">Essex Improv</button>
  <button class="fbtn" data-filter="Stranger Than Fiction Improv">Stranger Than Fiction</button>
  <button class="fbtn" data-filter="Queen City Improv">Queen City Improv</button>
  <button class="fbtn" data-filter="YES&amp;Co.">YES&amp;Co.</button>
  <button class="fbtn" data-filter="Maine Improv Studio">Maine Improv Studio</button>
  <button class="fbtn" data-filter="Seacoast Improv Incubator">Seacoast Incubator</button>
</div>

<main class="listings">
{cards_html}
</main>

<footer>
  <span>Updated {last_updated} · Sources: esseximprov.com · stfimprov.com · queencityimprov.com · yesandcoimprov.com · maineimprovstudio.com · meetup.com/seacoast-improv-incubator</span>
  <span>Not affiliated with any organization listed.</span>
</footer>

<script>
// Card click — open event URL, but not when clicking the map link
document.querySelectorAll('.card').forEach(card => {{
  card.addEventListener('click', e => {{
    if (e.target.closest('.map-link')) return;
    window.open(card.dataset.href, '_blank', 'noopener');
  }});
  card.addEventListener('keydown', e => {{
    if (e.key === 'Enter' || e.key === ' ') window.open(card.dataset.href, '_blank', 'noopener');
  }});
}});

// Filter buttons
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
      if (f === 'Incubator') show = type === 'Incubator';
      card.classList.toggle('hidden', !show);
    }});
  }});
}});
</script>
</body>
</html>"""

with open("index.html","w") as f:
    f.write(html)
print(f"Done. {len(events)} events.")
