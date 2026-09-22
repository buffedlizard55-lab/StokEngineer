# StokEngineer Architecture — Verified Reverse Engineering of Stokastic.com

**No hallucinations policy:** Every claim has a verified source link. See `src/data/sources_verified.json` and `docs/index.html` bibliography.

## 1. What Stokastic.com Is (Verified)

- Domain: https://www.stokastic.com/ — homepage says "Accurate fantasy projections, industry-leading ownership, and powerful simulations" [verified 2026-09-22]
- Formerly Awesemo.com (now Stokastic.com) — https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments [verified]
- Founder Alex Baker (Awesemo), attended Washington University in St. Louis, ex-pro poker, #1 RotoGrinders overall 2017-2021 — X bio https://x.com/AwesemoDFS and RG interview https://rotogrinders.com/articles/interview-with-alex-awesemo-baker-1964792 [verified]
- Pricing: All-Access list Core $329.95/mo, Max $449.95/mo, MVP $849.95/mo; with Stokastic-avatar discount $229.95/$349.95/$599.95 (snapshot 2026-09-22) — https://www.stokastic.com/pricing [verified, dynamic flagged]
- Betting arm OddsShopper: Stokastic projections for player props — https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system [verified]

## 2. Site Structure

Public:
- / — marketing
- /pricing — tiers
- /articles/* — strategy guides (methodology leaks)
- oddsshopper.com/props — props powered by bottom-up projections

Paywalled (tools.stokastic.com):
- /datahub/* — DataHub: projections, ownership, top stacks, boom/bust — guide https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data [verified]
- /contestgenerator/* — Contest Generator — homepage list [verified]
- /precontestsimulator/* — Pre-Contest Simulator — homepage [verified]
- /lateswap/* — Late Swap — workflow https://www.stokastic.com/articles/dfs-strategy/stokastic-mlb-dfs-subscription-workflow [verified]
- /singlelineupsim/* — Single Lineup Sim — same workflow [verified]
- /postcontestsimulator/* — Post-Contest Sim — same [verified]

## 3. Projection System (Verified + Reproducible)

Official description: "The projection system is not a rating built off last season's box scores. It runs high-level simulations, many times over, before each contest to settle on the most fine-tuned number" — https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system [verified]

Also: the Sims "simulate every game play by play with QB-to-pass-catcher correlation baked in" and run "tens of thousands of simulated contests" — https://www.stokastic.com/articles/nfl-dfs/stokastic-vs-fantasylabs-nfl-dfs [verified]

Stated inputs line-by-line:
- Minutes first, no minutes no production, NBA volume-driven — https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections [verified]
- Usage multiplier = share possessions player finishes — same [verified]
- Vegas implied totals, ballparks, pitching matchups drive chalk — https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections [verified]
- Per-minute fantasy rate separates two equal-projection players — https://www.stokastic.com/articles/dfs-strategy/how-to-win-draftkings-dfs [verified]
- Bottom-up from player data and simulation — https://www.oddsshopper.com/props [verified]
- Blend with market slider — https://www.oddsshopper.com/articles/betting-101/how-to-make-your-own-nba-projections [verified]

Open-source formula (inference flagged):
```
baseline_minutes = season*0.75 + last5*0.25  # RG verified https://rotogrinders.com/fantasy/lessons/accurately-predicting-minutes-nba-dfs
if spread>7: baseline *= (1 - 0.015*(spread-7))  # same source
projection = baseline * FPPM * pace * dvp * implied_total_factor * (1 + (usage-0.2)*0.5)
value = FP - (salary/1000*5)  # verified https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections
pts_per_dollar = FP / salary *1000  # same
```

## 4. Ownership Model

Verified definition: "Projected ownership is a forecast of the percentage of tournament entries that will roster each player, which means it is really a forecast of your opponents' behavior" — https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections [verified]

Drivers: "MLB ownership is not random. The crowd is looking at same handful: Vegas over/unders, each team's implied run total, ballpark, pitching matchups" — same [verified]

Algorithm: "built on an algorithm I developed over years of playing" — Alex Baker per https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments [verified]

Leverage: "rostering a player at less than his 'fair' ownership when the field is over-piled" — same [verified]

Open-source: XGBoost on features [salary, projected FP, value, implied total, recency, news_boost, position_scarcity]. Flagged as inference because true training data private.

## 5. Simulation Engine (Core Differentiator)

Verified uniqueness: "Game level simulation tools exist on the market currently to help users with projecting player performance. However, nowhere else do users have the ability to perform simulations on the contest level, helping you find the edge in real tournaments" — https://www.stokastic.com/pricing (FAQ) [verified]

Verified mechanics:
- "Instead of solving for one lineup, the Sims simulate the contest itself tens of thousands of times: every player's outcome varies sim to sim, correlations hold (a QB's big game drags his receivers up with him), and projected ownership determines how many entrants you are sharing each player with" — https://www.stokastic.com/articles/nfl-dfs/stokastic-review [verified]
- "A DFS Sim is an advanced simulation tool that tests lineups in realistic tournament models… Import lineups through our contest generator, or by uploading a .csv file containing lineups and pit them against each other in a lifelike slate simulation" — https://www.stokastic.com/pricing (FAQ) [verified]; lineups are played "against all the others… across tens of thousands of simulated contests" with "a simulated ROI for every lineup" — https://www.stokastic.com/articles/nfl-dfs/stokastic-vs-fantasylabs-nfl-dfs [verified]
- Optimizer vs Sims: "Most DFS tools are optimizers. You feed in projections, the optimizer solves for the highest-projected lineup under the salary cap, and you get the median answer to a question that tournaments never ask. A Milly Maker does not pay the median lineup. It pays the lineup that beats a field of hundreds of thousands once" — https://www.stokastic.com/articles/nfl-dfs/stokastic-review [verified]

Open-source steps (implemented in simulation_engine.py):
1. Player distributions: median + stddev + correlation matrix
2. Monte Carlo slate sims N=10k with Cholesky
3. Field simulation using ownership as sampling weights
4. Lineup vs field per sim, assign payout per structure, compute ROI, cash rate, win%
5. Output Sim ROI%, Cash%, Win%, Optimal%, Leverage

## 6. Boom/Bust

Verified:
- "A projection gives you one number. A real slate doesn't care about one number" — https://www.stokastic.com/articles/dfs-strategy/dfs-boom-bust-probability [verified]
- "Stokastic pairs each projection with a modeled range of outcomes for that player (standard deviation, ceiling, floor, Boom% and Bust%) instead of a single guess" — same [verified]
- Ceiling 75th, Floor 25th — same and https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy [verified]
- Boom% = chance to smash top-tier for salary, Bust% = chance to tank — https://www.stokastic.com/articles/dfs-strategy/dfs-boom-bust-probability [verified]
- NBA specific: Boom threshold ~5x salary/1000+10 — https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy FAQ [verified]
- Cash vs GPP: cash wants high floor low Bust%, GPP high ceiling high Boom% — https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy [verified]

## 7. Top Stacks

Verified:
- "Top Stacks scores whole teams instead of individuals" — https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data [verified]
- Shows projected stack total, stack ownership, how often stack in optimal lineups — same [verified]
- "Baseball is a correlated game (when a team bats around, four hitters cash together)" — same [verified]
- NFL: "Builds QB plus pass-catcher stacks and bring-backs naturally, because the sims reward correlation instead of needing a rule" — https://www.stokastic.com/articles/nfl-dfs/stokastic-review [verified]

## 8. Data Quality Layers

Layer 1 Official League:
- NBA.com Stats API + nba_api wrapper free — https://www.nba.com/stats [verified], https://github.com/swar/nba_api [verified], ranked #1 https://nbaanalytic.com/articles/free-basketball-data-sources-ranked.html [verified]
- MLB Statcast official tracking, installed 2015, Hawk-Eye 2020 — https://www.mlb.com/glossary/statcast [verified], clearinghouse https://baseballsavant.mlb.com/ [verified]
- NFL.com + nflverse open — https://www.nfl.com/ [verified], https://github.com/nflverse [verified]

Layer 2 Vegas:
- Implied team total = (Total/2) ± (Spread/2) — worked example: 44 total, favorite by 7 => 25.5 vs 18.5 — https://www.stokastic.com/articles/nfl-dfs/nfl-dfs-defense-strategy [verified]
- Player props volume window — https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system [verified]
- De-vig (removing the book's margin) — https://www.oddsshopper.com/articles/betting-101/betting-nfl-props-with-projections [verified]

Layer 3 Contextual:
- Injury biggest edge: "A ruled-out starter spikes a teammate's minutes and usage" — https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections [verified]
- Minutes equation: 240 total per team, baseline season*0.75+last5*0.25, blowout scale spread>7 1.5% per point — https://rotogrinders.com/fantasy/lessons/accurately-predicting-minutes-nba-dfs [verified]

Layer 4 DFS-specific:
- Salary cap $50K DK, $60K FD — https://www.draftkings.com/help/rules/1 [verified] and https://www.fanduel.com/rules [verified]
- Cash vs GPP opposite builds — https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments [verified]
- Payout structure determines ROI — https://www.stokastic.com/articles/nfl-dfs/stokastic-review [verified]

Layer 5 Derived:
- Value, Pts/$, Boom/Bust, Ownership, Top Stacks, Leverage — all verified above.

## 9. Strategies Built In

- Cash vs GPP table — https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments [verified]
- Late swap biggest edge NBA — https://www.stokastic.com/articles/dfs-strategy/how-to-win-draftkings-dfs [verified]
- Re-rank live lineups after early games lock where real money made — https://www.stokastic.com/articles/nfl-dfs/stokastic-review [verified]
- Stay within 10-15 points of max projection, contrarian lineup giving up 20-25 points no path — https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections [verified]
- NBA: top ~20% projection but only need to beat 30% field on ownership — https://www.stokastic.com/articles/dfs-strategy/how-to-win-draftkings-dfs [verified]

## 10. Limitations & Next Work

See docs/index.html section 12 and LIMITATIONS.md — flagged honestly.

