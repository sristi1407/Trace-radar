#!/usr/bin/env python3
"""
score.py — combine the signals into a per-dress scorecard + two rankings.

Reads the latest snapshots this project produced:
  • Pickle per-brand pages  -> rental SUPPLY (total listings + listings of the trending style)
  • TikTok                  -> DEMAND (specific-dress views/saves/creators; brand-tag as context)
  • ShopMy                  -> buy-intent (qualitative, from watchlist — see note)

Outputs two deterministic, explainable rankings:
  • Trend Score       — how hot/accelerating it is (demand)
  • Opportunity Score — demand where rental SUPPLY is missing (TRACE's white space)

Run:
    python -m radar.score
"""
import json, os, glob
from datetime import datetime, timezone

from .match import matches_style

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")


def latest(pattern):
    files = glob.glob(os.path.join(DATA, pattern))
    return max(files, key=os.path.getmtime) if files else None


def load_json(path):
    return json.load(open(path)) if path and os.path.exists(path) else None


def pickle_supply(dress):
    """total listings for the brand page + how many are the trending STYLE."""
    cat = dress["pickle_category"].replace("/", "_")
    snap = load_json(latest(f"pickle_{cat}_*.json"))
    if not snap:
        return None, None
    listings = snap["listings"]
    term = dress.get("match") or ""
    style = sum(1 for x in listings if matches_style(x.get("title"), term))
    return len(listings), style


def norm(values):
    """min-max normalize a list to 0..1 (flat -> 0.5)."""
    lo, hi = min(values), max(values)
    return [0.5] * len(values) if hi == lo else [(v - lo) / (hi - lo) for v in values]


def gap_factor(style_supply):
    """More missing supply of the trending style = bigger opportunity."""
    if style_supply is None:
        return 0.5
    if style_supply == 0:
        return 1.0
    if style_supply <= 5:
        return 0.6
    if style_supply <= 20:
        return 0.35
    return 0.15


def main():
    watch = json.load(open(WATCHLIST))["dresses"]
    tiktok = (load_json(latest("tiktok_*.json")) or {}).get("results", {})

    rows = []
    for d in watch:
        node = tiktok.get(d["id"], {}) or {}
        tt = node.get("this_dress", {}) or {}      # the SPECIFIC dress = honest signal
        brand = node.get("brand_heat", {}) or {}    # brand-tag traffic = context only
        total, style = pickle_supply(d)
        rows.append({
            "id": d["id"], "name": d["name"], "brand": d["brand"],
            "views": tt.get("total_views", 0),
            "saves": tt.get("total_saves", 0),
            "fresh": tt.get("share_recent_14d", 0),   # momentum proxy
            "creators": tt.get("n_creators", 0),
            "brand_views": brand.get("total_views", 0),
            "supply_total": total, "supply_style": style,
            "shopmy": bool(d.get("shopmy_creators")) or d.get("shopmy_status", "partner-brand"),
        })

    # normalize demand signals across the dresses
    nv = norm([r["views"] for r in rows])
    ns = norm([r["saves"] for r in rows])
    nf = norm([r["fresh"] for r in rows])
    for r, v, s, f in zip(rows, nv, ns, nf):
        r["trend_score"] = round(100 * (0.5 * v + 0.3 * s + 0.2 * f), 1)
        r["opportunity_score"] = round(r["trend_score"] * gap_factor(r["supply_style"]), 1)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# TRACE Radar — scorecard ({stamp})\n"]
    lines.append("| Dress | Trend | Opportunity | TikTok views (dress) | Saves | Creators | Pickle supply (style) |")
    lines.append("|---|--:|--:|--:|--:|--:|--:|")
    for r in sorted(rows, key=lambda r: r["opportunity_score"], reverse=True):
        sup = "n/a" if r["supply_total"] is None else f"{r['supply_total']} ({r['supply_style']})"
        lines.append(f"| {r['name']} | {r['trend_score']} | **{r['opportunity_score']}** | "
                     f"{r['views']:,} | {r['saves']:,} | {r['creators']} | {sup} |")

    lines.append("\n**Trend Score** = 0.5·views + 0.3·saves + 0.2·freshness (normalized across dresses).")
    lines.append("**Opportunity Score** = Trend Score × supply-gap (higher when the trending style has "
                 "little/no Pickle rental supply). Pickle supply shows *total brand listings (of the trending style)*.")
    lines.append("\n> ShopMy is assessed at brand level (all tracked brands are ShopMy partners; creators link them). "
                 "Full per-product ShopMy scraping via api.shopmy.us is the next automation step.")

    out = "\n".join(lines)
    print("\n" + out + "\n")
    path = os.path.join(DATA, f"radar_{stamp}.md")
    open(path, "w").write(out + "\n")
    print(f"saved -> {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
