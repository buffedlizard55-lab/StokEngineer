"""Model tests: distributions, no look-ahead-free nonsense, and emergent correlation."""
import numpy as np
import pytest

from src.stokengineer.rules import PITCHER_POSITIONS
from src.stokengineer.models import (
    SimulationConfig,
    Slate,
    load_sample_slate,
    simulate_fantasy_points,
)
from src.stokengineer.correlation import teammate_correlation_summary


@pytest.fixture(scope="module")
def nfl_slate():
    return load_sample_slate("sample_nfl_dk.json")


@pytest.fixture(scope="module")
def mlb_slate():
    return load_sample_slate("sample_mlb_dk.json")


def test_samples_are_labelled_synthetic():
    for name in ("sample_nfl_dk.json", "sample_mlb_dk.json"):
        slate = load_sample_slate(name)
        assert slate.provenance.get("synthetic") is True
        assert "NOT real data" in slate.provenance.get("warning", "")


def test_nfl_simulation_shapes_and_ranges(nfl_slate):
    matrix, lines = simulate_fantasy_points(nfl_slate, n_sims=400, seed=1)
    assert matrix.shape == (400, len(nfl_slate.players))
    assert np.isfinite(matrix).all()
    # negative scores are real on both sites (interceptions, fumbles, DST points allowed);
    # they just must not be absurd.
    assert (matrix >= -15).all()
    means = matrix.mean(axis=0)
    qb = nfl_slate.players[[i for i, p in enumerate(nfl_slate.players) if "QB" in p.positions][0]]
    idx = nfl_slate.index()[qb.id]
    assert 5 < means[idx] < 40
    dsts = [i for i, p in enumerate(nfl_slate.players) if "DST" in p.positions]
    assert means[dsts].max() < 30
    assert matrix[:, idx].std() > 0


def test_simulation_is_deterministic(nfl_slate):
    a, _ = simulate_fantasy_points(nfl_slate, n_sims=200, seed=99)
    b, _ = simulate_fantasy_points(nfl_slate, n_sims=200, seed=99)
    assert np.array_equal(a, b)
    c, _ = simulate_fantasy_points(nfl_slate, n_sims=200, seed=100)
    assert not np.array_equal(a, c)


def test_teammates_correlate_more_than_non_teammates(nfl_slate):
    """The shared team volume/scoring factors must actually show up as correlation."""
    matrix, _ = simulate_fantasy_points(nfl_slate, n_sims=3000, seed=5)
    summary = teammate_correlation_summary(
        matrix, [p.team for p in nfl_slate.players], [p.positions[0] for p in nfl_slate.players]
    )
    assert summary["mean_teammate_corr"] > summary["mean_other_corr"]
    assert summary["mean_teammate_corr"] > 0.05


def test_qb_and_his_receivers_move_together(nfl_slate):
    matrix, _ = simulate_fantasy_points(nfl_slate, n_sims=3000, seed=6)
    index = nfl_slate.index()
    qb = next(p for p in nfl_slate.players if "QB" in p.positions)
    wr = next(p for p in nfl_slate.players if "WR" in p.positions and p.team == qb.team)
    corr = np.corrcoef(matrix[:, index[qb.id]], matrix[:, index[wr.id]])[0, 1]
    assert corr > 0.1, f"QB/WR correlation only {corr:.3f}"


def test_mlb_hitters_get_realistic_plate_appearances_and_scores(mlb_slate):
    matrix, lines = simulate_fantasy_points(mlb_slate, n_sims=400, seed=2)
    # DraftKings MLB lists starters as SP/RP, so "is a pitcher" means membership of the same
    # tuple the rules engine uses - not the string "P".
    pitcher_ids = [
        p.id for p in mlb_slate.players if set(p.positions) & set(PITCHER_POSITIONS)
    ]
    hitter_ids = [p.id for p in mlb_slate.players if p.id not in set(pitcher_ids)]
    hitter_means = matrix[:, [mlb_slate.index()[i] for i in hitter_ids]].mean(axis=0)
    pitcher_means = matrix[:, [mlb_slate.index()[i] for i in pitcher_ids]].mean(axis=0)
    assert 0 < hitter_means.mean() < 20
    assert 0 < pitcher_means.mean() < 40
    assert np.isfinite(matrix).all()
    # singles/doubles/triples/home runs are mutually exclusive outcomes, never negative
    for key in ("single", "double", "triple", "hr", "bb", "hbp"):
        assert (lines[hitter_ids[0]][key] >= 0).all()


def test_mlb_team_offence_drives_teammate_correlation(mlb_slate):
    matrix, _ = simulate_fantasy_points(mlb_slate, n_sims=2500, seed=3)
    summary = teammate_correlation_summary(
        matrix, [p.team for p in mlb_slate.players], [p.positions[0] for p in mlb_slate.players]
    )
    assert summary["mean_teammate_corr"] > 0


def test_slate_validation_rejects_bad_rows():
    slate = Slate.from_dict({
        "sport": "nfl", "site": "draftkings",
        "players": [
            {"id": "a", "name": "A", "positions": ["QB"], "salary": 0},
            {"id": "a", "name": "A2", "positions": [], "salary": 100},
        ],
    })
    problems = slate.validate()
    assert any("duplicate" in p for p in problems)
    assert any("no positions" in p for p in problems)
    assert any("salary" in p for p in problems)


# ---------------------------------------------------------------------------
# correlation calibration (the thing a stack is betting on)
# ---------------------------------------------------------------------------
def test_teammates_are_more_correlated_than_opponents(mlb_slate):
    """The verified claim is that a simulation must respect within-team correlation."""
    matrix, _ = simulate_fantasy_points(mlb_slate, n_sims=1200, seed=4)
    teams = [p.team for p in mlb_slate.players]
    correlation = np.corrcoef(matrix.T)
    same, different = [], []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            (same if teams[i] == teams[j] else different).append(correlation[i, j])
    assert np.mean(same) > np.mean(different)
    assert np.mean(same) > 0.2, (
        "teammate correlation is too weak for a stack to be worth anything; the calibration "
        "in apply_teammate_correlation has stopped working"
    )


def test_correlation_calibration_preserves_every_marginal():
    """Ceilings, floors and boom rates are functions of the marginals: they must not move."""
    slate = load_sample_slate("sample_nfl_dk.json")
    base, _ = simulate_fantasy_points(
        slate, n_sims=1500, seed=6, config=SimulationConfig(target_teammate_correlation=0.0)
    )
    calibrated, _ = simulate_fantasy_points(
        slate, n_sims=1500, seed=6, config=SimulationConfig(target_teammate_correlation=0.4)
    )
    assert np.allclose(base.mean(axis=0), calibrated.mean(axis=0), atol=1.0)
    ratio = calibrated.std(axis=0) / np.where(base.std(axis=0) > 0, base.std(axis=0), 1.0)
    assert np.allclose(ratio, 1.0, atol=0.08)
