#!/usr/bin/env python3
"""
dashboard.py — renders a single-page visual dashboard (dashboard.html) from the
latest snapshots. No server needed: just open the file. This is the "dashboard
showing trending dresses" prototype form from the brief, aimed at a non-technical
reader (and great for a live walkthrough).

Run after the pipeline:
    python -m radar.dashboard        # -> dashboard.html
"""
import glob, json, os
from datetime import datetime, timezone
from urllib.parse import quote

from .match import matches_style, brand_filter
from .velocity import compute as vel_compute, label as vel_label

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")
OUT = os.path.join(HERE, "..", "dashboard.html")

PATTERN = {
    "cora":   ("Convergence", "#16a34a", "Real brand-anchored demand (245K) + 76 rentals + proven (now-cooling) ShopMy → match renters to owners today."),
    "merabi": ("High-value convergence", "#0ea5e9", "Top demand — but brand/occasion-level (1.8M; people search 'a Nadine Merabi for a wedding', not 'Nina'), anchored to the Nina Gold SKU (10 rentals). The strongest all-round play; onboard the creators to light up ShopMy."),
    "sculpt": ("Signal contamination", "#dc2626", "Looked #1 at 4.9M — but brand-anchoring exposed it as 100% Pilates (homonym). 0 confirmed dress posts in our sample; the real dress needs brand-anchored / LLM capture."),
}

# TikTok links per dress, each a list of (label, url). Use a clean dress TAG where one
# exists (path-based → opens everywhere), or a brand+style SEARCH where the tag is
# unusable (#thesculpt is Pilates). Nadine Merabi is anchored to its one signature look,
# the Gold sequin. (?q= search opens in a real browser but is stripped by some preview panes.)
_S = "https://www.tiktok.com/search?q="
TIKTOK_LINK = {
    "cora":   [("see it on TikTok", "https://www.tiktok.com/tag/coradress")],
    "sculpt": [("see it on TikTok", _S + quote("the sculpt bandage mini dress house of cb"))],
    "merabi": [("see it on TikTok", _S + quote("nadine merabi dress nina gold"))],
}

# ShopMy shop-search per dress (proves creators feature it — our 14-creator scrape sample
# missed them, but ShopMy's directory surfaces them). ?query= opens in a real browser.
SHOPMY_LINK = {
    "cora":   "https://shopmy.us/shop/product/2128245",   # direct ShopMy product page for The Cora (path-based)
    "sculpt": "https://shopmy.us/shop?query=house+of+cb+bandage-mini-dress",
    "merabi": "https://shopmy.us/shop?query=nadine+merabi+dress+nina+gold&tab=popular",
}

CSS = """
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#0b0f17;color:#e8eef7}
header{padding:26px 32px;border-bottom:1px solid #1e2634}header h1{margin:0;font-size:22px}header p{margin:5px 0 0;color:#8aa0bd;font-size:13px}
section{padding:22px 32px}h2{font-size:15px;color:#c9d7ee;font-weight:600;margin:0 0 14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}
.card{background:#121826;border:1px solid #1e2634;border-radius:12px;padding:16px}
.pat{display:inline-block;color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;letter-spacing:.3px}
.card h3{margin:11px 0 4px;font-size:16px}
.scores{display:flex;gap:22px;margin:10px 0 12px}
.scores .big{font-size:26px;font-weight:700;line-height:1}.scores .lbl{font-size:10px;color:#8aa0bd;text-transform:uppercase;letter-spacing:.5px;display:block;margin-top:3px}
table.sig{width:100%;border-collapse:collapse;font-size:13px}table.sig td{padding:7px 0;border-top:1px solid #1e2634;vertical-align:top}table.sig td:first-child{width:86px;color:#c9d7ee;white-space:nowrap}
.muted{color:#6b7d96}.desc{font-size:12.5px;color:#a9bcd6;margin:11px 0 8px;line-height:1.5}.links a{color:#5aa9ff;text-decoration:none;font-size:12px}
table.feed{width:100%;border-collapse:collapse;font-size:13px}table.feed th{text-align:left;color:#8aa0bd;font-weight:600;padding:7px 10px;border-bottom:1px solid #1e2634}table.feed td{padding:9px 10px;border-bottom:1px solid #151c2a}
.new{background:#0f2f1a;color:#5bd77e;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px}
.tier{display:flex;align-items:center;gap:9px;padding:5px 0;font-size:13px}.dot{width:10px;height:10px;border-radius:50%}.g{background:#16a34a}.y{background:#d97706}.r{background:#dc2626}
footer{padding:18px 32px;color:#6b7d96;font-size:12px;border-top:1px solid #1e2634}
"""


