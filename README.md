# TRACE Demand & Liquidity Radar — Proof of Concept
*Sristi Prasad · Applied AI Engineering Exercise · Aug 2026*

**▶ [Live dashboard](https://sristi1407.github.io/Trace-radar/dashboard.html)** — interactive; each dress links out to TikTok · ShopMy · Pickle · the product page. *(Served via GitHub Pages; or open `dashboard.html` from the repo in a browser.)*

> **Thesis:** TikTok tells you *what's gaining desire*, ShopMy *resolves that desire to a buyable product*, and Pickle tells you *whether that item actually has rental supply*. Combining present **and absent** signals reveals where TRACE should concentrate demand — sometimes *before* rental supply exists.

> **How this was built (honest note):** this is a lightweight PoC. I care more about showing *how I investigate an ambiguous problem, make tradeoffs, and reason about what's reliable* than about a polished system. Limitations are called out throughout — that's deliberate.

---

## TL;DR — findings
Three dresses, three *different* patterns for TRACE. **TikTok demand is brand-anchored** — I require the brand name in the caption, because style words alone are homonym-ridden. That single choice is the headline finding: it exposed that one dress's apparent **4.9M "demand" was 100% Pilates** ("sculpt" the workout, not the House of CB dress), which flipped my own scorecard's #1.

| Dress (brand) | TikTok (brand-anchored) | ShopMy (buy-intent) | Pickle (supply) | Pattern → what TRACE should do |
|---|---|---|---|---|
| **Nadine Merabi — Nina Gold** | **1.8M views · 24 creators** (top, all real) | on ShopMy ([product](https://shopmy.us/shop?query=nadine+merabi+dress+nina+gold&tab=popular)) | **10 Nina rentals** ($60–119) | **High-value convergence** → the strongest play; onboard the creators |
| **Réalisation Par — The Cora** | 245K views · 10 creators | **34.7K lifetime clicks · 991 promoters** *(recent ≈ 0)* | **76 of 800** | **Convergence** → match renters/owners now (proven demand, now cooling) |
| **House of CB — The Sculpt** | **0 confirmed** — its 4.9M was 100% Pilates | — | 0 of 798 | **Signal contamination** → the homonym trap; real demand needs brand-anchored/LLM capture |

### The exact products (specific styles, not just brands)
- **House of CB — "The Sculpt" bandage dress** (halter; mini + midi). The dress is real and viral (see the brand+style [TikTok search](https://www.tiktok.com/search?q=the%20sculpt%20bandage%20mini%20dress%20house%20of%20cb)), **but our hashtag capture (`#thesculpt`) was 100% Pilates** — 0 posts survive brand-anchoring — so we can't quantify its demand from this sample. That's the cautionary finding; the fix (now in the code) is to anchor capture on the brand, not the style word.
- **Réalisation Par — "The Cora," _Mirage_ colorway** — silk bias-cut, multicolour-striped midi with a cowl neck + detachable half-slip (~$330–375). *(realisationpar.com/the-cora-mirage)*
- **Nadine Merabi — the "Nina Gold" dress** — the signature gold sequin SKU of a British "wedding-guest" event label (~$300–600 retail); **10 copies rentable on Pickle (gold from $60)**, [product page](https://www.us.nadinemerabi.com/products/nina-gold-dress). *The radar discovered this brand on its own (see below) and I promoted it into the watchlist.*

> Note: the Pickle supply counts (0 / 76 / 10) are **style-specific** — matched on the exact style name in listing titles across all 798 / 800 / 603 of each brand's dresses — so the supply signal is genuinely per-dress, not per-brand. They're **point-in-time and wobble a listing or two between scrapes** (the Cora read 78 one day, 76 the next) — that's the page-rotation sampling my `diff.py` guard exists to catch, not real churn.

**The creators driving them (brand-anchored, verified):** Nadine Merabi — `@kathjay89` (108K), `@kathryn.mueller` (139K), `@omolabbake`. Cora — `@courtneyyyyy__`, `@amirajasminnn`, `@jaderselise` (55K). Sculpt — **none survive brand-anchoring** (every "sculpt" post was Pilates), which is itself the finding. These are exactly who TRACE would contact to seed supply & buy-intent.

---

## How I approached this (and the tradeoffs I made)
*The part that matters most: how I thought about an open-ended problem, not just the output.*

**Where I began.** TRACE's hardest problem is density / cold-start — on a *presale* marketplace, demand has to emerge *before* supply exists. So rather than boil the ocean, I started from the single most reliable, verifiable signal (**Pickle rental supply**), built outward to demand (**TikTok**) and buy-intent (**ShopMy**), and focused on a few *specific* trending dresses that could tell a clear story.

**Key tradeoffs — all deliberate:**
- **Depth over breadth** — one reliable TikTok → ShopMy → Pickle chain on 3 specific dresses, not a thin pass over hundreds. Prove the signal, don't sample everything shallowly.
- **Reliability over raw counts** — when TikTok keyword search was down I fell back to hashtags; when matching was brittle I made it word-aware + fuzzy; I measured supply from brand pages (reliable) instead of Pickle's fuzzy site search (which returns *ski goggles* for a "giggle" query).
- **Brand heat ≠ product demand** — my first third dress (an Aritzia style) had loud *brand-tag* traffic but **zero** posts about the specific dress. I dropped it rather than dress up brand noise as product demand, and made the dashboard headline the *specific-dress* signal with brand-tag as muted context. Then I let the radar's own inverse-search pick the replacement — **Nadine Merabi** — and validated it end-to-end (1.8M brand views, 24 creators, and its signature Nina Gold SKU with 10 rentable copies).
- **I caught my own #1 was noise — the headline finding.** An earlier scorecard ranked **Sculpt #1 at 4.9M views**. Brand-anchoring the TikTok match (requiring "House of CB", not just the word "sculpt") revealed that traffic was **100% Pilates** — 0 real dress posts in the sample. The real ranking is Nadine Merabi, then Cora; Sculpt is a cautionary tale. Building the check that catches your own top metric being wrong is the point.
- **Automate the highest-leverage piece** — I built the discovery + daily-diff + alerting loop, and *documented* (rather than built) the heavier production pieces (LLM relevance filtering, orchestration DAG, catalog API), to respect the "lightweight PoC" scope and the deadline.

**Two insights the three dresses expose:** (1) **style words are homonym magnets** — "sculpt" is a Pilates move, "cora" is a person / a black cat / prison slang — so demand only means something when it's *brand-anchored*. (2) Demand shows up at **different granularities**: the Cora is a specific viral SKU, while Nadine Merabi is *occasion-level* (people search "a Nadine Merabi for a wedding," not one SKU). A real radar has to handle both — which is why matching (brand vs. style, SKU vs. occasion) is a first-class design choice, not an afterthought.

## Per-dress analysis — the 7 factors
Each dress evaluated across the factors the brief asks for:

| Factor | **Nadine Merabi** (Nina Gold) | **Cora** (Réalisation Par) | **The Sculpt** (House of CB) |
|---|---|---|---|
| **Current heat (brand-anchored)** | **~1.8M dress views, 24 creators** (top) | ~245K views, 10 creators | **0 confirmed** — the 4.9M "sculpt" traffic was 100% Pilates |
| **Momentum (per-post velocity)** | needs a 2nd comparable snapshot | **+2.1% over 2d** (12 shared posts, +2.5K views/day) | n/a — 0 real posts |
| **Creator activity (verified)** | @kathjay89 (108K), @kathryn.mueller (139K), @omolabbake | @courtneyyyyy__, @amirajasminnn, @jaderselise (55K) | **none survive brand-anchoring** (all Pilates) |
| **Cross-platform breadth** | TikTok ✓ · Pickle ✓ · ShopMy (searchable) | **all three** (TikTok ✓ · ShopMy ✓ · Pickle ✓) | capture failed (homonym) · Pickle 0 |
| **Commerce intent (ShopMy)** | on ShopMy (searchable); seed the 24 creators | **proven — ~34.7K _lifetime_ clicks, 991 promoters** (pinned by @sophcrump, @nadiaorr → [product](https://shopmy.us/shop/product/2128245)); **recent ≈ 0** — real but cooling | — |
| **Rental liquidity** | **10 Nina Gold copies** ($60–119) | **76 of 800** ($50–90/wk) — deep | 0 of 798 |
| **→ Pattern** | **High-value convergence** | **Convergence** | **Signal contamination** |

**Product & evidence links** (all verified live):
- **The Sculpt:** [product](https://www.houseofcb.com/the-sculpt-black-bandage-mini-dress.html) · [Pickle — brand deep, 0 Sculpt](https://www.shoponpickle.com/shop/rent/house-of-cb/dresses) · [TikTok brand+style search](https://www.tiktok.com/search?q=the%20sculpt%20bandage%20mini%20dress%20house%20of%20cb) *(#thesculpt is **100% Pilates** — 0 posts survive brand-anchoring; the dress is real but our hashtag pipeline couldn't isolate it)*
- **Cora:** [product](https://realisationpar.com/the-cora-mirage/) · [Pickle rentals (76)](https://www.shoponpickle.com/shop/rent/realisation-par/dresses) · [TikTok](https://www.tiktok.com/tag/coradress) · [ShopMy product](https://shopmy.us/shop/product/2128245)
- **Nadine Merabi — Nina Gold:** [product](https://www.us.nadinemerabi.com/products/nina-gold-dress) · [Pickle rental ($60)](https://www.shoponpickle.com/product/0c69581d-803f-11ef-96eb-71bced824269) · [TikTok](https://www.tiktok.com/search?q=nadine%20merabi%20dress%20nina%20gold) · [ShopMy](https://shopmy.us/shop?query=nadine+merabi+dress+nina+gold&tab=popular) *(featured on ShopMy; click magnitude not in our 14-creator sample)*

## Creators to recruit (the other half of the ask)
The brief weights creators alongside dresses. These three are already *driving* the tracked dresses — pulled straight from the scraped TikTok data (reach = follower count where the scrape captured it; post = their top video on that dress, linked):

| Creator | Dress | Reach | Top post (views · date) | Why recruit |
|---|---|---|---|---|
| **[@kathjay89](https://www.tiktok.com/@kathjay89)** | Nadine Merabi | **108K** | [859K · Aug 2026](https://www.tiktok.com/@kathjay89/video/7670613372982840598) | Tags @Nadine Merabi directly; wedding-guest occasion where it rents at $60–119 → high-GMV. |
| **[@kathryn.mueller](https://www.tiktok.com/@kathryn.mueller)** | Nadine Merabi | **139K** | [160K · Jun 2026](https://www.tiktok.com/@kathryn.mueller/video/7652755088863202591) | "Dress is @Nadine Merabi!" — biggest reach of the set; second seed for the top-demand dress. |
| **[@courtneyyyyy__](https://www.tiktok.com/@courtneyyyyy__)** | Réalisation Par — Cora | 2.4K | [81K · Aug 2026](https://www.tiktok.com/@courtneyyyyy__/video/7675101137422372110) | Names "Realisation P@r Cora" directly; the Cora is already liquid (76 rentals) → match-now partner. |

Every creator above **explicitly names the brand** (that's the brand-anchoring filter — no bridal-gown or Pilates false matches). **Sculpt has none** — every "sculpt" creator was Pilates, which is the finding, not an omission.

**How I'd action them:** ask each to link the product on **ShopMy** (so buy-intent becomes measurable, not just inferred). This list isn't hand-curated — `discover.py` regenerates it daily from whoever's actually driving engagement, so it stays current.

## Supply density — where it actually is (size & city)
The brief names **sizes** and locations as density dimensions. Every Pickle listing carries both at ~100% fill, so this is free (`radar/density.py`):

| Brand | Listings | Top cities | Size skew |
|---|--:|---|---|
| **Réalisation Par** | 724 | **NYC 69%** · LA/CA 15% · FL 3% | S/XS = **66%** (S×281 · XS×201) |
| **House of CB** | 693 | **NYC 46%** · LA/CA 18% · TX 8% | S/XS = **71%** (S×292 · XS×203) |
| **Nadine Merabi** | 231 | **NYC 42%** · LA/CA 16% · TX 7% | S/XS = **63%** (S×84 · XS×61) |

**Two things TRACE can act on:** (1) supply is **NYC-first** across all three (42–69%) — so a presale/matching launch should start in NYC metro, where renter *and* owner liquidity already co-locate. (2) Supply skews hard to **S/XS (63–71%)** — so M+ renters are structurally underserved, a concrete gap to recruit owners against. (The Nina Gold's 10 copies mirror this: XS/S/S/S/M/L/6/6/8, four in NYC metro, rents $60–119.)

## Recommendation for TRACE
1. **Lead with Nadine Merabi's Nina Gold — the top *real* demand.** 1.8M brand-anchored views, 24 creators, and 10 rentable copies ($60–119) → the strongest all-round play. Onboard the 24 discovered creators to light up ShopMy and match wedding-guest renters to owners now.
2. **Capture the Cora (Réalisation Par) as proven-but-cooling liquidity.** 245K demand, 76 rentals, and the strongest lifetime buy-intent (**991 promoters, ~34.7K clicks**) all exist → match renters to owners today. Own the caveat: recent monthly clicks ≈ 0, so this is *activating an existing pool*, not chasing a live spike.
3. **Treat "The Sculpt" as a cautionary tale, not a pick.** It topped an earlier scorecard at 4.9M — but brand-anchoring showed that was **100% Pilates**. The dress is genuinely viral (manual brand+style search confirms), but our hashtag pipeline couldn't isolate it, so I won't spend on it until brand-anchored/LLM capture can measure the real signal. The check that caught this is now in the pipeline.
4. **The absence of a signal is informative** — a Pickle zero is a build opportunity; a "demand" number that's 100% homonym is a trap. Distinguishing the two is the whole job.
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
- **Orchestration + state (now scheduled, not just described).** A **GitHub Action** ([`.github/workflows/daily.yml`](.github/workflows/daily.yml)) runs the whole pipeline every morning, commits the **atomic dated snapshots** (which accumulate the rolling 30-day baseline the percentile scoring needs), and **regenerates `dashboard.html` in CI** — so "recurring" is verifiable to a reviewer, and the README/scorecard/dashboard can't drift apart again. At larger scale this graduates to a Prefect/Dagster DAG with a `_SUCCESS` marker so `diff.py` compares only *complete* runs (guarding the apples-to-oranges failure I hit diffing a capped snapshot against a full one).

### Open questions I'd pressure-test next
- **ShopMy resolution is best-effort.** TikTok and ShopMy handles don't always match. Refinements: a manual **handle-mapping table** for high-value creators, plus a **product-name search fallback** — if a creator can't be resolved, search ShopMy for the dress name directly (which I already do for the watchlist). *(This is the open gap on Nadine Merabi: strong TikTok + Pickle, ShopMy buy-intent still to be seeded from the discovered creators.)*
- **LLM relevance filtering has real tradeoffs.** Filtering 1,000+ captions/day adds up even on gpt-4o-mini — so I'd set a **budget**, run it **async/batched** (never blocking the pipeline), and validate it against a small **labeled caption set**. At scale, a fine-tuned lightweight classifier (e.g. DistilBERT) may beat per-call LLM cost + latency.
- **False negatives are the harder problem.** Today I guard against false *positives* (Pilates → "Sculpt"); I'd still *miss* a trending dress if the caption doesn't name the brand, the hashtag isn't in my list, or search is down. The co-occurrence trigger (brand posts + ≥3 creators in 48h) helps; the fuller fix is an LLM that **infers the product from context** even when it isn't explicitly named.

## How it works (architecture)
```
discover.py ─ [INVERSE SEARCH] trending hashtags → extract brand/product → surface NEW viral dresses
      │        (feeds the watchlist automatically — this is how Nadine Merabi was found)
      ▼
TikTok  (Apify)      ─ demand: views, saves (brand-anchored — see brand_terms; kills homonyms)
ShopMy  (Apify)      ─ buy-intent: creator links + clicks + #promoters per product
Pickle  (Playwright) ─ supply: rental listings (word-aware + fuzzy match, match.py)
      │
      ▼
score.py ─ Trend + Opportunity      velocity.py ─ per-post Δviews/day (demand momentum)
      │                              diff.py ─ Pickle turnover (supply momentum, overlap-guarded)
      │
      ▼
dashboard.py ─ single-page visual UI (dashboard.html); each card links all 3 platforms
```

## What I automated, and why
Two recurring pieces, both designed to run daily:

1. **Inverse-search discovery (`discover.py`) — the headline.** Instead of checking a known watchlist, it scrapes trending fashion hashtags (`#fashionhaul`, `#grwm`, `#weddingguestdress`…), extracts brand/product mentions from captions, and surfaces *emerging* dresses **not on any watchlist**. A live run flagged **Nadine Merabi at ~9.2M views as 🆕 NEW** — which I then **promoted into the watchlist and validated end-to-end** (1.8M brand views, 24 creators, signature Nina Gold SKU with 10 rentable copies). The very next run then shows it as `(tracked)` and surfaces the *next* wave — **Revolve (7.4M), Norma Kamali (2.6M), Cult Gaia (1.1M)**. This is the "alert TRACE when *any* dress goes viral" engine: **discovery, not just monitoring — and the discover→track loop closing in one build.**
2. **Momentum — measured two ways, both guarded (`velocity.py` + `diff.py`).** For *demand* momentum, `velocity.py` intersects consecutive TikTok snapshots **by post id** and computes Δviews/day on the *same* posts — a real acceleration curve, not the flat freshness proxy (the Cora's 12 shared posts grew **+2.1% in two days**; Sculpt has 0 real posts; Merabi awaits its 2nd snapshot). For *supply* momentum, `diff.py` diffs Pickle — but I found Pickle's brand pages serve a **rotating subset** (~33% listing overlap), so it **suppresses turnover unless snapshots genuinely overlap** rather than firing "half the inventory rented overnight." Same comparability principle applied to both diffs. `score.py` re-ranks after each run.

Together they demonstrate a credible path to a system that **refreshes daily, detects momentum, and alerts**. *(Bonus findings that made this work: Pickle's web is server-rendered/scrapable — richer than the brief assumed — so supply needs no API key; and style matching is word-aware + fuzzy (`match.py`), so counts are robust to title variants.)*

### Alert policy
Alerts are tiered, with a per-dress cooldown so nothing spams daily:

| Level | Trigger (on **raw** signals, not the normalized score) | Action |
|---|---|---|
| 🟢 **Discovery** | `discover.py` finds a *new* product with **> 1M views** | Log + daily digest |
| 🟡 **Momentum** | a tracked dress's **raw views or saves rise > 30% day-over-day** (from the dated snapshots), or its Pickle supply drops ≥ 3 | Telegram `#trending` |
| 🔴 **Gap** | **> 2M raw views** (trailing) **and** Pickle style-supply = 0 | Telegram + email + draft a TRACE campaign |

> **Why raw, not the Trend score:** the Trend score is min-max *normalized within each run*, so the top dress is always ~100 and the bottom ~0 — a threshold like "Trend > 70" would fire on whatever's #1 that day, and day-over-day deltas would be dominated by set composition, not real movement. So alerts key off **absolute raw signals** (views, saves, listing counts) from the dated snapshots; the normalized score is only for *within-run ranking*. (Once `run_daily`/the Action accumulate a 30-day baseline, these become percentile triggers.)

**Cooldown:** a dress won't re-alert at the same level for 7 days — it only re-fires if it **escalates** a level (🟡 → 🔴) or re-accelerates after cooling. Keeps the signal high and the channel quiet. *(`diff.py` implements the threshold logic; this tiering + cooldown is the policy layer on top.)*

## The scorecard (real data)
| Dress | Trend | Opportunity | TikTok views (the dress) | Saves | Creators | Pickle (style) |
|---|--:|--:|--:|--:|--:|--:|
| Nadine Merabi — Nina Gold | 95.2 | 33.3 | 1,756,181 | 5,003 | 24 | 603 (10) |
| Réalisation Par Cora | 37.4 | 5.6 | 245,891 | 1,726 | 10 | 800 (76) |
| House of CB Sculpt | 0.0 | 0.0 | 0 | 0 | 0 | 798 (0) |

*Trend = 0.5·views + 0.3·saves + 0.2·freshness (min-max normalized). Opportunity = Trend × supply-gap — so dresses that already have supply (Cora, Nadine Merabi) score low on **Opportunity** by design: they're **monetize-now**, not build-the-market. Sculpt's Trend is an upper bound (Pilates noise).*

> **Owning the scoring:** demand is **brand-anchored**, so the ranking reflects *real* dress mentions — Nadine Merabi (1.8M) > Cora (245K) > Sculpt (**0**, all Pilates). Freshness (~0.22) barely differentiates, so Trend is volume-led; with N=3 the weights matter far less than the brand-anchoring that makes the volume real in the first place. That's why the *recommendation* leans on the pattern (convergence vs. contamination), not the raw number — and why Sculpt's old 100 was a red flag, not a result.

## What each signal proves — and doesn't (responsible inference)
- **TikTok views** = attention, **not** purchase intent. **Saves** ≈ "I want this" (stronger). **Freshness** (share of posts <14d) = momentum. I headline the **specific-dress** signal and show brand-tag traffic only as context — *brand heat is not product demand.*
- **Pickle** has no views/saves — supply only. A listing **disappearing** ≈ rented/sold, but could be a lender delisting → treat as noisy velocity.
- **ShopMy** = buy-intent: a creator linking the product + its click count; `num_promoters` = how many creators link it across *all* of ShopMy (catalog-wide breadth). Measured across a 14-creator sample.
- **Absence** is informative: high demand + zero rental supply = a demand-organizing opportunity.

## Tradeoffs & what's uncertain (and how I handled it)
- **TikTok keyword-search is down** (the actor's search sorting is "under maintenance"), so I scraped by **hashtags** and split each dress into *brand-tag* vs *this-dress* (caption actually names the style). Product-level isolation is clean for Cora; Sculpt's this-dress count still carries some Pilates noise; and Nadine Merabi's demand is measured at the brand level (the Nina Gold SKU is the supply anchor).
- **Homonym pollution — the core signal-validity fix.** Style words are homonyms: "cora" is also a person / a black cat / prison slang; "sculpt" is a Pilates move. Crucially, **whole-word or fuzzy matching does *not* fix this** — Pilates captions contain the whole word "sculpt" — so I brand-anchor instead: a post counts only if it names the brand (`brand_terms` in the watchlist). That dropped Sculpt from a fake **4.9M → 0** (all Pilates) and Cora from 1.0M → a clean **245K**, and it's what surfaced that my own scorecard's #1 was noise. The dashboard's TikTok links similarly use brand+style searches, not the raw `#thesculpt` tag.
- **Brand heat vs product demand:** an early third pick (an Aritzia style) had big brand-tag traffic but **0** posts about the specific dress, so I dropped it. The radar's own inverse search surfaced **Nadine Merabi** as the replacement, which I validated across all three platforms.
- **Pickle's on-site search is fuzzy** — a "giggle" search returns *ski goggles*. So I measured supply from each brand's listing page with **exact style-name matching**, and used **scroll-until-stable** to beat the ~280-item scroll cap → "0 of 798 / 76 of 800 / 10 of 603" is catalog-wide, not a sample.
- **Momentum diff is guarded, not asserted.** Pickle's brand pages return a *rotating subset* — two same-depth scrapes share only ~33% of listings — so a naive UUID-diff over-reports turnover badly (I measured 53–67% "disappeared" with total counts *flat*, which can't be real rentals). `diff.py`'s comparability guard suppresses those and reports turnover only where snapshots overlap ≥70% (Nadine Merabi's 1-day pair passed → a genuine 10%). Trustworthy rental velocity needs a stable per-listing ID or the inventory feed, not the paginated page.
- **ShopMy is creator-sampled** — I scraped 14 fashion creators' recent picks (via Apify), so coverage is directional, not exhaustive; `num_promoters` gives a catalog-wide breadth check per product (the Cora shows 991). Nadine Merabi's buy-intent needs the 24 discovered wedding creators seeded in.
- **A double-count I caught in my own headline metric.** `total_clicks` on a ShopMy pick is a *per-product lifetime* figure, so when two creators pin the same product, summing over picks double-counts. I fixed it at the source — `summarize()` now dedupes per product — which dropped the Cora's clicks from an inflated **69.5K → the real 34.7K**, and re-derived both snapshots from the persisted picks (not a hand-edit). The **more telling** number is `monthly_clicks ≈ 0`: the Cora's lifetime buy-intent is real, but the click spike has passed — so I frame it as *activating existing liquidity*, not a live surge.
- **Inverse-search extraction is heuristic** (brand list + regex) — it catches *named* brands but misses captions that don't name one; an LLM/NER pass would resolve exact SKUs far better (the code leaves that hook).
- **Style matching is word-aware** (`match.py`, with a fuzzy fallback available). To be precise: whole-word matching *alone* produced the counts here — the fuzzy path didn't need to fire — and switching from naive substring left them unchanged, confirming the gaps aren't a matching artifact. `score.py` **and** `diff.py` both use `match.py`, so "cora" never matches "coral"/"decorated" on either path.
- **Scoring** uses min-max over only 3 items, which squashes the middle. It stabilizes as `discover.py` surfaces more dresses — and the production version would use **percentile ranks against a rolling 30-day baseline** (accumulated by the daily Action's dated snapshots), removing the small-N compression artifact entirely.
- **Data sourcing & ToS (flagging for a build/buy call).** Every signal except Google Trends is scraper-based — TikTok & ShopMy via Apify actors, Pickle via headless Playwright — which runs against the letter of those platforms' terms. For a rate-limited PoC that's a deliberate tradeoff; for production I'd move to **official rails** (TikTok's API / partner program, ShopMy's API, a direct Pickle integration) before shipping. Not a blocker for a prototype, but a real cost to price in.

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
python -m radar.diff          # -> data/diff_<date>.md   (Pickle supply turnover, overlap-guarded)
python -m radar.velocity      # -> data/velocity_<date>.md (per-post demand momentum)
python -m radar.density       # -> data/density_<date>.md  (size & city breakdown)

# — or run the entire pipeline in one command (logs to data/logs/):
python -m radar.run_daily            # add --loop to repeat every 24h
# (In CI this runs daily via .github/workflows/daily.yml — add APIFY_TOKEN as a repo secret.)

python -m radar.dashboard            # -> dashboard.html (visual UI; open in a browser)
```
> `.env` (APIFY_TOKEN) is git-ignored. Pickle is scraped politely (throttled, headless).
