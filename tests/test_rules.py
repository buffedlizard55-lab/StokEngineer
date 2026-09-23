"""Rule and scoring tests.

Every number asserted here was read off the official rules page cited in
src/data/scoring_rules.json; the derived metrics are checked against the worked examples in
the Stokastic articles (claims c07 and c09 in src/data/claims.json).
"""
import numpy as np
import pytest

from src.stokengineer import rules


def test_registry_of_rules_is_structurally_sound():
    assert rules.verify_rules() == []


@pytest.mark.parametrize("site,sport", [
    ("draftkings", "nfl"), ("draftkings", "nba"), ("draftkings", "mlb"), ("draftkings", "nhl"),
    ("fanduel", "nfl"), ("fanduel", "nba"), ("fanduel", "mlb"), ("fanduel", "nhl"),
])
def test_every_site_sport_has_sourced_scoring(site, sport):
    scoring = rules.load_scoring(site, sport)
    assert scoring.source.startswith("https://")
    assert scoring.verified in {"official", "third-party"}


def test_draftkings_nba_scoring_including_double_double():
    line = {"pts": 30, "fg3m": 4, "reb": 10, "ast": 8, "stl": 1, "blk": 0, "to": 2}
    # 30*1 + 4*0.5 + 10*1.25 + 8*1.5 + 1*2 + 0 - 2*0.5 = 57.5, plus a double-double (+1.5)
    # (points and rebounds both reached 10)
    assert rules.score_statline(line, "draftkings", "nba") == pytest.approx(59.0)


def test_triple_double_requires_three_categories():
    line = {"pts": 12, "fg3m": 1, "reb": 11, "ast": 10, "stl": 0, "blk": 0, "to": 1}
    # 12 + 0.5 + 13.75 + 15 - 0.5 = 40.75; double-double (+1.5) and triple-double (+3) both hit
    assert rules.score_statline(line, "draftkings", "nba") == pytest.approx(45.25)


def test_fanduel_nba_has_no_double_double_bonus():
    line = {"fg2m": 11, "fg3m": 4, "ft": 3, "reb": 10, "ast": 8, "stl": 1, "blk": 0, "to": 2}
    expected = 11 * 2 + 4 * 3 + 3 * 1 + 10 * 1.2 + 8 * 1.5 + 1 * 3 + 0 - 2 * 1
    assert rules.score_statline(line, "fanduel", "nba") == pytest.approx(expected)


def test_draftkings_nfl_yardage_bonus():
    line = {"pass_yd": 305, "pass_td": 3, "pass_int": 1, "rush_yd": 20, "rush_td": 0}
    expected = 305 * 0.04 + 3 * 4 - 1 + 20 * 0.1 + 3  # 300-yard bonus
    assert rules.score_statline(line, "draftkings", "nfl", positions=("QB",)) == pytest.approx(expected)


def test_fanduel_nfl_half_ppr():
    line = {"rec": 8, "rec_yd": 96, "rec_td": 1}
    expected = 8 * 0.5 + 96 * 0.1 + 6
    assert rules.score_statline(line, "fanduel", "nfl", positions=("WR",)) == pytest.approx(expected)


def test_draftkings_mlb_hitting():
    line = {"single": 2, "hr": 1, "rbi": 3, "run": 2, "bb": 1, "sb": 1}
    expected = 2 * 3 + 10 + 3 * 2 + 2 * 2 + 2 + 5
    assert rules.score_statline(line, "draftkings", "mlb", positions=("OF",)) == pytest.approx(expected)


def test_draftkings_mlb_pitching_uses_pitching_table_only():
    line = {"ip": 6.0, "so": 8, "win": 1, "er": 2, "hit_against": 6, "bb_against": 2}
    expected = 6 * 2.25 + 8 * 2 + 4 - 2 * 2 - 6 * 0.6 - 2 * 0.6
    assert rules.score_statline(line, "draftkings", "mlb", positions=("P",)) == pytest.approx(expected)


