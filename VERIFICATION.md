# Verification Log — Line-by-Line No Hallucinations

This file is the authoritative verification log. Every claim in docs/index.html and code must have a source here.

## Method
- Fetched live on 2026-09-22 UTC via fetch_page and web_search tools
- Each claim requires URL that directly states claim
- If no direct source, flag as irregular/inference
- All sources stored in src/data/sources_verified.json

## 2026-09-22 Re-Verification Pass (this session)

Every source was re-fetched live with `fetch_page`/`web_search`. Corrections applied where the site had moved/redirected since the original build:

1. **Founder/rebrand claims** — `who-is-awesemo-what-is-stokastic` now redirects to the homepage. Re-sourced: rebrand to the "I started Awesemo.com (now Stokastic.com)" statement in how-to-win-dfs-tournaments; founder background to the RotoGrinders interview (WashU St. Louis, pro poker). The "Mathematics, WashU 2008" degree claim was replaced with the verified wording ("attended Washington University in St. Louis"; degree not restated on the live page).
2. **Contest-level sim uniqueness** — old `/stokastic-nfl-faq/` redirects. Re-sourced verbatim to the pricing-page FAQ.
3. **Sim workflow quotes** — old `/join-stokastic-all-access...` redirects. Re-sourced to pricing-page FAQ + stokastic-vs-fantasylabs (both fetched live).
4. **Implied team total** — old `/nba/how-to-use-vegas-odds...` redirects. Re-sourced to the DST-strategy article's worked example (44 total, -7 => 25.5/18.5).
5. **DK scoring** — old DK Network / DK Nation article links redirect/404. Re-sourced to official `draftkings.com/help/rules/1-4`, which state every number identically.
6. **Pricing** — the pricing page defaults to the Stokastic-avatar toggle. Corrected to show list ($329.95/$449.95/$849.95) vs avatar-discounted ($229.95/$349.95/$599.95). Older builds listed the avatar prices as if list.
7. **"millions of data points"** — lived on a now-redirecting page. Re-sourced to live copy ("tens of thousands of simulated contests" + play-by-play correlation) in stokastic-vs-fantasylabs; flagged.
8. **Sim ROI bug** — `simulation_engine.py` demo produced ~21,000% Sim ROI because field lineups were generated from a pool the same size as the roster (every field lineup tied the user lineup). Fixed with a realistic payout curve, pool larger than roster, and a guard that raises when pool size == lineup size.

## Verified Claims (24 lines)

| # | Claim | Source URL | Status |
|---|-------|------------|--------|
| 1 | Stokastic domain is stokastic.com | https://www.stokastic.com/ | verified |
| 2 | Formerly Awesemo.com | https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments | verified |
| 3 | Founder Alex Baker — WashU St. Louis, ex-pro poker | https://rotogrinders.com/articles/interview-with-alex-awesemo-baker-1964792 | verified |
| 4 | #1 ranked RotoGrinders overall 2017-2021 | https://x.com/AwesemoDFS (bio) + https://rotogrinders.com/articles/interview-with-alex-awesemo-baker-1964792 | verified |
| 5 | Projections run high-level simulations many times | https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system | verified |
| 6 | Contest Sims simulate contest tens of thousands times, ranking by ROI | https://www.stokastic.com/articles/nfl-dfs/stokastic-review | verified |
| 7 | Correlations hold: QB big game drags receivers | https://www.stokastic.com/articles/nfl-dfs/stokastic-review | verified |
| 8 | Boom/Bust: Ceiling 75th, Floor 25th, Boom% smash, Bust% dud | https://www.stokastic.com/articles/dfs-strategy/dfs-boom-bust-probability + https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy | verified |
| 9 | Ownership forecast = % of entries rostering player, map of field behavior | https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections | verified |
| 10 | MLB chalk follows Vegas implied totals, ballpark, pitching matchups | https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections | verified |
| 11 | Value formula = FP - (Salary/1000*5) | https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections | verified |
| 12 | Pts/$ = FP / Salary *1000 | https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections | verified |
| 13 | Minutes first, no minutes no production, NBA volume-driven | https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections | verified |
| 14 | Usage = share possessions player finishes | https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections | verified |
| 15 | Cash vs GPP need opposite builds | https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments | verified |
| 16 | Late swap biggest edge in NBA | https://www.stokastic.com/articles/dfs-strategy/how-to-win-draftkings-dfs | verified |
| 17 | Props bottom-up from player data and simulation, vs 15+ books, X-Win/X-ROI/Hold | https://www.oddsshopper.com/props + https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system | verified |
| 18 | DK NBA scoring: 1 pt, 0.5 3pt bonus, 1.25 reb, 1.5 ast, 2 stl/blk, -0.5 TO, 1.5 DD, 3 TD | https://www.draftkings.com/help/rules/4 | verified |
| 19 | FD Rules page contains official scoring | https://www.fanduel.com/rules | verified |
| 20 | MLB Statcast is official tracking tech, installed 2015, Hawk-Eye 2020 | https://www.mlb.com/glossary/statcast | verified |
| 21 | NBA stats sources ranked: nba_api free wrapper around stats.nba.com | https://nbaanalytic.com/articles/free-basketball-data-sources-ranked.html + https://github.com/swar/nba_api | verified |
| 22 | All-Access pricing: list $329.95/$449.95/$849.95; avatar $229.95/$349.95/$599.95 (snapshot 2026-09-22) | https://www.stokastic.com/pricing | verified + dynamic flagged |
| 23 | Exact projection weights proprietary | No public formula found — flagged as proprietary | irregular flagged |
| 24 | Ownership model algorithm developed over years by Alex Baker | https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments | verified |

## Irregularities Flagged for Review

1. **Pricing dynamic + avatar default** — Pricing page uses coupon gating, changes seasonally, and defaults to the Stokastic-avatar discount toggle. Snapshot taken 2026-09-22 (both toggles recorded). Manual reviewer should re-fetch https://www.stokastic.com/pricing live. Flagged in site with orange banner.

2. **Projection weights proprietary** — Stokastic does not publish exact weights. We use industry-standard heuristic (minutes 40%, usage 25%, matchup 20%, recent form 10%, other 5%). Flagged as inference, not leak.

3. **Historical ownership private** — True ownership accuracy requires private contest history. We proxy with optimal% + salary. Need to purchase historical data for production. Flagged in limitations.

4. **Correlation matrix not public** — True correlations require play-by-play joint distributions. We use heuristic 0.6 QB-WR, 0.3 WR-WR, etc. Flagged as inference, need to compute from nflverse in next session.

## No Hallucinations Check

- All sources have URL starting http
- All sources have verifies field describing what it proves
- No source invented — each fetched via fetch_page tool live
- See src/data/sources_verified.json for machine-readable list

## Manual Review Links

All links in docs/index.html bibliography are clickable. Reviewer can click each to verify claim.

Last verified: 2026-09-22 UTC
