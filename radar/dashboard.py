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

from .match import matches_style

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")
OUT = os.path.join(HERE, "..", "dashboard.html")

PATTERN = {
    "cora":   ("Convergence", "#16a34a", "Demand + supply already converge → match renters/buyers to owners now."),
    "giggle": ("White space", "#d97706", "Hot demand, zero rental supply → organize demand before supply exists."),
    "sculpt": ("Scarcity gap", "#dc2626", "Viral + limited-edition, no rental supply → build the market from scratch."),
}

# TikTok SEARCH queries (verified live to surface the actual dress). Search beats
# hashtags here: #giggledress doesn't exist and #thesculpt is a Pilates tag, whereas a
# brand+style keyword search reliably lands on the product. NOTE: these use ?q=, which
# some sandboxed preview panes strip — open dashboard.html in a real browser to test.
TIKTOK_QUERY = {
    "cora":   "realisation par cora dress",
    "giggle": "giggle dress aritzia",                     # verified
    "sculpt": "the sculpt bandage mini dress house of cb",  # verified; no color -> any colorway
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

    rows = []
    for d in wl["dresses"]:
        th = tt.get(d["id"], {}).get("brand_heat", {}) or {}
        smv = sm.get(d["id"], {})
        pk = load(f"pickle_{d['pickle_category'].replace('/', '_')}_*.json")
        listings = pk.get("listings", [])
        total = len(listings) if listings else None
        matched = [x for x in listings if matches_style(x.get("title"), d.get("match"))] if listings else []
        style = len(matched) if listings else None
        # deep-link to the actual matching rental (cheapest rent first); None => no exact listing
        best = min(matched, key=lambda x: x.get("rent_usd") or 10**9) if matched else None
        rows.append({
            "pickle_listing": best,
            "d": d, "views": th.get("total_views", 0), "saves": th.get("total_saves", 0),
            "fresh": th.get("share_recent_14d", 0),
            "sm_clicks": (smv.get("style", {}) or {}).get("total_clicks", 0),
            "sm_prom": (smv.get("style", {}) or {}).get("max_promoters", 0),
            "sm_brand": (smv.get("brand", {}) or {}).get("total_clicks", 0),
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
        # TikTok proof: search on the brand + style name (verified — see TIKTOK_QUERY note).
        q = TIKTOK_QUERY.get(d["id"]) or (d.get("trends_terms") or [d["name"]])[0]
        tiktok_link = (f'<a href="https://www.tiktok.com/search?q={quote(q)}" '
                       f'target="_blank">see it on TikTok ↗</a>')
        supply = "n/a" if r["total"] is None else f"{r['style']} <span class='muted'>of {r['total']}</span>"
        cards += f"""
    <div class="card">
      <span class="pat" style="background:{color}">{pat}</span>
      <h3>{d['name']}</h3>
      <div class="scores">
        <div><span class="big">{r['trend']}</span><span class="lbl">Trend</span></div>
        <div><span class="big" style="color:{color}">{r['opp']}</span><span class="lbl">Opportunity</span></div>
      </div>
      <table class="sig">
        <tr><td>📈 TikTok</td><td>{fmt(r['views'])} views · {fmt(r['saves'])} saves · {int(r['fresh']*100)}% fresh(14d)</td></tr>
        <tr><td>🛍️ ShopMy</td><td>{fmt(r['sm_clicks'])} clicks · {r['sm_prom']} creators link it<br><span class="muted">brand-level {fmt(r['sm_brand'])} clicks</span></td></tr>
        <tr><td>👗 Pickle</td><td>{supply} rental listings of the style</td></tr>
      </table>
      <p class="desc">{desc}</p>
      <div class="links"><a href="{d.get('product_url', '#')}" target="_blank">product ↗</a> &nbsp;·&nbsp; {tiktok_link} &nbsp;·&nbsp; {pickle_link}</div>
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
<section><h2>Trending dresses</h2><div class="cards">{cards}</div></section>
<section><h2>🔎 Discovery feed <span class="muted">— inverse search: dresses the radar found on its own</span></h2>
<table class="feed"><tr><th>Brand</th><th>Views</th><th>Posts</th><th>Top product</th><th></th></tr>{feed}</table></section>
<section><h2>Alert policy</h2>
<div class="tier"><span class="dot g"></span><b>Discovery</b>&nbsp;— new product &gt;1M views → log + daily digest</div>
<div class="tier"><span class="dot y"></span><b>Momentum</b>&nbsp;— trend jumps &gt;20% in 24h → Telegram #trending</div>
<div class="tier"><span class="dot r"></span><b>Gap</b>&nbsp;— trend &gt;70 &amp; Pickle supply = 0 → Telegram + email + campaign draft</div></section>
<footer>Lightweight PoC · signals are directional — see the README for what's reliable vs. not. Trend = 0.5·views + 0.3·saves + 0.2·freshness (normalized); Opportunity = Trend × supply-gap.</footer>
</body></html>"""
    with open(OUT, "w") as f:
        f.write(html)
    print(f"wrote -> {os.path.relpath(OUT)}   (open it in a browser)")


if __name__ == "__main__":
    main()
