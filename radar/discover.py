#!/usr/bin/env python3
"""
discover.py — INVERSE SEARCH (TikTok → Product). The discovery engine.

Instead of checking a known watchlist, this finds what's trending in the first
place: scrape trending fashion hashtags, detect brand/product mentions in the
captions, and rank emerging candidates by engagement + recency. New candidates
that aren't already on the watchlist are flagged — that's how TRACE gets alerted
when *any* dress starts blowing up (a celeb wears it, a creator's post pops).

Pipeline:
    trending hashtags (Apify TikTok)
      -> extract (brand, product-phrase) from each caption   [regex + brand list; swap in an LLM/NER to improve]
      -> aggregate by brand: engagement, #posts, recency, top post
      -> rank; flag candidates NOT already tracked
      -> (next step) auto-resolve via ShopMy + check Pickle supply

Run:
    python -m radar.discover
    python -m radar.discover fashionhaul grwm weddingguestdress

NOTE: caption-based product extraction is heuristic — an LLM (Claude/GPT) or a
fine-tuned NER would resolve the exact SKU far better. This PoC shows the shape.
"""
import json, os, re, sys, statistics
from datetime import datetime, timezone

from dotenv import load_dotenv
from apify_client import ApifyClient

from .match import matches_style

load_dotenv()
HERE = os.path.dirname(__file__)
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")
SNAP_DIR = os.path.join(HERE, "..", "data")
ACTOR = "clockworks/tiktok-scraper"
RESULTS_PER_HASHTAG = 40
TOKEN = os.getenv("APIFY_TOKEN")

DEFAULT_HASHTAGS = ["fashionhaul", "grwm", "weddingguestdress", "dresshaul", "outfitinspo"]

# Fashion brands to detect in captions. Extend freely — or replace with an LLM/NER pass.
BRANDS = [
    "Réalisation Par", "Realisation Par", "House of CB", "Aritzia", "Sunday Best",
    "Reformation", "Cult Gaia", "Retrofete", "Zimmermann", "Meshki", "Rat & Boa",
    "Free People", "With Jean", "Selkie", "For Love & Lemons", "Nadine Merabi",
    "Self-Portrait", "Staud", "Ganni", "De La Vali", "Sandy Liang", "Revolve",
    "Sabina Musayev", "Shona Joy", "Bec & Bridge", "Norma Kamali", "Alemais",
]
_TYPE = r"(?:dress|gown|maxi|midi|mini|slip|set|skirt|jumpsuit)"


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
    raise RuntimeError("no dataset id")


def extract_products(text):
    """Best-effort (brand, product-phrase) pairs from a caption. Heuristic, not an LLM."""
    hits = []
    low = text.lower()
    for b in BRANDS:
        i = low.find(b.lower())
        if i == -1:
            continue
        # grab the phrase around the brand up to a product-type word, e.g. "the Cora dress"
        window = text[max(0, i - 25): i + len(b) + 40]
        m = re.search(rf"([A-Z][A-Za-z]+(?:\s+[A-Za-z]+){{0,3}}\s+{_TYPE})", window, re.I)
        product = m.group(1).strip() if m else None
        hits.append((b, product))
    return hits


def main():
    if not TOKEN:
        raise SystemExit("Set APIFY_TOKEN in .env.")
    hashtags = sys.argv[1:] or DEFAULT_HASHTAGS
    tracked = {d["brand"].lower() for d in json.load(open(WATCHLIST))["dresses"]}
    client = ApifyClient(TOKEN)

    print(f"Inverse search over #{hashtags} ...")
    run = client.actor(ACTOR).call(run_input={
        "hashtags": hashtags, "resultsPerPage": RESULTS_PER_HASHTAG,
        "shouldDownloadVideos": False, "shouldDownloadCovers": False,
    })
    posts = list(client.dataset(_dataset_id(run)).iterate_items())
    print(f"  {len(posts)} posts scraped")

    agg = {}            # brand -> stats
    creators_seen = {}  # author -> best views (creators posting about a detected brand)
    for p in posts:
        text = p.get("text") or ""
        views = _num(p.get("playCount"))
        hits = extract_products(text)
        author = (p.get("authorMeta") or {}).get("name")
        if hits and author:
            creators_seen[author] = max(creators_seen.get(author, 0), views)
        for brand, product in hits:
            a = agg.setdefault(brand, {"brand": brand, "posts": 0, "views": 0,
                                       "saves": 0, "products": {}, "example": None, "top_views": -1})
            a["posts"] += 1
            a["views"] += views
            a["saves"] += _num(p.get("collectCount"))
            if product:
                a["products"][product] = a["products"].get(product, 0) + 1
            if views > a["top_views"]:
                a["top_views"] = views
                a["example"] = p.get("webVideoUrl")

    ranked = sorted(agg.values(), key=lambda a: a["views"], reverse=True)
    for a in ranked:
        a["is_new"] = a["brand"].lower() not in tracked
        a["top_products"] = sorted(a["products"].items(), key=lambda x: -x[1])[:3]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    os.makedirs(SNAP_DIR, exist_ok=True)
    # creators the radar just found — handed off to ShopMy (closes the loop)
    discovered_creators = [a for a, _ in sorted(creators_seen.items(), key=lambda x: -x[1])][:15]
    json.dump({"scraped_at": stamp, "hashtags": hashtags, "candidates": ranked,
               "discovered_creators": discovered_creators},
              open(os.path.join(SNAP_DIR, f"discover_{stamp}.json"), "w"), indent=2)
    print(f"saved -> data/discover_{stamp}.json")
    print(f"  discovered creators (feed to ShopMy via --from-discover): {discovered_creators[:8]}\n")

    print("=== emerging brand candidates (by engagement) ===")
    print(f"{'brand':<22}{'posts':>6}{'views':>12}   top product / status")
    for a in ranked[:12]:
        prod = a["top_products"][0][0] if a["top_products"] else "—"
        flag = "🆕 NEW" if a["is_new"] else "(tracked)"
        print(f"{a['brand'][:21]:<22}{a['posts']:>6}{a['views']:>12,}   {prod[:30]:<30} {flag}")


if __name__ == "__main__":
    main()
