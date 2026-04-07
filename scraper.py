"""
Seacoast Improv Scene — scraper.py
Fetches events from all sources and writes events.json
"""

import json, re, sys
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SeacoastImprovBot/1.0)"}
TODAY = date.today()

def fetch_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def parse_date(s):
    s = re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+', '', s.strip(), flags=re.IGNORECASE)
    s = re.sub(r'(st|nd|rd|th)\b', '', s)
    for fmt in ["%B %d, %Y","%b %d, %Y","%B %d","%b %d"]:
        try:
            d = datetime.strptime(s.strip(), fmt)
            if d.year == 1900: d = d.replace(year=TODAY.year)
            return d.date()
        except ValueError: continue
    return None

def find_date_in_text(text):
    m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d+(?:st|nd|rd|th)?,?\s*\d{4}', text, re.IGNORECASE)
    if not m:
        m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d+(?:st|nd|rd|th)?', text, re.IGNORECASE)
    return parse_date(m.group(0)) if m else None

def scrape_essex():
    events = []
    soup = fetch_soup("https://esseximprov.com/classes")
    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if not title or title.lower() == "classes": continue
        h4 = h2.find_next("h4")
        date_str = h4.get_text(strip=True) if h4 else ""
        d = find_date_in_text(date_str)
        link = h2.find_next("a", href=True)
        url = link["href"] if link else "https://esseximprov.com/classes"
        if url.startswith("/"): url = "https://esseximprov.com" + url
        events.append({"title":title,"date":str(d) if d else None,"date_str":date_str,"type":"Class","org":"Essex Improv","location":"Beverly, MA","url":url})
    soup = fetch_soup("https://esseximprov.com/events")
    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if not title or title.lower() == "events": continue
        h4 = h2.find_next("h4")
        date_str = h4.get_text(strip=True) if h4 else ""
        d = find_date_in_text(date_str)
        if d and d < TODAY: continue
        link = h2.find_next("a", href=True)
        url = link["href"] if link else "https://esseximprov.com/events"
        if url.startswith("/"): url = "https://esseximprov.com" + url
        tl = title.lower()
        etype = "Audition" if "audition" in tl else ("Jam" if ("jam" in tl or "jelly" in tl) else ("Workshop" if ("workshop" in tl or "training" in tl) else "Show"))
        events.append({"title":title,"date":str(d) if d else None,"date_str":date_str,"type":etype,"org":"Essex Improv","location":"Off Cabot Comedy & Events, Beverly, MA","url":url})
    return events

def scrape_stf():
    events = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://www.stfimprov.com", wait_until="networkidle", timeout=30000)
        content = page.content()
        browser.close()
    soup = BeautifulSoup(content, "html.parser")
    seen = set()
    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if not title or len(title) < 4 or title in seen: continue
        seen.add(title)
        parent = h2.find_parent()
        full = parent.get_text(" ", strip=True) if parent else ""
        if not re.search(r'\$[\d,]+', full): continue
        m = re.search(r'Started?\s+([A-Za-z]+\s+\d+)', full)
        date_str = f"Started {m.group(1)}" if m else "See website"
        link = h2.find_next("a", href=True)
        url = link["href"] if link else "https://www.stfimprov.com"
        if url.startswith("/"): url = "https://www.stfimprov.com" + url
        events.append({"title":title,"date":None,"date_str":date_str,"type":"Class","org":"Stranger Than Fiction Improv","location":"Portsmouth, NH","url":url})
    return events