def test_mlb_hitter_stats_do_not_score_pitching_stats():
    """Official note: pitching stats for hitters do not count (dk_rules_mlb)."""
    with pytest.raises(ValueError):
        rules.score_statline({"so": 5, "ip": 3.0}, "draftkings", "mlb", positions=("1B",))


def test_dst_points_allowed_tiers():
    assert rules.score_statline({"dst_pa": 0}, "draftkings", "nfl", positions=("DST",)) == 10
    assert rules.score_statline({"dst_pa": 21}, "draftkings", "nfl", positions=("DST",)) == 0
    assert rules.score_statline({"dst_pa": 40}, "draftkings", "nfl", positions=("DST",)) == -4


def test_unknown_stat_key_is_rejected():
    with pytest.raises(ValueError):
        rules.score_statline({"touchdowns": 3}, "draftkings", "nfl", positions=("RB",))


def test_scalar_and_vectorised_scorers_agree():
    rng = np.random.default_rng(0)
    for site in ("draftkings", "fanduel"):
        for _ in range(25):
            line = {
                "pts": float(rng.integers(0, 40)), "fg3m": float(rng.integers(0, 6)),
                "reb": float(rng.integers(0, 16)), "ast": float(rng.integers(0, 14)),
                "stl": float(rng.integers(0, 5)), "blk": float(rng.integers(0, 5)),
                "to": float(rng.integers(0, 7)),
            }
            if site == "fanduel":
                line.pop("pts")
                line.update({"fg2m": float(rng.integers(0, 15)), "ft": float(rng.integers(0, 10))})
            scalar = rules.score_statline(line, site, "nba")
            vector = rules.score_array({k: np.array([v]) for k, v in line.items()}, site, "nba")[0]
            assert scalar == pytest.approx(vector)


def test_published_value_and_points_per_dollar_examples():
    # claim c09: 55 FP at $10,000 -> Pts/$ 5.5 and Value 5.0
    assert rules.pts_per_dollar(55, 10000) == pytest.approx(5.5)
    assert rules.value(55, 10000) == pytest.approx(5.0)
    # claim c09: 32 FP at $5,800 -> Value 3.0
    assert rules.value(32, 5800) == pytest.approx(3.0)
    assert rules.pts_per_dollar(32, 5800) == pytest.approx(5.5172, abs=1e-3)


def test_published_boom_and_bust_thresholds():
    # claim c07: $9,000 needs ~45 to clear value and ~55 to boom; $4,000 punt ~20 and ~30
    assert rules.bust_threshold(9000) == pytest.approx(45.0)
    assert rules.boom_threshold(9000) == pytest.approx(55.0)
    assert rules.bust_threshold(4000) == pytest.approx(20.0)
    assert rules.boom_threshold(4000) == pytest.approx(30.0)


def test_implied_team_total_matches_published_example():
    # claim c23: 44 total with a -7 spread -> favourite 25.5, underdog 18.5
    fav, dog = rules.implied_team_total(44, -7)
    assert float(fav) == pytest.approx(25.5)
    assert float(dog) == pytest.approx(18.5)


def test_double_double_counts_categories_not_boolean_flags():
    """Regression: NumPy boolean addition saturates, which used to hide the bonus."""
    two_categories = {"pts": 10, "reb": 10, "ast": 3, "stl": 0, "blk": 1, "fg3m": 0, "to": 1}
    one_category = {"pts": 10, "reb": 9, "ast": 3, "stl": 0, "blk": 1, "fg3m": 0, "to": 1}
    # the two lines differ by one rebound (1.25) *and* by the double-double (1.5)
    assert rules.score_statline(two_categories, "draftkings", "nba") == pytest.approx(
        rules.score_statline(one_category, "draftkings", "nba") + 1.25 + 1.5
    )


