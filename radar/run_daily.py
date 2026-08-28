#!/usr/bin/env python3
"""
run_daily.py — lightweight daily orchestrator (no Prefect needed for the PoC).

Runs the radar pipeline in order, logs every stage to data/logs/run_<date>.log,
and CONTINUES past a failed stage (a broken TikTok run won't kill Pickle+diff).
This is the PoC-scale version of the DAG described in the README's hardening section.

    python -m radar.run_daily          # one full run
    python -m radar.run_daily --loop   # run now, then repeat every 24h

Cron it (daily 9am):
    0 9 * * * cd ~/Desktop/trace-radar && .venv/bin/python -m radar.run_daily
"""
import os, subprocess, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
LOGDIR = os.path.join(HERE, "..", "data", "logs")
BRANDS = ["house-of-cb/dresses", "realisation-par/dresses", "nadine-merabi/dresses"]

# ordered pipeline: discover new dresses -> gather signals -> score -> diff/alert
STAGES = [
    ["radar.discover"],
    ["radar.pickle_scraper", *BRANDS],
    ["radar.tiktok_signals"],
    ["radar.shopmy_signals", "--from-discover"],   # consume creators discover.py just found
    ["radar.score"],
    ["radar.diff"],
    ["radar.velocity"],     # per-post momentum (Δviews on the same posts across snapshots)
    ["radar.dashboard"],    # regenerate the UI so it never drifts from the data
]


def run_once(log):
    ok = 0
    for stage in STAGES:
        name = stage[0]
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        header = f"\n===== {ts}  {name} ====="
        print(f"[{ts}] {name} ...")
        log.write(header + "\n"); log.flush()
        r = subprocess.run([sys.executable, "-m", *stage], capture_output=True, text=True)
        log.write(r.stdout or ""); log.write(r.stderr or "")
        status = "OK" if r.returncode == 0 else f"FAILED (exit {r.returncode})"
        ok += r.returncode == 0
        print(f"    -> {status}")
        log.write(f"----- {name}: {status}\n"); log.flush()
    return ok, len(STAGES)


def main():
    os.makedirs(LOGDIR, exist_ok=True)
    loop = "--loop" in sys.argv
    while True:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(LOGDIR, f"run_{stamp}.log")
        print(f"=== radar daily run {stamp} ===")
        with open(path, "a") as log:
            ok, total = run_once(log)
        print(f"{ok}/{total} stages OK · logged -> {os.path.relpath(path)}")
        if not loop:
            break
        time.sleep(24 * 3600)


if __name__ == "__main__":
    main()
