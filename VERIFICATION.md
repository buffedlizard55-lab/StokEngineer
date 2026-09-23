# Verification

How each class of statement in this repository was checked, what could not be checked, and what is
flagged for a human to look at. The machine-readable versions are
`src/data/sources_verified.json` (sources) and `src/data/claims.json` (claims).

## The mechanism

* **`sources_verified.json`** declares every external source with id, URL, publisher, what it
  provides, licence/terms, whether it is free, whether a key is required, whether it is the
  publisher's own page, and *how it was verified*:
  * `fetched_live` — read from the live page in the session that recorded it (13 sources);
  * `github_api` — verified through the GitHub API, including the licence file (5 sources);
  * `carried_over` — recorded in an earlier session and **not** re-fetched (11 sources). These are
    treated as unverified: no claim in this repository cites one as proof.
* **`claims.json`** records every factual assertion with the exact quote and the source id.
  Statuses: `verified` (19), `flagged` (5 — true as quoted but with a caveat a reader must know, or
  an undocumented endpoint), `not_verified` (1 — the one thing that simply cannot be known from
  outside: the paid product's internal weights).
* `Registry.validate()` fails on an undeclared source id, a duplicate id, a non-https URL or a
  missing verification marker. `python -m src.stokengineer.cli verify` runs that plus the rules
  integrity checks plus the sample-slate checks, and exits non-zero on any problem. CI runs it.
* Every report the CLI writes goes through `provenance.write_json_with_provenance`, which records
  the command, UTC timestamp, python/numpy versions, the payload's SHA-256 and the source ids the
  run relied on. `reports/` in this repo contains examples produced exactly that way.
* `tools/check_links.py` walks every URL in the data files, the site and the documentation and
  reports dead links. It is designed for CI (this sandbox blocks most hosts, so `doctor` reports
  `PARTIAL` rather than pretending otherwise). URLs that are deliberately not fetched (an http-only
  copyright notice, a test fixture that must stay unreachable) are listed as exempt, with reasons.
* `tools/check_site_data.py` regenerates the site payload and compares it with the committed copy.
  Claim-level sections (sources, claim ledger, rules, limitations, integrity status) must match
  **exactly** or the build fails. The demo section is a live engine run, and optimisation ties are
  not portable between machines, so drift there is reported as a warning - with the numbers - rather
  than silently accepted or falsely declared identical. Nothing about the demo is used as evidence
  for any claim on the site.

## What was verified, and how

| Claim area | Source | How |
| --- | --- | --- |
| DraftKings scoring, roster shape, caps, multi-game rules (NFL, NBA, MLB, NHL) | `dk_rules_*` | page fetched live; every coefficient transcribed into `scoring_rules.json` / `roster_rules.json` next to its source id |
| FanDuel scoring (all four sports) | `fd_rules` | page fetched live; roster shapes/caps deliberately left third-party and flagged |
| MLB schedules, box scores, season aggregates are keyless and official | `mlb_statsapi` | endpoints called live; response shapes confirmed field-by-field; parsed in `ingest.py` |
| Game odds → implied team totals | `espn_scoreboard`, `sk_nfl_defense` | odds structure read live; the published formula is reproduced and unit-tested against its worked example |
| Contest metadata (entry fee, prize pool, draft group) is available keyless | `dk_lobby` | endpoint called live; values matched a real contest; flagged as undocumented |
| Published DFS methodology being reimplemented (boom/bust, value, points-per-$) | `sk_nba_boom_bust`, `sk_nba_projections` | both articles fetched live; the formulas are quoted in the claim ledger and implemented with unit tests |
| Simulation methodology (correlated sims, ownership-weighted field, ROI-ranked lineups, late swap) | `sk_nfl_review` | review article fetched live; drives the simulator's design |
| Historical player data is free and openly licensed | `nflverse_data` + assets (CC-BY-4.0), `nba_api` (MIT) | repo metadata and licence files read through the GitHub API |
| The engine's own behaviour | this repository | 100 tests: rule legality (including the double-double and points-allowed bugs), model distributions, correlation calibration, optimiser legality and solver-vs-fallback agreement, payout arithmetic, leak-free forward-test inputs, registry integrity |

## What could **not** be verified here

* **Live data integration end to end.** This sandbox blocks `statsapi.mlb.com`, `espn`, and
  `draftkings.com` (see `doctor`). Shapes and URLs were confirmed by fetching pages, parsers are
  unit-tested against those shapes, and the forward test is implemented — but it has not been
  executed against live MLB data from here. Run it in CI or locally.
* **Anything behind a login or a paywall.** No credentials were used or requested anywhere in this
  work. Stokastic's internal projection weights, sigma model and ownership coefficients are
  explicitly recorded as `not_verified` (`c24`) because they cannot be honestly obtained.
* **FanDuel classic roster shapes and salary caps** (`c18`): not published on the official rules
  page that was checked.

## Flagged irregularities (for a human to review)

1. `https://www.draftkings.com/lobby/getcontests` and the ESPN scoreboard are **undocumented**
   endpoints. Public, keyless, live-verified — but not published contracts. Best-effort with CSV
   fallbacks, and their terms are worth a human read before heavy use. (`c21`, `c22`)
2. **FanDuel roster/cap gap** (`c18`) — third-party values in use for FanDuel lineups; scoring is
   official, roster shapes are not.
3. **MLB box scores are large** (23 fetch-page chunks) and carry MLB's copyright notice; the
   response shape was confirmed from the visible region, and the parser handles the fields it needs.
4. **Boom/bust thresholds are borrowed from an NBA article** and applied to all sports; they are
   aggressive where the salary-to-points relationship differs (notably MLB pitchers). (`c05`, `c07`)
5. Nine URLs recorded in earlier sessions were **downgraded** rather than silently reused; they are
   listed in `sources_verified.json → removed_or_downgraded` with the reason, and no claim cites
   them as verified.

## Reproducing this verification

```bash
pip install -r requirements.txt
python -m src.stokengineer.cli doctor          # environment, hosts actually reachable, registry
python -m src.stokengineer.cli verify          # registry + claims + rules + sample integrity
python -m src.stokengineer.cli rules --site draftkings --sport nfl   # every number + its source
pytest                                          # the behaviour claims above
python tools/check_links.py                     # every cited URL (needs network)
python tools/make_sample_data.py --check        # fixtures are reproducible, not hand-edited
python tools/build_site_data.py                 # rebuild the site data from the above
```
