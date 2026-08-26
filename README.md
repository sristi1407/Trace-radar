# TRACE Demand & Liquidity Radar — Proof of Concept
*Sristi Prasad · Applied AI Engineering Exercise · Aug 2026*

> **Thesis:** TikTok tells you *what's gaining desire*, ShopMy *resolves that desire to a buyable product*, and Pickle tells you *whether that item actually has rental supply*. Combining present **and absent** signals reveals where TRACE should concentrate demand — sometimes *before* rental supply exists.

> **How this was built (honest note):** this is a lightweight PoC. I care more about showing *how I investigate an ambiguous problem, make tradeoffs, and reason about what's reliable* than about a polished system. Limitations are called out throughout — that's deliberate.

---

## TL;DR — findings
Three currently-trending dresses, chosen to show three *different* patterns for TRACE:

| Dress (brand) | TikTok (demand) | ShopMy (buy-intent) | Pickle (supply) | Pattern → what TRACE should do |
|---|---|---|---|---|
| **Réalisation Par — The Cora** | ~6.9M views; wedding-guest | **69.5K clicks · 991 creators link it** | **78 of 800** | **Convergence (all 3)** → match renters/buyers to owners *now* |
| **Aritzia — Giggle** | ~3.2M views; **freshest (90% <14d)** | brand-level only (Aritzia 130K clicks; style not linked) | **0 of 763** | **White space** → organize demand + recruit owners *before* supply |
| **House of CB — The Sculpt** | **~43.2M** views (most viral) | **none** in creator sample | **0 of 799** | **Scarcity gap / no commerce rails** → build the market from scratch |

### The exact products (specific styles, not just brands)
- **Réalisation Par — "The Cora," _Mirage_ colorway** — silk bias-cut, multicolour-striped midi with a cowl neck + detachable half-slip (~$330–375). *(realisationpar.com/the-cora-mirage)*
- **Aritzia — "Giggle Dress" (Sunday Best line), style #130273** — sleeveless fitted micro-dress with built-in shorts.
- **House of CB — "The Sculpt" bandage dress** (halter; mini + midi) — part of the limited-edition Bandage Collection ("once sold out, no restock").

> Note: the Pickle supply counts (78 / 0 / 0) are **style-specific** — matched on the exact style name in listing titles across all 800 / 763 / 799 of each brand's dresses — so the supply signal is genuinely per-dress, not per-brand.

**The creators driving them** — Cora: `@amirajasminnn`, `@nadiaorr_` (brand-tagged), `@lindleysavage`, `@cosycosy5`, `@realisationpar`. Sculpt: `@suelamehmedi` (“bandage is so back @houseofcb”) + HOCB's large program. Giggle: haul-driven (`@hannagrace.b`, `@ameliamulligan`) — notably *no dedicated creator/tag*, which is itself a signal.

---

## Per-dress analysis — the 7 factors
Each dress evaluated across the factors the brief asks for:

| Factor | **Cora** (Réalisation Par) | **Giggle** (Aritzia) | **The Sculpt** (House of CB) |
|---|---|---|---|
| **Current heat** | ~6.9M brand views, 60 posts | ~3.2M views, 59K saves | **~43.2M views, 507K saves** (most viral) |
| **Momentum** | moderate (15% of posts <14d) | **highest — 90% of posts <14d, accelerating** | strong at brand level (style-level noisy) |
| **Recency** | newest post <1 day ago | **newest post today** | newest ~2 days ago |
| **Creator activity** | many & distinct (amirajasminnn, nadiaorr_, lindleysavage, cosycosy5, @realisationpar) | haul-driven & diffuse — no hero creator, no dedicated tag | large program (suelamehmedi + HOCB influencers) |
| **Cross-platform breadth** | **all three** (TikTok ✓ · ShopMy ✓ · Pickle ✓) | TikTok ✓ · ShopMy brand-level · **not Pickle** | **TikTok-dominant** (ShopMy thin · not Pickle) |
| **Commerce intent (ShopMy, measured)** | **strong — 69,540 clicks; 991 creators link the Cora** | brand-level — Aritzia 129,887 clicks, but the Giggle *style* isn't linked (unstructured) | **weak — no House of CB links in the creator sample** despite huge attention |
| **Rental liquidity** | **78 listings** on Pickle ($50–90/wk) — deep | **0 of 763** Aritzia dresses | **0 of 799** HOCB dresses |
| **→ Pattern** | **Convergence** | **White space** | **Scarcity gap** |

