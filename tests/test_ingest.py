"""Ingest tests. No network needed: HTTP behaviour is exercised through file:// URLs and
parsers are exercised against fixtures copied from the real, verified response shapes."""
import json
from pathlib import Path

import pytest

from src.stokengineer.ingest import (
    Fetcher,
    OfflineError,
    boxscore_stat_lines,
    forward_test_props,
    implied_totals_from_espn,
    import_actuals_csv,
    import_ownership_csv,
    import_projections_csv,
    season_rates,
    subtract_game_from_season,
)

# Shape verified live on 2026-09-22 from statsapi.mlb.com (source id mlb_statsapi)
BOXSCORE_FIXTURE = {
    "teams": {
        "away": {
            "team": {"abbreviation": "TOR"},
            "players": {
                "ID1": {
                    "person": {"id": 1, "fullName": "Test Hitter"},
                    "position": {"abbreviation": "CF"},
                    "stats": {
                        "batting": {"hits": 3, "doubles": 1, "triples": 0, "homeRuns": 1,
                                    "rbi": 2, "runs": 2, "baseOnBalls": 1, "hitByPitch": 1,
                                    "stolenBases": 1, "atBats": 4, "sacFlies": 0},
                        "pitching": {},
                    },
                }
            },
        },
        "home": {
            "team": {"abbreviation": "BAL"},
            "players": {
                "ID2": {
                    "person": {"id": 2, "fullName": "Test Pitcher"},
                    "position": {"abbreviation": "P"},
                    "stats": {
                        "batting": {},
                        "pitching": {"outs": 18, "strikeOuts": 8, "wins": 1, "earnedRuns": 2,
                                     "hits": 6, "baseOnBalls": 2, "hitBatsmen": 0,
                                     "completeGames": 1, "shutouts": 0},
                    },
                }
            },
        },
    }
}

# Shape verified live on 2026-09-22 from statsapi.mlb.com/api/v1/stats
SEASON_STATS_FIXTURE = {
    "stats": [
        {
            "splits": [
                {
                    "player": {"id": 1, "fullName": "Test Hitter"},
                    "team": {"id": 141},
                    "stat": {"gamesPlayed": 100, "plateAppearances": 400, "hits": 100,
                             "doubles": 20, "triples": 2, "homeRuns": 18, "baseOnBalls": 40,
                             "hitByPitch": 4, "runs": 60, "rbi": 55, "stolenBases": 10},
                }
            ]
        }
    ]
}


def test_boxscore_parser_maps_official_fields_explicitly():
    rows = {r["name"]: r for r in boxscore_stat_lines(BOXSCORE_FIXTURE)}
    hitter = rows["Test Hitter"]
    assert hitter["stats"]["single"] == 3 - 1 - 0 - 1  # hits minus XBH
    assert hitter["stats"]["hr"] == 1 and hitter["stats"]["sb"] == 1
    pitcher = rows["Test Pitcher"]
    assert pitcher["stats"]["ip"] == pytest.approx(6.0)
    assert pitcher["stats"]["so"] == 8 and pitcher["stats"]["er"] == 2
    assert pitcher["stats"]["complete_game"] == 1.0


def test_season_rates_become_per_pa_probabilities():
    rates = season_rates(SEASON_STATS_FIXTURE, "hitting")
    row = rates[1]
    total = row["p_single"] + row["p_double"] + row["p_triple"] + row["p_hr"] + row["p_bb"] + row["p_hbp"]
    assert 0 < total < 0.6
    assert row["p_hr"] == pytest.approx(18 / 400)


def test_espn_odds_convert_to_implied_totals():
    board = {
        "events": [
            {
                "id": "1",
                "name": "A at B",
                "competitions": [
                    {
                        "competitors": [
                            {"homeAway": "home", "team": {"abbreviation": "BUF"}},
                            {"homeAway": "away", "team": {"abbreviation": "DET"}},
                        ],
                        "odds": [{"overUnder": 52.0, "spread": -6.5}],
                    }
                ],
            }
        ]
    }
    (game,) = implied_totals_from_espn(board)
    assert game["total"] == 52.0
    fav, dog = game["home_implied_total"], game["away_implied_total"]
    assert fav > dog
    assert fav + dog == pytest.approx(52.0)


def test_subtract_game_from_season_prevents_lookahead():
    season = {"pa": 400.0, "hits_total": 120.0, "games": 100.0}
    game = {"pa": 4.0}
    prior = subtract_game_from_season(season, game)
    assert prior["pa_per_game_before"] == pytest.approx(396.0 / 99.0)


