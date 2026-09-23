window.STOKENGINEER_DATA = {
 "meta": {
  "version": "0.4.0",
  "generated_at": "2026-09-23T01:23:17+00:00",
  "git_revision": "8806323",
  "synthetic_reference": "Sample slates in src/data/samples are synthetic and labelled as such. They exist so the engine can be tested deterministically offline; they are not real salaries or real projections, and no report generated from them describes real players."
 },
 "status": {
  "registry_problems": [],
  "rules_problems": [],
  "tests": {
   "passed": 88,
   "failed": 0,
   "skipped": 0
  }
 },
 "sources": [
  {
   "id": "dk_rules_nfl",
   "url": "https://www.draftkings.com/help/rules/1",
   "title": "DraftKings Rules & Scoring - NFL Classic",
   "publisher": "DraftKings",
   "provides": "Official NFL Classic scoring table (pass TD 4, 0.04/pass yd, +3 at 300 pass yd, INT -1, rush/receiving TD 6, 0.1/yd, +3 at 100 yds, reception 1, return TD 6, fumble lost -1, 2-pt 2; DST sack 1, INT 2, fumble rec 2, return TD 6, safety 2, blocked kick 2, points-allowed tiers +10/+7/+4/+1/0/-1/-4), lineup requirements (9 players, >=2 games, 1 QB / 2 RB / 3 WR / 1 TE / 1 FLEX / 1 DST) and the $50,000 salary cap.",
   "licence": "DraftKings site terms; numbers are facts about their published contest rules.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "dk_rules_nba",
   "url": "https://www.draftkings.com/help/rules/4",
   "title": "DraftKings Rules & Scoring - NBA Classic",
   "publisher": "DraftKings",
   "provides": "Official NBA Classic scoring (point 1, made 3 +0.5, rebound 1.25, assist 1.5, steal 2, block 2, turnover -0.5, double-double +1.5, triple-double +3), lineup requirements (8 players, >=2 games, PG/SG/SF/PF/C/G/F/UTIL) and the $50,000 salary cap.",
   "licence": "DraftKings site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "dk_rules_mlb",
   "url": "https://www.draftkings.com/help/rules/2",
   "title": "DraftKings Rules & Scoring - MLB Classic",
   "publisher": "DraftKings",
   "provides": "Official MLB Classic scoring (1B 3, 2B 5, 3B 8, HR 10, RBI 2, R 2, BB 2, HBP 2, SB 5; P: IP 2.25 with 0.75/out, SO 2, W 4, ER -2, H -0.6, BB -0.6, HBP -0.6, CG 2.5, CGSO 2.5, NH 5), lineup requirements (10 players, >=2 games, no more than 5 hitters from one team, 2 P / C / 1B / 2B / 3B / SS / 3 OF) and the $50,000 salary cap.",
   "licence": "DraftKings site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "dk_rules_nhl",
   "url": "https://www.draftkings.com/help/rules/3",
   "title": "DraftKings Rules & Scoring - NHL Classic",
   "publisher": "DraftKings",
   "provides": "Official NHL Classic scoring (goal 8.5, assist 5, SOG 1.5, blocked shot 1.3, short-handed point 2, shootout goal 1.5, hat trick +3, 5+ shots +3, 3+ blocks +3, 3+ points +3; goalies: win 6, save 0.7, GA -3.5, shutout +4, OT loss 2, 35+ saves +3), lineup requirements (9 players, skaters from >=3 teams, 2 C / 3 W / 2 D / 1 UTIL / 1 G) and the $50,000 salary cap.",
   "licence": "DraftKings site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "fd_rules",
   "url": "https://www.fanduel.com/rules",
   "title": "FanDuel Rules & Scoring",
   "publisher": "FanDuel",
   "provides": "Official FanDuel scoring for every sport: NFL (0.5 PPR, 0.1/rec yd, +3 at 100 rec yds, 6 rec TD, 0.1/rush yd, +3 at 100 rush yds, 0.04/pass yd, +3 at 300 pass yds, 4 pass TD, -1 INT, fumble -2, 2-pt 2, FG 3/4/5, XP 1, DST table), MLB (1B 3, 2B 6, 3B 9, HR 12, RBI 3.5, R 3.2, BB 3, SB 6, HBP 3; P: W 6, QS 4, ER -3, SO 3, IP 3), NBA (3PM 3, 2PM 2, FT 1, REB 1.2, AST 1.5, BLK 3, STL 3, TO -1), NHL (G 12, A 8, SOG 1.6, SHP +2, PPP +0.5, BLK 1.6; goalies W 12, GA -4, SV 0.8, SO 8).",
   "licence": "FanDuel site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "fd_rules_gap",
   "url": "https://www.fanduel.com/rules",
   "title": "FanDuel rules page does not publish roster shapes or salary caps",
   "publisher": "FanDuel",
   "provides": "Negative result that matters: as of 2026-09-22 the official FanDuel rules page documents scoring only. There is no public official FanDuel page stating the classic roster shapes (QB/RB/RB/WR/WR/WR/TE/FLEX/DEF) or the $60,000 cap. fanduel.com/nfl-guide now redirects to FanDuel Research. Those values are therefore marked verified:third-party in src/data/roster_rules.json.",
   "licence": "FanDuel site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "sk_pricing",
   "url": "https://www.stokastic.com/pricing",
   "title": "Stokastic pricing and product FAQ",
   "publisher": "Stokastic",
   "provides": "All-Access price points shown with the Stokastic avatar toggle on (Core $229.95/mo, Max $349.95/mo, MVP $599.95/mo) and the contest-level simulation claim: 'Game level simulation tools exist on the market currently to help users with projecting player performance. However, nowhere else do users have the ability to perform simulations on the contest level'. Also the tier lineup limits (Core 2K; Max 5K NBA/MLB/CFB, 10K NFL/NASCAR/PGA/NHL classic, 50K NFL showdown; MVP 25K classic, 50K showdown).",
   "licence": "Stokastic site terms; quoted for commentary/criticism.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "sk_nfl_review",
   "url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review",
   "title": "Stokastic Review 2026 (written by Stokastic)",
   "publisher": "Stokastic",
   "provides": "Sim mechanics: 'the Sims simulate the contest itself tens of thousands of times: every player's outcome varies sim to sim, correlations hold (a QB's big game drags his receivers up with him), and projected ownership determines how many entrants you are sharing each player with. Every lineup that comes out is then ranked by simulated ROI against the real payout structure of the contest you tell it you are entering.' Also documents the percent-to-first setting, custom projection/ownership CSV upload, Late Swap ('re-rank your live lineups after the early games lock'), and sport-specific 2026 pricing (NFL Core $149.95/mo, Max $229.95/mo, MVP $349.95/mo).",
   "licence": "Stokastic site terms; quoted.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "sk_nba_boom_bust",
   "url": "https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy",
   "title": "NBA DFS Boom Bust: Read Ceiling And Floor Like A Pro",
   "publisher": "Stokastic (author Alex Baker)",
   "provides": "Boom/Bust definitions used by this engine: ceiling = 75th-percentile outcome, floor = 25th-percentile outcome, Boom = reaching about 5 x (salary/1000) + 10 fantasy points, Bust = falling short of 5 x (salary/1000); worked examples ($9,000 player clears value at ~45 and booms at ~55; $4,000 punt at ~20 and ~30). Also states that in basketball player-to-player correlation barely matters, and that Stokastic does not use Contest Sims for cash games.",
   "licence": "Stokastic site terms; quoted.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "sk_nba_projections",
   "url": "https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections",
   "title": "How To Use NBA DFS Projections To Build Better Lineups",
   "publisher": "Stokastic (author Josh Engleman)",
   "provides": "The two salary metrics this engine implements: Pts/$ = FP / Salary x 1000 (worked example 55 FP at $10,000 = 5.5) and Value = FP - (Salary / 1000 x 5) (worked example 55 - 50 = 5.0; the $5,800 guard at 32 FP = 3.0). Also: minutes come first, usage = share of a team's possessions a player finishes with a shot, a trip to the line, or a turnover, and same-day injury news is the biggest edge.",
   "licence": "Stokastic site terms; quoted.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "mlb_statsapi",
   "url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-09-21&hydrate=team,linescore",
   "title": "MLB Stats API (official, keyless)",
   "publisher": "MLB Advanced Media",
   "provides": "Official MLB game data: schedules, live feeds, box scores, and player season stats. Keyless. Verified live this session: the call above returned the real 2026-09-21 slate with gamePk 824787 (Blue Jays at Orioles) final 3-4. The response carries an MLB copyright notice pointing at http://gdx.mlb.com/components/copyright.txt - read it before redistributing.",
   "licence": "MLB Advanced Media terms; see http://gdx.mlb.com/components/copyright.txt",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "nflverse_data",
   "url": "https://github.com/nflverse/nflverse-data",
   "title": "nflverse-data (open NFL data releases)",
   "publisher": "nflverse (open source project, not the NFL)",
   "provides": "Free, no-key NFL datasets published as GitHub release assets: play-by-play (pbp), player stats, schedules (games.csv), snap counts, depth charts, weekly rosters, injuries, Next Gen Stats, FTN charting. Licence confirmed CC-BY-4.0 through the GitHub API this session.",
   "licence": "CC-BY-4.0 (confirmed via GitHub API 2026-09-22)",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "github_api"
  },
  {
   "id": "nflverse_schedules_asset",
   "url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv",
   "title": "nflverse schedules/games.csv release asset",
   "publisher": "nflverse",
   "provides": "One row per NFL game with teams, date/time, roof, surface, spread/total where available. Asset name verified through the GitHub API this session (tag 'schedules' exposes games.csv, games.csv.gz, games.parquet, games.qs, games.rds, timestamp.json).",
   "licence": "CC-BY-4.0",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "github_api"
  },
  {
   "id": "nflverse_player_stats_asset",
   "url": "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.csv",
   "title": "nflverse player_stats release asset",
   "publisher": "nflverse",
   "provides": "Per-player per-week NFL stat lines (used to build the empirical game-to-game variance and covariance the models are calibrated against). Asset naming verified via the GitHub API this session (player_stats_YYYY.csv / .csv.gz / .parquet / .qs / .rds).",
   "licence": "CC-BY-4.0",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "github_api"
  },
  {
   "id": "nflverse_injuries_asset",
   "url": "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2025.csv",
   "title": "nflverse injuries release asset",
   "publisher": "nflverse",
   "provides": "Weekly NFL injury report statuses (used as the context layer for availability adjustments). Asset naming verified via the GitHub API this session (injuries_YYYY.csv and parquet/qs/rds).",
   "licence": "CC-BY-4.0",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "github_api"
  },
  {
   "id": "nba_api",
   "url": "https://github.com/swar/nba_api",
   "title": "nba_api - Python client for stats.nba.com",
   "publisher": "swar (community), wrapping the official NBA stats endpoints",
   "provides": "Free, no-key access to the NBA's own stats endpoints (league dashboards, box scores, play-by-play). MIT licensed (confirmed via GitHub API this session). The upstream NBA endpoints are rate limited and occasionally flaky; the ingest layer caches and backs off.",
   "licence": "MIT (confirmed via GitHub API 2026-09-22)",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "github_api"
  },
  {
   "id": "espn_scoreboard",
   "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
   "title": "ESPN public scoreboard/odds feed",
   "publisher": "ESPN",
   "provides": "Keyless JSON for games, venues, scores and (where posted) betting odds including spread and total - the free path to implied team totals. Verified live this session: returned the real 2026 NFL regular season week 2 with Buffalo 41 - Detroit (2026-09-18). Not an official league API and not documented as a public API; use politely and cache.",
   "licence": "ESPN terms; undocumented public endpoint. Flagged as best-effort.",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "fetched_live"
  },
  {
   "id": "dk_lobby_api",
   "url": "https://www.draftkings.com/lobby/getcontests?sport=NFL",
   "title": "DraftKings public lobby JSON",
   "publisher": "DraftKings",
   "provides": "Keyless JSON listing live contests with entry fee (a), max entries (mec), prize pool (po) and the draft group id (dg) needed to pull that slate's player pool. Verified live this session (returned real NFL contests for the 2026-09-20 main slate, draft group 153769). This is an undocumented public endpoint; DraftKings' terms may restrict automated access. The engine treats it as best-effort and always accepts a user-supplied CSV instead.",
   "licence": "DraftKings site terms; automated access may be restricted - flagged as an irregularity.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "fetched_live"
  },
  {
   "id": "sk_home",
   "url": "https://www.stokastic.com/",
   "title": "Stokastic home page",
   "publisher": "Stokastic",
   "provides": "Product surface: projections, ownership, sims; links the tool suite (DataHub, Contest Generator, Pre-Contest Simulator, Single Lineup Simulator, Post-Contest Simulator, Late Swap) at tools.stokastic.com.",
   "licence": "Stokastic site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "carried_over"
  },
  {
   "id": "sk_boom_bust_probability",
   "url": "https://www.stokastic.com/articles/dfs-strategy/dfs-boom-bust-probability",
   "title": "DFS Boom Bust probability (general)",
   "publisher": "Stokastic",
   "provides": "General statement that a projection is the middle of a range and that Stokastic pairs each projection with a modelled range (standard deviation, ceiling, floor, Boom%, Bust%).",
   "licence": "Stokastic site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "carried_over"
  },
  {
   "id": "sk_mlb_ownership",
   "url": "https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections",
   "title": "MLB DFS ownership projections",
   "publisher": "Stokastic",
   "provides": "Ownership is a forecast of the percentage of tournament entries that will roster a player (i.e. a forecast of opponent behaviour), and chalk is driven by Vegas over/unders, implied run totals, ballparks and pitching matchups.",
   "licence": "Stokastic site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "carried_over"
  },
  {
   "id": "sk_mlb_datahub",
   "url": "https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data",
   "title": "How to use MLB DFS data (DataHub columns)",
   "publisher": "Stokastic",
   "provides": "DataHub column set (Name, Team, Salary, Position, Order, projected FP, Value, projected ownership) and the Top Stacks tool: team-level stacks with projected stack total, stack ownership and how often the stack lands in optimal lineups.",
   "licence": "Stokastic site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "carried_over"
  },
  {
   "id": "sk_nfl_defense",
   "url": "https://www.stokastic.com/articles/nfl-dfs/nfl-dfs-defense-strategy",
   "title": "NFL DFS defense strategy (implied team totals)",
   "publisher": "Stokastic",
   "provides": "The implied team total arithmetic implemented in rules.py: total/2 + spread/2 for the favourite, total/2 - spread/2 for the underdog (worked example 44 total with -7 giving 25.5 and 18.5).",
   "licence": "Stokastic site terms.",
   "free": true,
   "key_required": false,
   "official": true,
   "verification": "carried_over"
  },
  {
   "id": "os_projection_system",
   "url": "https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system",
   "title": "Stokastic projection system (OddsShopper, Stokastic's betting arm)",
   "publisher": "OddsShopper / Stokastic",
   "provides": "Description of the projection system as simulation-driven rather than a rating built off last season's box scores.",
   "licence": "OddsShopper site terms.",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "carried_over"
  },
  {
   "id": "rg_minutes_lesson",
   "url": "https://rotogrinders.com/fantasy/lessons/accurately-predicting-minutes-nba-dfs",
   "title": "Accurately predicting NBA minutes (RotoGrinders lesson)",
   "publisher": "RotoGrinders",
   "provides": "Third-party minutes heuristic used as the NBA minutes prior: 240 team minutes per game, baseline blending season minutes with recent minutes, and a blowout haircut as the spread grows. Not a Stokastic source and not official; labelled as an external prior.",
   "licence": "RotoGrinders site terms.",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "carried_over"
  },
  {
   "id": "rg_baker_interview",
   "url": "https://rotogrinders.com/articles/interview-with-alex-awesemo-baker-1964792",
   "title": "Interview with Alex 'Awesemo' Baker",
   "publisher": "RotoGrinders",
   "provides": "Founder background (Washington University in St. Louis, professional poker, DFS).",
   "licence": "RotoGrinders site terms.",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "carried_over"
  },
  {
   "id": "awesemo_x",
   "url": "https://x.com/AwesemoDFS",
   "title": "Alex Baker on X",
   "publisher": "X / Alex Baker",
   "provides": "Self-described ranking history ('2017-2021 #1 ranked overall for daily fantasy') and Stokastic cofounder status. Social profile: not machine-checkable, treat as a claim by the person, not a verified statistic.",
   "licence": "X terms.",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "carried_over"
  },
  {
   "id": "splashplay_review",
   "url": "https://splashplaypodcast.com/stokastic-review/",
   "title": "Third-party Stokastic review (2026)",
   "publisher": "Splash Play Podcast",
   "provides": "Independent commentary on tiers/price increases and the absence of a free trial. Third-party opinion, not evidence about Stokastic's internals.",
   "licence": "Site terms.",
   "free": true,
   "key_required": false,
   "official": false,
   "verification": "carried_over"
  },
  {
   "id": "optional_odds_api",
   "url": "https://the-odds-api.com/",
   "title": "The Odds API (optional, key required)",
   "publisher": "The Odds API",
   "provides": "Odds aggregation across books with a free monthly request quota. REQUIRES A SIGN-UP KEY, so per this project's rules it is optional only: nothing in the default pipeline calls it, and the keyless ESPN feed is the default odds path.",
   "licence": "Commercial terms; free tier with key.",
   "free": true,
   "key_required": true,
   "official": false,
   "verification": "carried_over"
  }
 ],
 "claims": [
  {
   "id": "c01",
   "claim": "Stokastic sells DFS projections, ownership projections and contest-level simulations for DraftKings and FanDuel.",
   "quote": "A DFS Sim is an advanced simulation tool that tests lineups in realistic tournament models to find how lineups perform against the field.",
   "status": "verified",
   "relevance": "Product scope we are rebuilding.",
   "source_id": "sk_pricing",
   "source_url": "https://www.stokastic.com/pricing",
   "source_title": "Stokastic pricing and product FAQ"
  },
  {
   "id": "c02",
   "claim": "Contest-level simulation is Stokastic's stated differentiator versus ordinary game-level simulators and optimizers.",
   "quote": "Game level simulation tools exist on the market currently to help users with projecting player performance. However, nowhere else do users have the ability to perform simulations on the contest level, helping you find the edge in real tournaments.",
   "status": "verified",
   "relevance": "Defines the core feature of src/stokengineer/simulate.py.",
   "source_id": "sk_pricing",
   "source_url": "https://www.stokastic.com/pricing",
   "source_title": "Stokastic pricing and product FAQ"
  },
  {
   "id": "c03",
   "claim": "Their simulation runs the contest tens of thousands of times, varies every player's outcome, holds correlations, and uses projected ownership to decide how many entrants you share a player with.",
   "quote": "the Sims simulate the contest itself tens of thousands of times: every player's outcome varies sim to sim, correlations hold (a QB's big game drags his receivers up with him), and projected ownership determines how many entrants you are sharing each player with",
   "status": "verified",
   "relevance": "Exact specification implemented by the contest simulator.",
   "source_id": "sk_nfl_review",
   "source_url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review",
   "source_title": "Stokastic Review 2026 (written by Stokastic)"
  },
  {
   "id": "c04",
   "claim": "Lineups are ranked by simulated ROI against the real payout structure of the contest the user says they are entering, including a percent-to-first style setting.",
   "quote": "Every lineup that comes out is then ranked by simulated ROI against the real payout structure of the contest you tell it you are entering ... the \"percent to first\" setting changes how the Sims value ceiling",
   "status": "verified",
   "relevance": "Drives simulate.py payout handling: payout structures are inputs, not hard-coded guesses.",
   "source_id": "sk_nfl_review",
   "source_url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review",
   "source_title": "Stokastic Review 2026 (written by Stokastic)"
  },
  {
   "id": "c05",
   "claim": "Users can override projections and ownership (CSV upload or manual edit) and re-run the sims.",
   "quote": "Upload a CSV with player name, projection and ownership, or edit single players by hand, and the Sims re-run on your numbers",
   "status": "verified",
   "relevance": "Our ingest layer accepts the same kind of user CSV, which is free and avoids paid feeds.",
   "source_id": "sk_nfl_review",
   "source_url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review",
   "source_title": "Stokastic Review 2026 (written by Stokastic)"
  },
  {
   "id": "c06",
   "claim": "Late Swap re-ranks live lineups after the early games lock.",
   "quote": "Re-rank your live lineups after the early games lock, which is where a lot of the real money gets made",
   "status": "verified",
   "relevance": "Implemented as optimizer locks + re-simulation in late-swap mode.",
   "source_id": "sk_nfl_review",
   "source_url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review",
   "source_title": "Stokastic Review 2026 (written by Stokastic)"
  },
  {
   "id": "c07",
   "claim": "Boom% and Bust% are salary-relative: boom is about 5 x (salary/1000) + 10 fantasy points, bust is falling short of 5 x (salary/1000).",
   "quote": "Success (\"boom\") is reaching about 5 x (salary/1000) + 10 fantasy points ... failure (\"bust\") is falling short of 5 x (salary/1000) ... a $9,000 player needs ~45 to clear value and ~55 to \"boom,\" while a $4,000 punt only needs ~20 and ~30.",
   "status": "verified",
   "relevance": "rules.boom_threshold / rules.bust_threshold and the boom/bust table.",
   "source_id": "sk_nba_boom_bust",
   "source_url": "https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy",
   "source_title": "NBA DFS Boom Bust: Read Ceiling And Floor Like A Pro"
  },
  {
   "id": "c08",
   "claim": "Ceiling is the 75th-percentile outcome; floor is the 25th-percentile outcome; the projection is the median of a distribution.",
   "quote": "Ceiling projection - the 75th-percentile outcome ... Floor projection - the 25th-percentile outcome",
   "status": "verified",
   "relevance": "Distribution percentiles reported by the models.",
   "source_id": "sk_nba_boom_bust",
   "source_url": "https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy",
   "source_title": "NBA DFS Boom Bust: Read Ceiling And Floor Like A Pro"
  },
  {
   "id": "c09",
   "claim": "Value = FP - (salary/1000 * 5) and Pts/$ = FP / salary * 1000.",
   "quote": "Value = Fantasy Projection - (Salary / 1,000 x 5) ... Points per dollar (Pts/$) ... Fantasy Points / Salary x 1,000",
   "status": "verified",
   "relevance": "rules.value() and rules.pts_per_dollar(); both are unit-tested against the article's worked numbers.",
   "source_id": "sk_nba_projections",
   "source_url": "https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections",
   "source_title": "How To Use NBA DFS Projections To Build Better Lineups"
  },
  {
   "id": "c10",
   "claim": "Minutes come first in NBA projection ('no minutes, no production') and usage is the share of a team's possessions a player finishes with a shot, a trip to the line, or a turnover.",
   "quote": "Minutes come first. No minutes, no production. ... Usage rate is the share of a team's possessions a player finishes with a shot, a trip to the line, or a turnover.",
   "status": "verified",
   "relevance": "NBA model is minutes-first with usage scaling.",
   "source_id": "sk_nba_projections",
   "source_url": "https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections",
   "source_title": "How To Use NBA DFS Projections To Build Better Lineups"
  },
  {
   "id": "c11",
   "claim": "In basketball, player-to-player correlation barely matters, which is why NBA plays are graded individually.",
   "quote": "in basketball, player-to-player correlation barely matters, so you can judge almost every play on its own merits",
   "status": "verified",
   "relevance": "Justifies a low cross-player correlation for NBA in the simulator while NFL/MLB get structural team factors.",
   "source_id": "sk_nba_boom_bust",
   "source_url": "https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy",
   "source_title": "NBA DFS Boom Bust: Read Ceiling And Floor Like A Pro"
  },
  {
   "id": "c12",
   "claim": "Stokastic does not use Contest Sims for cash games; it uses the highest-floor lineup for cash and the sims for GPPs.",
   "quote": "I do not run the Contest Sims for cash. The Sims and the simulated-tournament pool are a GPP tool.",
   "status": "verified",
   "relevance": "Our evaluator offers cash-mode (floor maximisation) and GPP-mode (sim ROI) separately.",
   "source_id": "sk_nba_boom_bust",
   "source_url": "https://www.stokastic.com/articles/nba-dfs/nba-dfs-boom-bust-strategy",
   "source_title": "NBA DFS Boom Bust: Read Ceiling And Floor Like A Pro"
  },
  {
   "id": "c13",
   "claim": "All-Access pricing displayed with the avatar toggle on is Core $229.95, Max $349.95, MVP $599.95 per month; sport-specific NFL pricing published 2026-09-22 is Core $149.95/mo, Max $229.95/mo, MVP $349.95/mo.",
   "quote": "Core All Access $229.95/mo ... Max All Access $349.95/mo ... MVP All Access $599.95/mo ... NFL Core $149.95 a month ... Max is $229.95 a month",
   "status": "flagged",
   "relevance": "Snapshot only. The pricing page defaults to the avatar-discounted toggle and prices change; re-read the live page before quoting.",
   "source_id": "sk_pricing",
   "source_url": "https://www.stokastic.com/pricing",
   "source_title": "Stokastic pricing and product FAQ"
  },
  {
   "id": "c14",
   "claim": "Tier lineup ceilings: Core 2K; Max 5K (NBA/MLB/CFB), 10K (NFL/NASCAR/PGA/NHL classic), 50K (NFL showdown); MVP 25K classic, 50K showdown.",
   "quote": "2K lineups ... 5K lineups for NBA, MLB, CFB, 10K lineups for NFL, Nascar, PGA, NHL classic, 50K lineups for NFL showdown, MMA ... 25K lineups for most classic slates, 50K lineups for Nascar, MMA, and all showdown slates",
   "status": "flagged",
   "relevance": "Scale target for our portfolio/sim engine; snapshot as of 2026-09-22.",
   "source_id": "sk_pricing",
   "source_url": "https://www.stokastic.com/pricing",
   "source_title": "Stokastic pricing and product FAQ"
  },
  {
   "id": "c15",
   "claim": "DraftKings NFL Classic pays 4 points per passing TD, 1 point per reception, +3 bonuses at 300 passing / 100 rushing / 100 receiving yards, and uses a $50,000 cap with 9 players from at least 2 games.",
   "quote": "Passing TD +4 Pts ... Reception +1 Pt ... 300+ Yard Passing Game +3 Pts ... Lineups will consist of 9 players and must include players from at least 2 different NFL games ... must not exceed the salary cap of $50,000",
   "status": "verified",
   "relevance": "Feeds src/data/scoring_rules.json and roster_rules.json.",
   "source_id": "dk_rules_nfl",
   "source_url": "https://www.draftkings.com/help/rules/1",
   "source_title": "DraftKings Rules & Scoring - NFL Classic"
  },
  {
   "id": "c16",
   "claim": "DraftKings NBA Classic scores 1.25 per rebound, 1.5 per assist, +1.5 for a double-double and +3 for a triple-double, with an 8-player roster from at least 2 games and a $50,000 cap.",
   "quote": "Rebound +1.25 Pts ... Assist +1.5 Pts ... Double-Double +1.5 Pts ... Triple-Double +3 Pts ... Lineups will consist of 8 players and must include players from at least 2 different NBA games",
   "status": "verified",
   "relevance": "Non-linear bonuses are why the NBA model samples full stat lines rather than scoring a mean.",
   "source_id": "dk_rules_nba",
   "source_url": "https://www.draftkings.com/help/rules/4",
   "source_title": "DraftKings Rules & Scoring - NBA Classic"
  },
  {
   "id": "c17",
   "claim": "DraftKings MLB Classic caps lineups at 5 hitters from any one team and pays 2.25 per inning pitched with 0.75 per out.",
   "quote": "Lineups must have no more than 5 hitters from any one team ... Inning Pitched +2.25 Pts (+0.75 Pts / Out)",
   "status": "verified",
   "relevance": "Implemented as max_hitters_per_team in the optimizer.",
   "source_id": "dk_rules_mlb",
   "source_url": "https://www.draftkings.com/help/rules/2",
   "source_title": "DraftKings Rules & Scoring - MLB Classic"
  },
  {
   "id": "c18",
   "claim": "FanDuel publishes per-sport scoring officially but not classic roster shapes or salary caps: its rules page documents scoring, and fanduel.com/nfl-guide redirects away.",
   "quote": "3-pt FG=3pts, 2-pt FG=2pts, FT=1pt, Rebound=1.2pts, Assist=1.5pts, Block=3pts, Steal=3pts, Turnover=-1pt",
   "status": "flagged",
   "relevance": "FanDuel scoring in the engine is official; FanDuel roster/cap values are marked verified:third-party and must be confirmed in-client.",
   "source_id": "fd_rules_gap",
   "source_url": "https://www.fanduel.com/rules",
   "source_title": "FanDuel rules page does not publish roster shapes or salary caps"
  },
  {
   "id": "c19",
   "claim": "The MLB Stats API is keyless and returns official game data, including final scores.",
   "quote": "{\"copyright\":\"Copyright 2026 MLB Advanced Media, L.P. ...\",\"dates\":[{\"date\":\"2026-09-21\" ... \"gamePk\":824787 ... \"status\":{\"abstractGameState\":\"Final\"",
   "status": "verified",
   "relevance": "Primary free source for MLB schedules, box scores and player stats.",
   "source_id": "mlb_statsapi",
   "source_url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-09-21&hydrate=team,linescore",
   "source_title": "MLB Stats API (official, keyless)"
  },
  {
   "id": "c20",
   "claim": "nflverse publishes free NFL data releases (play-by-play, player stats, schedules, snap counts, injuries, depth charts) under CC-BY-4.0.",
   "quote": "nflverse/nflverse-data - Automated nflverse data repository - license CC-BY-4.0; release tags include pbp, player_stats, schedules, snap_counts, injuries, depth_charts",
   "status": "verified",
   "relevance": "Primary free source for NFL modelling and for empirical variance/correlation calibration.",
   "source_id": "nflverse_data",
   "source_url": "https://github.com/nflverse/nflverse-data",
   "source_title": "nflverse-data (open NFL data releases)"
  },
  {
   "id": "c21",
   "claim": "The DraftKings lobby endpoint is keyless and exposes live contests with entry fee, max entries, prize pool and draft group id.",
   "quote": "{\"SelectedSport\":\"NFL\", ... \"n\":\"NFL $2.75M Fantasy Football Millionaire [$1M to 1st]\", ... \"a\":555, ... \"po\":2750000.0000000000, ... \"dg\":153769",
   "status": "flagged",
   "relevance": "Free path to real contest config and salary pools, but undocumented: treated as best-effort with a CSV fallback.",
   "source_id": "dk_lobby_api",
   "source_url": "https://www.draftkings.com/lobby/getcontests?sport=NFL",
   "source_title": "DraftKings public lobby JSON"
  },
  {
   "id": "c22",
   "claim": "ESPN's keyless scoreboard feed carries game-level odds (spread and total) that can produce implied team totals.",
   "quote": "site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard returned the real 2026 week 2 games with venue and odds payloads",
   "status": "flagged",
   "relevance": "Default keyless odds path; the paid odds API is optional-only.",
   "source_id": "espn_scoreboard",
   "source_url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
   "source_title": "ESPN public scoreboard/odds feed"
  },
  {
   "id": "c23",
   "claim": "Implied team total = total/2 +/- spread/2.",
   "quote": "worked example: 44 total with a -7 spread gives the favourite 25.5 and the underdog 18.5",
   "status": "verified",
   "relevance": "rules.implied_team_total() with the article's numbers as a unit test.",
   "source_id": "sk_nfl_defense",
   "source_url": "https://www.stokastic.com/articles/nfl-dfs/nfl-dfs-defense-strategy",
   "source_title": "NFL DFS defense strategy (implied team totals)"
  },
  {
   "id": "c24",
   "claim": "Stokastic's exact projection weights, sigma model and ownership coefficients are NOT public.",
   "quote": "No public page states the weights, the sigma model or the ownership coefficients. This project therefore ships documented priors and a calibration harness instead of pretending to have copied them.",
   "status": "not_verified",
   "relevance": "The central honesty constraint of the rebuild: we reproduce published mechanics, not undisclosed internals.",
   "source_id": "sk_pricing",
   "source_url": "https://www.stokastic.com/pricing",
   "source_title": "Stokastic pricing and product FAQ"
  },
  {
   "id": "c25",
   "claim": "FanDuel NBA has no double-double or triple-double bonus, unlike DraftKings.",
   "quote": "FanDuel NBA table: 3-pt FG=3pts, 2-pt FG=2pts, FT=1pt, Rebound=1.2pts, Assist=1.5pts, Block=3pts, Steal=3pts, Turnover=-1pt (no DD/TD rows)",
   "status": "verified",
   "relevance": "Site-specific stat projection: DK NBA needs DD/TD modelling, FanDuel does not.",
   "source_id": "fd_rules",
   "source_url": "https://www.fanduel.com/rules",
   "source_title": "FanDuel Rules & Scoring"
  }
 ],
 "removed_or_downgraded": [
  {
   "url": "https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments",
   "reason": "Carried over from the previous session as the source for several strategy claims. NOT re-fetched in this session, so no claim in this repo cites it as verified. Re-fetch and re-quote before reusing."
  },
  {
   "url": "https://nbaanalytic.com/articles/free-basketball-data-sources-ranked.html",
   "reason": "Third-party blog ranking. Removed from the engine's provenance: nba_api's own repository is the citable source for the NBA data path."
  },
  {
   "url": "https://www.oddsshopper.com/props",
   "reason": "Marketing page describing the props product; the projection methodology claim is better sourced to os_projection_system. Kept out of the registry rather than half-verified."
  },
  {
   "url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-vs-fantasylabs-nfl-dfs",
   "reason": "Carried over previously; not re-fetched this session. Equivalent claims are now quoted from sk_nfl_review, which was read live."
  }
 ],
 "rules": [
  {
   "site": "draftkings",
   "sport": "nfl",
   "salary_cap": 50000.0,
   "roster_size": 9,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "QB"
     ],
     "count": 1
    },
    {
     "eligible": [
      "RB"
     ],
     "count": 2
    },
    {
     "eligible": [
      "WR"
     ],
     "count": 3
    },
    {
     "eligible": [
      "TE"
     ],
     "count": 1
    },
    {
     "eligible": [
      "RB",
      "WR",
      "TE"
     ],
     "count": 1
    },
    {
     "eligible": [
      "DST"
     ],
     "count": 1
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": null,
   "bonus_rules": [
    {
     "id": "pass_300_bonus",
     "when": "pass_yd >= 300",
     "points": 3
    },
    {
     "id": "rush_100_bonus",
     "when": "rush_yd >= 100",
     "points": 3
    },
    {
     "id": "rec_100_bonus",
     "when": "rec_yd >= 100",
     "points": 3
    }
   ],
   "scoring": {
    "dst_2pt_ret": 2.0,
    "dst_blocked_kick": 2.0,
    "dst_fum_rec": 2.0,
    "dst_int": 2.0,
    "dst_ret_td": 6.0,
    "dst_sack": 1.0,
    "dst_safety": 2.0,
    "fumble_lost": -1.0,
    "off_fum_rec_td": 6.0,
    "pass_300_bonus": 3.0,
    "pass_int": -1.0,
    "pass_td": 4.0,
    "pass_yd": 0.04,
    "rec": 1.0,
    "rec_100_bonus": 3.0,
    "rec_td": 6.0,
    "rec_yd": 0.1,
    "ret_td": 6.0,
    "rush_100_bonus": 3.0,
    "rush_td": 6.0,
    "rush_yd": 0.1,
    "two_pt": 2.0
   },
   "source_id": "https://www.draftkings.com/help/rules/1",
   "source_url": null,
   "verified": "official"
  },
  {
   "site": "draftkings",
   "sport": "nba",
   "salary_cap": 50000.0,
   "roster_size": 8,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "PG"
     ],
     "count": 1
    },
    {
     "eligible": [
      "SG"
     ],
     "count": 1
    },
    {
     "eligible": [
      "SF"
     ],
     "count": 1
    },
    {
     "eligible": [
      "PF"
     ],
     "count": 1
    },
    {
     "eligible": [
      "C"
     ],
     "count": 1
    },
    {
     "eligible": [
      "PG",
      "SG"
     ],
     "count": 1
    },
    {
     "eligible": [
      "SF",
      "PF"
     ],
     "count": 1
    },
    {
     "eligible": [
      "PG",
      "SG",
      "SF",
      "PF",
      "C"
     ],
     "count": 1
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": null,
   "bonus_rules": [
    {
     "id": "double_double",
     "when": "at least two of {pts, reb, ast, stl, blk} >= 10",
     "points": 1.5,
     "max_per_player": 1
    },
    {
     "id": "triple_double",
     "when": "at least three of {pts, reb, ast, stl, blk} >= 10",
     "points": 3,
     "max_per_player": 1
    }
   ],
   "scoring": {
    "ast": 1.5,
    "blk": 2.0,
    "fg3m": 0.5,
    "pts": 1.0,
    "reb": 1.25,
    "stl": 2.0,
    "to": -0.5
   },
   "source_id": "https://www.draftkings.com/help/rules/4",
   "source_url": null,
   "verified": "official"
  },
  {
   "site": "draftkings",
   "sport": "mlb",
   "salary_cap": 50000.0,
   "roster_size": 10,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "P",
      "SP",
      "RP"
     ],
     "count": 2
    },
    {
     "eligible": [
      "C"
     ],
     "count": 1
    },
    {
     "eligible": [
      "1B"
     ],
     "count": 1
    },
    {
     "eligible": [
      "2B"
     ],
     "count": 1
    },
    {
     "eligible": [
      "3B"
     ],
     "count": 1
    },
    {
     "eligible": [
      "SS"
     ],
     "count": 1
    },
    {
     "eligible": [
      "OF"
     ],
     "count": 3
    }
   ],
   "max_hitters_per_team": 5,
   "min_skater_teams": null,
   "bonus_rules": [
    {
     "id": "complete_game",
     "when": "complete_game == true",
     "points": 2.5
    },
    {
     "id": "complete_game_shutout",
     "when": "complete_game_shutout == true",
     "points": 2.5
    },
    {
     "id": "no_hitter",
     "when": "no_hitter == true",
     "points": 5
    }
   ],
   "scoring": {
    "bb": 2.0,
    "bb_against": -0.6,
    "double": 5.0,
    "er": -2.0,
    "hbp": 2.0,
    "hit_against": -0.6,
    "hit_batsman": -0.6,
    "hr": 10.0,
    "ip": 2.25,
    "rbi": 2.0,
    "run": 2.0,
    "sb": 5.0,
    "single": 3.0,
    "so": 2.0,
    "triple": 8.0,
    "win": 4.0
   },
   "source_id": "https://www.draftkings.com/help/rules/2",
   "source_url": null,
   "verified": "official"
  },
  {
   "site": "draftkings",
   "sport": "nhl",
   "salary_cap": 50000.0,
   "roster_size": 9,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "C"
     ],
     "count": 2
    },
    {
     "eligible": [
      "LW",
      "RW"
     ],
     "count": 3
    },
    {
     "eligible": [
      "D"
     ],
     "count": 2
    },
    {
     "eligible": [
      "LW",
      "RW",
      "C",
      "D"
     ],
     "count": 1
    },
    {
     "eligible": [
      "G"
     ],
     "count": 1
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": 3,
   "bonus_rules": [
    {
     "id": "hat_trick",
     "when": "goal >= 3",
     "points": 3
    },
    {
     "id": "shots_5plus",
     "when": "sog >= 5",
     "points": 3
    },
    {
     "id": "blocks_3plus",
     "when": "blocked_shot >= 3",
     "points": 3
    },
    {
     "id": "points_3plus",
     "when": "goal + assist >= 3",
     "points": 3
    },
    {
     "id": "saves_35plus",
     "when": "g_save >= 35",
     "points": 3
    }
   ],
   "scoring": {
    "assist": 5.0,
    "blocked_shot": 1.3,
    "g_ga": -3.5,
    "g_ot_loss": 2.0,
    "g_save": 0.7,
    "g_shutout": 4.0,
    "g_win": 6.0,
    "goal": 8.5,
    "shootout_goal": 1.5,
    "shp": 2.0,
    "sog": 1.5
   },
   "source_id": "https://www.draftkings.com/help/rules/3",
   "source_url": null,
   "verified": "official"
  },
  {
   "site": "fanduel",
   "sport": "nfl",
   "salary_cap": 60000.0,
   "roster_size": 9,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "QB"
     ],
     "count": 1
    },
    {
     "eligible": [
      "RB"
     ],
     "count": 2
    },
    {
     "eligible": [
      "WR"
     ],
     "count": 3
    },
    {
     "eligible": [
      "TE"
     ],
     "count": 1
    },
    {
     "eligible": [
      "RB",
      "WR",
      "TE"
     ],
     "count": 1
    },
    {
     "eligible": [
      "DST"
     ],
     "count": 1
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": null,
   "bonus_rules": [],
   "scoring": {
    "dst_2pt_ret": 2.0,
    "dst_blocked_kick": 2.0,
    "dst_fum_rec": 2.0,
    "dst_int": 2.0,
    "dst_ret_td": 6.0,
    "dst_sack": 1.0,
    "dst_safety": 2.0,
    "fg_0_39": 3.0,
    "fg_40_49": 4.0,
    "fg_50_plus": 5.0,
    "fumble_lost": -2.0,
    "off_fum_rec_td": 6.0,
    "pass_300_bonus": 3.0,
    "pass_int": -1.0,
    "pass_td": 4.0,
    "pass_yd": 0.04,
    "rec": 0.5,
    "rec_100_bonus": 3.0,
    "rec_td": 6.0,
    "rec_yd": 0.1,
    "ret_td": 6.0,
    "rush_100_bonus": 3.0,
    "rush_td": 6.0,
    "rush_yd": 0.1,
    "two_pt": 2.0,
    "two_pt_pass": 2.0,
    "xp": 1.0
   },
   "source_id": "https://www.fanduel.com/rules",
   "source_url": null,
   "verified": "third-party"
  },
  {
   "site": "fanduel",
   "sport": "nba",
   "salary_cap": 60000.0,
   "roster_size": 9,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "PG"
     ],
     "count": 2
    },
    {
     "eligible": [
      "SG"
     ],
     "count": 2
    },
    {
     "eligible": [
      "SF"
     ],
     "count": 2
    },
    {
     "eligible": [
      "PF"
     ],
     "count": 2
    },
    {
     "eligible": [
      "C"
     ],
     "count": 1
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": null,
   "bonus_rules": [],
   "scoring": {
    "ast": 1.5,
    "blk": 3.0,
    "fg2m": 2.0,
    "fg3m": 3.0,
    "ft": 1.0,
    "reb": 1.2,
    "stl": 3.0,
    "to": -1.0
   },
   "source_id": "https://www.fanduel.com/rules",
   "source_url": null,
   "verified": "third-party"
  },
  {
   "site": "fanduel",
   "sport": "mlb",
   "salary_cap": 60000.0,
   "roster_size": 10,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "P",
      "SP",
      "RP"
     ],
     "count": 2
    },
    {
     "eligible": [
      "C"
     ],
     "count": 1
    },
    {
     "eligible": [
      "1B"
     ],
     "count": 1
    },
    {
     "eligible": [
      "2B"
     ],
     "count": 1
    },
    {
     "eligible": [
      "3B"
     ],
     "count": 1
    },
    {
     "eligible": [
      "SS"
     ],
     "count": 1
    },
    {
     "eligible": [
      "OF"
     ],
     "count": 3
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": null,
   "bonus_rules": [],
   "scoring": {
    "bb": 3.0,
    "double": 6.0,
    "er": -3.0,
    "hbp": 3.0,
    "hr": 12.0,
    "ip": 3.0,
    "quality_start": 4.0,
    "rbi": 3.5,
    "run": 3.2,
    "sb": 6.0,
    "single": 3.0,
    "so": 3.0,
    "triple": 9.0,
    "win": 6.0
   },
   "source_id": "https://www.fanduel.com/rules",
   "source_url": null,
   "verified": "third-party"
  },
  {
   "site": "fanduel",
   "sport": "nhl",
   "salary_cap": 55000.0,
   "roster_size": 9,
   "min_games": 2,
   "slots": [
    {
     "eligible": [
      "C"
     ],
     "count": 2
    },
    {
     "eligible": [
      "LW",
      "RW"
     ],
     "count": 3
    },
    {
     "eligible": [
      "D"
     ],
     "count": 2
    },
    {
     "eligible": [
      "LW",
      "RW",
      "C",
      "D"
     ],
     "count": 1
    },
    {
     "eligible": [
      "G"
     ],
     "count": 1
    }
   ],
   "max_hitters_per_team": null,
   "min_skater_teams": null,
   "bonus_rules": [],
   "scoring": {
    "assist": 8.0,
    "blocked_shot": 1.6,
    "g_ga": -4.0,
    "g_save": 0.8,
    "g_shutout": 8.0,
    "g_win": 12.0,
    "goal": 12.0,
    "ppp": 0.5,
    "shp": 2.0,
    "sog": 1.6
   },
   "source_id": "https://www.fanduel.com/rules",
   "source_url": null,
   "verified": "third-party"
  }
 ],
 "demo": [
  {
   "sample": "sample_mlb_dk.json",
   "sport": "mlb",
   "site": "draftkings",
   "date": "2026-09-21",
   "synthetic": true,
   "n_sims": 1000,
   "field_size": 600,
   "payout_source": "ILLUSTRATIVE curve generated in-engine (not a real contest)",
   "field_baseline": {
    "lineups_sampled": 60,
    "best_decile_roi_pct": -9.9,
    "best_decile_note": "the top 10% of the simulated field, by mean simulated score, scored as if it were the user. Large ROI here too means the payout curve's tail, not the lineup, is doing the work.",
    "own_draw_rois_pct": [
     43.5,
     182.6,
     128.6,
     449.9,
     369.9,
     175.0
    ],
    "own_draws_note": "the same optimiser, six independent noisy views (sd 25%), one lineup each. The spread across draws is larger than the difference between the builds, which is why no single ROI number should be read as an edge.",
    "mean_roi_pct": -17.9,
    "mean_cash_rate_pct": 20.1,
    "mean_percentile": 53.1,
    "note": "the same simulation run with a random sample of the field as the user. A cash rate near the paid fraction pins the ROI to the payout curve; anything far from the rake means the field model, not the strategy, is driving the number."
   },
   "projection_table": [
    {
     "player_id": "mlb-sp-62",
     "name": "Synthetic SEA SP2",
     "team": "SEA",
     "opponent": "HOU",
     "positions": [
      "SP"
     ],
     "salary": 7623.0,
     "projection": 23.19,
     "stddev": 8.31,
     "ceiling": 28.36,
     "floor": 16.97,
     "boom_pct": 0.4,
     "bust_pct": 95.1,
     "boom_threshold": 48.12,
     "bust_threshold": 38.12,
     "value": -14.92,
     "pts_per_dollar": 3.04
    },
    {
     "player_id": "mlb-sp-77",
     "name": "Synthetic HOU SP2",
     "team": "HOU",
     "opponent": "SEA",
     "positions": [
      "SP"
     ],
     "salary": 8209.0,
     "projection": 22.66,
     "stddev": 7.6,
     "ceiling": 27.42,
     "floor": 17.52,
     "boom_pct": 0.0,
     "bust_pct": 98.5,
     "boom_threshold": 51.05,
     "bust_threshold": 41.05,
     "value": -18.38,
     "pts_per_dollar": 2.76
    },
    {
     "player_id": "mlb-sp-63",
     "name": "Synthetic SEA SP3",
     "team": "SEA",
     "opponent": "HOU",
     "positions": [
      "SP"
     ],
     "salary": 5316.0,
     "projection": 22.04,
     "stddev": 7.27,
     "ceiling": 26.79,
     "floor": 16.95,
     "boom_pct": 2.8,
     "bust_pct": 74.2,
     "boom_threshold": 36.58,
     "bust_threshold": 26.58,
     "value": -4.54,
     "pts_per_dollar": 4.15
    },
    {
     "player_id": "mlb-sp-31",
     "name": "Synthetic SF SP1",
     "team": "SF",
     "opponent": "LAD",
     "positions": [
      "SP"
     ],
     "salary": 9186.0,
     "projection": 21.94,
     "stddev": 7.57,
     "ceiling": 26.78,
     "floor": 16.83,
     "boom_pct": 0.0,
     "bust_pct": 99.8,
     "boom_threshold": 55.93,
     "bust_threshold": 45.93,
     "value": -23.99,
     "pts_per_dollar": 2.39
    },
    {
     "player_id": "mlb-sp-34",
     "name": "Synthetic SF SP4",
     "team": "SF",
     "opponent": "LAD",
     "positions": [
      "SP"
     ],
     "salary": 6933.0,
     "projection": 21.23,
     "stddev": 7.73,
     "ceiling": 26.06,
     "floor": 15.94,
     "boom_pct": 0.6,
     "bust_pct": 95.6,
     "boom_threshold": 44.66,
     "bust_threshold": 34.66,
     "value": -13.44,
     "pts_per_dollar": 3.06
    },
    {
     "player_id": "mlb-sp-109",
     "name": "Synthetic ATL SP4",
     "team": "ATL",
     "opponent": "PHI",
     "positions": [
      "SP"
     ],
     "salary": 6715.0,
     "projection": 20.87,
     "stddev": 7.22,
     "ceiling": 25.66,
     "floor": 15.74,
     "boom_pct": 0.0,
     "bust_pct": 95.3,
     "boom_threshold": 43.58,
     "bust_threshold": 33.58,
     "value": -12.7,
     "pts_per_dollar": 3.11
    },
    {
     "player_id": "mlb-sp-47",
     "name": "Synthetic LAD SP2",
     "team": "LAD",
     "opponent": "SF",
     "positions": [
      "SP"
     ],
     "salary": 5492.0,
     "projection": 20.86,
     "stddev": 7.56,
     "ceiling": 25.95,
     "floor": 15.73,
     "boom_pct": 2.1,
     "bust_pct": 81.7,
     "boom_threshold": 37.46,
     "bust_threshold": 27.46,
     "value": -6.6,
     "pts_per_dollar": 3.8
    },
    {
     "player_id": "mlb-sp-49",
     "name": "Synthetic LAD SP4",
     "team": "LAD",
     "opponent": "SF",
     "positions": [
      "SP"
     ],
     "salary": 8726.0,
     "projection": 20.68,
     "stddev": 7.15,
     "ceiling": 25.07,
     "floor": 15.63,
     "boom_pct": 0.0,
     "bust_pct": 99.7,
     "boom_threshold": 53.63,
     "bust_threshold": 43.63,
     "value": -22.95,
     "pts_per_dollar": 2.37
    },
    {
     "player_id": "mlb-sp-91",
     "name": "Synthetic PHI SP1",
     "team": "PHI",
     "opponent": "ATL",
     "positions": [
      "SP"
     ],
     "salary": 5648.0,
     "projection": 20.67,
     "stddev": 7.39,
     "ceiling": 25.06,
     "floor": 15.77,
     "boom_pct": 1.6,
     "bust_pct": 85.4,
     "boom_threshold": 38.24,
     "bust_threshold": 28.24,
     "value": -7.57,
     "pts_per_dollar": 3.66
    },
    {
     "player_id": "mlb-sp-108",
     "name": "Synthetic ATL SP3",
     "team": "ATL",
     "opponent": "PHI",
     "positions": [
      "SP"
     ],
     "salary": 7259.0,
     "projection": 20.57,
     "stddev": 7.28,
     "ceiling": 24.6,
     "floor": 15.7,
     "boom_pct": 0.4,
     "bust_pct": 97.3,
     "boom_threshold": 46.3,
     "bust_threshold": 36.3,
     "value": -15.72,
     "pts_per_dollar": 2.83
    },
    {
     "player_id": "mlb-sp-2",
     "name": "Synthetic BOS SP2",
     "team": "BOS",
     "opponent": "NYY",
     "positions": [
      "SP"
     ],
     "salary": 6985.0,
     "projection": 20.13,
     "stddev": 7.61,
     "ceiling": 24.49,
     "floor": 14.81,
     "boom_pct": 0.4,
     "bust_pct": 96.5,
     "boom_threshold": 44.93,
     "bust_threshold": 34.93,
     "value": -14.8,
     "pts_per_dollar": 2.88
    },
    {
     "player_id": "mlb-sp-46",
     "name": "Synthetic LAD SP1",
     "team": "LAD",
     "opponent": "SF",
     "positions": [
      "SP"
     ],
     "salary": 6961.0,
     "projection": 20.11,
     "stddev": 7.06,
     "ceiling": 24.39,
     "floor": 15.3,
     "boom_pct": 0.2,
     "bust_pct": 97.5,
     "boom_threshold": 44.8,
     "bust_threshold": 34.8,
     "value": -14.7,
     "pts_per_dollar": 2.89
    },
    {
     "player_id": "mlb-sp-3",
     "name": "Synthetic BOS SP3",
     "team": "BOS",
     "opponent": "NYY",
     "positions": [
      "SP"
     ],
     "salary": 7585.0,
     "projection": 19.63,
     "stddev": 7.32,
     "ceiling": 24.23,
     "floor": 14.72,
     "boom_pct": 0.1,
     "bust_pct": 98.6,
     "boom_threshold": 47.92,
     "bust_threshold": 37.92,
     "value": -18.29,
     "pts_per_dollar": 2.59
    },
    {
     "player_id": "mlb-sp-17",
     "name": "Synthetic NYY SP2",
     "team": "NYY",
     "opponent": "BOS",
     "positions": [
      "SP"
     ],
     "salary": 5658.0,
     "projection": 18.96,
     "stddev": 7.59,
     "ceiling": 23.5,
     "floor": 13.78,
     "boom_pct": 1.7,
     "bust_pct": 88.8,
     "boom_threshold": 38.29,
     "bust_threshold": 28.29,
     "value": -9.33,
     "pts_per_dollar": 3.35
    },
    {
     "player_id": "mlb-sp-106",
     "name": "Synthetic ATL SP1",
     "team": "ATL",
     "opponent": "PHI",
     "positions": [
      "SP"
     ],
     "salary": 9257.0,
     "projection": 18.87,
     "stddev": 6.81,
     "ceiling": 22.94,
     "floor": 14.06,
     "boom_pct": 0.0,
     "bust_pct": 100.0,
     "boom_threshold": 56.28,
     "bust_threshold": 46.28,
     "value": -27.41,
     "pts_per_dollar": 2.04
    },
    {
     "player_id": "mlb-sp-16",
     "name": "Synthetic NYY SP1",
     "team": "NYY",
     "opponent": "BOS",
     "positions": [
      "SP"
     ],
     "salary": 8187.0,
     "projection": 18.52,
     "stddev": 6.68,
     "ceiling": 22.75,
     "floor": 13.96,
     "boom_pct": 0.0,
     "bust_pct": 99.8,
     "boom_threshold": 50.93,
     "bust_threshold": 40.93,
     "value": -22.42,
     "pts_per_dollar": 2.26
    },
    {
     "player_id": "mlb-sp-76",
     "name": "Synthetic HOU SP1",
     "team": "HOU",
     "opponent": "SEA",
     "positions": [
      "SP"
     ],
     "salary": 9198.0,
     "projection": 18.45,
     "stddev": 7.13,
     "ceiling": 22.62,
     "floor": 13.52,
     "boom_pct": 0.0,
     "bust_pct": 99.8,
     "boom_threshold": 55.99,
     "bust_threshold": 45.99,
     "value": -27.54,
     "pts_per_dollar": 2.01
    },
    {
     "player_id": "mlb-sp-18",
     "name": "Synthetic NYY SP3",
     "team": "NYY",
     "opponent": "BOS",
     "positions": [
      "SP"
     ],
     "salary": 7052.0,
     "projection": 18.26,
     "stddev": 6.88,
     "ceiling": 22.66,
     "floor": 13.79,
     "boom_pct": 0.0,
     "bust_pct": 99.4,
     "boom_threshold": 45.26,
     "bust_threshold": 35.26,
     "value": -17.0,
     "pts_per_dollar": 2.59
    },
    {
     "player_id": "mlb-sp-4",
     "name": "Synthetic BOS SP4",
     "team": "BOS",
     "opponent": "NYY",
     "positions": [
      "SP"
     ],
     "salary": 7202.0,
     "projection": 18.15,
     "stddev": 6.71,
     "ceiling": 22.29,
     "floor": 13.64,
     "boom_pct": 0.1,
     "bust_pct": 98.9,
     "boom_threshold": 46.01,
     "bust_threshold": 36.01,
     "value": -17.86,
     "pts_per_dollar": 2.52
    },
    {
     "player_id": "mlb-sp-48",
     "name": "Synthetic LAD SP3",
     "team": "LAD",
     "opponent": "SF",
     "positions": [
      "SP"
     ],
     "salary": 8514.0,
     "projection": 18.14,
     "stddev": 6.59,
     "ceiling": 22.27,
     "floor": 13.26,
     "boom_pct": 0.0,
     "bust_pct": 100.0,
     "boom_threshold": 52.57,
     "bust_threshold": 42.57,
     "value": -24.43,
     "pts_per_dollar": 2.13
    },
    {
     "player_id": "mlb-sp-61",
     "name": "Synthetic SEA SP1",
     "team": "SEA",
     "opponent": "HOU",
     "positions": [
      "SP"
     ],
     "salary": 9599.0,
     "projection": 17.66,
     "stddev": 6.61,
     "ceiling": 21.8,
     "floor": 13.17,
     "boom_pct": 0.0,
     "bust_pct": 100.0,
     "boom_threshold": 58.0,
     "bust_threshold": 48.0,
     "value": -30.33,
     "pts_per_dollar": 1.84
    },
    {
     "player_id": "mlb-sp-92",
     "name": "Synthetic PHI SP2",
     "team": "PHI",
     "opponent": "ATL",
     "positions": [
      "SP"
     ],
     "salary": 8858.0,
     "projection": 17.45,
     "stddev": 6.43,
     "ceiling": 21.63,
     "floor": 12.86,
     "boom_pct": 0.0,
     "bust_pct": 100.0,
     "boom_threshold": 54.29,
     "bust_threshold": 44.29,
     "value": -26.84,
     "pts_per_dollar": 1.97
    },
    {
     "player_id": "mlb-sp-19",
     "name": "Synthetic NYY SP4",
     "team": "NYY",
     "opponent": "BOS",
     "positions": [
      "SP"
     ],
     "salary": 8094.0,
     "projection": 17.26,
     "stddev": 6.47,
     "ceiling": 21.43,
     "floor": 12.74,
     "boom_pct": 0.0,
     "bust_pct": 99.8,
     "boom_threshold": 50.47,
     "bust_threshold": 40.47,
     "value": -23.21,
     "pts_per_dollar": 2.13
    },
    {
     "player_id": "mlb-sp-33",
     "name": "Synthetic SF SP3",
     "team": "SF",
     "opponent": "LAD",
     "positions": [
      "SP"
     ],
     "salary": 7419.0,
     "projection": 16.89,
     "stddev": 6.86,
     "ceiling": 21.07,
     "floor": 12.25,
     "boom_pct": 0.0,
     "bust_pct": 99.1,
     "boom_threshold": 47.09,
     "bust_threshold": 37.09,
     "value": -20.2,
     "pts_per_dollar": 2.28
    },
    {
     "player_id": "mlb-sp-64",
     "name": "Synthetic SEA SP4",
     "team": "SEA",
     "opponent": "HOU",
     "positions": [
      "SP"
     ],
     "salary": 5504.0,
     "projection": 16.81,
     "stddev": 6.67,
     "ceiling": 20.48,
     "floor": 12.21,
     "boom_pct": 0.0,
     "bust_pct": 92.5,
     "boom_threshold": 37.52,
     "bust_threshold": 27.52,
     "value": -10.71,
     "pts_per_dollar": 3.05
    }
   ],
   "ownership_top": [
    {
     "name": "Synthetic NYY 1B1",
     "team": "NYY",
     "positions": [
      "1B"
     ],
     "salary": 2538.0,
     "ownership_pct": 81.0
    },
    {
     "name": "Synthetic BOS C1",
     "team": "BOS",
     "positions": [
      "C"
     ],
     "salary": 2584.0,
     "ownership_pct": 71.5
    },
    {
     "name": "Synthetic SEA SP3",
     "team": "SEA",
     "positions": [
      "SP"
     ],
     "salary": 5316.0,
     "ownership_pct": 69.0
    },
    {
     "name": "Synthetic SEA SS1",
     "team": "SEA",
     "positions": [
      "SS"
     ],
     "salary": 2639.0,
     "ownership_pct": 69.0
    },
    {
     "name": "Synthetic LAD 3B1",
     "team": "LAD",
     "positions": [
      "3B"
     ],
     "salary": 3061.0,
     "ownership_pct": 62.5
    },
    {
     "name": "Synthetic SF 2B1",
     "team": "SF",
     "positions": [
      "2B"
     ],
     "salary": 2522.0,
     "ownership_pct": 61.0
    },
    {
     "name": "Synthetic HOU OF3",
     "team": "HOU",
     "positions": [
      "OF"
     ],
     "salary": 2571.0,
     "ownership_pct": 44.5
    },
    {
     "name": "Synthetic LAD SP2",
     "team": "LAD",
     "positions": [
      "SP"
     ],
     "salary": 5492.0,
     "ownership_pct": 40.5
    },
    {
     "name": "Synthetic SF OF5",
     "team": "SF",
     "positions": [
      "OF"
     ],
     "salary": 2789.0,
     "ownership_pct": 29.5
    },
    {
     "name": "Synthetic PHI SP1",
     "team": "PHI",
     "positions": [
      "SP"
     ],
     "salary": 5648.0,
     "ownership_pct": 29.5
    },
    {
     "name": "Synthetic SEA OF3",
     "team": "SEA",
     "positions": [
      "OF"
     ],
     "salary": 2919.0,
     "ownership_pct": 28.0
    },
    {
     "name": "Synthetic PHI OF2",
     "team": "PHI",
     "positions": [
      "OF"
     ],
     "salary": 3323.0,
     "ownership_pct": 25.0
    },
    {
     "name": "Synthetic LAD OF3",
     "team": "LAD",
     "positions": [
      "OF"
     ],
     "salary": 2813.0,
     "ownership_pct": 21.5
    },
    {
     "name": "Synthetic HOU OF4",
     "team": "HOU",
     "positions": [
      "OF"
     ],
     "salary": 3106.0,
     "ownership_pct": 21.0
    },
    {
     "name": "Synthetic NYY SP2",
     "team": "NYY",
     "positions": [
      "SP"
     ],
     "salary": 5658.0,
     "ownership_pct": 18.0
    }
   ],
   "lineups": [
    {
     "label": "lineup_1",
     "method": "milp",
     "salary": 49398.0,
     "projected": 151.12,
     "players": [
      {
       "name": "Synthetic BOS C1",
       "positions": [
        "C"
       ],
       "team": "BOS",
       "salary": 2584.0
      },
      {
       "name": "Synthetic NYY SP1",
       "positions": [
        "SP"
       ],
       "team": "NYY",
       "salary": 8187.0
      },
      {
       "name": "Synthetic NYY 1B1",
       "positions": [
        "1B"
       ],
       "team": "NYY",
       "salary": 2538.0
      },
      {
       "name": "Synthetic LAD 3B1",
       "positions": [
        "3B"
       ],
       "team": "LAD",
       "salary": 3061.0
      },
      {
       "name": "Synthetic LAD OF6",
       "positions": [
        "OF"
       ],
       "team": "LAD",
       "salary": 6405.0
      },
      {
       "name": "Synthetic HOU SS1",
       "positions": [
        "SS"
       ],
       "team": "HOU",
       "salary": 6126.0
      },
      {
       "name": "Synthetic PHI SP1",
       "positions": [
        "SP"
       ],
       "team": "PHI",
       "salary": 5648.0
      },
      {
       "name": "Synthetic PHI OF4",
       "positions": [
        "OF"
       ],
       "team": "PHI",
       "salary": 4042.0
      },
      {
       "name": "Synthetic ATL 2B1",
       "positions": [
        "2B"
       ],
       "team": "ATL",
       "salary": 4798.0
      },
      {
       "name": "Synthetic ATL OF2",
       "positions": [
        "OF"
       ],
       "team": "ATL",
       "salary": 6009.0
      }
     ],
     "roi_pct": 205.8,
     "cash_rate_pct": 28.2,
     "win_rate_pct": 1.3,
     "median_rank": 274.0,
     "mean_percentile": 53.3
    },
    {
     "label": "lineup_2",
     "method": "milp",
     "salary": 47785.0,
     "projected": 150.72,
     "players": [
      {
       "name": "Synthetic BOS C1",
       "positions": [
        "C"
       ],
       "team": "BOS",
       "salary": 2584.0
      },
      {
       "name": "Synthetic BOS OF1",
       "positions": [
        "OF"
       ],
       "team": "BOS",
       "salary": 4791.0
      },
      {
       "name": "Synthetic NYY SP1",
       "positions": [
        "SP"
       ],
       "team": "NYY",
       "salary": 8187.0
      },
      {
       "name": "Synthetic NYY 1B1",
       "positions": [
        "1B"
       ],
       "team": "NYY",
       "salary": 2538.0
      },
      {
       "name": "Synthetic SF SS1",
       "positions": [
        "SS"
       ],
       "team": "SF",
       "salary": 3764.0
      },
      {
       "name": "Synthetic LAD 3B1",
       "positions": [
        "3B"
       ],
       "team": "LAD",
       "salary": 3061.0
      },
      {
       "name": "Synthetic LAD OF6",
       "positions": [
        "OF"
       ],
       "team": "LAD",
       "salary": 6405.0
      },
      {
       "name": "Synthetic PHI SP1",
       "positions": [
        "SP"
       ],
       "team": "PHI",
       "salary": 5648.0
      },
      {
       "name": "Synthetic ATL 2B1",
       "positions": [
        "2B"
       ],
       "team": "ATL",
       "salary": 4798.0
      },
      {
       "name": "Synthetic ATL OF2",
       "positions": [
        "OF"
       ],
       "team": "ATL",
       "salary": 6009.0
      }
     ],
     "roi_pct": 210.9,
     "cash_rate_pct": 28.6,
     "win_rate_pct": 1.0,
     "median_rank": 290.0,
     "mean_percentile": 52.6
    },
    {
     "label": "lineup_3",
     "method": "milp",
     "salary": 49697.0,
     "projected": 138.22,
     "players": [
      {
       "name": "Synthetic BOS OF1",
       "positions": [
        "OF"
       ],
       "team": "BOS",
       "salary": 4791.0
      },
      {
       "name": "Synthetic NYY C1",
       "positions": [
        "C"
       ],
       "team": "NYY",
       "salary": 5850.0
      },
      {
       "name": "Synthetic NYY OF5",
       "positions": [
        "OF"
       ],
       "team": "NYY",
       "salary": 4420.0
      },
      {
       "name": "Synthetic SF SS1",
       "positions": [
        "SS"
       ],
       "team": "SF",
       "salary": 3764.0
      },
      {
       "name": "Synthetic SEA SP3",
       "positions": [
        "SP"
       ],
       "team": "SEA",
       "salary": 5316.0
      },
      {
       "name": "Synthetic HOU SP2",
       "positions": [
        "SP"
       ],
       "team": "HOU",
       "salary": 8209.0
      },
      {
       "name": "Synthetic PHI 2B1",
       "positions": [
        "2B"
       ],
       "team": "PHI",
       "salary": 3125.0
      },
      {
       "name": "Synthetic PHI 3B1",
       "positions": [
        "3B"
       ],
       "team": "PHI",
       "salary": 4418.0
      },
      {
       "name": "Synthetic PHI OF4",
       "positions": [
        "OF"
       ],
       "team": "PHI",
       "salary": 4042.0
      },
      {
       "name": "Synthetic ATL 1B1",
       "positions": [
        "1B"
       ],
       "team": "ATL",
       "salary": 5762.0
      }
     ],
     "roi_pct": 403.2,
     "cash_rate_pct": 40.2,
     "win_rate_pct": 2.0,
     "median_rank": 184.0,
     "mean_percentile": 61.8
    }
   ],
   "notes": [
    "Sample slates in src/data/samples are synthetic and labelled as such. They exist so the engine can be tested deterministically offline; they are not real salaries or real projections, and no report generated from them describes real players.",
    "lineups were built from a view of the projections as noisy as the field's (sd 25%): the honest-test setting. Building them from the model's own projections makes simulated ROI meaningless, because the field is given error and the lineup is not.",
    "ownership is a simulated-field estimate, not observed contest ownership",
    "the payout structure is ILLUSTRATIVE; ROI is only meaningful with the real contest payout table imported from a CSV",
    "compare each lineup's ROI with the field baseline in this same run: if a random field entry also earns far more than the rake, the number is about the field model, not the lineups",
    "lineup_1: simulated ROI 206% with a 28% cash rate. A cash rate near the paid fraction cannot justify that ROI unless the lineup is winning top prizes far more often than the field. Check (1) the field model, (2) whether the lineups were built on info the field lacked, (3) the payout structure.",
    "payout structure is illustrative, so ROI is a ranking aid only"
   ]
  },
  {
   "sample": "sample_nfl_dk.json",
   "sport": "nfl",
   "site": "draftkings",
   "date": "2026-09-20",
   "synthetic": true,
   "n_sims": 1000,
   "field_size": 600,
   "payout_source": "ILLUSTRATIVE curve generated in-engine (not a real contest)",
   "field_baseline": {
    "lineups_sampled": 60,
    "best_decile_roi_pct": -0.8,
    "best_decile_note": "the top 10% of the simulated field, by mean simulated score, scored as if it were the user. Large ROI here too means the payout curve's tail, not the lineup, is doing the work.",
    "own_draw_rois_pct": [
     85.9,
     227.7,
     296.1,
     248.3,
     182.3,
     185.4
    ],
    "own_draws_note": "the same optimiser, six independent noisy views (sd 25%), one lineup each. The spread across draws is larger than the difference between the builds, which is why no single ROI number should be read as an edge.",
    "mean_roi_pct": -20.9,
    "mean_cash_rate_pct": 21.2,
    "mean_percentile": 52.7,
    "note": "the same simulation run with a random sample of the field as the user. A cash rate near the paid fraction pins the ROI to the payout curve; anything far from the rake means the field model, not the strategy, is driving the number."
   },
   "projection_table": [
    {
     "player_id": "nfl-rb-68",
     "name": "Synthetic PHI RB1",
     "team": "PHI",
     "opponent": "DET",
     "positions": [
      "RB"
     ],
     "salary": 7230.0,
     "projection": 22.75,
     "stddev": 9.44,
     "ceiling": 28.39,
     "floor": 15.82,
     "boom_pct": 1.7,
     "bust_pct": 91.2,
     "boom_threshold": 46.15,
     "bust_threshold": 36.15,
     "value": -13.4,
     "pts_per_dollar": 3.15
    },
    {
     "player_id": "nfl-wr-45",
     "name": "Synthetic SF WR1",
     "team": "SF",
     "opponent": "DAL",
     "positions": [
      "WR"
     ],
     "salary": 5358.0,
     "projection": 20.29,
     "stddev": 10.6,
     "ceiling": 26.92,
     "floor": 12.26,
     "boom_pct": 7.3,
     "bust_pct": 74.6,
     "boom_threshold": 36.79,
     "bust_threshold": 26.79,
     "value": -6.5,
     "pts_per_dollar": 3.79
    },
    {
     "player_id": "nfl-qb-14",
     "name": "Synthetic KC QB1",
     "team": "KC",
     "opponent": "BUF",
     "positions": [
      "QB"
     ],
     "salary": 6720.0,
     "projection": 20.24,
     "stddev": 8.13,
     "ceiling": 25.46,
     "floor": 14.09,
     "boom_pct": 0.8,
     "bust_pct": 93.7,
     "boom_threshold": 43.6,
     "bust_threshold": 33.6,
     "value": -13.36,
     "pts_per_dollar": 3.01
    },
    {
     "player_id": "nfl-wr-35",
     "name": "Synthetic DAL WR4",
     "team": "DAL",
     "opponent": "SF",
     "positions": [
      "WR"
     ],
     "salary": 3979.0,
     "projection": 19.78,
     "stddev": 10.8,
     "ceiling": 26.78,
     "floor": 11.67,
     "boom_pct": 17.1,
     "bust_pct": 56.0,
     "boom_threshold": 29.89,
     "bust_threshold": 19.89,
     "value": -0.11,
     "pts_per_dollar": 4.97
    },
    {
     "player_id": "nfl-qb-1",
     "name": "Synthetic BUF QB1",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "QB"
     ],
     "salary": 6049.0,
     "projection": 19.74,
     "stddev": 8.17,
     "ceiling": 24.71,
     "floor": 13.92,
     "boom_pct": 1.5,
     "bust_pct": 89.2,
     "boom_threshold": 40.25,
     "bust_threshold": 30.25,
     "value": -10.5,
     "pts_per_dollar": 3.26
    },
    {
     "player_id": "nfl-te-63",
     "name": "Synthetic DET TE1",
     "team": "DET",
     "opponent": "PHI",
     "positions": [
      "TE"
     ],
     "salary": 7086.0,
     "projection": 19.29,
     "stddev": 10.1,
     "ceiling": 25.59,
     "floor": 11.77,
     "boom_pct": 1.8,
     "bust_pct": 91.9,
     "boom_threshold": 45.43,
     "bust_threshold": 35.43,
     "value": -16.14,
     "pts_per_dollar": 2.72
    },
    {
     "player_id": "nfl-rb-55",
     "name": "Synthetic DET RB1",
     "team": "DET",
     "opponent": "PHI",
     "positions": [
      "RB"
     ],
     "salary": 4933.0,
     "projection": 19.08,
     "stddev": 8.62,
     "ceiling": 23.72,
     "floor": 13.25,
     "boom_pct": 5.0,
     "bust_pct": 78.1,
     "boom_threshold": 34.66,
     "bust_threshold": 24.66,
     "value": -5.58,
     "pts_per_dollar": 3.87
    },
    {
     "player_id": "nfl-qb-2",
     "name": "Synthetic BUF QB2",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "QB"
     ],
     "salary": 6264.0,
     "projection": 18.82,
     "stddev": 7.44,
     "ceiling": 22.79,
     "floor": 13.27,
     "boom_pct": 1.0,
     "bust_pct": 93.4,
     "boom_threshold": 41.32,
     "bust_threshold": 31.32,
     "value": -12.5,
     "pts_per_dollar": 3.0
    },
    {
     "player_id": "nfl-wr-19",
     "name": "Synthetic KC WR1",
     "team": "KC",
     "opponent": "BUF",
     "positions": [
      "WR"
     ],
     "salary": 6394.0,
     "projection": 18.75,
     "stddev": 10.2,
     "ceiling": 24.86,
     "floor": 11.22,
     "boom_pct": 2.8,
     "bust_pct": 89.3,
     "boom_threshold": 41.97,
     "bust_threshold": 31.97,
     "value": -13.22,
     "pts_per_dollar": 2.93
    },
    {
     "player_id": "nfl-rb-17",
     "name": "Synthetic KC RB2",
     "team": "KC",
     "opponent": "BUF",
     "positions": [
      "RB"
     ],
     "salary": 4339.0,
     "projection": 18.73,
     "stddev": 8.91,
     "ceiling": 23.98,
     "floor": 12.42,
     "boom_pct": 7.3,
     "bust_pct": 66.5,
     "boom_threshold": 31.7,
     "bust_threshold": 21.7,
     "value": -2.96,
     "pts_per_dollar": 4.32
    },
    {
     "player_id": "nfl-rb-3",
     "name": "Synthetic BUF RB1",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "RB"
     ],
     "salary": 6538.0,
     "projection": 18.64,
     "stddev": 8.83,
     "ceiling": 23.8,
     "floor": 12.12,
     "boom_pct": 1.0,
     "bust_pct": 93.1,
     "boom_threshold": 42.69,
     "bust_threshold": 32.69,
     "value": -14.05,
     "pts_per_dollar": 2.85
    },
    {
     "player_id": "nfl-qb-67",
     "name": "Synthetic PHI QB2",
     "team": "PHI",
     "opponent": "DET",
     "positions": [
      "QB"
     ],
     "salary": 6386.0,
     "projection": 18.52,
     "stddev": 7.74,
     "ceiling": 23.1,
     "floor": 12.91,
     "boom_pct": 0.8,
     "bust_pct": 94.7,
     "boom_threshold": 41.93,
     "bust_threshold": 31.93,
     "value": -13.41,
     "pts_per_dollar": 2.9
    },
    {
     "player_id": "nfl-rb-16",
     "name": "Synthetic KC RB1",
     "team": "KC",
     "opponent": "BUF",
     "positions": [
      "RB"
     ],
     "salary": 6242.0,
     "projection": 18.44,
     "stddev": 8.67,
     "ceiling": 23.29,
     "floor": 12.2,
     "boom_pct": 1.6,
     "bust_pct": 90.9,
     "boom_threshold": 41.21,
     "bust_threshold": 31.21,
     "value": -12.77,
     "pts_per_dollar": 2.95
    },
    {
     "player_id": "nfl-qb-66",
     "name": "Synthetic PHI QB1",
     "team": "PHI",
     "opponent": "DET",
     "positions": [
      "QB"
     ],
     "salary": 6086.0,
     "projection": 18.11,
     "stddev": 7.58,
     "ceiling": 22.33,
     "floor": 12.89,
     "boom_pct": 0.9,
     "bust_pct": 93.2,
     "boom_threshold": 40.43,
     "bust_threshold": 30.43,
     "value": -12.32,
     "pts_per_dollar": 2.98
    },
    {
     "player_id": "nfl-wr-74",
     "name": "Synthetic PHI WR4",
     "team": "PHI",
     "opponent": "DET",
     "positions": [
      "WR"
     ],
     "salary": 6732.0,
     "projection": 18.08,
     "stddev": 9.6,
     "ceiling": 23.7,
     "floor": 11.06,
     "boom_pct": 1.4,
     "bust_pct": 93.2,
     "boom_threshold": 43.66,
     "bust_threshold": 33.66,
     "value": -15.58,
     "pts_per_dollar": 2.69
    },
    {
     "player_id": "nfl-wr-6",
     "name": "Synthetic BUF WR1",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "WR"
     ],
     "salary": 6660.0,
     "projection": 17.98,
     "stddev": 9.98,
     "ceiling": 23.86,
     "floor": 10.41,
     "boom_pct": 1.8,
     "bust_pct": 91.4,
     "boom_threshold": 43.3,
     "bust_threshold": 33.3,
     "value": -15.32,
     "pts_per_dollar": 2.7
    },
    {
     "player_id": "nfl-te-11",
     "name": "Synthetic BUF TE1",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "TE"
     ],
     "salary": 4015.0,
     "projection": 17.94,
     "stddev": 10.21,
     "ceiling": 23.93,
     "floor": 10.58,
     "boom_pct": 11.5,
     "bust_pct": 63.8,
     "boom_threshold": 30.07,
     "bust_threshold": 20.07,
     "value": -2.13,
     "pts_per_dollar": 4.47
    },
    {
     "player_id": "nfl-rb-42",
     "name": "Synthetic SF RB1",
     "team": "SF",
     "opponent": "DAL",
     "positions": [
      "RB"
     ],
     "salary": 6972.0,
     "projection": 17.92,
     "stddev": 7.94,
     "ceiling": 22.75,
     "floor": 12.14,
     "boom_pct": 0.1,
     "bust_pct": 97.1,
     "boom_threshold": 44.86,
     "bust_threshold": 34.86,
     "value": -16.94,
     "pts_per_dollar": 2.57
    },
    {
     "player_id": "nfl-qb-28",
     "name": "Synthetic DAL QB2",
     "team": "DAL",
     "opponent": "SF",
     "positions": [
      "QB"
     ],
     "salary": 6555.0,
     "projection": 17.79,
     "stddev": 7.28,
     "ceiling": 22.21,
     "floor": 12.33,
     "boom_pct": 0.4,
     "bust_pct": 96.7,
     "boom_threshold": 42.77,
     "bust_threshold": 32.77,
     "value": -14.99,
     "pts_per_dollar": 2.71
    },
    {
     "player_id": "nfl-wr-71",
     "name": "Synthetic PHI WR1",
     "team": "PHI",
     "opponent": "DET",
     "positions": [
      "WR"
     ],
     "salary": 4875.0,
     "projection": 17.51,
     "stddev": 9.57,
     "ceiling": 22.4,
     "floor": 10.84,
     "boom_pct": 5.5,
     "bust_pct": 78.8,
     "boom_threshold": 34.38,
     "bust_threshold": 24.38,
     "value": -6.86,
     "pts_per_dollar": 3.59
    },
    {
     "player_id": "nfl-rb-4",
     "name": "Synthetic BUF RB2",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "RB"
     ],
     "salary": 4396.0,
     "projection": 17.47,
     "stddev": 8.9,
     "ceiling": 22.45,
     "floor": 10.96,
     "boom_pct": 6.4,
     "bust_pct": 73.5,
     "boom_threshold": 31.98,
     "bust_threshold": 21.98,
     "value": -4.51,
     "pts_per_dollar": 3.97
    },
    {
     "player_id": "nfl-rb-30",
     "name": "Synthetic DAL RB2",
     "team": "DAL",
     "opponent": "SF",
     "positions": [
      "RB"
     ],
     "salary": 5145.0,
     "projection": 17.37,
     "stddev": 8.26,
     "ceiling": 22.48,
     "floor": 11.16,
     "boom_pct": 2.9,
     "bust_pct": 84.5,
     "boom_threshold": 35.72,
     "bust_threshold": 25.72,
     "value": -8.35,
     "pts_per_dollar": 3.38
    },
    {
     "player_id": "nfl-wr-32",
     "name": "Synthetic DAL WR1",
     "team": "DAL",
     "opponent": "SF",
     "positions": [
      "WR"
     ],
     "salary": 4736.0,
     "projection": 17.33,
     "stddev": 9.77,
     "ceiling": 23.02,
     "floor": 10.35,
     "boom_pct": 7.2,
     "bust_pct": 76.5,
     "boom_threshold": 33.68,
     "bust_threshold": 23.68,
     "value": -6.35,
     "pts_per_dollar": 3.66
    },
    {
     "player_id": "nfl-wr-7",
     "name": "Synthetic BUF WR2",
     "team": "BUF",
     "opponent": "KC",
     "positions": [
      "WR"
     ],
     "salary": 6812.0,
     "projection": 17.25,
     "stddev": 9.87,
     "ceiling": 23.33,
     "floor": 9.84,
     "boom_pct": 1.0,
     "bust_pct": 93.5,
     "boom_threshold": 44.06,
     "bust_threshold": 34.06,
     "value": -16.81,
     "pts_per_dollar": 2.53
    },
    {
     "player_id": "nfl-rb-29",
     "name": "Synthetic DAL RB1",
     "team": "DAL",
     "opponent": "SF",
     "positions": [
      "RB"
     ],
     "salary": 4346.0,
     "projection": 16.69,
     "stddev": 7.95,
     "ceiling": 21.23,
     "floor": 11.1,
     "boom_pct": 5.0,
     "bust_pct": 77.2,
     "boom_threshold": 31.73,
     "bust_threshold": 21.73,
     "value": -5.04,
     "pts_per_dollar": 3.84
    }
   ],
   "ownership_top": [
    {
     "name": "Synthetic DAL WR4",
     "team": "DAL",
     "positions": [
      "WR"
     ],
     "salary": 3979.0,
     "ownership_pct": 88.0
    },
    {
     "name": "Synthetic BUF TE1",
     "team": "BUF",
     "positions": [
      "TE"
     ],
     "salary": 4015.0,
     "ownership_pct": 83.0
    },
    {
     "name": "Synthetic KC RB2",
     "team": "KC",
     "positions": [
      "RB"
     ],
     "salary": 4339.0,
     "ownership_pct": 69.0
    },
    {
     "name": "Synthetic DAL DST1",
     "team": "DAL",
     "positions": [
      "DST"
     ],
     "salary": 2366.0,
     "ownership_pct": 53.0
    },
    {
     "name": "Synthetic PHI WR1",
     "team": "PHI",
     "positions": [
      "WR"
     ],
     "salary": 4875.0,
     "ownership_pct": 53.0
    },
    {
     "name": "Synthetic SF WR1",
     "team": "SF",
     "positions": [
      "WR"
     ],
     "salary": 5358.0,
     "ownership_pct": 47.0
    },
    {
     "name": "Synthetic BUF RB2",
     "team": "BUF",
     "positions": [
      "RB"
     ],
     "salary": 4396.0,
     "ownership_pct": 46.5
    },
    {
     "name": "Synthetic DAL WR1",
     "team": "DAL",
     "positions": [
      "WR"
     ],
     "salary": 4736.0,
     "ownership_pct": 46.5
    },
    {
     "name": "Synthetic DAL RB1",
     "team": "DAL",
     "positions": [
      "RB"
     ],
     "salary": 4346.0,
     "ownership_pct": 45.0
    },
    {
     "name": "Synthetic DET RB1",
     "team": "DET",
     "positions": [
      "RB"
     ],
     "salary": 4933.0,
     "ownership_pct": 44.0
    },
    {
     "name": "Synthetic BUF QB1",
     "team": "BUF",
     "positions": [
      "QB"
     ],
     "salary": 6049.0,
     "ownership_pct": 24.5
    },
    {
     "name": "Synthetic DET DST1",
     "team": "DET",
     "positions": [
      "DST"
     ],
     "salary": 2553.0,
     "ownership_pct": 20.5
    },
    {
     "name": "Synthetic KC TE2",
     "team": "KC",
     "positions": [
      "TE"
     ],
     "salary": 3834.0,
     "ownership_pct": 17.5
    },
    {
     "name": "Synthetic KC WR5",
     "team": "KC",
     "positions": [
      "WR"
     ],
     "salary": 4231.0,
     "ownership_pct": 16.0
    },
    {
     "name": "Synthetic DAL RB2",
     "team": "DAL",
     "positions": [
      "RB"
     ],
     "salary": 5145.0,
     "ownership_pct": 16.0
    }
   ],
   "lineups": [
    {
     "label": "lineup_1",
     "method": "milp",
     "salary": 49596.0,
     "projected": 191.37,
     "players": [
      {
       "name": "Synthetic BUF QB2",
       "positions": [
        "QB"
       ],
       "team": "BUF",
       "salary": 6264.0
      },
      {
       "name": "Synthetic KC RB1",
       "positions": [
        "RB"
       ],
       "team": "KC",
       "salary": 6242.0
      },
      {
       "name": "Synthetic KC RB2",
       "positions": [
        "RB"
       ],
       "team": "KC",
       "salary": 4339.0
      },
      {
       "name": "Synthetic DAL WR4",
       "positions": [
        "WR"
       ],
       "team": "DAL",
       "salary": 3979.0
      },
      {
       "name": "Synthetic DAL DST1",
       "positions": [
        "DST"
       ],
       "team": "DAL",
       "salary": 2366.0
      },
      {
       "name": "Synthetic SF WR1",
       "positions": [
        "WR"
       ],
       "team": "SF",
       "salary": 5358.0
      },
      {
       "name": "Synthetic DET TE1",
       "positions": [
        "TE"
       ],
       "team": "DET",
       "salary": 7086.0
      },
      {
       "name": "Synthetic PHI RB1",
       "positions": [
        "RB"
       ],
       "team": "PHI",
       "salary": 7230.0
      },
      {
       "name": "Synthetic PHI WR4",
       "positions": [
        "WR"
       ],
       "team": "PHI",
       "salary": 6732.0
      }
     ],
     "roi_pct": 603.0,
     "cash_rate_pct": 48.8,
     "win_rate_pct": 2.6,
     "median_rank": 130.0,
     "mean_percentile": 70.6
    },
    {
     "label": "lineup_2",
     "method": "milp",
     "salary": 48817.0,
     "projected": 191.22,
     "players": [
      {
       "name": "Synthetic BUF QB2",
       "positions": [
        "QB"
       ],
       "team": "BUF",
       "salary": 6264.0
      },
      {
       "name": "Synthetic KC RB1",
       "positions": [
        "RB"
       ],
       "team": "KC",
       "salary": 6242.0
      },
      {
       "name": "Synthetic DAL WR4",
       "positions": [
        "WR"
       ],
       "team": "DAL",
       "salary": 3979.0
      },
      {
       "name": "Synthetic DAL DST1",
       "positions": [
        "DST"
       ],
       "team": "DAL",
       "salary": 2366.0
      },
      {
       "name": "Synthetic SF WR1",
       "positions": [
        "WR"
       ],
       "team": "SF",
       "salary": 5358.0
      },
      {
       "name": "Synthetic DET RB1",
       "positions": [
        "RB"
       ],
       "team": "DET",
       "salary": 4933.0
      },
      {
       "name": "Synthetic DET WR1",
       "positions": [
        "WR"
       ],
       "team": "DET",
       "salary": 5359.0
      },
      {
       "name": "Synthetic DET TE1",
       "positions": [
        "TE"
       ],
       "team": "DET",
       "salary": 7086.0
      },
      {
       "name": "Synthetic PHI RB1",
       "positions": [
        "RB"
       ],
       "team": "PHI",
       "salary": 7230.0
      }
     ],
     "roi_pct": 668.1,
     "cash_rate_pct": 42.0,
     "win_rate_pct": 3.2,
     "median_rank": 170.0,
     "mean_percentile": 66.1
    },
    {
     "label": "lineup_3",
     "method": "milp",
     "salary": 48372.0,
     "projected": 176.14,
     "players": [
      {
       "name": "Synthetic BUF RB1",
       "positions": [
        "RB"
       ],
       "team": "BUF",
       "salary": 6538.0
      },
      {
       "name": "Synthetic BUF TE1",
       "positions": [
        "TE"
       ],
       "team": "BUF",
       "salary": 4015.0
      },
      {
       "name": "Synthetic KC RB2",
       "positions": [
        "RB"
       ],
       "team": "KC",
       "salary": 4339.0
      },
      {
       "name": "Synthetic KC WR1",
       "positions": [
        "WR"
       ],
       "team": "KC",
       "salary": 6394.0
      },
      {
       "name": "Synthetic SF QB1",
       "positions": [
        "QB"
       ],
       "team": "SF",
       "salary": 6464.0
      },
      {
       "name": "Synthetic SF DST1",
       "positions": [
        "DST"
       ],
       "team": "SF",
       "salary": 3598.0
      },
      {
       "name": "Synthetic DET RB1",
       "positions": [
        "RB"
       ],
       "team": "DET",
       "salary": 4933.0
      },
      {
       "name": "Synthetic DET WR1",
       "positions": [
        "WR"
       ],
       "team": "DET",
       "salary": 5359.0
      },
      {
       "name": "Synthetic PHI WR4",
       "positions": [
        "WR"
       ],
       "team": "PHI",
       "salary": 6732.0
      }
     ],
     "roi_pct": 130.1,
     "cash_rate_pct": 24.1,
     "win_rate_pct": 0.7,
     "median_rank": 316.0,
     "mean_percentile": 51.0
    }
   ],
   "notes": [
    "Sample slates in src/data/samples are synthetic and labelled as such. They exist so the engine can be tested deterministically offline; they are not real salaries or real projections, and no report generated from them describes real players.",
    "lineups were built from a view of the projections as noisy as the field's (sd 25%): the honest-test setting. Building them from the model's own projections makes simulated ROI meaningless, because the field is given error and the lineup is not.",
    "ownership is a simulated-field estimate, not observed contest ownership",
    "the payout structure is ILLUSTRATIVE; ROI is only meaningful with the real contest payout table imported from a CSV",
    "compare each lineup's ROI with the field baseline in this same run: if a random field entry also earns far more than the rake, the number is about the field model, not the lineups",
    "lineup_1: simulated ROI 603% with a 49% cash rate. A cash rate near the paid fraction cannot justify that ROI unless the lineup is winning top prizes far more often than the field. Check (1) the field model, (2) whether the lineups were built on info the field lacked, (3) the payout structure.",
    "payout structure is illustrative, so ROI is a ranking aid only"
   ]
  }
 ],
 "reports": [
  {
   "file": "example_optimize_nfl.json",
   "keys": [
    "_provenance",
    "payload"
   ],
   "provenance": {
    "command": "python -m src.stokengineer.cli optimize --sample sample_nfl_dk.json",
    "engine_version": "0.4.0",
    "generated_at_utc": "2026-09-23T01:03:46+00:00",
    "notes": [
     "lineups built from a noisy view of the projections (sd 25%)",
     "Sample slates in src/data/samples are synthetic and labelled as such. They exist so the engine can be tested deterministically offline; they are not real salaries or real projections, and no report generated from them describes real players."
    ],
    "payload_sha256": "1918953a37f6ac3f6236d4f761e4b10ef49be412b6dea03204423825e73d574f",
    "platform": "Linux-6.1.158+-x86_64-with-glibc2.36",
    "python": "3.11.2",
    "sources": [
     {
      "id": "dk_lobby_api",
      "publisher": "DraftKings",
      "title": "DraftKings public lobby JSON",
      "url": "https://www.draftkings.com/lobby/getcontests?sport=NFL"
     },
     {
      "id": "dk_rules_mlb",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - MLB Classic",
      "url": "https://www.draftkings.com/help/rules/2"
     },
     {
      "id": "dk_rules_nba",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NBA Classic",
      "url": "https://www.draftkings.com/help/rules/4"
     },
     {
      "id": "dk_rules_nfl",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NFL Classic",
      "url": "https://www.draftkings.com/help/rules/1"
     },
     {
      "id": "dk_rules_nhl",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NHL Classic",
      "url": "https://www.draftkings.com/help/rules/3"
     },
     {
      "id": "espn_scoreboard",
      "publisher": "ESPN",
      "title": "ESPN public scoreboard/odds feed",
      "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
     },
     {
      "id": "nflverse_data",
      "publisher": "nflverse (open source project, not the NFL)",
      "title": "nflverse-data (open NFL data releases)",
      "url": "https://github.com/nflverse/nflverse-data"
     },
     {
      "id": "nflverse_injuries_asset",
      "publisher": "nflverse",
      "title": "nflverse injuries release asset",
      "url": "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2025.csv"
     },
     {
      "id": "nflverse_player_stats_asset",
      "publisher": "nflverse",
      "title": "nflverse player_stats release asset",
      "url": "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.csv"
     },
     {
      "id": "nflverse_schedules_asset",
      "publisher": "nflverse",
      "title": "nflverse schedules/games.csv release asset",
      "url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
     },
     {
      "id": "os_projection_system",
      "publisher": "OddsShopper / Stokastic",
      "title": "Stokastic projection system (OddsShopper, Stokastic's betting arm)",
      "url": "https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system"
     },
     {
      "id": "sk_home",
      "publisher": "Stokastic",
      "title": "Stokastic home page",
      "url": "https://www.stokastic.com/"
     },
     {
      "id": "sk_nfl_review",
      "publisher": "Stokastic",
      "title": "Stokastic Review 2026 (written by Stokastic)",
      "url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review"
     },
     {
      "id": "sk_pricing",
      "publisher": "Stokastic",
      "title": "Stokastic pricing and product FAQ",
      "url": "https://www.stokastic.com/pricing"
     },
     {
      "id": "splashplay_review",
      "publisher": "Splash Play Podcast",
      "title": "Third-party Stokastic review (2026)",
      "url": "https://splashplaypodcast.com/stokastic-review/"
     }
    ]
   },
   "kind": "python -m src.stokengineer.cli optimize --sample sample_nfl_dk.json"
  },
  {
   "file": "example_project_mlb.json",
   "keys": [
    "_provenance",
    "payload"
   ],
   "provenance": {
    "command": "python -m src.stokengineer.cli project --sample sample_mlb_dk.json",
    "engine_version": "0.4.0",
    "generated_at_utc": "2026-09-23T01:03:46+00:00",
    "notes": [
     "Sample slates in src/data/samples are synthetic and labelled as such. They exist so the engine can be tested deterministically offline; they are not real salaries or real projections, and no report generated from them describes real players."
    ],
    "payload_sha256": "ae7c1ee4ae091f6f6494a84e20b6fe557ec48669ac172ccce991994c1ba8b60b",
    "platform": "Linux-6.1.158+-x86_64-with-glibc2.36",
    "python": "3.11.2",
    "sources": [
     {
      "id": "dk_lobby_api",
      "publisher": "DraftKings",
      "title": "DraftKings public lobby JSON",
      "url": "https://www.draftkings.com/lobby/getcontests?sport=NFL"
     },
     {
      "id": "dk_rules_mlb",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - MLB Classic",
      "url": "https://www.draftkings.com/help/rules/2"
     },
     {
      "id": "dk_rules_nba",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NBA Classic",
      "url": "https://www.draftkings.com/help/rules/4"
     },
     {
      "id": "dk_rules_nfl",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NFL Classic",
      "url": "https://www.draftkings.com/help/rules/1"
     },
     {
      "id": "dk_rules_nhl",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NHL Classic",
      "url": "https://www.draftkings.com/help/rules/3"
     },
     {
      "id": "espn_scoreboard",
      "publisher": "ESPN",
      "title": "ESPN public scoreboard/odds feed",
      "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
     },
     {
      "id": "mlb_statsapi",
      "publisher": "MLB Advanced Media",
      "title": "MLB Stats API (official, keyless)",
      "url": "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-09-21&hydrate=team,linescore"
     },
     {
      "id": "os_projection_system",
      "publisher": "OddsShopper / Stokastic",
      "title": "Stokastic projection system (OddsShopper, Stokastic's betting arm)",
      "url": "https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system"
     },
     {
      "id": "sk_home",
      "publisher": "Stokastic",
      "title": "Stokastic home page",
      "url": "https://www.stokastic.com/"
     },
     {
      "id": "sk_mlb_datahub",
      "publisher": "Stokastic",
      "title": "How to use MLB DFS data (DataHub columns)",
      "url": "https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data"
     },
     {
      "id": "sk_mlb_ownership",
      "publisher": "Stokastic",
      "title": "MLB DFS ownership projections",
      "url": "https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections"
     },
     {
      "id": "sk_nfl_review",
      "publisher": "Stokastic",
      "title": "Stokastic Review 2026 (written by Stokastic)",
      "url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review"
     },
     {
      "id": "sk_pricing",
      "publisher": "Stokastic",
      "title": "Stokastic pricing and product FAQ",
      "url": "https://www.stokastic.com/pricing"
     },
     {
      "id": "splashplay_review",
      "publisher": "Splash Play Podcast",
      "title": "Third-party Stokastic review (2026)",
      "url": "https://splashplaypodcast.com/stokastic-review/"
     }
    ]
   },
   "kind": "python -m src.stokengineer.cli project --sample sample_mlb_dk.json"
  },
  {
   "file": "example_simulate_nfl.json",
   "keys": [
    "_provenance",
    "payload"
   ],
   "provenance": {
    "command": "python -m src.stokengineer.cli simulate --sample sample_nfl_dk.json",
    "engine_version": "0.4.0",
    "generated_at_utc": "2026-09-23T01:04:11+00:00",
    "notes": [
     "lineups were built from a noisy view of the projections (sd 25%); this models the user's own projection error",
     "ownership is a simulated-field estimate (see ownership.py); it is not observed contest ownership",
     "field model: 35% of entries draft with sharp error, the rest with a looser view (see ownership.generate_field_lineups). Simulated ROI is sensitive to this assumption and to the payout structure; read it as a ranking, not a forecast.",
     "lineup_1: simulated ROI 490% with a 37% cash rate. A cash rate near the paid fraction cannot justify that ROI unless the lineup is winning top prizes far more often than the field. Check (1) the field model, (2) whether the lineups were built on info the field lacked, (3) the payout structure.",
     "payout structure is illustrative, so ROI is a ranking aid only",
     "payout structure is ILLUSTRATIVE: supply the real contest payout (CSV) before treating any ROI here as expected money",
     "Sample slates in src/data/samples are synthetic and labelled as such. They exist so the engine can be tested deterministically offline; they are not real salaries or real projections, and no report generated from them describes real players."
    ],
    "payload_sha256": "a8c677f0573baf0b2ac51601ecc93150b93bfa2b09a4a11c08ea10f50ab3314c",
    "platform": "Linux-6.1.158+-x86_64-with-glibc2.36",
    "python": "3.11.2",
    "sources": [
     {
      "id": "dk_lobby_api",
      "publisher": "DraftKings",
      "title": "DraftKings public lobby JSON",
      "url": "https://www.draftkings.com/lobby/getcontests?sport=NFL"
     },
     {
      "id": "dk_rules_mlb",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - MLB Classic",
      "url": "https://www.draftkings.com/help/rules/2"
     },
     {
      "id": "dk_rules_nba",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NBA Classic",
      "url": "https://www.draftkings.com/help/rules/4"
     },
     {
      "id": "dk_rules_nfl",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NFL Classic",
      "url": "https://www.draftkings.com/help/rules/1"
     },
     {
      "id": "dk_rules_nhl",
      "publisher": "DraftKings",
      "title": "DraftKings Rules & Scoring - NHL Classic",
      "url": "https://www.draftkings.com/help/rules/3"
     },
     {
      "id": "espn_scoreboard",
      "publisher": "ESPN",
      "title": "ESPN public scoreboard/odds feed",
      "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
     },
     {
      "id": "nflverse_data",
      "publisher": "nflverse (open source project, not the NFL)",
      "title": "nflverse-data (open NFL data releases)",
      "url": "https://github.com/nflverse/nflverse-data"
     },
     {
      "id": "nflverse_injuries_asset",
      "publisher": "nflverse",
      "title": "nflverse injuries release asset",
      "url": "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2025.csv"
     },
     {
      "id": "nflverse_player_stats_asset",
      "publisher": "nflverse",
      "title": "nflverse player_stats release asset",
      "url": "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2025.csv"
     },
     {
      "id": "nflverse_schedules_asset",
      "publisher": "nflverse",
      "title": "nflverse schedules/games.csv release asset",
      "url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
     },
     {
      "id": "os_projection_system",
      "publisher": "OddsShopper / Stokastic",
      "title": "Stokastic projection system (OddsShopper, Stokastic's betting arm)",
      "url": "https://www.oddsshopper.com/articles/betting-101/stokastic-projection-system"
     },
     {
      "id": "sk_home",
      "publisher": "Stokastic",
      "title": "Stokastic home page",
      "url": "https://www.stokastic.com/"
     },
     {
      "id": "sk_nfl_review",
      "publisher": "Stokastic",
      "title": "Stokastic Review 2026 (written by Stokastic)",
      "url": "https://www.stokastic.com/articles/nfl-dfs/stokastic-review"
     },
     {
      "id": "sk_pricing",
      "publisher": "Stokastic",
      "title": "Stokastic pricing and product FAQ",
      "url": "https://www.stokastic.com/pricing"
     },
     {
      "id": "splashplay_review",
      "publisher": "Splash Play Podcast",
      "title": "Third-party Stokastic review (2026)",
      "url": "https://splashplaypodcast.com/stokastic-review/"
     }
    ]
   },
   "kind": "python -m src.stokengineer.cli simulate --sample sample_nfl_dk.json"
  }
 ],
 "limitations": [
  {
   "heading": "1. Simulated ROI is not yet a forecast (highest priority)",
   "body": "against an illustrative GPP payout curve. The engine now labels this itself"
  },
  {
   "heading": "2. Payout structures are user-supplied by design",
   "body": "No free source publishes contest payout tables as data. `PayoutStructure.from_csv` reads the table"
  },
  {
   "heading": "3. Correlation is a documented prior, not a calibrated measurement",
   "body": "Teammate correlation is imposed by `models.apply_teammate_correlation` at"
  },
  {
   "heading": "4. Model parameters are priors",
   "body": "Per-stat dispersions, minutes variance, team volume/scoring sigmas and MLB run/RBI propensities are"
  },
  {
   "heading": "5. Boom/bust thresholds are a published rule of thumb, applied across sports",
   "body": "`boom_threshold = 5 \u00d7 (salary/1000) + 10` and `bust_threshold = 5 \u00d7 (salary/1000)` come from"
  },
  {
   "heading": "6. FanDuel roster shapes and caps are third-party (claim `c18`)",
   "body": "`fanduel.com/rules` publishes scoring for all four sports but not classic roster shapes or salary"
  },
  {
   "heading": "7. Data-source irregularities flagged for review",
   "body": "* **`dk_lobby` (DraftKings lobby JSON) and `espn_scoreboard` are undocumented endpoints.** They are"
  },
  {
   "heading": "8. The forward test has not been executed in this environment",
   "body": "`forward-test --sport mlb` builds its inputs from **season totals minus the game being predicted**"
  },
  {
   "heading": "9. Scope that is knowingly incomplete",
   "body": "* **NHL** scoring and roster rules are transcribed and enforced, but there is no NHL projection"
  }
 ],
 "test_summary": {
  "passed": 88,
  "failed": 0,
  "skipped": 0
 }
};