def latest(pat):
    fs = glob.glob(os.path.join(DATA, pat))
    return max(fs, key=os.path.getmtime) if fs else None


def load(pat):
    p = latest(pat)
    return json.load(open(p)) if p and os.path.exists(p) else {}


def fmt(n):
    n = n or 0
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 1_000:
        return f"{n / 1e3:.0f}K"
    return str(int(n))


def norm(vals):
    lo, hi = min(vals), max(vals)
    return [0.5] * len(vals) if hi == lo else [(v - lo) / (hi - lo) for v in vals]


def gap_factor(style):
    if style is None:
        return 0.5
    return 1.0 if style == 0 else 0.6 if style <= 5 else 0.35 if style <= 20 else 0.15


def main():
    wl = json.load(open(WATCHLIST))
    tt = load("tiktok_*.json").get("results", {})
    sm = load("shopmy_*.json").get("results", {})
    disc = load("discover_*.json")
    vel, _, _ = vel_compute()          # per-post momentum from the two latest snapshots

    rows = []
    for d in wl["dresses"]:
        node = tt.get(d["id"], {}) or {}
        td = node.get("this_dress", {}) or {}     # the SPECIFIC dress = honest headline
        bh = node.get("brand_heat", {}) or {}      # brand-tag traffic = context only
        smv = sm.get(d["id"], {})
        pk = load(f"pickle_{d['pickle_category'].replace('/', '_')}_*.json")
        listings = brand_filter(pk.get("listings", []), d.get("brand"))   # Pickle pages are contaminated
        total = len(listings) if listings else None
        matched = [x for x in listings if matches_style(x.get("title"), d.get("match"))] if listings else []
        style = len(matched) if listings else None
        # deep-link to the actual matching rental (cheapest rent first); None => no exact listing
        best = min(matched, key=lambda x: x.get("rent_usd") or 10**9) if matched else None
        rows.append({
            "pickle_listing": best,
            "d": d, "views": td.get("total_views", 0), "saves": td.get("total_saves", 0),
            "fresh": td.get("share_recent_14d", 0), "tt_creators": td.get("n_creators", 0),
            "brand_views": bh.get("total_views", 0),
            "sm_clicks": (smv.get("style", {}) or {}).get("total_clicks", 0),
            "sm_prom": (smv.get("style", {}) or {}).get("max_promoters", 0),
            "sm_monthly": (smv.get("style", {}) or {}).get("monthly_clicks", 0),
            "total": total, "style": style,
        })

    nv, ns, nf = norm([r["views"] for r in rows]), norm([r["saves"] for r in rows]), norm([r["fresh"] for r in rows])
    for r, v, s, f in zip(rows, nv, ns, nf):
        r["trend"] = round(100 * (0.5 * v + 0.3 * s + 0.2 * f), 1)
        r["opp"] = round(r["trend"] * gap_factor(r["style"]), 1)

    cards = ""
    for r in sorted(rows, key=lambda r: r["opp"], reverse=True):
        d = r["d"]
        pat, color, desc = PATTERN.get(d["id"], ("—", "#556", ""))
        cat_url = "https://www.shoponpickle.com/shop/rent/" + d["pickle_category"]
        pk = r.get("pickle_listing")
        if pk:   # exact style is rentable -> link straight to that listing
            rent = f" · ${pk['rent_usd']}/rent" if pk.get("rent_usd") else ""
            pickle_link = f'<a href="{pk["url"]}" target="_blank">rent this on pickle ↗{rent}</a>'
        else:    # brand is on Pickle but this exact dress is not -> the gap, made clickable
            pickle_link = f'<a href="{cat_url}" target="_blank" class="muted">no exact rental yet · browse brand ↗</a>'
        # TikTok proof: one or more "see it" links per dress.
        tks = TIKTOK_LINK.get(d["id"], [])
        if len(tks) == 1:
            tiktok_link = f'<a href="{tks[0][1]}" target="_blank">see it on TikTok ↗</a>'
        elif tks:
            inner = " · ".join(f'<a href="{u}" target="_blank">{lbl} ↗</a>' for lbl, u in tks)
            tiktok_link = f'on TikTok: {inner}'
        else:
            tiktok_link = ""
        sm_url = SHOPMY_LINK.get(d["id"])
        shopmy_link = f'<a href="{sm_url}" target="_blank">on ShopMy ↗</a>' if sm_url else ""
        supply = "n/a" if r["total"] is None else f"{r['style']} <span class='muted'>of {r['total']}</span>"
        # TikTok: specific-dress headline; if it's ~all of brand_heat, it's really brand-level (label it honestly)
        lvl = " <span class='muted'>(brand/occasion-level)</span>" if r['brand_views'] and r['views'] >= 0.9 * r['brand_views'] else ""
        tiktok_cell = (f"{fmt(r['views'])} views · {fmt(r['saves'])} saves · {r['tt_creators']} creators{lvl}"
                       f"<br><span class='muted'>brand tag {fmt(r['brand_views'])} views · {int(r['fresh']*100)}% posted &lt;14d</span>")
        if r['sm_clicks'] or r['sm_prom']:
            # clicks are lifetime; flag when recent monthly activity is ~0 (don't oversell "hot now")
            recent = "" if r['sm_monthly'] else " <span class='muted'>(lifetime; recent monthly ≈ 0)</span>"
            shopmy_cell = f"{fmt(r['sm_clicks'])} clicks · {r['sm_prom']} creators link it{recent}"
        else:   # our 14-creator sample missed it; the ShopMy link lets you check directly
            shopmy_cell = f"<span class='muted'>on ShopMy (see link) · click volume not captured in our 14-creator sample</span>"
        cards += f"""
    <div class="card">
      <span class="pat" style="background:{color}">{pat}</span>
      <h3>{d['name']}</h3>
      <div class="scores">
        <div><span class="big">{r['trend']}</span><span class="lbl">Trend</span></div>
        <div><span class="big" style="color:{color}">{r['opp']}</span><span class="lbl">Opportunity</span></div>
      </div>
      <table class="sig">
        <tr><td>📈 TikTok</td><td>{tiktok_cell}</td></tr>
        <tr><td>⚡ Momentum</td><td>{vel_label(vel.get(d['id']))}</td></tr>
        <tr><td>🛍️ ShopMy</td><td>{shopmy_cell}</td></tr>
        <tr><td>👗 Pickle</td><td>{supply} rental listings of the style</td></tr>
      </table>
      <p class="desc">{desc}</p>
      <div class="links"><a href="{d.get('product_url', '#')}" target="_blank">product ↗</a> &nbsp;·&nbsp; {tiktok_link} &nbsp;·&nbsp; {shopmy_link} &nbsp;·&nbsp; {pickle_link}</div>
    </div>"""

    feed = ""
    for c in (disc.get("candidates") or [])[:8]:
        tp = c.get("top_products") or []
        prod = tp[0][0] if tp else "—"
        badge = "<span class='new'>NEW</span>" if c.get("is_new") else "<span class='muted'>tracked</span>"
        feed += f"<tr><td><b>{c['brand']}</b></td><td>{fmt(c['views'])}</td><td>{c['posts']}</td><td class='muted'>{prod}</td><td>{badge}</td></tr>"

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>TRACE Radar</title>
<style>{CSS}</style></head><body>
<header><h1>TRACE — Demand &amp; Liquidity Radar</h1>
<p>TikTok × ShopMy × Pickle · ranked by opportunity (demand where rental supply is missing) · {stamp}</p></header>
<section><h2>Trending dresses <span class="muted" style="font-weight:400;font-size:12px">— Trend &amp; Opportunity are 0–100, normalized within these 3 dresses (100 = top of the set)</span></h2><div class="cards">{cards}</div></section>
<section><h2>🔎 Discovery feed <span class="muted">— inverse search: dresses the radar found on its own</span></h2>
<table class="feed"><tr><th>Brand</th><th>Views</th><th>Posts</th><th>Top product</th><th></th></tr>{feed}</table></section>
<section><h2>Alert policy</h2>
<div class="tier"><span class="dot g"></span><b>Discovery</b>&nbsp;— new product &gt;1M raw views → log + daily digest</div>
<div class="tier"><span class="dot y"></span><b>Momentum</b>&nbsp;— raw views/saves &gt;30% day-over-day → Telegram #trending</div>
<div class="tier"><span class="dot r"></span><b>Gap</b>&nbsp;— &gt;2M raw views &amp; Pickle supply = 0 → Telegram + email + campaign draft</div>
<div class="tier muted" style="font-size:11px">Alerts key off <b>raw</b> signals (views/saves/listings), not the normalized score — which only ranks within a run.</div></section>
<footer>Lightweight PoC · signals are directional — see the README for what's reliable vs. not.<br>Trend = 0.5·views + 0.3·saves + 0.2·freshness, <b>min-max normalized across these 3 dresses</b> — so 100 is the highest in <i>this set</i>, not an absolute scale (production would use percentile ranks vs. a rolling 30-day baseline). Opportunity = Trend × supply-gap (higher when the trending style has little/no rental supply).</footer>
</body></html>"""
    with open(OUT, "w") as f:
        f.write(html)
    print(f"wrote -> {os.path.relpath(OUT)}   (open it in a browser)")


if __name__ == "__main__":
    main()