**Product & evidence links** (all verified live):
- **Cora:** [product](https://realisationpar.com/the-cora-mirage/) · [Pickle rentals (78)](https://www.shoponpickle.com/shop/rent/realisation-par/dresses) · [TikTok example](https://www.tiktok.com/@nadiaorr_/video/7648330858142649614)
- **Giggle:** [product #130273](https://www.aritzia.com/us/en/product/giggle-dress/130273.html) · [Pickle — brand present, 0 Giggle](https://www.shoponpickle.com/shop/rent/aritzia/dresses) *(TikTok signal is brand-level — no dedicated tag)*
- **The Sculpt:** [product](https://www.houseofcb.com/the-sculpt-black-bandage-mini-dress.html) · [Pickle — brand deep, 0 Sculpt](https://www.shoponpickle.com/shop/rent/house-of-cb/dresses) *(TikTok #thesculpt is Pilates-polluted — brand-level heat used)*

## Recommendation for TRACE
1. **Concentrate the initial presale marketplace around the two white-space dresses — Aritzia Giggle and House of CB Sculpt.** Both have loud, fresh demand and **zero** rental supply of the trending style. This is exactly TRACE's wedge: *organize demand and recruit owners before conventional rental supply exists.* Giggle is the cleanest opportunity (freshest signal, uncontaminated) and the one I'd act on first. **⚠️ Note the scorecard tension:** Sculpt *tops* the raw Trend/Opportunity table (80 vs. Giggle's 22), but that number is inflated by the `#thesculpt` Pilates noise — so I'd treat Sculpt as high-potential-**but-validate-manually**, and lead with Giggle, whose signal is clean. (This is exactly why the write-up matters more than the raw score: the model ranks Sculpt #1, but a human read of the data says Giggle first.)
2. **Use Réalisation Par's Cora as proof-of-category and immediate liquidity** — demand *and* 78 rental listings already exist, so TRACE can match renters/buyers to owners today.
3. **Recruit the creators already driving each dress** (listed above) rather than starting cold.
4. **The absence of a Pickle listing is a buy signal, not a dead end** — it's where TRACE creates the market.

---

## Vision — what this becomes for TRACE
Today this is a daily radar over a watchlist. The natural product it points to:

1. **One-click, any-product intelligence.** Paste any product (or a link) → instantly see its cross-platform pulse: who's posting it (TikTok), who's linking/buying it (ShopMy), and whether it's rentable (Pickle) — with a Trend + Opportunity score. *(The PoC already does this for a watchlist; generalizing the product resolver makes it one-click for anything.)*
2. **Always-on viral detection.** Continuously watch for **any** item spiking on **any** platform — a post crossing a view/velocity threshold, a jump in ShopMy clicks, or Pickle listings vanishing fast — and alert TRACE the moment something starts accelerating. *(`diff.py` + `score.py` are the seed of this; the Telegram hook is the alert channel.)*
3. **Celebrity / big-creator triggers.** Weight the signal by reach — when a high-follower creator or a celebrity is seen wearing or linking an item, fire an instant alert. That moment is often the *spark* of a trend, and catching it early is the whole game.
4. **The attraction loop (why it grows TRACE).** The instant something goes viral, notify interested users — *"this dress is blowing up — presale or reserve it on TRACE now."* That converts fleeting attention into locked-in demand and directly attacks TRACE's cold-start problem: you **organize demand around a product before supply exists.**

In one line: *watch demand across the web, catch it while it's accelerating, and pull buyers, renters, and owners together around the exact item — automatically.*

### Hardening it for daily reliability
Running this daily surfaced two failure modes I'd engineer around next — both drawn directly from what broke during this build:

- **Signal pollution → LLM relevance filtering.** Keyword/hashtag matching misfires on homonyms ("sculpt" → Pilates classes, "giggle" → ski goggles, "cora" → a dog). Fix: pass each candidate caption through a cheap LLM (gpt-4o-mini / Gemini Flash) — *"does this video actually feature and recommend THIS dress? Ignore Pilates, pets, and generic brand mentions"* — to produce a clean per-video **`confidence_score`** instead of trusting raw counts. (This is exactly why I lead with the human read over the raw scorecard.)
- **Keyword-search outages → fallback chaining.** TikTok's keyword search was down during this build, so I fell back to hashtags. In production I'd chain further: the brand's **official account feed** + the feeds of the **top ~50 ShopMy creators**. A **co-occurrence trigger** — the brand posts a style *and* ≥3 creators post the same style within 48h — is a stronger, more reliable signal than raw hashtag volume anyway.
- **Dynamic creator discovery (loop now wired).** Trends come from *new* creators, not a fixed 14. `discover.py` emits the high-engagement creators it finds, and `shopmy_signals.py --from-discover` scrapes them automatically — a self-expanding feedback loop: **TikTok finds the creator → ShopMy reads their links → Pickle checks the products.** (Handle resolution is best-effort — TikTok and ShopMy usernames don't always match — which the fuller version would reconcile via ShopMy's search API.)
- **Catalog-wide validation, not just a sample.** Pull breadth metrics (e.g. the Cora's 991 promoters) from ShopMy's product search / sitemap rather than the 14-creator sample, and take a **weekly per-brand catalog baseline** (Aritzia, House of CB, Réalisation Par, Retrofete) so buy-intent is measured against *all* linked products.
- **Orchestration + state (make it a real daily job).** Wrap the pipeline in a Prefect/Dagster DAG (scrape → resolve → score → diff → alert) with **atomic, dated snapshots + a `_SUCCESS` marker**. `diff.py` then compares only *complete* runs — so a half-failed scrape can't produce a false zero-delta (exactly the apples-to-oranges failure I hit diffing a capped snapshot against a full one).

## How it works (architecture)
```
discover.py ─ [INVERSE SEARCH] trending hashtags → extract brand/product → surface NEW viral dresses
      │        (feeds the watchlist automatically)
      ▼
TikTok  (Apify)      ─ demand: views, saves, freshness/momentum
ShopMy  (Apify)      ─ buy-intent: creator links + clicks + #promoters per product
Pickle  (Playwright) ─ supply: rental listings (word-aware + fuzzy match, match.py)
      │
      ▼
score.py ─ Trend Score + Opportunity Score      diff.py ─ [AUTOMATED] daily diff → alert on momentum
```

## What I automated, and why
Two recurring pieces, both designed to run daily:

1. **Inverse-search discovery (`discover.py`) — the headline.** Instead of checking a known watchlist, it scrapes trending fashion hashtags (`#fashionhaul`, `#grwm`, `#weddingguestdress`…), extracts brand/product mentions from captions, and surfaces *emerging* dresses **not on any watchlist**. A live run flagged **Nadine Merabi at ~9.2M views as 🆕 NEW** — a viral brand the radar discovered on its own. This is the "alert TRACE when *any* dress goes viral" engine: **discovery, not just monitoring.**
2. **Momentum + scoring (`diff.py` + `score.py`).** Daily Pickle snapshot-diff (what rented out overnight) → re-score → alert when a style accelerates or a gap appears.

Together they demonstrate a credible path to a system that **refreshes daily, detects momentum, and alerts**. *(Bonus findings that made this work: Pickle's web is server-rendered/scrapable — richer than the brief assumed — so supply needs no API key; and style matching is word-aware + fuzzy (`match.py`), so counts are robust to title variants.)*

### Alert policy
Alerts are tiered, with a per-dress cooldown so nothing spams daily:

| Level | Trigger | Action |
|---|---|---|
| 🟢 **Discovery** | `discover.py` finds a *new* product with > 1M views | Log + daily digest |
| 🟡 **Momentum** | Trend score jumps > 20% in 24h (or a style's Pickle supply drops ≥ 3) | Telegram `#trending` |
| 🔴 **Gap** | Trend > 70 **and** Pickle supply = 0 (hot demand, no rental supply) | Telegram + email + draft a TRACE campaign |

**Cooldown:** a dress won't re-alert at the same level for 7 days — it only re-fires if it **escalates** a level (🟡 → 🔴) or re-accelerates after cooling. Keeps the signal high and the channel quiet. *(`diff.py` implements the threshold logic; this tiering + cooldown is the policy layer on top.)*

## The scorecard (real data)
| Dress | Trend | Opportunity | TikTok views | Saves | Fresh(14d) | Pickle (style) |
|---|--:|--:|--:|--:|--:|--:|
| House of CB Sculpt | 80.0 | 80.0 | 43,247,910 | 507,719 | 0.12 | 799 (0) |
| Aritzia Giggle | 22.1 | 22.1 | 3,242,395 | 59,252 | 0.90 | 763 (0) |
| Réalisation Par Cora | 5.4 | 0.8 | 6,941,217 | 25,107 | 0.15 | 800 (78) |

*Trend = 0.5·views + 0.3·saves + 0.2·freshness (min-max normalized). Opportunity = Trend × supply-gap.*

## What each signal proves — and doesn't (responsible inference)
- **TikTok views** = attention, **not** purchase intent. **Saves** ≈ "I want this" (stronger). **Freshness** (share of posts <14d) = momentum.
- **Pickle** has no views/saves — supply only. A listing **disappearing** ≈ rented/sold, but could be a lender delisting → treat as noisy velocity.
- **ShopMy** = buy-intent: a creator linking the product + its click count; `num_promoters` = how many creators link it across *all* of ShopMy (catalog-wide breadth). Measured across a 14-creator sample.
- **Absence** is informative: high demand + zero rental supply = a demand-organizing opportunity.

## Tradeoffs & what's uncertain (and how I handled it)
- **TikTok keyword-search is down** (the actor's search sorting is "under maintenance"), so I scraped by **hashtags** instead. Product-level isolation is reliable only for Cora; Giggle/Sculpt are tracked at brand level.
- **Homonym pollution:** naive caption matching caught false positives — "cora" → *a dog / a horror film*, "sculpt" → *Pilates classes*, "giggle" → nothing (no dedicated tag). I flag this rather than trust it; brand-level heat is the sounder signal, and Sculpt's Trend is *over-estimated* by `#thesculpt` Pilates noise.
- **Pickle's on-site search is fuzzy** — a search for "giggle" returns *ski goggles* (603 "items"). So I measured supply from each brand's listing page with **exact style-name matching**, and used **scroll-until-stable** to beat the 280-item scroll cap → "0 of 763 / 0 of 799" is now catalog-wide, not a sample.
- **Momentum diff** needs two *comparable* full scrapes; `diff.py` proves the capability, but live signal comes from running it daily.
- **ShopMy is creator-sampled** — I scraped 14 fashion creators' recent picks (via Apify), so coverage is directional, not exhaustive; 3 handles didn't resolve and keyword matches need care (a stray "sculpt" pick was a false match). `num_promoters` gives a catalog-wide breadth check per product (the Cora shows 991).
- **Google-Trends seasonality** is the remaining next step.
- **Inverse-search extraction is heuristic** (brand list + regex) — it catches *named* brands but misses captions that don't name one; an LLM/NER pass would resolve exact SKUs far better (the code leaves that hook). A live run still surfaced **Nadine Merabi (~9.2M views) as a 🆕 NEW candidate** the radar wasn't told to watch.
- **Style matching is word-aware + fuzzy** (`match.py`); switching from naive substring left the supply counts unchanged (0 / 0 / 78), confirming the gaps aren't a matching artifact.
- **Scoring** uses min-max over only 3 items, which squashes the middle (Cora scores low despite 6.9M views). It stabilizes as `discover.py` surfaces more dresses — and the production version would use **percentile ranks against a rolling 30-day baseline** (accumulated by `run_daily.py`'s dated snapshots), removing the small-N compression artifact entirely.

## What the radar surfaces next
Pickle's most-listed rental brands (proven demand) include **Retrofete, De La Vali, House of CB** — a natural place to find the *next* convergence dress if one is also rising on TikTok.

## How to run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && playwright install chromium
cp .env.example .env          # add APIFY_TOKEN
python -m radar.discover        # inverse search: surface NEW trending dresses
python -m radar.pickle_scraper aritzia/dresses realisation-par/dresses house-of-cb/dresses
python -m radar.tiktok_signals
python -m radar.shopmy_signals   # -> data/shopmy_<date>.json  (buy-intent)
python -m radar.score         # -> data/radar_<date>.md
python -m radar.diff          # -> data/diff_<date>.md  (run daily for momentum)

# — or run the entire pipeline in one command (logs to data/logs/, cron-friendly):
python -m radar.run_daily            # add --loop to repeat every 24h
```
> `.env` (APIFY_TOKEN) is git-ignored. Pickle is scraped politely (throttled, headless).
