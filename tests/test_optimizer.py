"""Optimizer tests: legality, constraints, and MILP-vs-heuristic behaviour."""
import pytest

from src.stokengineer.models import load_sample_slate
from src.stokengineer.optimizer import LineupConstraints, StackSpec, optimize_lineup, optimize_portfolio
from src.stokengineer.rules import get_site_rules, validate_lineup

SAMPLE = "sample_nfl_dk.json"


@pytest.fixture(scope="module")
def slate():
    return load_sample_slate(SAMPLE)


@pytest.fixture(scope="module")
def projections(slate):
    # deterministic stand-in for model output: salary value plus a positional tilt
    tilt = {"QB": 6.0, "RB": 3.0, "WR": 3.5, "TE": 2.0, "DST": 0.0}
    return {
        p.id: p.salary / 1000 * 2.2 + tilt.get(p.positions[0], 0.0) for p in slate.players
    }


def _records(slate, lineup):
    index = {p.id: p for p in slate.players}
    return [index[pid].as_validation_record() for pid in lineup.player_ids]


def test_milp_lineup_is_legal(slate, projections):
    lineup = optimize_lineup(slate, projections)
    assert lineup.method in {"milp", "heuristic"}
    assert validate_lineup(_records(slate, lineup), slate.site, slate.sport) == []
    assert lineup.salary <= get_site_rules(slate.site, slate.sport).salary_cap


def test_heuristic_fallback_is_also_legal(slate, projections):
    lineup = optimize_lineup(slate, projections, prefer_milp=False)
    assert lineup.method == "heuristic"
    assert validate_lineup(_records(slate, lineup), slate.site, slate.sport) == []


def test_milp_matches_or_beats_heuristic(slate, projections):
    milp = optimize_lineup(slate, projections)
    if milp.method != "milp":  # pulp not installed in this environment
        pytest.skip("pulp not available")
    heuristic = optimize_lineup(slate, projections, prefer_milp=False)
    assert milp.objective_value >= heuristic.objective_value - 1e-6


def test_locks_and_exclusions_are_respected(slate, projections):
    locked = slate.players[0].id
    excluded = {p.id for p in slate.players if p.id != locked}
    excluded = set(sorted(excluded))  # keep it deterministic for review
    excluded = {pid for pid in sorted(excluded)[::3]}
    lineup = optimize_lineup(
        slate, projections, constraints=LineupConstraints(locked={locked}, excluded=excluded)
    )
    assert locked in lineup.player_ids
    assert not (set(lineup.player_ids) & excluded)


def test_impossible_constraints_say_why_instead_of_returning_silence(slate, projections):
    """Excluding every DST makes the roster impossible; the error must name the reason."""
    excluded = {p.id for p in slate.players if "DST" in p.positions}
    with pytest.raises(ValueError) as excinfo:
        optimize_lineup(slate, projections, constraints=LineupConstraints(excluded=excluded))
    assert "DST" in str(excinfo.value)


def test_dfs_fallback_finds_the_same_optimum_as_the_milp_on_this_slate(slate, projections):
    """The fallback is a branch-and-bound search, not a greedy walk, so it should not lose."""
    milp = optimize_lineup(slate, projections)
    if milp.method != "milp":
        pytest.skip("pulp not available")
    dfs = optimize_lineup(slate, projections, prefer_milp=False)
    assert dfs.method == "heuristic"
    assert dfs.objective_value >= milp.objective_value - 1e-6


def test_dfs_respects_the_two_game_rule_and_salary_cap(slate, projections):
    rules = get_site_rules(slate.site, slate.sport)
    lineup = optimize_lineup(slate, projections, prefer_milp=False)
    records = _records(slate, lineup)
    games = {p.get("game_id") or (p.get("team"), p.get("opponent")) for p in records}
    assert len(games) >= rules.min_games
    assert sum(p["salary"] for p in records) <= rules.salary_cap


def test_team_limit_is_respected(slate, projections):
    lineup = optimize_lineup(
        slate, projections, constraints=LineupConstraints(max_players_per_team=3)
    )
    teams = [next(p.team for p in slate.players if p.id == pid) for pid in lineup.player_ids]
    assert max(teams.count(t) for t in set(teams)) <= 3


