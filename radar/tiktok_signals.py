#!/usr/bin/env python3
"""
tiktok_signals.py — DEMAND / momentum layer.

Pulls recent TikTok posts per dress via an Apify actor (clockworks/tiktok-scraper),
using HASHTAGS (keyword `searchQueries` is currently under maintenance / returns 0).
For each dress we scrape its brand + product hashtags, then split results into:
  • brand heat   — everything under those hashtags (context)
  • this dress   — posts that mention the BRAND (brand-anchored). Style words alone are
                   homonym-ridden ("sculpt"=Pilates, "cora"=a person/cat), so requiring the
                   brand is what isolates the dress. See brand_terms in the watchlist.
Aggregates views, saves ("in the bag"), creators, and recency (momentum proxy).

Setup:
    pip install apify-client python-dotenv
    # add APIFY_TOKEN=apify_api_xxx to .env  (apify.com -> Settings -> API & Integrations)

Run:
    python -m radar.tiktok_signals
"""
import json, os, statistics
from datetime import datetime, timezone

from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()
HERE = os.path.dirname(__file__)
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")
SNAP_DIR = os.path.join(HERE, "..", "data")
ACTOR = "clockworks/tiktok-scraper"
RESULTS_PER_HASHTAG = 20        # each result ≈ $0.0037; keep modest to save credit
TOKEN = os.getenv("APIFY_TOKEN")


def _num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def days_since(created):
    if not created:
        return None
    try:
        if str(created).isdigit():
            dt = datetime.fromtimestamp(int(created), tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
    except Exception:
        return None


def normalize(item):
    author = item.get("authorMeta") or {}
    tags = [h.get("name") for h in (item.get("hashtags") or []) if isinstance(h, dict)]
    return {
        "id": item.get("id"),
        "url": item.get("webVideoUrl"),
        "views": _num(item.get("playCount")),
        "likes": _num(item.get("diggCount")),
        "comments": _num(item.get("commentCount")),
        "shares": _num(item.get("shareCount")),
        "saves": _num(item.get("collectCount")),     # "in the bag" / bookmark proxy
        "created": item.get("createTimeISO") or item.get("createTime"),
        "author": author.get("name") or author.get("nickName"),
        "author_fans": _num(author.get("fans")),
        "text": (item.get("text") or ""),
        "hashtags": tags,
    }


def aggregate(posts):
    if not posts:
        return {"n_posts": 0, "n_creators": 0, "total_views": 0, "total_saves": 0}
    views = [p["views"] for p in posts]
    ages = [d for p in posts if (d := days_since(p["created"])) is not None]
    recent = sum(1 for a in ages if a <= 14)
    return {
        "n_posts": len(posts),
        "n_creators": len({p["author"] for p in posts if p["author"]}),
        "total_views": sum(views),
        "median_views": int(statistics.median(views)) if views else 0,
        "total_likes": sum(p["likes"] for p in posts),
        "total_saves": sum(p["saves"] for p in posts),
        "total_shares": sum(p["shares"] for p in posts),
        "newest_days_ago": round(min(ages), 1) if ages else None,
        "share_recent_14d": round(recent / len(posts), 2) if posts else 0,  # momentum proxy
    }


def top_creators(posts, k=3):
    best = {}
    for p in posts:
        a = p.get("author")
        if a and (a not in best or p["views"] > best[a]["views"]):
            best[a] = {"author": a, "views": p["views"], "fans": p["author_fans"], "url": p["url"]}
    return sorted(best.values(), key=lambda x: x["views"], reverse=True)[:k]


def _dataset_id(run):
    """apify-client's .call() returns a dict (older) or a Run object (newer);
    pull the default dataset id either way."""
    if isinstance(run, dict):
        return run.get("defaultDatasetId") or run.get("default_dataset_id")
    for attr in ("default_dataset_id", "defaultDatasetId"):
        if (v := getattr(run, attr, None)):
            return v
    for m in ("model_dump", "to_dict"):
        if callable(fn := getattr(run, m, None)):
            d = fn() or {}
            return d.get("defaultDatasetId") or d.get("default_dataset_id")
    raise RuntimeError(f"can't get dataset id from {type(run).__name__}")


def fetch(client, hashtags):
    run = client.actor(ACTOR).call(run_input={
        "hashtags": hashtags,
        "resultsPerPage": RESULTS_PER_HASHTAG,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    })
    return list(client.dataset(_dataset_id(run)).iterate_items())


def main():
    if not TOKEN:
        raise SystemExit("Set APIFY_TOKEN in .env "
                         "(free at apify.com -> Settings -> API & Integrations).")
    watch = json.load(open(WATCHLIST))["dresses"]
    client = ApifyClient(TOKEN)

    results = {}
    for d in watch:
        tags = d.get("tiktok_hashtags", [])
        term = (d.get("match") or "").lower()
        print(f"TikTok: {d['name']}  #{tags}")
        try:
            raw = fetch(client, tags)
        except Exception as e:
            print(f"  [error] {e}")
            raw = []
        # dedupe by video id
        posts, seen = [], set()
        for it in raw:
            p = normalize(it)
            if p["id"] and p["id"] not in seen:
                seen.add(p["id"])
                posts.append(p)
        # "this dress" = posts that mention the BRAND (brand-anchored). Style words alone are
        # homonym-ridden — "sculpt" is Pilates, "cora" is a person/a cat/prison slang — so a bare
        # `term in text` count is contaminated. Requiring the brand is what actually isolates the
        # dress (verified: it drops Sculpt's #thesculpt Pilates posts from 20 to 0).
        brand_terms = [t.lower() for t in d.get("brand_terms", [])] or [term]
        def _brand_hit(p):
            blob = ((p.get("text") or "") + " " + " ".join(p.get("hashtags") or [])).lower()
            return any(bt in blob for bt in brand_terms)
        mention = [p for p in posts if _brand_hit(p)]
        results[d["id"]] = {
            "name": d["name"], "brand": d["brand"],
            "brand_heat": aggregate(posts),           # context: all posts under the tags
            "this_dress": aggregate(mention),         # precise: posts mentioning the dress
            "top_creators": top_creators(mention or posts),
            "mention_posts": mention,
        }
        bh, td = results[d["id"]]["brand_heat"], results[d["id"]]["this_dress"]
        print(f"  brand tags: {bh['n_posts']} posts / {bh['total_views']:,} views | "
              f"THIS DRESS: {td['n_posts']} posts / {td['total_views']:,} views / "
              f"{td['total_saves']:,} saves / {td['n_creators']} creators")

    os.makedirs(SNAP_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(SNAP_DIR, f"tiktok_{stamp}.json")
    json.dump({"scraped_at": stamp, "results": results}, open(path, "w"), indent=2)
    print(f"\nsaved -> {os.path.relpath(path)}")

    print("\n=== TikTok comparison (THIS DRESS = caption mentions the product) ===")
    print(f"{'dress':<34}{'posts':>6}{'views':>13}{'saves':>10}{'creators':>9}")
    for r in results.values():
        a = r["this_dress"]
        print(f"{r['name'][:33]:<34}{a['n_posts']:>6}{a['total_views']:>13,}"
              f"{a['total_saves']:>10,}{a['n_creators']:>9}")


if __name__ == "__main__":
    main()
