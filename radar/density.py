#!/usr/bin/env python3
"""
density.py — WHERE the supply sits: size & city breakdown per brand + SKU.

The brief names "products, brands, **sizes**, occasions, and time periods" as the density
dimensions. Every Pickle listing already carries `size` and `location` at ~100% fill, so this
is free — no new scraping.

Two things it surfaces: (1) size/city concentration, and (2) that Pickle's "brand" pages are
contaminated — the Nadine Merabi page is only ~38% Nadine Merabi — so the honest supply
denominator is the brand-filtered count (via match.brand_filter), not the raw page count.

    python -m radar.density
"""
import glob, json, os, re, collections
from datetime import datetime, timezone

from .match import matches_style, brand_filter

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")


def _date(path):
    # parse the date from the FILENAME (mtime is unreliable — identical after a CI checkout)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    return m.group(1) if m else "0000-00-00"


def latest(cat):
    fs = glob.glob(os.path.join(DATA, f"pickle_{cat.replace('/', '_')}_*.json"))
    return max(fs, key=_date) if fs else None


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


def _fmt(s):
    cities = " · ".join(f"{c} {n / s['n'] * 100:.0f}%" for c, n in s["cities"].most_common(3))
    sizes = " · ".join(f"{sz}×{n}" for sz, n in s["sizes"].most_common(6))
    rent = f"${s['rents'][0]}–${s['rents'][-1]}" if s["rents"] else "n/a"
    return cities, sizes, rent


def main():
    dresses = json.load(open(WATCHLIST))["dresses"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = [f"# Supply density — size & city ({stamp})\n",
           "`size` + `location` come from every Pickle listing (~100% fill), so this needs no extra "
           "scraping. Counts are **brand-filtered** — Pickle's brand pages mix in other labels.\n"]
    for d in dresses:
        snap = latest(d["pickle_category"])
        if not snap:
            continue
        page = json.load(open(snap))["listings"]
        L = brand_filter(page, d["brand"])
        if not L:
            continue
        pct = len(L) / len(page) * 100
        cities, sizes, rent = _fmt(summarize(L))
        out.append(f"## {d['brand']} — {len(L)} listings "
                   f"({pct:.0f}% of the {len(page)}-item page — the rest are other labels) · rent {rent}")
        out.append(f"- **Cities:** {cities}")
        out.append(f"- **Sizes:** {sizes}")
        sku = summarize(L, style=d.get("match"))            # SKU-level (e.g. the Nina Gold)
        if 0 < sku["n"] < len(L):
            sc, ss, sr = _fmt(sku)
            out.append(f"- **'{d['match']}' SKU:** {sku['n']} copies · sizes {ss} · {sc} · rent {sr}")
        out.append("")
    text = "\n".join(out)
    print("\n" + text + "\n")
    open(os.path.join(DATA, f"density_{stamp}.md"), "w").write(text + "\n")
    print(f"saved -> data/density_{stamp}.md")


if __name__ == "__main__":
    main()
