# Limitations and open work

This file is deliberately uncomfortable to read. It lists what is **not** trustworthy yet, what is
unverified, and what a reviewer should attack first. Nothing here is hidden in code comments.

## 1. Simulated ROI is not yet a forecast (highest priority)

**Symptom.** On the synthetic samples the contest simulator reports ROI in the hundreds of percent
against an illustrative GPP payout curve. The engine now labels this itself
(`simulate.plausibility_warnings`) and the site prints the controls below next to every number.

**What was measured** (one build of `tools/build_site_data.py`, 600-entry field, 1,000 simulations,
illustrative payout, synthetic slates — reproducible from this repository):

| Measurement | NFL sample | MLB sample |
| --- | --- | --- |
| Field baseline: random simulated entries scored as if they were the user | −20.9% | −18.2% |
| Best decile of that same field, by mean simulated score | −0.8% | −10.1% |
| Engine lineups built from a 25%-noise view (one draw) | +130% … +668% | +206% … +398% |
| The same optimiser across six independent noisy draws | +86% … +296% | +43% … +448% |

**What that means.** Two things, and both matter:

1. The simulator is *internally* consistent: a random field entry lands near the rake (−18% to
   −21%), which is the sanity check any contest simulator must pass. The field also drafts with the
   same machinery as the user (26% of entries run a bounded branch-and-bound search, the rest a
   first-fit search, spread over four documented strategies), so the gap is not "solver versus
   pushovers" any more.
2. The engine's lineups still clear the field by far more than a real edge would, and the spread
   across draws (43%–448% for the *same* method) is larger than any difference between builds. The
   mechanism is the obvious one: with a top-heavy payout, ROI is dominated by the right tail, and a
   differentiated lineup takes the top prizes far more often against a *clustered* field than it
   would against a realistic one. Our synthetic field is still clustered (mean pairwise lineup
   correlation ≈ 0.65) because the synthetic slates are small — 78 NFL players, 120 MLB players,
   versus 300+ on a real slate — so every entry leans on the same handful of players.

**Therefore: ROI from this engine is a ranking aid between builds, never an expectation.** The
engine says so in every report, in the site, and here. The honest fixes, in order:

1. calibrate the field against **real, free ownership exports** (a user's own contest results CSV
   contains actual ownership) so `OwnershipModel.features` weights are fitted rather than assumed;
2. calibrate `sharp_share` (0.35), `noise` (25% / 8%), `strong_share` (25%), `max_player_share`
   (50%) and `strategy_weights` from the same exports — they are documented priors today;
3. run the demo on a **full-size slate** rather than a synthetic one, where the field is naturally
   more diverse;
4. replace the illustrative payout curve with the user's real contest table
   (`PayoutStructure.from_csv`) and publish the ROI *distribution* (mean, spread, percentiles)
   rather than a single number.

## 2. Payout structures are user-supplied by design

No free source publishes contest payout tables as data. `PayoutStructure.from_csv` reads the table
from a contest the user actually entered (DraftKings shows it on the contest page). The built-in
`illustrative_gpp` / `flat_cash` builders exist to exercise the machinery, are labelled
`ILLUSTRATIVE` in their `source` field, and appear in `SlateRun.notes` whenever they are used.
A rake of 12% and a min-cash of 1.7× the entry fee are documented assumptions, not measurements.

## 3. Correlation is a documented prior, not a calibrated measurement

Teammate correlation is imposed by `models.apply_teammate_correlation` at
`target_teammate_correlation` (default 0.12), which currently produces ≈ 0.36 measured within-team
correlation and ≈ 0.07 across the slate. Real DFS correlations vary by position pair (QB–WR1 ≫
RB–WR3). Calibrating a per-position-pair matrix from free historical data (nflverse play-by-play,
MLB box scores) is outstanding work; the hook is `SimulationConfig.from_history` plus
`correlation.py`.

## 4. Model parameters are priors

Per-stat dispersions, minutes variance, team volume/scoring sigmas and MLB run/RBI propensities are
priors chosen to look like real DFS distributions, not fitted values. `SimulationConfig.from_history`
can fit a single multiplicative dispersion scale from game logs; wiring it to real logs (nflverse,
MLB StatsAPI, nba_api) is the obvious next step and needs no paid data.

## 5. Boom/bust thresholds are a published rule of thumb, applied across sports

`boom_threshold = 5 × (salary/1000) + 10` and `bust_threshold = 5 × (salary/1000)` come from
Stokastic's **NBA** boom/bust article (claim `c05`/`c07`). They are applied uniformly here, which
makes them aggressive for, e.g., MLB pitchers. Per-sport calibration (the salary/points relationship
differs by position) is not done. The formula is displayed with its source so a reader can see
exactly what is being applied.

## 6. FanDuel roster shapes and caps are third-party (claim `c18`)

`fanduel.com/rules` publishes scoring for all four sports but not classic roster shapes or salary
caps. Those entries in `src/data/roster_rules.json` are marked `"verified": "third-party"`, are used
only when a user explicitly asks for `--site fanduel`, and should be replaced the moment FanDuel
publishes them (or confirmed from a user's own salary export).

## 7. Data-source irregularities flagged for review

* **`dk_lobby` (DraftKings lobby JSON) and `espn_scoreboard` are undocumented endpoints.** They are
  public and keyless, they were live-verified in this session, and they are the free way to get live
  contest metadata and game odds — but they are not published APIs. The engine treats them as
  best-effort, caches every response, and has CSV fallbacks. If they change or their terms forbid
  automated use, the CSV path still works. (Claims `c21`, `c22`.)
* **MLB StatsAPI box scores exceed a single page fetch** (23 chunks in this session's environment).
  The shape was verified, and parsed in code, but that path has not been executed end-to-end here
  because this sandbox blocks `statsapi.mlb.com`.
* **MLB box scores carry MLB's copyright notice.** Records of facts are fine; redistributing the
  feed is not. `ingest.Fetcher` caches locally rather than republishing.

## 8. The forward test has not been executed in this environment

`forward-test --sport mlb` builds its inputs from **season totals minus the game being predicted**
(`ingest.forward_test_props`), which is the only version of that test that means anything. This
sandbox has no egress to MLB (see `doctor` — it reports `PARTIAL`), so the path is verified by unit
tests on the real response shapes and must be run in CI or on a machine with network access. It
raises `OfflineError` rather than fabricating results.

The same applies to nflverse ingestion: asset names and licence were verified through the GitHub
API; downloads have not run here.

## 9. Scope that is knowingly incomplete

* **NHL** scoring and roster rules are transcribed and enforced, but there is no NHL projection
  model and no NHL sample slate. `project --sport nhl` is not implemented.
* **NBA** has a projection model but no sample slate and no forward test (free NBA data needs
  `nba_api`, which is a separate optional dependency).
* **Late swap** (swapping players in lineups after a game starts) is not implemented.
* **Showdown / single-game** contests are not modelled (DK's showdown salary caps and captain
  multipliers came up in the pricing source but are not transcribed).
* **Entries-per-player exposure limits across multiple contests** are not modelled.
* **Weather** (NWS hourly forecast is a free source) is not yet an input to any model.
* **Backtesting** is limited to what free historical data supports. Actual DFS points require a
  historical box-score/stats pull per sport; MLB is done, NFL/NBA need the nflverse/nba_api wiring.
