#!/usr/bin/env python3
"""
density.py — WHERE the supply sits: size & city breakdown per brand.

The brief names "products, brands, **sizes**, occasions, and time periods" as the density
dimensions. Every Pickle listing already carries `size` and `location` at ~100% fill, so this
is free — no new scraping. Answers "which sizes/cities is supply concentrated in?"

    python -m radar.density
"""
import glob, json, os, collections, unicodedata
from datetime import datetime, timezone

from .match import matches_style


def _norm(s):
    # strip accents so "Réalisation" and "Realisation" match (the brand field has both)
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")


def latest(cat):
    fs = glob.glob(os.path.join(DATA, f"pickle_{cat.replace('/', '_')}_*.json"))
    return max(fs, key=os.path.getmtime) if fs else None


def region(loc):
    if not loc:
        return None
    c, st = loc.split(",")[0].strip(), loc.split(",")[-1].strip()
    if st == "NY" or c in ("New York", "Brooklyn", "Queens", "Manhattan"):
        return "NYC metro"
    if st == "NJ" and c in ("Weehawken", "Hoboken", "Jersey City"):
        return "NYC metro"                      # commuter belt
    if st == "CA" or c in ("Los Angeles", "Beverly Hills", "Santa Monica"):
        return "LA / CA"
    return st or "other"


def brand_listings(dress):
    snap = latest(dress["pickle_category"])
    if not snap:
        return []
    key = _norm(dress["brand"].split()[0])          # 'realisation' / 'house' / 'nadine'
    return [x for x in json.load(open(snap))["listings"] if key in _norm(x.get("brand"))]


def summarize(listings, style=None):
    if style:
        listings = [x for x in listings if matches_style(x.get("title"), style)]
    n = len(listings)
    return {
        "n": n,
        "sizes": collections.Counter(x.get("size") for x in listings if x.get("size")),
        "cities": collections.Counter(region(x.get("location")) for x in listings if x.get("location")),
        "rents": sorted(x["rent_usd"] for x in listings if x.get("rent_usd")),
    }


def main():
    dresses = json.load(open(WATCHLIST))["dresses"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = [f"# Supply density — size & city ({stamp})\n",
           "Where the rental supply actually sits. `size` + `location` come from every Pickle "
           "listing (~100% fill), so this needs no extra scraping.\n"]
    for d in dresses:
        L = brand_listings(d)
        if not L:
            continue
        s = summarize(L)
        cities = " · ".join(f"{c} {n / s['n'] * 100:.0f}%" for c, n in s["cities"].most_common(3))
        sizes = " · ".join(f"{sz}×{n}" for sz, n in s["sizes"].most_common(6))
        rent = f"${s['rents'][0]}–${s['rents'][-1]}" if s["rents"] else "n/a"
        out.append(f"## {d['brand']} — {s['n']} listings  ·  rent {rent}")
        out.append(f"- **Cities:** {cities}")
        out.append(f"- **Sizes:** {sizes}\n")
    text = "\n".join(out)
    print("\n" + text + "\n")
    open(os.path.join(DATA, f"density_{stamp}.md"), "w").write(text + "\n")
    print(f"saved -> data/density_{stamp}.md")


if __name__ == "__main__":
    main()
