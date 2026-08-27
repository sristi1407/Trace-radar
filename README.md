# TRACE Demand & Liquidity Radar — Proof of Concept
*Sristi Prasad · Applied AI Engineering Exercise · Aug 2026*

**▶ [Live dashboard](https://htmlpreview.github.io/?https://github.com/sristi1407/Trace-radar/blob/main/dashboard.html)** — interactive; each dress links out to TikTok · ShopMy · Pickle · the product page. *(Or open `dashboard.html` from the repo in a browser.)*

> **Thesis:** TikTok tells you *what's gaining desire*, ShopMy *resolves that desire to a buyable product*, and Pickle tells you *whether that item actually has rental supply*. Combining present **and absent** signals reveals where TRACE should concentrate demand — sometimes *before* rental supply exists.

> **How this was built (honest note):** this is a lightweight PoC. I care more about showing *how I investigate an ambiguous problem, make tradeoffs, and reason about what's reliable* than about a polished system. Limitations are called out throughout — that's deliberate.

---

## TL;DR — findings
Three currently-trending dresses, chosen to show three *different* patterns for TRACE. **TikTok numbers are the specific dress** (posts that actually name it), with brand-tag traffic shown only as context — because *brand heat ≠ product demand*.

| Dress (brand) | TikTok (the dress) | ShopMy (buy-intent) | Pickle (supply) | Pattern → what TRACE should do |
|---|---|---|---|---|
| **House of CB — The Sculpt** | **4.9M views · 19 creators** (top demand) | thin in creator sample | **0 of 799** | **Scarcity gap** → build the market: recruit owners *before* supply exists |
| **Réalisation Par — The Cora** | 1.0M views · 29 creators | **69.5K clicks · 991 creators link it** | **78 of 800** | **Convergence** → match renters/buyers to owners *now* |
| **Nadine Merabi — Nina Gold** | 1.8M views · 24 creators (brand-level) | featured on ShopMy (clicks not sampled) | **10 Nina rentals** (gold from $60) | **High-value liquidity** → monetize the signature SKU |

### The exact products (specific styles, not just brands)
- **House of CB — "The Sculpt" bandage dress** (halter; mini + midi) — part of the limited-edition Bandage Collection ("once sold out, no restock"). *Trends across colorways (black + nude/gold).*
- **Réalisation Par — "The Cora," _Mirage_ colorway** — silk bias-cut, multicolour-striped midi with a cowl neck + detachable half-slip (~$330–375). *(realisationpar.com/the-cora-mirage)*
- **Nadine Merabi — the "Nina Gold" dress** — the signature gold sequin SKU of a British "wedding-guest" event label (~$300–600 retail); **10 copies rentable on Pickle (gold from $60)**, [product page](https://www.us.nadinemerabi.com/products/nina-gold-dress). *The radar discovered this brand on its own (see below) and I promoted it into the watchlist.*

> Note: the Pickle supply counts (0 / 78 / 10) are **style-specific** — matched on the exact style name in listing titles across all 799 / 800 / 602 of each brand's dresses — so the supply signal is genuinely per-dress, not per-brand.

**The creators driving them** — Sculpt: `@suelamehmedi` (“bandage is so back @houseofcb”) + HOCB's large program. Cora: `@amirajasminnn`, `@nadiaorr_` (brand-tagged), `@lindleysavage`, `@sophcrump`. Nadine Merabi: `@kathjay89`, `@maisie_crompton`, `@alexxcoll`, `@kathryn.mueller` (wedding/bridal creators) — **these 24 are exactly who TRACE would contact to seed supply & buy-intent.**

---

## How I approached this (and the tradeoffs I made)
*The part that matters most: how I thought about an open-ended problem, not just the output.*

**Where I began.** TRACE's hardest problem is density / cold-start — on a *presale* marketplace, demand has to emerge *before* supply exists. So rather than boil the ocean, I started from the single most reliable, verifiable signal (**Pickle rental supply**), built outward to demand (**TikTok**) and buy-intent (**ShopMy**), and focused on a few *specific* trending dresses that could tell a clear story.

**Key tradeoffs — all deliberate:**
- **Depth over breadth** — one reliable TikTok → ShopMy → Pickle chain on 3 specific dresses, not a thin pass over hundreds. Prove the signal, don't sample everything shallowly.
- **Reliability over raw counts** — when TikTok keyword search was down I fell back to hashtags; when matching was brittle I made it word-aware + fuzzy; I measured supply from brand pages (reliable) instead of Pickle's fuzzy site search (which returns *ski goggles* for a "giggle" query).
- **Brand heat ≠ product demand** — my first third dress (an Aritzia style) had loud *brand-tag* traffic but **zero** posts about the specific dress. I dropped it rather than dress up brand noise as product demand, and made the dashboard headline the *specific-dress* signal with brand-tag as muted context. Then I let the radar's own inverse-search pick the replacement — **Nadine Merabi** — and validated it end-to-end (1.8M brand views, 24 creators, and its signature Nina Gold SKU with 10 rentable copies).
- **Human read over the model when a signal is noisy** — the scorecard ranks **Sculpt #1**, and I agree it's the biggest *build* opportunity, but its score is partly inflated by `#thesculpt` Pilates content, so I treat it as **validate-before-you-trust**. Knowing when *not* to trust your own number is the point.
- **Automate the highest-leverage piece** — I built the discovery + daily-diff + alerting loop, and *documented* (rather than built) the heavier production pieces (LLM relevance filtering, orchestration DAG, catalog API), to respect the "lightweight PoC" scope and the deadline.

**One insight the three dresses expose:** demand shows up at **different granularities**. Cora and Sculpt are *SKU-level* viral (one specific dress). Nadine Merabi's is *occasion-level* — people search "a Nadine Merabi for a wedding," not one SKU — so I measure its demand at the brand level but anchor it to its most-rented signature SKU, the Nina Gold. A real radar has to handle both, which is why matching granularity is a first-class design choice.

## Per-dress analysis — the 7 factors
Each dress evaluated across the factors the brief asks for:

| Factor | **The Sculpt** (House of CB) | **Cora** (Réalisation Par) | **Nadine Merabi** (occasionwear) |
|---|---|---|---|
| **Current heat** | **~4.9M dress views, 107K saves** (most viral) | ~1.0M dress views, 15K saves | ~1.8M dress views, 5K saves |
| **Momentum** | strong (brand tag 25% of posts <14d) | moderate (25% of posts <14d) | steady, wedding-season driven (22% <14d) |
| **Recency** | newest ~2 days ago | newest <1 day ago | newest this week |
| **Creator activity** | large program (suelamehmedi + HOCB influencers) | many & distinct (amirajasminnn, nadiaorr_, lindleysavage, sophcrump) | 24 wedding/bridal creators (kathjay89, maisie_crompton, alexxcoll…) |
| **Cross-platform breadth** | **TikTok-dominant** (ShopMy thin · not Pickle) | **all three** (TikTok ✓ · ShopMy ✓ · Pickle ✓) | TikTok ✓ · **Pickle ✓ (deep)** · ShopMy to-seed |
| **Commerce intent (ShopMy)** | **on ShopMy** (searchable), but not in our 14-creator sample | **strong — 69,540 clicks; 991 creators link the Cora** | **on ShopMy** (searchable); magnitude needs the wedding creators seeded |
| **Rental liquidity** | **0 of 799** HOCB dresses | **78 listings** on Pickle ($50–90/wk) — deep | **10 Nina Gold copies** (gold from $60) — liquid for one SKU |
| **→ Pattern** | **Scarcity gap** | **Convergence** | **High-value liquidity** |

**Product & evidence links** (all verified live):
- **The Sculpt:** [product](https://www.houseofcb.com/the-sculpt-black-bandage-mini-dress.html) · [Pickle — brand deep, 0 Sculpt](https://www.shoponpickle.com/shop/rent/house-of-cb/dresses) · [TikTok](https://www.tiktok.com/search?q=the%20sculpt%20bandage%20mini%20dress%20house%20of%20cb) *(#thesculpt is Pilates-polluted — I use a precise brand+style search)*
- **Cora:** [product](https://realisationpar.com/the-cora-mirage/) · [Pickle rentals (78)](https://www.shoponpickle.com/shop/rent/realisation-par/dresses) · [TikTok](https://www.tiktok.com/tag/coradress)
- **Nadine Merabi — Nina Gold:** [product](https://www.us.nadinemerabi.com/products/nina-gold-dress) · [Pickle rental ($60)](https://www.shoponpickle.com/product/0c69581d-803f-11ef-96eb-71bced824269) · [TikTok](https://www.tiktok.com/search?q=nadine%20merabi%20dress%20nina%20gold) · [ShopMy](https://shopmy.us/shop?query=nadine+merabi+dress+nina+gold&tab=popular) *(featured on ShopMy; click magnitude not in our 14-creator sample)*

## Recommendation for TRACE
1. **Build the wedge around The Sculpt (House of CB).** It has the loudest demand (~4.9M dress-level views) and **zero** rental supply of the trending style — exactly TRACE's presale play: *organize demand and recruit owners before conventional supply exists.* **⚠️ Validate first:** the `#thesculpt` tag is contaminated by Pilates content, so I'd treat its #1 scorecard rank as an **upper bound** and confirm the true dress-share with an LLM relevance pass (below) before committing spend.
2. **Capture immediate liquidity with the Cora (Réalisation Par).** Demand *and* 78 rental listings *and* the strongest measured buy-intent (**991 creators link it, 69.5K clicks**) already exist — so TRACE can match renters/buyers to owners **today**. This is the safest, proof-of-category play.
3. **Monetize the signature SKU — Nadine Merabi's Nina Gold.** 10 rentable copies (gold from **$60**) plus real wedding-guest demand (1.8M brand views, 24 creators) = **high GMV per rental**. Onboard the 24 discovered creators to light up ShopMy buy-intent and close the loop.
4. **The absence of a Pickle listing is a buy signal, not a dead end** — Sculpt is where TRACE *creates* the market; Cora and Nadine Merabi are where it *monetizes* one that already exists.

---

## Vision — what this becomes for TRACE
Today this is a daily radar over a watchlist. The natural product it points to:

1. **One-click, any-product intelligence.** Paste any product (or a link) → instantly see its cross-platform pulse: who's posting it (TikTok), who's linking/buying it (ShopMy), and whether it's rentable (Pickle) — with a Trend + Opportunity score. *(The PoC already does this for a watchlist; generalizing the product resolver makes it one-click for anything.)*
2. **Always-on viral detection.** Continuously watch for **any** item spiking on **any** platform — a post crossing a view/velocity threshold, a jump in ShopMy clicks, or Pickle listings vanishing fast — and alert TRACE the moment something starts accelerating. *(`diff.py` + `score.py` are the seed of this; the Telegram hook is the alert channel.)*
3. **Celebrity / big-creator triggers.** Weight the signal by reach — when a high-follower creator or a celebrity is seen wearing or linking an item, fire an instant alert. That moment is often the *spark* of a trend, and catching it early is the whole game.
4. **The attraction loop (why it grows TRACE).** The instant something goes viral, notify interested users — *"this dress is blowing up — presale or reserve it on TRACE now."* That converts fleeting attention into locked-in demand and directly attacks TRACE's cold-start problem: you **organize demand around a product before supply exists.**

In one line: *watch demand across the web, catch it while it's accelerating, and pull buyers, renters, and owners together around the exact item — automatically.*

### Hardening it for daily reliability
Running this daily surfaced failure modes I'd engineer around next — all drawn directly from what broke during this build:

- **Signal pollution → LLM relevance filtering.** Keyword/hashtag matching misfires on homonyms ("sculpt" → Pilates classes, "cora" → a dog / a horror film) and on brand-vs-product ambiguity. Fix: pass each candidate caption through a cheap LLM (gpt-4o-mini / Gemini Flash) — *"does this video actually feature and recommend THIS dress? Ignore Pilates, pets, and generic brand mentions"* — to produce a clean per-video **`confidence_score`** instead of trusting raw counts. (This is exactly why I lead with the human read over the raw scorecard, and why I dropped a brand-only third dress in favor of a validated one.)
- **Keyword-search outages → fallback chaining.** TikTok's keyword search was down during this build, so I fell back to hashtags. In production I'd chain further: the brand's **official account feed** + the feeds of the **top ~50 ShopMy creators**. A **co-occurrence trigger** — the brand posts a style *and* ≥3 creators post the same style within 48h — is a stronger, more reliable signal than raw hashtag volume anyway.
- **Dynamic creator discovery (loop now wired).** Trends come from *new* creators, not a fixed list. `discover.py` emits the high-engagement creators it finds, and `shopmy_signals.py --from-discover` scrapes them automatically — a self-expanding feedback loop: **TikTok finds the creator → ShopMy reads their links → Pickle checks the products.** This loop is exactly how Nadine Merabi went from *discovered* → *tracked* (below). (Handle resolution is best-effort — TikTok and ShopMy usernames don't always match — which the fuller version would reconcile via ShopMy's search API.)
- **Catalog-wide validation, not just a sample.** Pull breadth metrics (e.g. the Cora's 991 promoters) from ShopMy's product search / sitemap rather than the 14-creator sample, and take a **weekly per-brand catalog baseline** (House of CB, Réalisation Par, Nadine Merabi, Retrofete) so buy-intent is measured against *all* linked products.
- **Orchestration + state (make it a real daily job).** Wrap the pipeline in a Prefect/Dagster DAG (scrape → resolve → score → diff → alert) with **atomic, dated snapshots + a `_SUCCESS` marker**. `diff.py` then compares only *complete* runs — so a half-failed scrape can't produce a false zero-delta (exactly the apples-to-oranges failure I hit diffing a capped snapshot against a full one).

### Open questions I'd pressure-test next
- **ShopMy resolution is best-effort.** TikTok and ShopMy handles don't always match. Refinements: a manual **handle-mapping table** for high-value creators, plus a **product-name search fallback** — if a creator can't be resolved, search ShopMy for the dress name directly (which I already do for the watchlist). *(This is the open gap on Nadine Merabi: strong TikTok + Pickle, ShopMy buy-intent still to be seeded from the discovered creators.)*
- **LLM relevance filtering has real tradeoffs.** Filtering 1,000+ captions/day adds up even on gpt-4o-mini — so I'd set a **budget**, run it **async/batched** (never blocking the pipeline), and validate it against a small **labeled caption set**. At scale, a fine-tuned lightweight classifier (e.g. DistilBERT) may beat per-call LLM cost + latency.
- **False negatives are the harder problem.** Today I guard against false *positives* (Pilates → "Sculpt"); I'd still *miss* a trending dress if the caption doesn't name the brand, the hashtag isn't in my list, or search is down. The co-occurrence trigger (brand posts + ≥3 creators in 48h) helps; the fuller fix is an LLM that **infers the product from context** even when it isn't explicitly named.

## How it works (architecture)
```
discover.py ─ [INVERSE SEARCH] trending hashtags → extract brand/product → surface NEW viral dresses
      │        (feeds the watchlist automatically — this is how Nadine Merabi was found)
      ▼
TikTok  (Apify)      ─ demand: views, saves, freshness/momentum (specific-dress + brand-tag context)
ShopMy  (Apify)      ─ buy-intent: creator links + clicks + #promoters per product
Pickle  (Playwright) ─ supply: rental listings (word-aware + fuzzy match, match.py)
      │
      ▼
score.py ─ Trend Score + Opportunity Score      diff.py ─ [AUTOMATED] daily diff → alert on momentum
      │
      ▼
dashboard.py ─ single-page visual UI (dashboard.html); each card links all 3 platforms
```

## What I automated, and why
Two recurring pieces, both designed to run daily:

1. **Inverse-search discovery (`discover.py`) — the headline.** Instead of checking a known watchlist, it scrapes trending fashion hashtags (`#fashionhaul`, `#grwm`, `#weddingguestdress`…), extracts brand/product mentions from captions, and surfaces *emerging* dresses **not on any watchlist**. A live run flagged **Nadine Merabi at ~9.2M views as 🆕 NEW** — which I then **promoted into the watchlist and validated end-to-end** (1.8M brand views, 24 creators, signature Nina Gold SKU with 10 rentable copies). The very next run then shows it as `(tracked)` and surfaces the *next* wave — **Revolve (7.4M), Norma Kamali (2.6M), Cult Gaia (1.1M)**. This is the "alert TRACE when *any* dress goes viral" engine: **discovery, not just monitoring — and the discover→track loop closing in one build.**
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
| Dress | Trend | Opportunity | TikTok views (the dress) | Saves | Creators | Pickle (style) |
|---|--:|--:|--:|--:|--:|--:|
| House of CB Sculpt | 100.0 | 100.0 | 4,860,807 | 107,287 | 19 | 799 (0) |
| Réalisation Par Cora | 22.9 | 3.4 | 1,035,725 | 14,838 | 29 | 800 (78) |
| Nadine Merabi — Nina Gold | 9.4 | 3.3 | 1,756,181 | 5,003 | 24 | 602 (10) |

*Trend = 0.5·views + 0.3·saves + 0.2·freshness (min-max normalized). Opportunity = Trend × supply-gap — so dresses that already have supply (Cora, Nadine Merabi) score low on **Opportunity** by design: they're **monetize-now**, not build-the-market. Sculpt's Trend is an upper bound (Pilates noise).*

## What each signal proves — and doesn't (responsible inference)
- **TikTok views** = attention, **not** purchase intent. **Saves** ≈ "I want this" (stronger). **Freshness** (share of posts <14d) = momentum. I headline the **specific-dress** signal and show brand-tag traffic only as context — *brand heat is not product demand.*
- **Pickle** has no views/saves — supply only. A listing **disappearing** ≈ rented/sold, but could be a lender delisting → treat as noisy velocity.
- **ShopMy** = buy-intent: a creator linking the product + its click count; `num_promoters` = how many creators link it across *all* of ShopMy (catalog-wide breadth). Measured across a 14-creator sample.
- **Absence** is informative: high demand + zero rental supply = a demand-organizing opportunity.

## Tradeoffs & what's uncertain (and how I handled it)
- **TikTok keyword-search is down** (the actor's search sorting is "under maintenance"), so I scraped by **hashtags** and split each dress into *brand-tag* vs *this-dress* (caption actually names the style). Product-level isolation is clean for Cora; Sculpt's this-dress count still carries some Pilates noise; and Nadine Merabi's demand is measured at the brand level (the Nina Gold SKU is the supply anchor).
- **Homonym pollution:** naive caption matching caught false positives — "cora" → *a dog / a horror film*, "sculpt" → *Pilates classes*. I flag this rather than trust it, and it's why Sculpt's Trend is an over-estimate. The dashboard's TikTok links pick the best target per dress — a clean dress tag where one exists (`#coradress`, `#nadinemerabi`), or a precise brand+style search where the tag is unusable (`#thesculpt` is Pilates; `#giggledress` doesn't even exist).
- **Brand heat vs product demand:** an early third pick (an Aritzia style) had big brand-tag traffic but **0** posts about the specific dress, so I dropped it. The radar's own inverse search surfaced **Nadine Merabi** as the replacement, which I validated across all three platforms.
- **Pickle's on-site search is fuzzy** — a "giggle" search returns *ski goggles*. So I measured supply from each brand's listing page with **exact style-name matching**, and used **scroll-until-stable** to beat the ~280-item scroll cap → "0 of 799 / 78 of 800 / 10 of 602" is catalog-wide, not a sample.
- **Momentum diff** needs two *comparable* full scrapes; `diff.py` proves the capability, but live signal comes from running it daily.
- **ShopMy is creator-sampled** — I scraped 14 fashion creators' recent picks (via Apify), so coverage is directional, not exhaustive; `num_promoters` gives a catalog-wide breadth check per product (the Cora shows 991). Nadine Merabi's buy-intent needs the 24 discovered wedding creators seeded in.
- **Inverse-search extraction is heuristic** (brand list + regex) — it catches *named* brands but misses captions that don't name one; an LLM/NER pass would resolve exact SKUs far better (the code leaves that hook).
- **Style matching is word-aware + fuzzy** (`match.py`); switching from naive substring left the supply counts unchanged, confirming the gaps aren't a matching artifact.
- **Scoring** uses min-max over only 3 items, which squashes the middle. It stabilizes as `discover.py` surfaces more dresses — and the production version would use **percentile ranks against a rolling 30-day baseline** (accumulated by `run_daily.py`'s dated snapshots), removing the small-N compression artifact entirely.

## What the radar surfaces next
Pickle's most-listed rental brands (proven demand) include **Retrofete, De La Vali, House of CB** — and inverse search is already pointing at **Revolve, Norma Kamali, Cult Gaia** — a natural place to find the *next* convergence dress if one is also rising on TikTok.

## How to run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && playwright install chromium
cp .env.example .env          # add APIFY_TOKEN
python -m radar.discover        # inverse search: surface NEW trending dresses
python -m radar.pickle_scraper house-of-cb/dresses realisation-par/dresses nadine-merabi/dresses
python -m radar.tiktok_signals
python -m radar.shopmy_signals   # -> data/shopmy_<date>.json  (buy-intent)
python -m radar.score         # -> data/radar_<date>.md
python -m radar.diff          # -> data/diff_<date>.md  (run daily for momentum)

# — or run the entire pipeline in one command (logs to data/logs/, cron-friendly):
python -m radar.run_daily            # add --loop to repeat every 24h

python -m radar.dashboard            # -> dashboard.html (visual UI; open in a browser)
```
> `.env` (APIFY_TOKEN) is git-ignored. Pickle is scraped politely (throttled, headless).
