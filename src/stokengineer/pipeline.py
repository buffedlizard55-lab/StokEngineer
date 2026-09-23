"""End-to-end pipeline: slate -> projections -> ownership -> lineups -> contest sim -> report.

``run_slate`` is the one function that ties the engine together, and it is used by the CLI,
the tests and the forward-test workflow, so a result produced in any of those places is
produced the same way. Everything it returns is a plain dict with a provenance block attached,
which is what the GitHub Pages site renders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import DATA_DIR
from .evaluate import ProjectionReport, evaluate_projections, write_report
from .models import (
    PlayerProjection,
    SimulationConfig,
    Slate,
    simulate_fantasy_points,
)
from .optimizer import LineupConstraints, OptimizedLineup, optimize_portfolio
from .ownership import OwnershipModel, generate_field_lineups, projected_ownership
from .provenance import Registry, utc_now
from .rules import get_site_rules, score_statline, summarise_distribution, validate_lineup
from .simulate import (
    PayoutStructure,
    boom_bust_table,
    field_lineups_from_ownership,
    plausibility_warnings,
    simulate_contest,
)

DEFAULT_SIM_CONFIG = SimulationConfig()


# ---------------------------------------------------------------------------
# projections for a slate
# ---------------------------------------------------------------------------
def project_slate(
    slate: Slate,
    n_sims: int = 4000,
    seed: Optional[int] = 7,
    config: Optional[SimulationConfig] = None,
    site: Optional[str] = None,
) -> Dict[str, Any]:
    """Simulate a slate and return the published-style projection table.

    Columns match what Stokastic's DataHub exposes (claim c22-era: projection, ceiling, floor,
    std dev, ownership) plus the boom/bust columns from claim c07/c08.
    """
    site = site or slate.site
    matrix, stat_lines = simulate_fantasy_points(
        slate, n_sims=n_sims, seed=seed, config=config or DEFAULT_SIM_CONFIG, site=site
    )
    projections: Dict[str, float] = {}
    rows: List[Dict[str, Any]] = []
    for idx, player in enumerate(slate.players):
        samples = matrix[:, idx]
        summary = summarise_distribution(samples, player.salary)
        mean = float(samples.mean())
        projections[player.id] = mean
        rows.append(
            {
                "player_id": player.id,
                "name": player.name,
                "team": player.team,
                "opponent": player.opponent,
                "positions": list(player.positions),
                "salary": player.salary,
                "projection": round(mean, 2),
                "stddev": round(summary.stddev, 2),
                "ceiling": round(summary.ceiling_75, 2),
                "floor": round(summary.floor_25, 2),
                "boom_pct": round(summary.boom_pct, 2),
                "bust_pct": round(summary.bust_pct, 2),
                "boom_threshold": round(summary.boom_threshold, 2),
                "bust_threshold": round(summary.bust_threshold, 2),
                "value": round(mean - (player.salary / 1000 * 5), 2),
                "pts_per_dollar": round(mean / player.salary * 1000, 2) if player.salary else None,
            }
        )
    return {
        "sport": slate.sport,
        "site": site,
        "date": slate.date,
        "n_sims": n_sims,
        "players": sorted(rows, key=lambda r: -r["projection"]),
        "matrix": matrix,
        "stat_lines": stat_lines,
        "projections": projections,
    }


# ---------------------------------------------------------------------------
# one full slate
# ---------------------------------------------------------------------------
@dataclass
class SlateRun:
    slate: Slate
    projection_table: List[Dict[str, Any]]
    ownership: Dict[str, float]
    lineups: List[OptimizedLineup]
    contest: List[Dict[str, Any]]
    payout: PayoutStructure
    notes: List[str] = field(default_factory=list)
    field_size: int = 0
    n_sims: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "sport": self.slate.sport,
            "site": self.slate.site,
            "date": self.slate.date,
            "n_sims": self.n_sims,
            "field_size": self.field_size,
            "payout": self.payout.as_dict(),
            "projections": self.projection_table,
            "ownership": {k: round(v, 2) for k, v in self.ownership.items()},
            "lineups": [lineup.as_dict() for lineup in self.lineups],
            "contest": self.contest,
            "notes": list(self.notes),
        }


def run_slate(
    slate: Slate,
    *,
    n_sims: int = 2000,
    n_lineups: int = 5,
    field_size: int = 2000,
    entry_fee: float = 20.0,
    payout: Optional[PayoutStructure] = None,
    seed: int = 11,
    max_exposure: float = 1.0,
    objective: str = "median",
    config: Optional[SimulationConfig] = None,
    site: Optional[str] = None,
    projection_error: float = 0.0,
    sharp_share: float = 0.35,
) -> SlateRun:
    """Project, price ownership, build lineups and simulate the contest for one slate.

    ``projection_error`` is the honest-testing knob. At 0 (the default) the lineups are built
    from the model's own projections: the simulated ROI then measures *relative* quality -
    "which of these builds is better" - because the field is generated from the same
    projections with error while the lineups are not. Setting it to e.g. 0.15 builds the
    lineups from a noisy view of the projections instead, which is what happens in real life,
    and produces a much smaller and more believable ROI. Every report records which mode ran.
    """
    site = site or slate.site
    notes: List[str] = []

    projection = project_slate(slate, n_sims=n_sims, seed=seed, config=config, site=site)
    projections = projection["projections"]
    matrix = projection["matrix"]

    model = OwnershipModel()
    weights = model.raw_weights(slate, projections)
    ownership = projected_ownership(slate, weights, n_entries=max(200, field_size // 4),
                                    seed=seed, site=site)

    ceiling = {row["player_id"]: row["ceiling"] for row in projection["players"]}
    floor = {row["player_id"]: row["floor"] for row in projection["players"]}

    optimization_view = projections
    if projection_error > 0:
        rng_view = np.random.default_rng(seed + 1)
        optimization_view = {
            p.id: max(0.0, projections[p.id] * (1.0 + rng_view.normal(0.0, projection_error)))
            for p in slate.players
        }
        notes.append(
            f"lineups were built from a noisy view of the projections (sd "
            f"{projection_error:.0%}); this models the user's own projection error"
        )
    lineups = optimize_portfolio(
        slate,
        optimization_view,
        n_lineups,
        max_exposure=max_exposure,
        constraints=LineupConstraints(objective=objective),
        site=site,
        ceiling=ceiling,
        floor=floor,
        seed=seed,
        objective=objective,
    )
    if not lineups:
        raise RuntimeError("no lineups could be built - check the slate and constraints")

    payout = payout or PayoutStructure.illustrative_gpp(field_size, entry_fee)
    if payout.entries != field_size:
        notes.append(
            f"payout structure is for {payout.entries} entries but the field is {field_size}; "
            f"pass a matching PayoutStructure for a meaningful ROI"
        )

    field = field_lineups_from_ownership(
        slate,
        ownership,
        field_size,
        seed=seed,
        site=site,
        projections=projections,
        sharp_share=sharp_share,
    )
    index = slate.index()
    user_idx = [[index[pid] for pid in lineup.player_ids] for lineup in lineups]
    results = simulate_contest(
        matrix,
        user_idx,
        payout,
        field_lineups=field,
        labels=[f"lineup_{i + 1}" for i in range(len(user_idx))],
    )
    contest_rows = []
    for result, lineup in zip(results, lineups):
        row = result.as_dict()
        row["projected_score"] = round(lineup.projected, 2)
        row["salary"] = round(lineup.salary, 2)
        row["slots"] = lineup.slot_assignment
        row["method"] = lineup.method
        contest_rows.append(row)

    notes.append(
        "ownership is a simulated-field estimate (see ownership.py); it is not observed "
        "contest ownership"
    )
    notes.append(
        f"field model: {sharp_share:.0%} of entries draft with sharp error, the rest with a "
        f"looser view (see ownership.generate_field_lineups). Simulated ROI is sensitive to "
        f"this assumption and to the payout structure; read it as a ranking, not a forecast."
    )
    notes.extend(plausibility_warnings(results, payout))
    if payout.source.startswith("ILLUSTRATIVE"):
        notes.append(
            "payout structure is ILLUSTRATIVE: supply the real contest payout (CSV) before "
            "treating any ROI here as expected money"
        )
    return SlateRun(
        slate=slate,
        projection_table=projection["players"],
        ownership=ownership,
        lineups=lineups,
        contest=contest_rows,
        payout=payout,
        notes=notes,
        field_size=field_size,
        n_sims=n_sims,
    )


# ---------------------------------------------------------------------------
# backtest / forward test
# ---------------------------------------------------------------------------
def backtest_projections(
    predicted: Mapping[str, float],
    actual: Mapping[str, float],
    salaries: Mapping[str, float],
    positions: Optional[Mapping[str, str]] = None,
    boom_probabilities: Optional[Mapping[str, float]] = None,
    sport: str = "",
    site: str = "",
) -> ProjectionReport:
    """Score a set of projections against what actually happened."""
    return evaluate_projections(
        predicted,
        actual,
        salaries=salaries,
        positions=positions,
        boom_probabilities=boom_probabilities,
        sport=sport,
        site=site,
    )


def mlb_forward_test(
    date: str,
    site: str = "draftkings",
    n_sims: int = 2000,
    seed: int = 23,
    report_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Forward test on completed MLB games using only free, keyless MLB data.

    Procedure, per completed game on ``date``:

    1. pull the official box score and score each player's real stat line with the official
       DK/FD table -> the "actual" column;
    2. build each player's model inputs from **season totals minus the game being predicted**,
       so nothing from the game itself leaks into the projection (see
       ``ingest.subtract_game_from_season``);
    3. run the simulator and compare its mean projection with the actual score.

    Requires network access. In a sandbox without egress this raises
    :class:`stokengineer.ingest.OfflineError` - it does not silently return zeros.
    """
    from .ingest import (  # imported lazily so the rest of the package works offline
        Fetcher,
        boxscore_stat_lines,
        forward_test_props,
        mlb_boxscore,
        mlb_final_games,
        mlb_schedule,
        mlb_season_stats,
        season_rates,
    )

    fetcher = Fetcher()
    season = int(str(date)[:4])
    hitting = season_rates(mlb_season_stats(fetcher, season, "hitting"), "hitting")
    pitching = season_rates(mlb_season_stats(fetcher, season, "pitching"), "pitching")

    games = mlb_final_games(mlb_schedule(fetcher, date))
    predicted: Dict[str, float] = {}
    actual: Dict[str, float] = {}
    salaries: Dict[str, float] = {}
    positions: Dict[str, str] = {}
    per_game: List[Dict[str, Any]] = []

    # Salary is not needed for accuracy metrics and is not available from the free official
    # feeds, so it is a constant placeholder here. The boom/bust columns are therefore NOT
    # reported from this run - a boom threshold is a function of salary, so computing one from
    # a placeholder would be a fabricated number.
    default_salary = 4000.0
    for game in games:
        box = mlb_boxscore(fetcher, int(game["gamePk"]))
        rows = boxscore_stat_lines(box)
        players: List[PlayerProjection] = []
        game_actuals: Dict[str, float] = {}
        for row in rows:
            name = str(row["name"])
            is_pitcher = bool(row["pitching"]) and not row["batting"]
            positions[name] = str(row["position"] or ("P" if is_pitcher else "H"))
            actual_fp = score_statline(
                {k: float(v) for k, v in row["stats"].items()},
                site,
                "mlb",
                positions=("P",) if is_pitcher else (),
            )
            game_actuals[name] = actual_fp
            rates = pitching.get(row["player_id"]) if is_pitcher else hitting.get(row["player_id"])
            if not rates:
                continue  # no season sample for this player (debut, call-up, or traded mid-year)
            props = forward_test_props(rates, row.get("game_context", {}), is_pitcher)
            players.append(
                PlayerProjection(
                    id=name,
                    name=name,
                    team=str(row["team"]),
                    opponent=str(row["opponent"]),
                    positions=("P",) if is_pitcher else ("H",),
                    salary=default_salary,
                    props=props,
                    game_id=str(game["gamePk"]),
                )
            )
        if not players:
            continue
        slate = Slate(
            sport="mlb",
            site=site,
            players=players,
            date=date,
            games=[{"game_id": str(game["gamePk"])}],
        )
        projection = project_slate(slate, n_sims=n_sims, seed=seed, site=site)
        for row in projection["players"]:
            name = row["name"]
            if name in game_actuals:
                predicted[name] = row["projection"]
                actual[name] = game_actuals[name]
                salaries[name] = default_salary
        per_game.append(
            {
                "game_pk": game["gamePk"],
                "matchup": f"{game['teams']['away']['team']['name']} at "
                           f"{game['teams']['home']['team']['name']}",
                "players_scored": len(players),
            }
        )

    if not predicted:
        raise RuntimeError(
            f"forward test found no scoreable players for {date} - check the date and that "
            f"games are final"
        )

    report = backtest_projections(
        predicted,
        actual,
        salaries=salaries,
        positions=positions,
        boom_probabilities=None,  # no real salaries on this path; see the note above
        sport="mlb",
        site=site,
    )
    payload = {
        "test": "mlb_forward_test",
        "date": date,
        "site": site,
        "n_players_scored": len(predicted),
        "n_sims": n_sims,
        "games": per_game,
        "metrics": report.as_dict(),
        "fetched": fetcher.provenance(),
    }
    if report_path:
        write_report(
            report_path,
            payload,
            source_ids=["mlb_statsapi"],
            command=f"python -m src.stokengineer.cli forward-test --sport mlb --date {date}",
            notes=[
                "inputs exclude the predicted game (season totals minus that game's line)",
                "salaries are constant placeholders, so no boom/bust calibration is reported",
                "metrics are accuracy only: a forward test with no salaries and no ownership "
                "cannot say anything about ROI",
            ],
        )
    return payload


# ---------------------------------------------------------------------------
# sample data helper
# ---------------------------------------------------------------------------
def synthetic_reference_note() -> str:
    return (
        "Sample slates in src/data/samples are synthetic and labelled as such. They exist so "
        "the engine can be tested deterministically offline; they are not real salaries or "
        "real projections, and no report generated from them describes real players."
    )


def available_samples() -> List[str]:
    return sorted(p.name for p in (Path(DATA_DIR) / "samples").glob("*.json"))