def test_forward_test_props_removes_the_predicted_game_from_every_rate():
    """A rate that still contains the game is a leak; this pins the arithmetic."""
    season = {
        "pa": 500.0, "hits_total": 150.0, "doubles_total": 30.0, "triples_total": 3.0,
        "hr_total": 20.0, "bb_total": 50.0, "hbp_total": 5.0, "runs_total": 80.0,
        "rbi_total": 70.0, "sb_total": 10.0, "games": 101.0,
    }
    # the game being predicted: 2-for-4 with a homer, a walk, a run and an RBI
    game = {"pa": 5.0, "hits": 2.0, "doubles": 0.0, "triples": 0.0, "hr": 1.0, "bb": 1.0,
            "hbp": 0.0, "run": 1.0, "rbi": 1.0, "sb": 0.0, "outs": 0.0}
    props = forward_test_props(season, game, is_pitcher=False)
    assert props["pa"] == pytest.approx(495.0 / 100.0)
    assert props["p_hr"] == pytest.approx(19.0 / 495.0)
    assert props["p_single"] == pytest.approx((148.0 - 30.0 - 3.0 - 19.0) / 495.0)


def test_forward_test_props_for_a_pitcher_excludes_his_own_start():
    season = {
        "outs_total": 420.0, "games": 21.0, "so_total": 130.0, "hits_total": 110.0,
        "bb_total": 35.0, "er_total": 40.0, "runs_total": 45.0, "hbp_total": 3.0,
        "wins_total": 9.0, "so_per_out": 0.31, "bb_per_out": 0.08, "hit_per_out": 0.26,
        "run_per_out": 0.11, "er_per_out": 0.095, "hbp_per_out": 0.007,
    }
    props = forward_test_props(season, {"outs": 18.0, "so": 7.0}, is_pitcher=True)
    assert props["outs"] == pytest.approx((420.0 - 18.0) / 20.0)
    assert props["so_per_out"] == pytest.approx((130.0 - 7.0) / (420.0 - 18.0))
    # win probability is shrunk halfway to the documented 0.35 prior
    assert props["win_prob"] == pytest.approx(0.5 * (9.0 / 20.0) + 0.5 * 0.35)


def test_boxscore_rows_expose_the_game_context_needed_to_remove_lookahead():
    rows = {r["name"]: r for r in boxscore_stat_lines(BOXSCORE_FIXTURE)}
    assert rows["Test Hitter"]["game_context"]["pa"] == 6.0  # 4 AB + 1 BB + 1 HBP-ish
    assert rows["Test Pitcher"]["game_context"]["outs"] == 18.0


def test_csv_importers_read_the_documented_columns(tmp_path: Path):
    slate_csv = tmp_path / "slate.csv"
    slate_csv.write_text(
        "name,team,opponent,positions,salary,projection,minutes,pts_per_min\n"
        "A Star,LAL,GSW,PG|SG,8500,48.2,35.5,0.62\n"
    )
    rows = import_projections_csv(slate_csv)
    assert rows[0]["positions"] == ["PG", "SG"]
    assert rows[0]["props"]["minutes"] == 35.5

    actuals = tmp_path / "actuals.csv"
    actuals.write_text("name,actual\nA Star,55.5\n")
    assert import_actuals_csv(actuals) == {"A Star": 55.5}

    ownership = tmp_path / "own.csv"
    ownership.write_text("name,ownership\nA Star,24.5%\n")
    assert import_ownership_csv(ownership) == {"A Star": 24.5}


def test_fetcher_caches_and_records_provenance(tmp_path: Path):
    source = tmp_path / "payload.json"
    source.write_text(json.dumps({"hello": "world"}))
    fetcher = Fetcher(cache_dir=tmp_path / "cache")
    first = fetcher.get_json(source.as_uri(), "test_source", suffix=".json")
    assert first == {"hello": "world"}
    assert fetcher.records[0].sha256 and fetcher.records[0].bytes > 0
    second = fetcher.get_json(source.as_uri(), "test_source", suffix=".json")
    assert second == first
    assert fetcher.records[1].from_cache is True


def test_fetcher_offline_error_is_explicit(tmp_path: Path):
    fetcher = Fetcher(cache_dir=tmp_path / "cache", retries=1, timeout=2)
    with pytest.raises(OfflineError) as excinfo:
        fetcher.get_bytes("https://127.0.0.1:9/definitely-not-listening", "bad_source")
    assert "no outbound network" in str(excinfo.value)
