"""Contest simulation and metric tests."""
import numpy as np
import pytest

from src.stokengineer.evaluate import (
    assert_no_leakage,
    brier_score,
    mae,
    reliability_table,
    rmse,
    r2,
    spearman,
    top_n_overlap,
)
from src.stokengineer.models import load_sample_slate, simulate_fantasy_points
from src.stokengineer.simulate import PayoutStructure, simulate_contest


def test_illustrative_payout_is_well_formed_and_rake_is_within_pool():
    payout = PayoutStructure.illustrative_gpp(entries=1000, entry_fee=20.0)
    assert payout.paid_entries == 200
    assert payout.total_pool <= payout.cost + 1e-6
    assert 0 < payout.rake < 0.2
    assert payout.payout_for_rank(1) > payout.payout_for_rank(2) > payout.payout_for_rank(199)
    assert payout.payout_for_rank(500) == 0
    # min cash must be a plausible multiple of the entry fee, not a jackpot
    assert payout.payout_for_rank(200) == pytest.approx(20 * 1.7)
    # and the tiers must reconstruct the pool within rounding
    reconstructed = sum(
        tier.amount * (tier.end_rank - tier.start_rank + 1) for tier in payout.tiers
    )
    assert reconstructed == pytest.approx(20000 * 0.88, rel=1e-9)


def test_illustrative_payout_refuses_to_promise_more_than_the_pool():
    with pytest.raises(ValueError):
        PayoutStructure.illustrative_gpp(entries=100, entry_fee=1.0, paid_fraction=0.9,
                                         min_cash_multiple=5.0)


def test_payout_validation_catches_bad_structures():
    with pytest.raises(ValueError):
        PayoutStructure.from_tiers(100, 10.0, [
            {"start_rank": 1, "end_rank": 10, "amount": 20},
            {"start_rank": 5, "end_rank": 20, "amount": 10},
        ])
    with pytest.raises(ValueError):
        PayoutStructure.from_tiers(10, 10.0, [{"start_rank": 1, "end_rank": 10, "amount": 20}])
    with pytest.raises(ValueError):
        PayoutStructure.from_tiers(100, 10.0, [{"start_rank": 1, "end_rank": 200, "amount": 1}])


def _toy_contest(user_is_best: bool):
    n_sims, n_players, roster = 40, 3, 2
    matrix = np.zeros((n_sims, n_players))
    matrix[:, 0] = 10
    matrix[:, 1] = 5
    matrix[:, 2] = 1
    payout = PayoutStructure.from_tiers(
        entries=4, entry_fee=10.0,
        tiers=[{"start_rank": 1, "end_rank": 1, "amount": 30.0}],
        source="test",
    )
    user = [[0, 1]] if user_is_best else [[1, 2]]
    field = [[0, 1], [0, 2], [1, 2]]
    (result,) = simulate_contest(matrix, user, payout, field_lineups=field)
    return result


def test_simulate_contest_rewards_the_better_lineup():
    best = _toy_contest(True)
    worst = _toy_contest(False)
    assert best.roi_pct > worst.roi_pct
    assert best.cash_rate_pct == 100.0
    assert best.win_rate_pct == 100.0
    assert worst.cash_rate_pct == 0.0
    assert worst.roi_pct == pytest.approx(-100.0)


def test_metrics_match_hand_calculations():
    predicted = np.array([1.0, 2.0, 3.0, 4.0])
    actual = np.array([1.0, 2.0, 3.0, 5.0])
    assert mae(predicted, actual) == pytest.approx(0.25)
    assert rmse(predicted, actual) == pytest.approx(0.5)
    # ss_res = 1, ss_tot = 8.75
    assert r2(predicted, actual) == pytest.approx(1 - 1 / 8.75, rel=1e-6)
    assert spearman(predicted, actual) == pytest.approx(1.0)
    assert spearman(predicted, -actual) == pytest.approx(-1.0)
    assert top_n_overlap(predicted, actual, 2) == pytest.approx(1.0)
    assert brier_score(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 0.0


def test_reliability_table_bins_partition_the_sample():
    rng = np.random.default_rng(0)
    probs = rng.random(500)
    outcomes = (rng.random(500) < probs).astype(float)
    table = reliability_table(probs, outcomes, bins=5)
    assert sum(row["n"] for row in table) == 500
    assert all(0 <= row["realised"] <= 1 for row in table)


def test_leakage_guard_raises_on_future_data():
    assert_no_leakage("2026-09-21", ["2026-09-20", "2026-09-21"])
    with pytest.raises(ValueError):
        assert_no_leakage("2026-09-21", ["2026-09-22"])


def test_payout_lookup_matches_the_tier_table_it_replaces():
    """The dense lookup replaced a per-simulation Python loop; the values must be identical."""
    payout = PayoutStructure.illustrative_gpp(entries=1000, entry_fee=20.0)
    lookup = payout.payout_lookup(1000)
    for rank in (1, 2, 15, 16, 100, 200, 201, 1000):
        assert lookup[rank] == pytest.approx(payout.payout_for_rank(rank))


def test_ranks_never_exceed_the_field():
    nfl_slate = load_sample_slate("sample_nfl_dk.json")
    """A rank larger than the field would index past the payout table."""
    matrix, _ = simulate_fantasy_points(nfl_slate, n_sims=200, seed=3)
    from src.stokengineer.optimizer import optimize_lineup
    projections = {p.id: float(matrix[:, i].mean()) for i, p in enumerate(nfl_slate.players)}
    lineup = optimize_lineup(nfl_slate, projections)
    index = nfl_slate.index()
    field = [list(range(len(nfl_slate.players)))[:9] for _ in range(50)]
    payout = PayoutStructure.flat_cash(50, 20.0)
    (result,) = simulate_contest(
        matrix,
        [[index[pid] for pid in lineup.player_ids]],
        payout,
        field_lineups=field,
    )
    assert result.best_rank >= 1
    assert result.best_rank <= len(field) + 1
    assert result.median_rank <= len(field) + 1
