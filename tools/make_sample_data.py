"""make_sample_data.py - regenerate the synthetic slates used for offline tests and demos.

The files this writes are **not real data**. They are deterministic fixtures whose only job is
to let the engine, the tests and the GitHub Pages demo run with no network and no paid feed.
Every generated file carries ``_meta.synthetic = true`` plus a warning, and the site labels any
output produced from them as synthetic.

Run:  python tools/make_sample_data.py            # write both files
      python tools/make_sample_data.py --check    # fail if the committed files differ
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "src" / "data" / "samples"
SEED = 20260922  # fixed: the fixtures must be byte-identical on every machine

NFL_POSITIONS = ("QB", "RB", "WR", "WR", "TE", "DST")
NFL_TEAMS = ("KC", "BUF", "SF", "DAL", "PHI", "DET")
NFL_GAMES = (("BUF", "KC"), ("DAL", "SF"), ("DET", "PHI"))
MLB_POSITIONS = ("SP", "SP", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF")
MLB_TEAMS = ("NYY", "BOS", "LAD", "SF", "HOU", "SEA", "ATL", "PHI")
MLB_GAMES = (("BOS", "NYY"), ("SF", "LAD"), ("SEA", "HOU"), ("PHI", "ATL"))


def _rng(seed: int):
    """Small deterministic RNG (PCG-flavoured LCG) so the fixtures never depend on numpy."""
    state = seed & 0xFFFFFFFF

    def next_float() -> float:
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return state / 0x7FFFFFFF

    return next_float


def _round(value: float, digits: int = 3) -> float:
    return float(f"{value:.{digits}f}")


def build_nfl() -> Dict[str, Any]:
    rnd = _rng(SEED)
    games: List[Dict[str, Any]] = []
    implied: Dict[str, float] = {}
    for away, home in NFL_GAMES:
        total = 43.5 + round(rnd() * 12.0, 1)
        margin = round(rnd() * 8.0 - 4.0, 1)
        games.append(
            {
                "game_id": f"{away}@{home}",
                "away_team": away,
                "home_team": home,
                "away_implied_total": round(total / 2 - margin / 2, 1),
                "home_implied_total": round(total / 2 + margin / 2, 1),
            }
        )
        implied[away] = round(total / 2 - margin / 2, 1)
        implied[home] = round(total / 2 + margin / 2, 1)

    players: List[Dict[str, Any]] = []
    counter = 0
    for away, home in NFL_GAMES:
        for team, opponent in ((away, home), (home, away)):
            # names must be unique: the validator rejects duplicate players, and a generator
            # that emits two "Team WR2" rows produces lineups that cannot be validated.
            sequence: Dict[str, int] = {}
            for slot_index, position in enumerate(NFL_POSITIONS):
                for depth in (1, 2, 3):
                    if position == "DST" and depth > 1:
                        continue
                    if position != "DST" and depth > 2 and slot_index not in (1, 2):
                        continue
                    counter += 1
                    sequence[position] = sequence.get(position, 0) + 1
                    label = f"{position}{sequence[position]}"
                    team_total = implied[team]
                    if position == "QB":
                        props = {
                            "pass_att": _round(28 + depth * -2 + rnd() * 8),
                            "comp_rate": _round(0.60 + rnd() * 0.10, 3),
                            "pass_yd_per_att": _round(6.6 + rnd() * 1.4),
                            "pass_td_per_att": _round(0.030 + rnd() * 0.020, 4),
                            "int_per_att": _round(0.012 + rnd() * 0.020, 4),
                            "rush_att": _round(3 + rnd() * 5),
                            "rush_yd_per_att": _round(3.5 + rnd() * 2.0),
                            "rush_td_per_att": _round(0.02 + rnd() * 0.03, 4),
                            "implied_total": team_total,
                        }
                        salary = int(5200 + rnd() * 2400)
                    elif position == "RB":
                        props = {
                            "rush_att": _round(16 - depth * 3 + rnd() * 6),
                            "rush_yd_per_att": _round(3.5 + rnd() * 1.8),
                            "rush_td_per_att": _round(0.02 + rnd() * 0.04, 4),
                            "targets": _round(4.5 - depth + rnd() * 3),
                            "catch_rate": _round(0.62 + rnd() * 0.20, 3),
                            "rec_yd_per_rec": _round(6.0 + rnd() * 3.5),
                            "rec_td_per_target": _round(0.02 + rnd() * 0.03, 4),
                            "implied_total": team_total,
                        }
                        salary = int(4300 + rnd() * 3000)
                    elif position == "DST":
                        props = {
                            "dst_sacks": _round(2.0 + rnd() * 2.0),
                            "dst_interceptions": _round(0.5 + rnd() * 1.5),
                            "dst_fumble_recoveries": _round(0.3 + rnd() * 1.2),
                            "dst_return_td": _round(0.05 + rnd() * 0.25, 3),
                            "dst_safeties": _round(rnd() * 0.2, 3),
                            "dst_blocked_kicks": _round(rnd() * 0.3, 3),
                            # points allowed: the opponent's implied total, jittered for realism
                            "dst_pa": _round(implied[opponent] + (rnd() - 0.5) * 6.0, 1),
                            "implied_total": team_total,
                        }
                        salary = int(2300 + rnd() * 1400)
                    else:
                        props = {
                            "targets": _round(8.0 - depth * 1.4 + rnd() * 3),
                            "catch_rate": _round(0.60 + rnd() * 0.20, 3),
                            "rec_yd_per_rec": _round(9.0 + rnd() * 5.0),
                            "rec_td_per_target": _round(0.03 + rnd() * 0.05, 4),
                            "implied_total": team_total,
                        }
                        salary = int(3800 + rnd() * 4200)
                    players.append(
                        {
                            "id": f"nfl-{position.lower()}-{counter}",
                            "name": f"Synthetic {team} {label}",
                            "team": team,
                            "opponent": opponent,
                            "positions": [position],
                            "salary": salary,
                            "game_id": f"{away}@{home}",
                            "props": props,
                        }
                    )
    return {
        "_meta": {
            "synthetic": True,
            "purpose": "Deterministic offline fixture for tests and CLI demos.",
            "warning": (
                "NOT real data. Names, salaries and projections are generated. Reports built "
                "from these files are labelled synthetic and must never be presented as real "
                "slate results."
            ),
            "generated_by": "tools/make_sample_data.py",
            "generated_on": "2026-09-22",
            "seed": SEED,
        },
        "sport": "nfl",
        "site": "draftkings",
        "date": "2026-09-20",
        "games": games,
        "players": players,
    }


def build_mlb() -> Dict[str, Any]:
    rnd = _rng(SEED + 1)
    games: List[Dict[str, Any]] = []
    implied: Dict[str, float] = {}
    for away, home in MLB_GAMES:
        total = 7.0 + rnd() * 5.0
        margin = rnd() * 1.6 - 0.8
        games.append(
            {
                "game_id": f"{away}@{home}",
                "away_team": away,
                "home_team": home,
                "away_implied_total": round(total / 2 - margin / 2, 1),
                "home_implied_total": round(total / 2 + margin / 2, 1),
            }
        )
        implied[away] = round(total / 2 - margin / 2, 1)
        implied[home] = round(total / 2 + margin / 2, 1)

    players: List[Dict[str, Any]] = []
    counter = 0
    for away, home in MLB_GAMES:
        for team, opponent in ((away, home), (home, away)):
            sequence: Dict[str, int] = {}
            for position in MLB_POSITIONS:
                depths = 2 if position in ("SP",) else (2 if position == "OF" else 1)
                for depth in range(1, depths + 1):
                    counter += 1
                    sequence[position] = sequence.get(position, 0) + 1
                    label = f"{position}{sequence[position]}"
                    runs = implied[team]
                    if position == "SP":
                        props = {
                            "outs": _round(14.0 + rnd() * 7.0),
                            "so_per_out": _round(0.22 + rnd() * 0.14, 4),
                            "bb_per_out": _round(0.06 + rnd() * 0.05, 4),
                            "hit_per_out": _round(0.22 + rnd() * 0.10, 4),
                            "run_per_out": _round(0.10 + rnd() * 0.06, 4),
                            "er_per_out": _round(0.09 + rnd() * 0.05, 4),
                            "hbp_per_out": _round(0.005 + rnd() * 0.010, 4),
                            "win_prob": _round(0.30 + rnd() * 0.30, 3),
                            "implied_runs": runs,
                        }
                        salary = int(5200 + rnd() * 4800)
                    else:
                        props = {
                            "pa": _round(3.6 + rnd() * 1.4),
                            "p_single": _round(0.12 + rnd() * 0.06, 4),
                            "p_double": _round(0.035 + rnd() * 0.035, 4),
                            "p_triple": _round(rnd() * 0.006, 4),
                            "p_hr": _round(0.015 + rnd() * 0.030, 4),
                            "p_bb": _round(0.06 + rnd() * 0.06, 4),
                            "p_hbp": _round(0.005 + rnd() * 0.012, 4),
                            "run_per_on_base": _round(0.18 + rnd() * 0.20, 3),
                            "rbi_per_on_base": _round(0.20 + rnd() * 0.22, 3),
                            "sb_rate": _round(rnd() * 0.22, 3),
                            "implied_runs": runs,
                        }
                        salary = int(2500 + rnd() * 4000)
                    players.append(
                        {
                            "id": f"mlb-{position.lower()}-{counter}",
                            "name": f"Synthetic {team} {label}",
                            "team": team,
                            "opponent": opponent,
                            "positions": [position],
                            "salary": salary,
                            "game_id": f"{away}@{home}",
                            "props": props,
                        }
                    )
    return {
        "_meta": {
            "synthetic": True,
            "purpose": "Deterministic offline fixture for tests and CLI demos.",
            "warning": (
                "NOT real data. Names, salaries and projections are generated. Reports built "
                "from these files are labelled synthetic and must never be presented as real "
                "slate results."
            ),
            "generated_by": "tools/make_sample_data.py",
            "generated_on": "2026-09-22",
            "seed": SEED + 1,
        },
        "sport": "mlb",
        "site": "draftkings",
        "date": "2026-09-21",
        "games": games,
        "players": players,
    }


def build_all() -> Dict[str, Dict[str, Any]]:
    return {"sample_nfl_dk.json": build_nfl(), "sample_mlb_dk.json": build_mlb()}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the files on disk differ")
    args = parser.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    differences = 0
    for name, payload in build_all().items():
        text = json.dumps(payload, indent=1, sort_keys=False) + "\n"
        path = OUT_DIR / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                print(f"DIFFERS: {name}")
                differences += 1
            else:
                print(f"ok: {name}")
            continue
        path.write_text(text)
        print(f"wrote {path} ({len(payload['players'])} players, {len(payload['games'])} games)")
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
