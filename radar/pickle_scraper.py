#!/usr/bin/env python3
"""
pickle_scraper.py — CORE signal. Scrapes Pickle (shoponpickle.com) rental listings.

Pickle is a Next.js App-Router site: listing data is streamed as RSC (not in JSON-LD
or __NEXT_DATA__), so plain requests can't read it reliably. We render with Playwright
and read each product card. Each listing is one <a href="/product/<uuid>"> whose text is:
  "NEW <title> Size: <size> · <city, ST> Orig. Retail $<retail> Rent $<rent>"

Snapshots are dated so a later run can DIFF them: listings that DISAPPEAR between days
are likely rented/sold (a liquidity/velocity signal).

Setup (one time):
    pip install playwright && playwright install chromium

Run:
    python -m radar.pickle_scraper
    python -m radar.pickle_scraper dresses aritzia/dresses realisation-par/dresses
"""
import json, os, re, sys, time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

BASE = "https://www.shoponpickle.com"
CATEGORY_URL = BASE + "/shop/rent/{category}"
SNAP_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SCROLL_ROUNDS, SCROLL_PAUSE = 6, 1.2   # scroll to lazy-load past the first ~40

PRICE_RETAIL = re.compile(r"Orig\.?\s*Retail\s*\$([\d,]+)")
PRICE_RENT   = re.compile(r"Rent\s*\$([\d,]+)")
SIZE_RE      = re.compile(r"Size:\s*([^·\n]+?)\s*(?:·|Orig|Rent|$)")
LOC_RE       = re.compile(r"·\s*([A-Za-z .]+,\s*[A-Z]{2})")


def to_int(s):
    return int(s.replace(",", "")) if s else None


# Known multi-word brands (longest-prefix wins so "House of CB" beats "House of").
# Extend this from your own snapshot titles — it's meant to grow.
KNOWN_BRANDS = sorted({
    "Réalisation Par", "Realisation Par", "House of CB", "House of Harlow",
    "Rat & Boa", "De La Vali", "Cult Gaia", "Retrofete", "Self-Portrait",
    "For Love & Lemons", "Faithfull the Brand", "Significant Other", "Bec & Bridge",
    "Norma Kamali", "Sabina Musayev", "Taller Marmo", "Arcina Ori", "With Jean",
    "Free People", "Nadine Merabi", "Shona Joy", "The Sei", "Tory Burch",
    "Reformation", "Aritzia", "Sunday Best", "Meshki", "Selkie", "Zimmermann",
    "Staud", "Ganni", "Alemais", "Baobab",
}, key=len, reverse=True)

_STOP = {"dress", "gown", "maxi", "midi", "mini", "skirt", "top", "set",
         "kaftan", "cape", "slip", "jumpsuit", "romper", "the"}

def brand_from_title(title):
    t = re.sub(r"^\s*NEW\s+", "", title or "").strip()
    low = t.lower()
    for b in KNOWN_BRANDS:                       # 1) known brand as a prefix
        if low.startswith(b.lower()):
            return b
    words, out = t.split(), []                   # 2) fallback: words until a product noun
    for w in words:
        if w.lower().strip("-,&") in _STOP:
            break
        out.append(w)
        if len(out) >= 3:
            break
    return " ".join(out) if out else (t or None)




def parse_card(href, title, text):
    text = re.sub(r"\s+", " ", text or "").strip()
    size, loc = SIZE_RE.search(text), LOC_RE.search(text)
    retail, rent = PRICE_RETAIL.search(text), PRICE_RENT.search(text)
    return {
        "uuid": href.rstrip("/").split("/")[-1],
        "url": BASE + href,
        "title": re.sub(r"^\s*NEW\s+", "", title or "").strip(),
        "brand": brand_from_title(title),
        "is_new": text.startswith("NEW"),
        "size": size.group(1).strip() if size else None,
        "location": loc.group(1).strip() if loc else None,
        "retail_usd": to_int(retail.group(1)) if retail else None,
        "rent_usd": to_int(rent.group(1)) if rent else None,
    }


def scrape_category(page, category):
    page.goto(CATEGORY_URL.format(category=category),
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_selector('a[href*="/product/"]', timeout=20000)

    # scroll until the listing count stops growing (exhaust the page), not a fixed count
    prev, stable = 0, 0
    for _ in range(60):                      # generous cap; brand pages are a few hundred
        page.mouse.wheel(0, 25000)
        time.sleep(SCROLL_PAUSE)
        n = page.eval_on_selector_all('a[href*="/product/"]', "els => els.length")
        if n == prev:
            stable += 1
            if stable >= 2:                  # two flat reads in a row = fully loaded
                break
        else:
            stable, prev = 0, n

    raw = page.eval_on_selector_all(
        'a[href*="/product/"]',
        """els => els.map(a => ({
            href: a.getAttribute('href'),
            title: (a.querySelector('img') && a.querySelector('img').getAttribute('alt')) || '',
            text: a.innerText
        }))""")
    seen, listings = set(), []
    for r in raw:
        if r["href"] and r["href"] not in seen:
            seen.add(r["href"])
            listings.append(parse_card(r["href"], r["title"], r["text"]))
    print(f"  {category}: {len(listings)} listings")
    return listings


def save_snapshot(category, listings):
    os.makedirs(SNAP_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(SNAP_DIR, f"pickle_{category.replace('/', '_')}_{stamp}.json")
    with open(path, "w") as f:
        json.dump({"category": category, "scraped_at": stamp,
                   "count": len(listings), "listings": listings}, f, indent=2)
    print(f"  saved -> {os.path.relpath(path)}")


def main():
    categories = sys.argv[1:] or ["dresses"]
    print(f"Scraping Pickle: {categories}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        for cat in categories:
            try:
                save_snapshot(cat, scrape_category(page, cat))
            except Exception as e:
                print(f"  [error] {cat}: {e}")
            time.sleep(2)
        browser.close()


if __name__ == "__main__":
    main()
