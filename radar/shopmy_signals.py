#!/usr/bin/env python3
"""
shopmy_signals.py — BUY-INTENT layer (the third platform).

ShopMy is creator-keyed: you scrape creators, then see which products they link
to a retailer, with click counts. So this reads a list of fashion creators'
RECENT picks (tab="latest") via Apify, then measures, per tracked dress:
  • exact-style hits  — picks whose title mentions the style ("cora"/"merabi"/"sculpt")
  • brand hits        — picks on that brand's retailer (merchant_name)
  • clicks + promoters — buy-intent (num_promoters = how many creators link that
                          product across ALL of ShopMy = catalog-wide breadth)
Plus a brand-level buy-intent leaderboard across everything scraped.

Setup:
    pip install apify-client python-dotenv   # already installed
    # APIFY_TOKEN in .env

Run:
    python -m radar.shopmy_signals
"""
import json, os, sys, glob, collections
from datetime import datetime, timezone

from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()
HERE = os.path.dirname(__file__)
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")
SNAP_DIR = os.path.join(HERE, "..", "data")
ACTOR = "getascraper/shopmy-creator-scraper"
TAB = "latest"          # "latest" catches CURRENT picks; "popular" is all-time (beauty-heavy)
MAX_PER_CREATOR = 40
TOKEN = os.getenv("APIFY_TOKEN")


def _num(v):
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _dataset_id(run):
    if isinstance(run, dict):
        return run.get("defaultDatasetId") or run.get("default_dataset_id")
    for a in ("default_dataset_id", "defaultDatasetId"):
        if (v := getattr(run, a, None)):
            return v
    raise RuntimeError(f"can't get dataset id from {type(run).__name__}")


def normalize(p):
    return {
        "creator": p.get("creator_username"),
        "brand": (p.get("brand") or ""),
        "merchant": (p.get("merchant_name") or "").lower(),
        "title": (p.get("product_title") or ""),
        "price": p.get("price"),
        "total_clicks": _num(p.get("total_clicks")),
        "weekly_clicks": _num(p.get("weekly_clicks")),
        "monthly_clicks": _num(p.get("monthly_clicks")),
        "promoters": _num(p.get("num_promoters")),   # catalog-wide breadth
        "url": p.get("product_url") or p.get("affiliate_url"),
    }


def summarize(picks):
    if not picks:
        return {"n_picks": 0, "n_products": 0, "n_creators": 0, "total_clicks": 0,
                "monthly_clicks": 0, "max_promoters": 0, "example": None}
    # A pick's clicks are a per-PRODUCT lifetime figure, NOT per-creator — so when two
    # creators pin the same product, summing over picks double-counts. Dedupe by product first.
    uniq = {}
    for p in picks:
        uniq[p.get("url") or p["title"].lower()] = p
    prods = list(uniq.values())
    return {
        "n_picks": len(picks),
        "n_products": len(prods),
        "n_creators": len({p["creator"] for p in picks if p["creator"]}),
        "total_clicks": sum(p["total_clicks"] for p in prods),
        "monthly_clicks": sum(p["monthly_clicks"] for p in prods),
        "max_promoters": max(p["promoters"] for p in picks),      # widest catalog breadth
        "example": next((p["url"] for p in picks if p["url"]), None),
    }


def main():
    if not TOKEN:
        raise SystemExit("Set APIFY_TOKEN in .env.")
    cfg = json.load(open(WATCHLIST))
    dresses, creators = cfg["dresses"], cfg.get("shopmy_creators", [])
    if "--from-discover" in sys.argv:   # dynamic creators from the latest discover run — closes the loop
        files = sorted(glob.glob(os.path.join(SNAP_DIR, "discover_*.json")), key=os.path.getmtime)
        if files:
            extra = json.load(open(files[-1])).get("discovered_creators", [])
            creators = list(dict.fromkeys(creators + extra))
            print(f"  + merged {len(extra)} TikTok-discovered creators (loop closed)")
    if not creators:
        raise SystemExit("Add a 'shopmy_creators' list to config/watchlist.json first.")

    client = ApifyClient(TOKEN)
    print(f"ShopMy: scraping {len(creators)} creators ({TAB})...")
    run = client.actor(ACTOR).call(run_input={
        "creators": creators, "tab": TAB, "maxItems": MAX_PER_CREATOR,
        "proxyConfiguration": {"useApifyProxy": True},
    })
    picks = [normalize(p) for p in client.dataset(_dataset_id(run)).iterate_items()]
    got_creators = {p["creator"] for p in picks if p["creator"]}
    print(f"  {len(picks)} picks from {len(got_creators)} resolving creators: {sorted(got_creators)}")

    results = {}
    for d in dresses:
        term = (d.get("match") or "").lower()
        merchants = [m.lower() for m in d.get("shopmy_merchant", [])]
        style = [p for p in picks if term and term in p["title"].lower()]
        brand = [p for p in picks if any(m in p["merchant"] or m in p["brand"].lower() for m in merchants)]
        results[d["id"]] = {"name": d["name"], "style": summarize(style), "brand": summarize(brand),
                            "style_picks": style, "brand_picks": brand}   # persist both so summaries are re-derivable
        s, b = results[d["id"]]["style"], results[d["id"]]["brand"]
        print(f"  {d['name']}: exact-style {s['n_picks']} picks / {s['total_clicks']:,} clicks "
              f"(max {s['max_promoters']} promoters) | brand {b['n_picks']} picks / {b['total_clicks']:,} clicks")

    # brand-level buy-intent leaderboard across everything scraped
    board = collections.Counter()
    for p in picks:
        if p["merchant"]:
            board[p["merchant"]] += p["total_clicks"]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    os.makedirs(SNAP_DIR, exist_ok=True)
    json.dump({"scraped_at": stamp, "results": results,
               "brand_leaderboard": board.most_common(20)},
              open(os.path.join(SNAP_DIR, f"shopmy_{stamp}.json"), "w"), indent=2)
    print(f"\nsaved -> data/shopmy_{stamp}.json")

    print("\n=== ShopMy buy-intent (your dresses) ===")
    for r in results.values():
        print(f"  {r['name'][:34]:<35} exact clicks {r['style']['total_clicks']:>8,} | "
              f"brand clicks {r['brand']['total_clicks']:>8,} ({r['brand']['n_creators']} creators)")
    print("\n=== top merchants by clicks (buy-intent leaderboard) ===")
    for m, c in board.most_common(10):
        print(f"  {c:>10,}  {m}")


if __name__ == "__main__":
    main()
