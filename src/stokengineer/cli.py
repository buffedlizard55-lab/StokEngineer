"""Command line entry point: ``python -m src.stokengineer.cli <command>``.

Commands are deliberately boring and inspectable:

``doctor``        environment + dependency + registry + rules checks (run this first)
``rules``         print the verified scoring and roster rules for a site/sport
``project``       run the projection model on a slate file and print the table
``ownership``     project ownership for a slate file from the simulated field
``optimize``      build one or more lineups
``simulate``      run a full contest simulation for a slate (projection + ownership + lineups)
``backtest``      score projections against actual results
``forward-test``  pull free official data for completed games and report accuracy
``site-data``     regenerate the JSON the GitHub Pages site renders
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import DATA_DIR, REPORTS_DIR, __version__
from .evaluate import write_report
from .models import Slate, SimulationConfig, load_sample_slate
from .optimizer import LineupConstraints, StackSpec, optimize_portfolio
from .ownership import OwnershipModel, projected_ownership
from .pipeline import project_slate, run_slate, synthetic_reference_note
from .provenance import Registry
from .rules import get_site_rules, load_scoring, verify_rules


def _load_slate(args: argparse.Namespace) -> Slate:
    if args.sample:
        return load_sample_slate(args.sample)
    if not args.slate:
        raise SystemExit("provide --slate PATH or --sample NAME (see src/data/samples)")
    return Slate.load(args.slate)


#: hosts the ingest layer actually needs. A bare socket probe to a random IP is not evidence
#: that these are reachable, so the doctor asks them.
DATA_HOSTS = (
    "https://statsapi.mlb.com/api/v1/sports",
    "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "https://www.draftkings.com/lobby/getcontests?sport=NFL",
    "https://github.com",
)


def _probe_hosts(timeout: float = 6.0) -> tuple:
    """(reachable, unreachable) host lists, by making the same kind of request ingest makes."""
    import urllib.request

    reachable: List[str] = []
    unreachable: List[str] = []
    for url in DATA_HOSTS:
        host = urllib.parse.urlparse(url).netloc
        request = urllib.request.Request(url, headers={"User-Agent": "stokengineer-doctor"})
        try:
            with urllib.request.urlopen(request, timeout=timeout):
                reachable.append(host)
        except Exception:
            unreachable.append(host)
    return reachable, unreachable


def cmd_doctor(_args: argparse.Namespace) -> int:
    print(f"StokEngineer {__version__}")
    print(f"python        : {sys.version.split()[0]}")
    print(f"data dir      : {DATA_DIR}")
    deps = {}
    for name in ("numpy", "pulp"):
        try:
            module = __import__(name)
            deps[name] = getattr(module, "__version__", "installed")
        except Exception:
            deps[name] = "MISSING"
    print(f"dependencies  : {deps}")
    if deps["pulp"] == "MISSING":
        print("  note: without pulp the optimizer falls back to a legal but non-optimal search")
    reachable, unreachable = _probe_hosts()
    if reachable and not unreachable:
        print(f"network       : reachable ({', '.join(reachable)}) - ingest commands can run here")
    elif reachable:
        print(f"network       : PARTIAL - reachable {reachable}, blocked {unreachable}")
        print("                ingest commands for the blocked hosts will raise OfflineError")
    else:
        print(f"network       : NOT reachable ({', '.join(unreachable)})")
        print("                use a CSV import, or run ingest commands in CI where egress exists")

    registry = Registry()
    problems = registry.validate()
    print(f"sources       : {len(registry.sources)} declared, "
          f"{len([s for s in registry.sources if s.verification == 'fetched_live'])} read live this session")
    print(f"claims        : {len(registry.claims)}")
    for problem in problems:
        print(f"  PROBLEM: {problem}")

    rule_problems = verify_rules()
    for problem in rule_problems:
        print(f"  RULE PROBLEM: {problem}")
    ok = not problems and not rule_problems
    print("status        : " + ("OK" if ok else "PROBLEMS FOUND"))
    return 0 if ok else 1


def cmd_rules(args: argparse.Namespace) -> int:
    rules = get_site_rules(args.site, args.sport)
    scoring = load_scoring(args.site, args.sport)
    print(f"{args.site}/{args.sport} roster (source {rules.source}, verified {rules.verified})")
    print(f"  salary cap : {rules.salary_cap:,.0f}")
    print(f"  roster size: {rules.roster_size}")
    print(f"  min games  : {rules.min_games}")
    for eligible, count in rules.slot_groups():
        print(f"  {count} x {'/'.join(eligible)}")
    if rules.max_hitters_per_team:
        print(f"  max hitters per team: {rules.max_hitters_per_team}")
    if rules.min_skater_teams:
        print(f"  min skater teams    : {rules.min_skater_teams}")
    print(f"\n{args.site}/{args.sport} scoring (source {scoring.source}, verified {scoring.verified})")
    for key, value in sorted(scoring.coefficients.items()):
        print(f"  {key:22s} {value}")
    for rule in scoring.bonus_rules:
        print(f"  bonus {rule['id']:22s} +{rule['points']} when {rule['when']}")
    if scoring.dst_points_allowed_table:
        tiers = ", ".join(
            f"{row['min']}-{row['max'] if row['max'] is not None else '+'}: {row['points']}"
            for row in scoring.dst_points_allowed_table
        )
        print(f"  points allowed tiers: {tiers}")
    return 0


def cmd_project(args: argparse.Namespace) -> int:
    slate = _load_slate(args)
    result = project_slate(slate, n_sims=args.n_sims, seed=args.seed, site=args.site or slate.site)
    rows = result["players"]
    print(f"{slate.sport} {slate.date} - {len(rows)} players, {args.n_sims} sims")
    header = f"{'name':28s} {'pos':5s} {'sal':>6s} {'proj':>6s} {'ceil':>6s} {'floor':>6s} {'boom%':>6s} {'bust%':>6s}"
    print(header)
    for row in rows[: args.top]:
        print(
            f"{row['name'][:28]:28s} {'/'.join(row['positions'])[:5]:5s} {row['salary']:6.0f} "
            f"{row['projection']:6.2f} {row['ceiling']:6.2f} {row['floor']:6.2f} "
            f"{row['boom_pct']:6.1f} {row['bust_pct']:6.1f}"
        )
    if args.out:
        write_report(
            args.out,
            {
                "sport": slate.sport,
                "site": args.site or slate.site,
                "date": slate.date,
                "n_sims": args.n_sims,
                "players": rows,
            },
            source_ids=sorted(Registry().source_ids_for_sport(slate.sport)),
            command=(
                f"python -m src.stokengineer.cli project --sample {args.sample}"
                if args.sample
                else f"python -m src.stokengineer.cli project --slate {args.slate}"
            ),
            notes=[synthetic_reference_note()] if args.sample else [],
        )
        print(f"wrote {args.out}")
    return 0


def cmd_ownership(args: argparse.Namespace) -> int:
    slate = _load_slate(args)
    projection = project_slate(slate, n_sims=args.n_sims, seed=args.seed, site=args.site or slate.site)
    weights = OwnershipModel().raw_weights(slate, projection["projections"])
    ownership = projected_ownership(
        slate, weights, n_entries=args.field_entries, seed=args.seed, site=args.site or slate.site
    )
    print(f"{'name':28s} {'proj':>6s} {'own%':>6s}")
    for row in projection["players"][: args.top]:
        print(f"{row['name'][:28]:28s} {row['projection']:6.2f} {ownership[row['player_id']]:6.2f}")
    total = sum(ownership.values())
    expected = get_site_rules(args.site or slate.site, slate.sport).roster_size * 100
    print(f"\nsum(ownership) = {total:.1f} (expected ~{expected} for a legal field)")
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    slate = _load_slate(args)
    site = args.site or slate.site
    projection = project_slate(slate, n_sims=args.n_sims, seed=args.seed, site=site)
    ceiling = {r["player_id"]: r["ceiling"] for r in projection["players"]}
    floor = {r["player_id"]: r["floor"] for r in projection["players"]}
    stddev = {r["player_id"]: r["stddev"] for r in projection["players"]}
    view = projection["projections"]
    notes: List[str] = []
    if args.projection_error > 0:
        rng = np.random.default_rng(args.seed + 1)
        view = {
            player.id: max(0.0, view[player.id] * (1.0 + rng.normal(0.0, args.projection_error)))
            for player in slate.players
        }
        notes.append(
            f"lineups built from a noisy view of the projections (sd {args.projection_error:.0%})"
        )
    constraints = LineupConstraints(
        objective=args.objective,
        locked=set(args.lock or []),
        excluded=set(args.exclude or []),
        max_players_per_team=args.max_per_team,
        stack=StackSpec(count=args.stack_count, include_qb=True, team=args.stack_team)
        if args.stack_count
        else None,
        bring_back=args.bring_back,
    )
    lineups = optimize_portfolio(
        slate,
        view,
        args.n_lineups,
        max_exposure=args.max_exposure,
        min_unique=args.min_unique,
        constraints=constraints,
        site=site,
        ceiling=ceiling,
        floor=floor,
        stddev=stddev,
        objective=args.objective,
        seed=args.seed,
        prefer_milp=not args.no_milp,
    )
    if not lineups:
        print("no legal lineups found under those constraints", file=sys.stderr)
        return 1
    index = {p.id: p for p in slate.players}
    for number, lineup in enumerate(lineups, start=1):
        print(
            f"lineup {number}: method {lineup.method}  salary {lineup.salary:,.0f}  "
            f"projected {lineup.projected:.2f}"
        )
        for slot, pid in sorted(lineup.slot_assignment.items()):
            player = index[pid]
            print(f"  {slot:6s} {player.name:32s} {player.team:4s} {player.salary:6.0f}")
        for note in lineup.notes:
            print(f"  note: {note}")
    for note in notes:
        print(f"note: {note}")
    print(
        "note: this is a lineup build only - it says nothing about expected money. To price "
        "these lineups against a field and a payout structure use `simulate`."
    )
    if args.out:
        write_report(
            args.out,
            {
                "sport": slate.sport,
                "site": site,
                "lineups": [lineup.as_dict() for lineup in lineups],
                "projections": view,
            },
            source_ids=sorted(Registry().source_ids_for_sport(slate.sport)),
            command=(
                f"python -m src.stokengineer.cli optimize --sample {args.sample}"
                if args.sample
                else "python -m src.stokengineer.cli optimize"
            ),
            notes=notes + ([synthetic_reference_note()] if args.sample else []),
        )
        print(f"wrote {args.out}")
    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    slate = _load_slate(args)
    if args.quick:  # deterministic smoke preset for CI; the numbers are still clearly labelled
        args.n_sims = min(args.n_sims, 400)
        args.field_size = min(args.field_size, 400)
        args.n_lineups = min(args.n_lineups, 2)
    run = run_slate(
        slate,
        n_sims=args.n_sims,
        n_lineups=args.n_lineups,
        field_size=args.field_size,
        entry_fee=args.entry_fee,
        seed=args.seed,
        max_exposure=args.max_exposure,
        objective=args.objective,
        projection_error=args.projection_error,
        sharp_share=args.sharp_share,
        config=SimulationConfig(),
        site=args.site or slate.site,
    )
    payload = run.as_dict()
    print(f"{slate.sport} {slate.date}: {len(payload['lineups'])} lineups vs "
          f"{payload['field_size']} field entries, {payload['n_sims']} sims")
    for row in payload["contest"]:
        print(
            f"  {row['label']:9s} proj {row['projected_score']:6.2f}  "
            f"ROI {row['roi_pct']:7.2f}%  cash {row['cash_rate_pct']:5.1f}%  "
            f"win {row['win_rate_pct']:6.3f}%  med rank {row['median_rank']:.0f}"
        )
    for note in payload["notes"]:
        print(f"  note: {note}")
    if args.out:
        notes = list(payload["notes"])
        if args.sample:
            notes.append(synthetic_reference_note())
        write_report(
            args.out,
            payload,
            source_ids=sorted(Registry().source_ids_for_sport(slate.sport)),
            command=(
                f"python -m src.stokengineer.cli simulate --sample {args.sample}"
                if args.sample
                else "python -m src.stokengineer.cli simulate"
            ),
            notes=notes,
        )
        print(f"wrote {args.out}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    from .ingest import import_actuals_csv
    from .pipeline import backtest_projections

    predicted_raw = json.loads(Path(args.predictions).read_text())
    predicted = predicted_raw.get("payload", predicted_raw)
    predicted_map = {
        row["name"]: row["projection"]
        for row in predicted.get("players", predicted.get("projections", []))
    }
    actual = import_actuals_csv(args.actuals)
    report = backtest_projections(predicted_map, actual, salaries={}, sport=args.sport, site=args.site)
    print(json.dumps(report.as_dict(), indent=2))
    if args.out:
        write_report(
            args.out,
            report.as_dict(),
            source_ids=[],
            command="python -m src.stokengineer.cli backtest",
        )
    return 0


def cmd_forward_test(args: argparse.Namespace) -> int:
    from .pipeline import mlb_forward_test

    if args.sport != "mlb":
        raise SystemExit("forward-test currently supports --sport mlb (free, keyless official source)")
    out = args.out or str(REPORTS_DIR / f"forward_test_mlb_{args.date}.json")
    payload = mlb_forward_test(args.date, site=args.site, n_sims=args.n_sims, report_path=out)
    metrics = payload["metrics"]["metrics"]  # ProjectionReport.as_dict() nests metrics
    print(f"forward test {args.date}: {payload['n_players_scored']} players over "
          f"{len(payload['games'])} games")
    print(f"  MAE {metrics['mae']:.3f}  RMSE {metrics['rmse']:.3f}  bias {metrics['bias']:+.3f}")
    print(f"  spearman {metrics['spearman']:.3f}  top20 overlap {metrics['top_20_overlap']:.2f}")
    print(f"wrote {out}")
    return 0


def cmd_site_data(args: argparse.Namespace) -> int:
    from tools.build_site_data import build  # type: ignore

    path = build(Path(args.out) if args.out else None)
    print(f"wrote {path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Check the whole knowledge base: registry, claims, rules, samples, site data."""
    problems: List[str] = []
    registry = Registry()
    problems += registry.validate()
    problems += verify_rules()
    for sample in sorted((DATA_DIR / "samples").glob("*.json")):
        try:
            slate = Slate.load(sample)
            problems += [f"{sample.name}: {p}" for p in slate.validate()]
            if not (json.loads(sample.read_text()).get("_meta", {}).get("synthetic")):
                problems.append(f"{sample.name}: sample is not labelled synthetic")
        except Exception as exc:  # pragma: no cover - reported, not raised
            problems.append(f"{sample.name}: {exc}")
    for problem in problems:
        print(f"PROBLEM: {problem}")
    print("verify: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    return 0 if not problems else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stokengineer", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--slate", help="slate JSON file")
        p.add_argument("--sample", help="bundled sample slate name, e.g. sample_nfl_dk.json")
        p.add_argument("--site", choices=["draftkings", "fanduel"])
        p.add_argument("--n-sims", type=int, default=2000)
        p.add_argument("--seed", type=int, default=7)

    p = sub.add_parser("doctor", help="environment, dependency and registry checks")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("rules", help="print verified rules for a site/sport")
    p.add_argument("--site", default="draftkings", choices=["draftkings", "fanduel"])
    p.add_argument("--sport", default="nfl", choices=["nfl", "nba", "mlb", "nhl"])
    p.set_defaults(func=cmd_rules)

    p = sub.add_parser("project", help="project a slate")
    add_common(p)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--out", help="write the projection table as a provenance-wrapped JSON report")
    p.set_defaults(func=cmd_project)

    p = sub.add_parser("ownership", help="project ownership for a slate")
    add_common(p)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--field-entries", type=int, default=800)
    p.set_defaults(func=cmd_ownership)

    p = sub.add_parser("optimize", help="build a lineup")
    add_common(p)
    p.add_argument("--objective", default="median", choices=["median", "ceiling", "floor", "sim_roi"])
    p.add_argument("--lock", action="append", help="player id to lock (repeatable)")
    p.add_argument("--exclude", action="append", help="player id to exclude (repeatable)")
    p.add_argument("--max-per-team", type=int)
    p.add_argument("--n-lineups", type=int, default=1)
    p.add_argument("--max-exposure", type=float, default=0.6)
    p.add_argument("--min-unique", type=int, default=2, help="different players vs each other lineup")
    p.add_argument("--stack-count", type=int, default=0, help="players from one team (NFL)")
    p.add_argument("--stack-team", help="force the stack onto this team")
    p.add_argument("--bring-back", type=int, default=0, help="players from the stack's opponent")
    p.add_argument(
        "--projection-error",
        type=float,
        default=0.0,
        help="simulate the user's own error: build lineups from a noisy view of the projections",
    )
    p.add_argument("--no-milp", action="store_true", help="force the DFS search (no solver)")
    p.add_argument("--out", help="write a JSON report here")
    p.set_defaults(func=cmd_optimize)

    p = sub.add_parser("simulate", help="full slate run: projections, ownership, lineups, contest sim")
    add_common(p)
    p.add_argument("--n-lineups", type=int, default=5)
    p.add_argument("--field-size", type=int, default=2000)
    p.add_argument("--entry-fee", type=float, default=20.0)
    p.add_argument("--max-exposure", type=float, default=1.0)
    p.add_argument("--objective", default="median", choices=["median", "ceiling", "floor"])
    p.add_argument(
        "--projection-error",
        type=float,
        default=0.25,
        help=(
            "how wrong our own projections are assumed to be (default 0.25). At 0 the lineups "
            "are built from the model's own projections while the field is not, which flatters "
            "ROI; use 0 only to compare builds against each other"
        ),
    )
    p.add_argument(
        "--sharp-share",
        type=float,
        default=0.35,
        help="share of the field assumed to draft with sharp (small-error) projections",
    )
    p.add_argument(
        "--quick",
        action="store_true",
        help="small deterministic preset (<=400 sims/entries) for smoke tests",
    )
    p.add_argument("--out", help="write a JSON report here")
    p.set_defaults(func=cmd_simulate)

    p = sub.add_parser("backtest", help="score projections against actual results")
    p.add_argument(
        "--predictions",
        required=True,
        help="JSON produced by `project --out` (or any JSON with a players/projections list)",
    )
    p.add_argument("--actuals", required=True, help="CSV with name,actual columns")
    p.add_argument("--sport", default="")
    p.add_argument("--site", default="")
    p.add_argument("--out")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("forward-test", help="pull free official data for a completed date")
    p.add_argument("--sport", default="mlb")
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--site", default="draftkings")
    p.add_argument("--n-sims", type=int, default=2000)
    p.add_argument("--out")
    p.set_defaults(func=cmd_forward_test)

    p = sub.add_parser("site-data", help="regenerate docs/assets/data.js")
    p.add_argument("--out")
    p.set_defaults(func=cmd_site_data)

    p = sub.add_parser("verify", help="check registry, claims, rules and samples")
    p.set_defaults(func=cmd_verify)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:  # surface a clean error instead of a traceback wall
        from .ingest import OfflineError

        if isinstance(exc, OfflineError):
            print(f"offline: {exc}", file=sys.stderr)
            return 3
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
