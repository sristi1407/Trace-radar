#!/usr/bin/env python3
"""
velocity.py — per-post momentum from two TikTok snapshots (the brief's "accelerating" ask).

The static freshness proxy (share of posts <14d) can't see acceleration — it reads ~0.22 for
every dress. Real momentum needs the SAME posts measured twice: intersect the two most-recent
snapshots by post id, compute Δviews/day on the shared (brand-anchored) set, aggregate per dress.

Same comparability principle as diff.py: don't diff a set that barely overlaps.

    python -m radar.velocity
"""
import glob, json, os, re
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
MIN_SHARED = 3          # need a few shared posts for a meaningful rate
MIN_OVERLAP = 0.5       # ...and they must actually be the same set


def _date(path):
    # parse the date from the FILENAME (mtime is unreliable — identical after a CI checkout)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    return m.group(1) if m else "0000-00-00"


def two_latest():
    fs = sorted(glob.glob(os.path.join(DATA, "tiktok_*.json")), key=_date)
    return fs[-2:] if len(fs) >= 2 else fs


def compute():
    """Return {dress_id: {...velocity...}}, and the (old_date, new_date) window."""
    pair = two_latest()
    if len(pair) < 2:
        return {}, None, None
    old, new = json.load(open(pair[0])), json.load(open(pair[1]))
    d0, d1 = _date(pair[0]), _date(pair[1])
    days = max((datetime.fromisoformat(d1) - datetime.fromisoformat(d0)).days, 1)

    out = {}
    for did, r in new.get("results", {}).items():
        if did not in old.get("results", {}):
            out[did] = {"status": "needs a 2nd comparable snapshot"}
            continue
        op = {p["id"]: p for p in old["results"][did].get("mention_posts", []) if p.get("id")}
        npp = {p["id"]: p for p in r.get("mention_posts", []) if p.get("id")}
        shared = set(op) & set(npp)
        overlap = len(shared) / max(len(op), 1)
        if len(shared) < MIN_SHARED or overlap < MIN_OVERLAP:
            out[did] = {"status": f"not comparable ({len(shared)} shared / {overlap:.0%} overlap)"}
            continue
        dv = sum(npp[i]["views"] - op[i]["views"] for i in shared)
        base = sum(op[i]["views"] for i in shared)
        out[did] = {
            "status": "ok", "n_shared": len(shared), "days": days,
            "delta_views": dv, "per_day": dv // days,
            "pct": round(dv / base * 100, 1) if base else 0.0,
            "window": f"{d0}→{d1}",
        }
    return out, d0, d1


def label(v):
    """One-line momentum string for a dress (used by the dashboard)."""
    if not v or v.get("status") != "ok":
        return (v or {}).get("status", "n/a")
    return f"{v['pct']:+.1f}% ({v['delta_views']:+,} views · {v['per_day']:+,}/day) over {v['days']}d, {v['n_shared']} posts"


def main():
    vel, d0, d1 = compute()
    if not vel:
        print("Need two TikTok snapshots to compute velocity.")
        return
    lines = [f"# TikTok momentum — per-post velocity ({d0} → {d1})\n",
             "Δviews on the SAME posts (intersected by id) over the brand-anchored set. The static "
             "freshness proxy can't see acceleration; this can. Same overlap guard as `diff.py`.\n"]
    for did, v in vel.items():
        lines.append(f"- **{did}** — {label(v)}")
    text = "\n".join(lines)
    print("\n" + text + "\n")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    open(os.path.join(DATA, f"velocity_{stamp}.md"), "w").write(text + "\n")
    print(f"saved -> data/velocity_{stamp}.md")


if __name__ == "__main__":
    main()
