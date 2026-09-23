# Three-pass build log

The brief was explicit: implement, then review for bugs/missing requirements/wrong assumptions/edge
cases, then re-check the whole thing against the original request. This is what each pass actually
found. Every item below is either fixed, or listed in `LIMITATIONS.md` with the reason it is not.

## Pass 1 — implement and verify

Built the engine (`src/stokengineer/`), the rule packs (`src/data/*.json`), the CLI, the synthetic
fixtures (`tools/make_sample_data.py`), the test suite and the site data builder
(`tools/build_site_data.py`). Verified every rule number against the sites' own pages, recorded each
source id, and made `verify` fail on an undeclared source.

Outcome: `pytest` 100 tests, `verify: OK`, CLI runs on both sample slates.

## Pass 2 — review: bugs, wrong assumptions, edge cases

Found by re-reading and by testing the assumptions rather than the happy path:

1. **The exact solver never ran.** The MILP summed a single `x[player]` variable over each slot
   group. For a roster with a FLEX slot that is arithmetically unsatisfiable (2 RB + 3 WR + 1 flex
   cannot be expressed as one shared binary per player), so CBC returned *Infeasible* and every
   "MILP" result in the documentation was silently the DFS fallback. Fixed with explicit
   `z[group, player]` assignment variables; there is now a regression test that fails if the solver
   returns no solution.
2. **The DFS fallback could not build a legal lineup at all** (it started at `depth = len(chosen)`
   after seating locked players and left the first slots unfilled). Rewritten as a real
   branch-and-bound search with an admissible upper bound, a first-fit phase so it always returns
   something legal, matching-based pruning for the remaining slots, and game/team/stack checks.
3. **Slot assignments named the wrong players.** `rules.assign_slots` indexes the list it is given
   (the chosen players), but the code indexed the slate with it, so reports showed nine players from
   one team next to a legal player list. Fixed, and `OptimizedLineup.slot_assignment` now maps
   slot → **player id** (indices do not survive serialisation).
4. **NumPy boolean addition saturates.** `True + True == True`, so the double-double predicate
   counted at most one category and DraftKings' +1.5 double-double bonus never fired for a real
   double-double. Fixed by casting hits to integers, with a regression test.
5. **Points-allowed tiers rejected simulated values.** The official tiers are whole numbers; a
   simulated 34.4 matched no tier and raised. Now rounded to the nearest integer, with a test.
6. **The forward test leaked the answer.** It built inputs from *full-season* rates including the
   game being predicted (on a season-to-date feed that leaks almost the entire result late in the
   year). Replaced with `ingest.forward_test_props`, which recomputes every rate from season totals
   minus that game's line, and box-score rows now carry the game context needed to do it.
7. **The field generator could produce illegal lineups** when applying stacks/bring-backs (swapping
   a player into a slot he cannot fill). Every rewritten lineup is now re-validated for slots,
   salary, the multi-game rule and the MLB hitter cap.
8. **The field was a field of pushovers.** It drafted by naive greedy while the user's lineups came
   from an exact solve, which is the main reason simulated ROI was fiction. Field entries now draft
   with the same search under their own noisy view, with a documented share cap.
9. **Teammate correlation was 0.09** — far too low for a stack to be worth anything, contradicting
   the verified claim that the sims must respect correlation. Added
   `models.apply_teammate_correlation`, which preserves each player's mean and standard deviation
   exactly and raises measured within-team correlation to ≈ 0.36 (tested both ways).
10. **Dead code and dropped results**: `simulate.flat_cash`'s unused `amount`, `field_sorted` built
    and deleted, a per-simulation Python loop over `payout_for_rank` (replaced by a dense lookup),
    `evaluate`'s `list.index()` inside a loop (O(n²)), `optimizer`'s `projections_placeholder`
    nan-sum, and a no-op `if "fanduel" in ...: pass`.
11. **The doctor claimed the network was reachable** because a raw socket to `1.1.1.1` succeeded,
    while every data host this engine needs was blocked. It now probes the actual hosts and reports
    `PARTIAL` with the blocked list.
12. **`tools/check_links.py` silently collected zero URLs** after the source-schema change (it
    reported success on an empty list). It now walks the tree and matches the current schema.

## Pass 3 — re-check against the original request

* *"Free, no premium, no trials, no subscriptions"* — every data path is keyless and free
  (`doctor` prints which hosts are reachable); nothing in the engine requires a paid feed, and the
  only paid product mentioned (Stokastic) is quoted as the thing being reimplemented.
* *"No manual input"* — slates come from JSON/CSV imports or `ingest`; sample fixtures are generated
  deterministically by `tools/make_sample_data.py --check`.
* *"Line by line verification with links"* — 29 sources with ids, 25 claims with quotes and source
  ids, enforced by `Registry.validate()` and `tests/test_provenance.py`.
* *"Flag irregularities"* — the DK lobby/ESPN endpoints, the FanDuel roster gap, the MLB fetch
  truncation and the boom/bust cross-sport application are all flagged in `LIMITATIONS.md` and on
  the site.
* *"Forward testing if backtesting is unavailable"* — the MLB forward test is implemented with a
  no-look-ahead input builder; this environment cannot reach MLB, so it is runnable but unrun here.
* *"Create a GitHub page"* — `docs/` is rebuilt from the registry, the claim ledger and a real
  engine run, and deploys through `.github/workflows/pages.yml`.
* *"PR then merge, and document what is left"* — see the pull request description and
  `LIMITATIONS.md` §1 (field calibration) and §9 (scope).

**What the final check changed:** the site no longer presents ROI as a headline number without the
plausibility warning beside it, the sample generator is now a committed tool instead of an inline
script, and the tests below were added specifically so the Pass-2 bugs cannot come back.


## Pass 3 (second review, after the first release candidate)

Re-reading the whole thing against the brief, plus measuring the things the earlier passes only
argued about:

13. **The simulated field was one strategy repeated N times.** Every entry drafted by the same
    projection-greedy rule, so entries were 0.90 correlated with each other and any lineup that
    differed from the crowd collected top prizes. The field now spreads over four documented
    strategies (projection-greedy, points-per-dollar, contrarian, ceiling mix) and a quarter of
    entries run a bounded branch-and-bound solve rather than a first-fit draft. Measured effect:
    pairwise lineup correlation 0.90 → 0.65, and the controls below became meaningful. The weights
    (`strategy_weights`, `strong_share`) are documented priors, not calibrated values.
14. **The demo published ROI with no control.** It now prints, in the same run, the ROI of a random
    sample of the field and of the field's best decile, plus the spread of the same optimiser across
    six independent noisy draws. Those numbers are what show a reader that a single ROI figure is
    mostly tail luck — and they are the honest answer to "does this thing actually win?".
15. **`tools/build_site_data.py` needed a reproducible timestamp**, otherwise the CI check that
    fails on stale site data could never pass. It now takes the timestamp from `SOURCE_DATE_EPOCH`
    or the HEAD commit, not the clock.
16. **The site could have drifted from the engine.** It renders `LIMITATIONS.md` at build time
    (so a limitation cannot be quietly dropped from the page), and CI rebuilds the payload and fails
    if the committed copy differs.
17. **README, LIMITATIONS, VERIFICATION and PASSES were re-read line by line against the code** -
    every command, module and number in them now matches what the repository actually does, and the
    measured ROI table in `LIMITATIONS.md` §1 was replaced with this session's real numbers rather
    than the earlier, weaker field's.