def scrape_qci():
    events = []
    soup = fetch_soup("https://www.queencityimprov.com")
    seen = set()
    for li in soup.select("li"):
        link = li.select_one("a[href*='/events/']")
        if not link: continue
        title = link.get_text(strip=True)
        if not title or title in seen: continue
        seen.add(title)
        full = li.get_text(" ", strip=True)
        m = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+', full, re.IGNORECASE)
        d, date_str = None, ""
        if m:
            date_str = m.group(0)
            d = parse_date(re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+','',date_str,flags=re.IGNORECASE))
        if d and d < TODAY: continue
        url = link["href"]
        if url.startswith("/"): url = "https://www.queencityimprov.com" + url
        tl = title.lower()
        etype = "Jam" if ("open session" in tl or "jam" in tl) else ("Workshop" if any(w in tl for w in ["workshop","reps","get out","get your"]) else ("Class" if any(w in tl for w in ["class","kidprov","teen"]) else "Show"))
        events.append({"title":title,"date":str(d) if d else None,"date_str":date_str or "See website","type":etype,"org":"Queen City Improv","location":"Manchester, NH","url":url})
    return events

def scrape_yesandco():
    events = []
    soup = fetch_soup("https://www.yesandcoimprov.com/upcoming-shows")
    for h3 in soup.select("h3"):
        title = h3.get_text(strip=True)
        if not title or "click here" in title.lower(): continue
        parent = h3.find_parent()
        full = parent.get_text(" ", strip=True) if parent else ""
        d = find_date_in_text(full)
        if d and d < TODAY: continue
        link = h3.find_next("a", href=True)
        url = link["href"] if link else "https://www.yesandcoimprov.com/upcoming-shows"
        events.append({"title":title,"date":str(d) if d else None,"date_str":d.strftime("%a, %b %-d @ 7pm") if d else "See website","type":"Show","org":"YES&Co.","location":"Portland Media Center, Portland, ME","url":url})
    return events

def scrape_incubator():
    events = []
    soup = fetch_soup("https://www.meetup.com/seacoast-improv-incubator/")
    seen_dates = set()
    for item in soup.select("a[href*='/events/']"):
        title = item.get_text(strip=True)
        if "Wednesday Night Incubator" not in title: continue
        parent = item.find_parent()
        full = parent.get_text(" ", strip=True) if parent else ""
        m = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+', full, re.IGNORECASE)
        if not m: continue
        d = parse_date(re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+','',m.group(0),flags=re.IGNORECASE))
        if not d or d < TODAY or str(d) in seen_dates: continue
        seen_dates.add(str(d))
        url = item["href"] if item.get("href","").startswith("http") else "https://www.meetup.com" + item.get("href","")
        events.append({"title":"Wednesday Night Incubator","date":str(d),"date_str":"Wed @ 7pm · $5 suggested","type":"Jam","org":"Seacoast Improv Incubator","location":"South Church UU, Portsmouth, NH","url":url})
    if not events:
        events.append({"title":"Wednesday Night Incubator","date":None,"date_str":"Every Wednesday @ 7pm · $5 suggested","type":"Jam","org":"Seacoast Improv Incubator","location":"South Church UU, Portsmouth, NH","url":"https://www.meetup.com/seacoast-improv-incubator/"})
    return events

def scrape_mist():
    events = []
    try:
        soup = fetch_soup("https://www.maineimprovstudio.com/classes")
    except Exception:
        soup = fetch_soup("https://www.maineimprovstudio.com")
    seen = set()
    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if not title or title in seen or len(title) < 4: continue
        seen.add(title)
        link = h2.find_next("a", href=True)
        url = link["href"] if link else "https://www.maineimprovstudio.com/classes"
        if url.startswith("/"): url = "https://www.maineimprovstudio.com" + url
        etype = "Workshop" if "workshop" in title.lower() else "Class"
        events.append({"title":title,"date":None,"date_str":"See website for schedule","type":etype,"org":"Maine Improv Studio","location":"Portland Media Center, Portland, ME","url":url})
    return events

if __name__ == "__main__":
    sources = [
        ("Essex Improv",              scrape_essex),
        ("Stranger Than Fiction",     scrape_stf),
        ("Queen City Improv",         scrape_qci),
        ("YES&Co.",                   scrape_yesandco),
        ("Seacoast Improv Incubator", scrape_incubator),
        ("Maine Improv Studio",       scrape_mist),
    ]
    all_events = []
    for name, fn in sources:
        print(f"Scraping {name}...", end=" ", flush=True)
        try:
            results = fn()
            print(f"{len(results)} events")
            all_events.extend(results)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)

    dated   = sorted([e for e in all_events if e["date"]], key=lambda x: x["date"])
    undated = [e for e in all_events if not e["date"]]
    all_events = dated + undated

    with open("events.json", "w") as f:
        json.dump(all_events, f, indent=2)
    print(f"\nTotal: {len(all_events)} events → events.json")