def test_stack_constraint_produces_a_qb_stack(slate, projections):
    lineup = optimize_lineup(
        slate,
        projections,
        constraints=LineupConstraints(stack=StackSpec(count=2, include_qb=True)),
    )
    index = {p.id: p for p in slate.players}
    by_team = {}
    for pid in lineup.player_ids:
        by_team.setdefault(index[pid].team, []).append(index[pid])
    assert any(
        any("QB" in p.positions for p in players) and len(players) >= 2
        for players in by_team.values()
    )


def test_ceiling_mode_requires_ceiling_input(slate, projections):
    with pytest.raises(ValueError):
        optimize_lineup(slate, projections, constraints=LineupConstraints(objective="ceiling"))


def test_portfolio_respects_exposure_and_uniqueness(slate, projections):
    lineups = optimize_portfolio(slate, projections, n_lineups=4, max_exposure=0.5, min_unique=1)
    assert lineups, "expected at least one lineup"
    for lineup in lineups:
        assert validate_lineup(_records(slate, lineup), slate.site, slate.sport) == []
    for i, first in enumerate(lineups):
        for second in lineups[i + 1:]:
            assert set(first.player_ids) != set(second.player_ids)
    counts = {}
    for lineup in lineups:
        for pid in lineup.player_ids:
            counts[pid] = counts.get(pid, 0) + 1
    assert max(counts.values()) <= 2  # ceil(0.5 * 4)


def test_impossible_constraints_fail_loudly(slate, projections):
    all_te = {p.id for p in slate.players if "TE" in p.positions}
    with pytest.raises(Exception):
        optimize_lineup(slate, projections, constraints=LineupConstraints(excluded=all_te))


# ---------------------------------------------------------------------------
# regressions found by reviewing the first pass
# ---------------------------------------------------------------------------
def test_slot_assignment_describes_the_lineup_it_is_attached_to(slate, projections):
    """Regression: the assignment indexed the slate, not the chosen players.

    That bug produced a report where every slot held somebody else's player - the lineups
    looked like nine players from one team while the player list was legal.
    """
    lineup = optimize_lineup(slate, projections)
    by_id = {p.id: p for p in slate.players}
    rules = get_site_rules(slate.site, slate.sport)
    eligible = {slot.id: slot.eligible for slot in rules.slots}
    assert set(lineup.slot_assignment.values()) == set(lineup.player_ids)
    for slot, pid in lineup.slot_assignment.items():
        assert set(by_id[pid].positions) & set(eligible[slot]), (
            f"{by_id[pid].name} is in the {slot} slot but is only eligible at "
            f"{by_id[pid].positions}"
        )


def test_the_exact_solver_actually_runs(slate, projections):
    """A silently infeasible MILP would make every number in the docs a fallback number."""
    if not _pulp_available():
        pytest.skip("pulp is not installed in this environment")
    lineup = optimize_lineup(slate, projections)
    assert lineup.method == "milp", (
        "the exact solver returned no solution; the formulation is broken and the DFS "
        "fallback is silently standing in for it"
    )


def test_optimizer_agrees_with_the_validator_on_the_hard_rules(slate, projections):
    rules = get_site_rules(slate.site, slate.sport)
    lineup = optimize_lineup(slate, projections)
    records = _records(slate, lineup)
    assert validate_lineup(records, slate.site, slate.sport) == []
    games = {p.get("game_id") or (p.get("team"), p.get("opponent")) for p in records}
    assert len(games) >= rules.min_games
    if rules.max_hitters_per_team:
        per_team = {}
        for record in records:
            if any(pos in {"P", "SP", "RP"} for pos in record["positions"]):
                continue
            per_team[record["team"]] = per_team.get(record["team"], 0) + 1
        assert all(count <= rules.max_hitters_per_team for count in per_team.values())


def _pulp_available() -> bool:
    try:
        import pulp  # noqa: F401

        return True
    except Exception:
        return False