def test_points_allowed_rounds_continuous_simulated_values():
    # the feed reports whole numbers; a simulated 34.4 must land in the 28-34 tier, not vanish
    assert rules.score_statline({"dst_pa": 34.4}, "draftkings", "nfl", positions=("DST",)) == -1
    assert rules.score_statline({"dst_pa": 34.6}, "draftkings", "nfl", positions=("DST",)) == -4


def test_distribution_summary_uses_published_percentiles():
    samples = np.arange(1, 101, dtype=float)  # 1..100
    summary = rules.summarise_distribution(samples, salary=6000)
    assert summary.median == pytest.approx(50.5)
    assert summary.ceiling_75 == pytest.approx(np.percentile(samples, 75))
    assert summary.floor_25 == pytest.approx(np.percentile(samples, 25))
    assert summary.bust_threshold == pytest.approx(30.0)
    assert summary.boom_threshold == pytest.approx(40.0)
    assert 0 <= summary.boom_pct <= 100 and 0 <= summary.bust_pct <= 100


def _dk_mlb_lineup():
    """A legal 10-man DK MLB lineup: 2 P, C, 1B, 2B, 3B, SS, 3 OF, spanning 3 games.

    Hitter counts per team: AAA 4 (C,1B,2B,3B), BBB 4 (SS, 3 registered as OF/CCC? no) - see
    the explicit team tags below, chosen so the 5-hitter cap is testable.
    """
    def player(pos, team, game, name):
        return {"name": name, "positions": [pos], "salary": 4000, "team": team,
                "opponent": "OPP", "game_id": game}
    return [
        player("P", "AAA", "g1", "AAA Pitcher 1"),
        player("P", "BBB", "g2", "BBB Pitcher 1"),
        player("C", "AAA", "g1", "AAA Catcher"),
        player("1B", "AAA", "g1", "AAA First Base"),
        player("2B", "AAA", "g1", "AAA Second Base"),
        player("3B", "AAA", "g1", "AAA Third Base"),
        player("SS", "BBB", "g2", "BBB Shortstop"),
        player("OF", "BBB", "g2", "BBB Outfielder 1"),
        player("OF", "CCC", "g3", "CCC Outfielder 1"),
        player("OF", "CCC", "g3", "CCC Outfielder 2"),
    ]


def test_validate_lineup_accepts_legal_dk_mlb_lineup():
    assert rules.validate_lineup(_dk_mlb_lineup(), "draftkings", "mlb") == []


def test_validate_lineup_enforces_five_hitter_cap():
    """DK MLB: 'no more than 5 hitters from any one team' (source dk_rules_mlb)."""
    lineup = _dk_mlb_lineup()
    assert rules.validate_lineup(lineup, "draftkings", "mlb") == []  # AAA has 4 hitters
    lineup[8] = {"name": "AAA Outfielder 1", "positions": ["OF"], "salary": 4000, "team": "AAA",
                 "opponent": "OPP", "game_id": "g1"}
    lineup[9] = {"name": "AAA Outfielder 2", "positions": ["OF"], "salary": 4000, "team": "AAA",
                 "opponent": "OPP", "game_id": "g1"}
    problems = rules.validate_lineup(lineup, "draftkings", "mlb")
    assert any("hitters from AAA" in p for p in problems)


def test_validate_lineup_enforces_min_games_and_cap():
    lineup = _dk_mlb_lineup()
    for player in lineup:
        player["game_id"] = "g1"
    problems = rules.validate_lineup(lineup, "draftkings", "mlb")
    assert any("at least 2" in p for p in problems)
    lineup = _dk_mlb_lineup()
    lineup[0]["salary"] = 20000
    problems = rules.validate_lineup(lineup, "draftkings", "mlb")
    assert any("exceeds cap" in p for p in problems)


def test_validate_lineup_rejects_impossible_positions():
    lineup = _dk_mlb_lineup()
    for player in lineup:
        player["positions"] = ["OF"]
    problems = rules.validate_lineup(lineup, "draftkings", "mlb")
    assert any("cannot fill slots" in p for p in problems)
