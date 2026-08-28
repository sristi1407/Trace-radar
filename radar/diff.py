#!/usr/bin/env python3
"""
diff.py — momentum / liquidity via Pickle snapshot diffing (the daily-radar core).

Compares the two most recent snapshots of each tracked brand page:
  • DISAPPEARED listings  -> likely rented or sold  = demand / velocity signal
  • NEW listings          -> fresh supply forming
  • change in the TRENDING STYLE's count -> the alert trigger

This is the piece that makes the radar "refresh daily, detect momentum, and alert."
Run it after each daily scrape:
    python -m radar.pickle_scraper house-of-cb/dresses realisation-par/dresses nadine-merabi/dresses
    python -m radar.diff

NOTE: a meaningful turnover diff needs the two snapshots to track the *same set*. Two
things break that: (a) different scroll depth (capped vs full), and — discovered here —
(b) Pickle serving a *rotating subset*: two same-depth scrapes two days apart share only
~33% of listings, so raw "disappeared" is mostly sampling, not rentals. The comparability
guard below catches both and suppresses turnover instead of firing false alerts. Reliable
rental velocity needs a stable per-listing ID or the full inventory feed (an integration),
not the paginated brand page — so momentum here leans on the TikTok signals, not Pickle churn.
"""
import glob, json, os, re
from datetime import datetime, timezone

from .match import matches_style


def _date(path):
    # order snapshots by the date in the FILENAME, not mtime (identical after a fresh git clone —
    # mtime ordering silently reverses the diff window on a clone)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    return m.group(1) if m else "0000-00-00"

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
WATCHLIST = os.path.join(HERE, "..", "config", "watchlist.json")
TURNOVER_ALERT = 0.15   # >15% of listings gone since last snapshot = hot rental demand
MIN_DISAPPEARED = 5     # ...but require an absolute floor too, so single-listing churn never fires
STYLE_DROP_ALERT = 3    # only flag a style whose supply drops by >=3 (ignore noise)


def two_latest(category):
    cat = category.replace("/", "_")
    files = sorted(glob.glob(os.path.join(DATA, f"pickle_{cat}_*.json")), key=_date)
    return files[-2:] if len(files) >= 2 else files


def load(path):
    return json.load(open(path))


def style_count(listings, term):
    # word-aware + fuzzy (match.py), same as score.py — so "cora" won't match "coral"/"decorated"
    return sum(1 for x in listings if matches_style(x.get("title"), term))


def main():
    watch = json.load(open(WATCHLIST))["dresses"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = [f"# Pickle momentum diff ({stamp})\n"]
    alerts = []

    for d in watch:
        pair = two_latest(d["pickle_category"])
        if len(pair) < 2:
            out.append(f"## {d['name']}\n_Only one snapshot — take another full scrape tomorrow to diff._\n")
            continue

        old, new = load(pair[0]), load(pair[1])
        old_ids = {x["uuid"]: x for x in old["listings"]}
        new_ids = {x["uuid"]: x for x in new["listings"]}
        # comparability guard. Two failure modes make a diff meaningless:
        #   (a) different scroll depth (capped vs full)  -> caught by the count ratio
        #   (b) the brand page serves a *rotating subset* -> caught by low UUID overlap
        # Empirically Pickle does (b): two same-depth scrapes 2 days apart share only ~33% of
        # UUIDs, so "disappeared" is mostly sampling, not rentals. Suppress rather than fire noise.
        ratio = len(new_ids) / max(len(old_ids), 1)
        overlap = len(old_ids.keys() & new_ids.keys()) / max(len(old_ids), 1)
        if not (0.67 <= ratio <= 1.5) or overlap < 0.70:
            reason = ("different scroll depth" if not (0.67 <= ratio <= 1.5)
                      else f"only {overlap:.0%} of listings persist across scrapes — the brand page serves a rotating subset")
            out.append(f"## {d['name']}  ({os.path.basename(pair[0])[-15:-5]} → {os.path.basename(pair[1])[-15:-5]})")
            out.append(f"- total listings: {len(old_ids)} → {len(new_ids)}")
            out.append(f"_⚠️ Not comparable ({reason}). Turnover suppressed — a reliable rental-velocity diff needs a "
                       f"stable per-listing ID or the full inventory feed, not the paginated brand page._\n")
            continue
        disappeared = [old_ids[i] for i in old_ids if i not in new_ids]  # rented/sold
        appeared = [new_ids[i] for i in new_ids if i not in old_ids]     # new supply
        turnover = len(disappeared) / len(old_ids) if old_ids else 0

        term = d.get("match")
        s_old, s_new = style_count(old["listings"], term), style_count(new["listings"], term)

        out.append(f"## {d['name']}  ({os.path.basename(pair[0])[-15:-5]} → {os.path.basename(pair[1])[-15:-5]})")
        out.append(f"- total listings: {len(old_ids)} → {len(new_ids)}")
        out.append(f"- disappeared (rented/sold): **{len(disappeared)}**  ·  new: {len(appeared)}  ·  turnover: {turnover:.0%}")
        out.append(f"- trending style '{term}': {s_old} → {s_new}\n")

        # --- alert logic (thresholds avoid single-listing / churn noise) ---
        if turnover >= TURNOVER_ALERT and len(disappeared) >= MIN_DISAPPEARED:
            alerts.append(f"🔥 {d['brand']}: {len(disappeared)} listings gone ({turnover:.0%}) since last snapshot — hot rental demand.")
        if s_old == 0 and s_new > 0:
            alerts.append(f"🚨 {d['name']}: the trending style just APPEARED on Pickle ({s_new} listings) — demand meeting supply.")
        elif (s_old - s_new) >= STYLE_DROP_ALERT:
            alerts.append(f"📈 {d['name']}: '{term}' supply dropping ({s_old}→{s_new}) — renting out faster than it's listed.")

    out.append("\n---\n## ⚠️ Alerts")
    out += [f"- {a}" for a in alerts] or ["- (none this run)"]

    text = "\n".join(out)
    print("\n" + text + "\n")
    path = os.path.join(DATA, f"diff_{stamp}.md")
    open(path, "w").write(text + "\n")
    print(f"saved -> {os.path.relpath(path)}")

    # Optional: push alerts to Telegram if you set TELEGRAM_TOKEN/CHAT_ID in .env
    # (reuses your job-hunt bot pattern) — left as a hook so the PoC shows the path.


if __name__ == "__main__":
    main()
