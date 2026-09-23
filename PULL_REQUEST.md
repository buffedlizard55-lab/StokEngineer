# Pull request — open DFS engine, verified sources, site and CI

Branch: `arena/01a0cb67-stokengineer` → `main`
Status when written: committed locally (`0924199`); **push blocked** because the GitHub token in this
environment is no longer valid (`gh auth status`: "The github.com token in GH_TOKEN is no longer
valid"). Reconnect GitHub in Arena, then:

```bash
git push -u origin arena/01a0cb67-stokengineer
gh pr create --base main --head arena/01a0cb67-stokengineer \
  --title "Open, source-verified DFS engine, site and CI" --body-file PULL_REQUEST.md
gh pr merge --squash --delete-branch=false
```

## What this does

Builds the thing the brief asked for, end to end, on **free data only**: no premium feeds, no
subscriptions, no manual data entry, and every assertion carrying the link a human needs to check it.

* **Engine** (`src/stokengineer/`, ~6k lines): rules loader and exact validator, per-sport stat-line
  simulators scored with the sites' own tables, team-latent correlation with a marginal-preserving
  calibration, a simulated ownership field, an exact MILP lineup optimiser with a branch-and-bound
  fallback, contest simulation with ranks and payouts, projection metrics, a leak-free MLB forward
  test, and free keyless ingestion (MLB StatsAPI, ESPN, nflverse, `nba_api`).
* **CLI**: `doctor`, `rules`, `project`, `ownership`, `optimize`, `simulate`, `backtest`,
  `forward-test`, `site-data`, `verify`.
* **Verification machinery**: `src/data/sources_verified.json` (29 sources, each with how it was
  verified), `src/data/claims.json` (25 claims with quotes), `Registry.validate()` fails on an
  undeclared source, every report carries a provenance envelope, `verify` and `doctor` are wired
  into CI, and the site payload is regenerated and diffed so the site cannot drift from the code.
* **Site** (`docs/`): data-driven GitHub Pages page — verified rules per site/sport, a real engine
  run on the synthetic samples, the source registry with verification status, the full claims ledger
  with filter boxes, the limitations rendered from `LIMITATIONS.md`, and a "next steps" section.

## What the numbers say (and what they do not)

The demo prints the engine's lineups **next to** the controls that make them readable: a random
sample of the same simulated field (ROI −18% to −21%, i.e. near the rake — the sanity check a
contest simulator must pass) and the field's best decile (−10% to −1%). The optimiser's own ROI
ranges from +43% to +668% **across independent noisy draws of its own projections**, which is the
honest headline: bigger than any difference between builds, so it is a ranking aid, not a forecast.
`LIMITATIONS.md` §1 has the table and the mechanism (a still-clustered synthetic field + a top-heavy
illustrative payout), plus the fix list.

## Verification

* `python -m pytest -q` → **86 passed, 0 failed, 0 skipped**.
* `python -m src.stokengineer.cli verify` → `verify: OK`; `doctor` → registry/rules OK, network
  `PARTIAL` in this sandbox (MLB/ESPN/DraftKings hosts blocked; the engine raises `OfflineError`
  instead of inventing data).
* `python tools/make_sample_data.py --check` → sample fixtures reproduce byte-for-byte.
* `python tools/check_site_data.py` → the committed site payload matches a fresh build.

## Known gaps (documented, not hidden)

1. **Simulated ROI is not a forecast** until the field model is calibrated against real ownership
   exports — `LIMITATIONS.md` §1.
2. **Correlation and model parameters are documented priors**, not fitted values (§3, §4).
3. **Boom/bust thresholds come from an NBA article** and are applied to all sports (§5).
4. **FanDuel roster shapes/caps are third-party** because FanDuel does not publish them (§6).
5. **The MLB forward test is implemented but unrun here** — this sandbox cannot reach MLB (§8).
6. **NHL has no projection model**, NBA has no sample slate, and late swap / showdown formats are
   not implemented (§9).
7. **Eleven earlier-session sources are marked `carried_over`** and are never cited as proof; a
   future session should re-fetch or drop them.
