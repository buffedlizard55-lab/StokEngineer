"""End-to-end tests on the bundled synthetic slates."""
import numpy as np
import pytest

from src.stokengineer.models import load_sample_slate
from src.stokengineer.pipeline import project_slate, run_slate
from src.stokengineer.rules import validate_lineup


@pytest.fixture(scope="module")
def nfl_slate():
    return load_sample_slate("sample_nfl_dk.json")


def test_projection_table_has_published_columns(nfl_slate):
    result = project_slate(nfl_slate, n_sims=300, seed=3)
    row = result["players"][0]
    for column in ("projection", "ceiling", "floor", "stddev", "boom_pct", "bust_pct",
                   "value", "pts_per_dollar"):
        assert column in row
    assert row["ceiling"] > row["floor"]
    for r in result["players"]:
        for column in ("projection", "ceiling", "floor", "stddev", "boom_pct", "bust_pct",
                       "value", "pts_per_dollar"):
            assert np.isfinite(r[column]), f"{r['name']}: {column} is not finite"


def test_run_slate_produces_legal_lineups_and_finite_roi(nfl_slate):
    run = run_slate(nfl_slate, n_sims=300, n_lineups=3, field_size=400, entry_fee=20.0, seed=13)
    assert len(run.lineups) == 3
    index = {p.id: p for p in nfl_slate.players}
    for lineup in run.lineups:
        records = [index[pid].as_validation_record() for pid in lineup.player_ids]
        assert validate_lineup(records, nfl_slate.site, nfl_slate.sport) == []
    for row in run.contest:
        assert np.isfinite(row["roi_pct"])
        assert 0 <= row["cash_rate_pct"] <= 100
        assert 0 <= row["win_rate_pct"] <= 100
    assert any("simulated-field estimate" in note for note in run.notes)
    assert any("ILLUSTRATIVE" in note for note in run.notes)


def test_run_slate_is_deterministic(nfl_slate):
    a = run_slate(nfl_slate, n_sims=200, n_lineups=2, field_size=300, seed=21).as_dict()
    b = run_slate(nfl_slate, n_sims=200, n_lineups=2, field_size=300, seed=21).as_dict()
    assert [l["player_ids"] for l in a["lineups"]] == [l["player_ids"] for l in b["lineups"]]
    assert [c["roi_pct"] for c in a["contest"]] == [c["roi_pct"] for c in b["contest"]]


def test_implausibly_good_roi_is_flagged_not_published_silently(nfl_slate):
    """The simulator must not print a fantasy ROI without a caveat.

    With oracle projections (projection_error=0) the field is necessarily weaker than the
    lineups, so ROI comes out high. That is expected - and it must be surfaced in the notes,
    not quietly reported as expected money.
    """
    run = run_slate(nfl_slate, n_sims=300, n_lineups=2, field_size=500, seed=5)
    assert any("ranking" in note for note in run.notes)
    assert any("illustrative" in note.lower() for note in run.notes)
    if max(row["roi_pct"] for row in run.contest) > 100:
        assert any("cannot justify that ROI" in note for note in run.notes)


def test_projection_error_mode_reduces_apparent_advantage(nfl_slate):
    oracle = run_slate(nfl_slate, n_sims=300, n_lineups=2, field_size=500, seed=9,
                       projection_error=0.0)
    realistic = run_slate(nfl_slate, n_sims=300, n_lineups=2, field_size=500, seed=9,
                          projection_error=0.30)
    assert max(r["mean_percentile"] for r in realistic.contest) <= max(
        r["mean_percentile"] for r in oracle.contest
    )
    assert any("noisy view" in note for note in realistic.notes)
