"""build_site_data.py - generate the JSON/JS the GitHub Pages site renders.

Everything on the site comes from this file, and everything in this file comes from one of:

* ``src/data/sources_verified.json`` - the source registry (url, licence, how it was verified);
* ``src/data/claims.json`` - the claim ledger (what we assert, the quote, the source id);
* ``src/data/{roster,scoring}_rules.json`` - the rules the engine enforces, each with a source;
* a real run of the engine on the bundled **synthetic** sample slates (clearly labelled);
* ``reports/*.json`` written by the CLI, each carrying its own provenance envelope.

The site therefore cannot claim anything this repository cannot point at. Numbers produced
from synthetic samples are labelled ``synthetic: true`` and the site renders the label.

Usage:  python tools/build_site_data.py [--out docs/assets/data.js]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import subprocess
from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.stokengineer import __version__  # noqa: E402
from src.stokengineer.models import load_sample_slate  # noqa: E402
from src.stokengineer.optimizer import (  # noqa: E402
    LineupConstraints,
    optimize_lineup,
    optimize_portfolio,
)
from src.stokengineer.ownership import OwnershipModel, projected_ownership  # noqa: E402
from src.stokengineer.pipeline import project_slate, synthetic_reference_note  # noqa: E402
from src.stokengineer.provenance import Registry, utc_now  # noqa: E402
from src.stokengineer.rules import get_site_rules, load_scoring, verify_rules  # noqa: E402
from src.stokengineer.simulate import (  # noqa: E402
    _scores_for,
    PayoutStructure,
    field_lineups_from_ownership,
    plausibility_warnings,
    simulate_contest,
)

#: The demo builds lineups from a view as noisy as the field's own view (25%). Anything
#: smaller claims an information edge nobody has paid for, and the resulting ROI is fiction.
DEMO_PROJECTION_ERROR = 0.25

SPORTS = ("nfl", "nba", "mlb", "nhl")
SITES = ("draftkings", "fanduel")


def git_revision() -> Optional[str]:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return None


def rules_summary() -> List[Dict[str, Any]]:
    """Every site/sport combination with its slots, cap and a link to the source."""
    rows: List[Dict[str, Any]] = []
    registry = Registry()
    for site in SITES:
        for sport in SPORTS:
            try:
                rules = get_site_rules(site, sport)
                scoring = load_scoring(site, sport)
            except KeyError:
                continue  # that combination is deliberately not published in the data files
            rows.append(
                {
                    "site": site,
                    "sport": sport,
                    "salary_cap": rules.salary_cap,
                    "roster_size": rules.roster_size,
                    "min_games": rules.min_games,
                    "slots": [
                        {"eligible": list(eligible), "count": count}
                        for eligible, count in rules.slot_groups()
                    ],
                    "max_hitters_per_team": rules.max_hitters_per_team,
                    "min_skater_teams": rules.min_skater_teams,
                    "bonus_rules": list(scoring.bonus_rules),
                    "scoring": {k: float(v) for k, v in sorted(scoring.coefficients.items())},
                    "source_id": rules.source,
                    "source_url": _source_url(registry, rules.source),
                    "verified": rules.verified,
                }
            )
    return rows


def _source_url(registry: Registry, source_id: str) -> Optional[str]:
    try:
        return registry.get(source_id).url
    except Exception:
        return None


def engine_demo(n_sims: int = 1000, field_size: int = 600, n_lineups: int = 3) -> List[Dict[str, Any]]:
    """Run the engine end to end on each synthetic sample and record what it produced."""
    demos: List[Dict[str, Any]] = []
    for name in sorted(path.name for path in (ROOT / "src" / "data" / "samples").glob("*.json")):
        slate = load_sample_slate(name)
        projection = project_slate(slate, n_sims=n_sims, seed=11, site=slate.site)
        projections = projection["projections"]
        # Build the demo lineups from a NOISY view of the projections. With the model's own
        # projections the lineups and the field come from the same numbers, which makes ROI
        # meaningless (it measures only that the field was given error and the lineup was not).
        rng_view = np.random.default_rng(12)
        view = {
            player.id: max(0.0, projections[player.id] * (1.0 + rng_view.normal(0.0, DEMO_PROJECTION_ERROR)))
            for player in slate.players
        }
        ceiling = {row["player_id"]: row["ceiling"] for row in projection["players"]}
        floor = {row["player_id"]: row["floor"] for row in projection["players"]}
        weights = OwnershipModel().raw_weights(slate, projections)
        ownership = projected_ownership(
            slate, weights, n_entries=max(200, field_size // 3), seed=11, site=slate.site
        )
        lineups = optimize_portfolio(
            slate,
            view,
            n_lineups,
            max_exposure=0.6,
            min_unique=2,
            constraints=LineupConstraints(objective="median"),
            site=slate.site,
            ceiling=ceiling,
            floor=floor,
            seed=11,
        )
        payout = PayoutStructure.illustrative_gpp(field_size, 20.0)
        field = field_lineups_from_ownership(
            slate, ownership, field_size, seed=11, site=slate.site, projections=projections,
            strong_share=0.25,
        )
        index = slate.index()  # player id -> column in the simulation matrix
        by_id = {player.id: player for player in slate.players}
        results = simulate_contest(
            projection["matrix"],
            [[index[pid] for pid in lineup.player_ids] for lineup in lineups],
            payout,
            field_lineups=field,
            labels=[f"lineup_{i + 1}" for i in range(len(lineups))],
        )
        # Score a SAMPLE OF THE FIELD the same way and print it next to the user's lineups.
        # If a random field entry also earns far more than the rake, the ROI number is telling
        # you about the field model, not about the lineups - which is exactly the honest read.
        baseline_sample = field[: min(60, len(field))]
        baseline_results = simulate_contest(
            projection["matrix"],
            baseline_sample,
            payout,
            field_lineups=field,
            labels=[f"field_{i + 1}" for i in range(len(baseline_sample))],
        )
        # The best decile of the FIELD, scored the same way. If those entries also earn large
        # ROI, the user's number is about being in the good tail of a top-heavy payout, not a
        # magic lineup.
        field_scores = _scores_for(projection["matrix"], field).mean(axis=0)
        best_field = [field[i] for i in np.argsort(-field_scores)[: max(1, len(field) // 10)]]
        best_results = simulate_contest(
            projection["matrix"],
            best_field,
            payout,
            field_lineups=field,
            labels=[f"top_field_{i + 1}" for i in range(len(best_field))],
        )
        # And the same optimiser on repeat draws of its own noisy view: the spread is the point.
        draw_rois = []
        for draw in range(6):
            draw_rng = np.random.default_rng(4000 + draw)
            draw_view = {
                player.id: max(
                    0.0,
                    projections[player.id] * (1.0 + draw_rng.normal(0.0, DEMO_PROJECTION_ERROR)),
                )
                for player in slate.players
            }
            draw_lineup = optimize_lineup(
                slate, draw_view, site=slate.site, ceiling=ceiling, floor=floor
            )
            draw_result = simulate_contest(
                projection["matrix"],
                [[index[pid] for pid in draw_lineup.player_ids]],
                payout,
                field_lineups=field,
                labels=[f"draw_{draw + 1}"],
            )
            draw_rois.append(round(draw_result[0].roi_pct, 1))
        baseline = {
            "lineups_sampled": len(baseline_sample),
            "best_decile_roi_pct": round(
                float(np.mean([r.roi_pct for r in best_results])), 1
            ),
            "best_decile_note": (
                "the top 10% of the simulated field, by mean simulated score, scored as if it "
                "were the user. Large ROI here too means the payout curve's tail, not the "
                "lineup, is doing the work."
            ),
            "own_draw_rois_pct": draw_rois,
            "own_draws_note": (
                "the same optimiser, six independent noisy views (sd 25%), one lineup each. The "
                "spread across draws is larger than the difference between the builds, which is "
                "why no single ROI number should be read as an edge."
            ),
            "mean_roi_pct": round(float(np.mean([r.roi_pct for r in baseline_results])), 1),
            "mean_cash_rate_pct": round(
                float(np.mean([r.cash_rate_pct for r in baseline_results])), 1
            ),
            "mean_percentile": round(
                float(np.mean([r.mean_percentile for r in baseline_results])), 1
            ),
            "note": (
                "the same simulation run with a random sample of the field as the user. A cash "
                "rate near the paid fraction pins the ROI to the payout curve; anything far from "
                "the rake means the field model, not the strategy, is driving the number."
            ),
        }
        demos.append(
            {
                "sample": name,
                "sport": slate.sport,
                "site": slate.site,
                "date": slate.date,
                "synthetic": True,
                "n_sims": n_sims,
                "field_size": field_size,
                "payout_source": payout.source,
                "field_baseline": baseline,
                "projection_table": projection["players"][:25],
                "ownership_top": sorted(
                    (
                        {
                            "name": player.name,
                            "team": player.team,
                            "positions": list(player.positions),
                            "salary": player.salary,
                            "ownership_pct": round(ownership.get(player.id, 0.0), 2),
                        }
                        for player in slate.players
                    ),
                    key=lambda row: -row["ownership_pct"],
                )[:15],
                "lineups": [
                    {
                        "label": result.label,
                        "method": lineup.method,
                        "salary": round(lineup.salary, 0),
                        "projected": round(lineup.projected, 2),
                        "players": [
                            {
                                "name": by_id[pid].name,
                                "positions": list(by_id[pid].positions),
                                "team": by_id[pid].team,
                                "salary": by_id[pid].salary,
                            }
                            for pid in lineup.player_ids
                        ],
                        # ROI/cash/win rates come from the simulator against an ILLUSTRATIVE
                        # payout curve and a simulated field: a ranking aid, not a forecast.
                        "roi_pct": round(result.roi_pct, 1),
                        "cash_rate_pct": round(result.cash_rate_pct, 1),
                        "win_rate_pct": round(result.win_rate_pct, 3),
                        "median_rank": round(result.median_rank, 0),
                        "mean_percentile": round(result.mean_percentile, 1),
                    }
                    for result, lineup in zip(results, lineups)
                ],
                "notes": [
                    synthetic_reference_note(),
                    "lineups were built from a view of the projections as noisy as the field's "
                    "(sd 25%): the honest-test setting. Building them from the model's own "
                    "projections makes simulated ROI meaningless, because the field is given "
                    "error and the lineup is not.",
                    "ownership is a simulated-field estimate, not observed contest ownership",
                    "the payout structure is ILLUSTRATIVE; ROI is only meaningful with the real "
                    "contest payout table imported from a CSV",
                    "compare each lineup's ROI with the field baseline in this same run: if a "
                    "random field entry also earns far more than the rake, the number is about "
                    "the field model, not the lineups",
                ]
                + plausibility_warnings(results, payout),
            }
        )
    return demos


def build_timestamp() -> str:
    """A reproducible build timestamp.

    CI regenerates this file and fails if the committed copy differs, so the timestamp must not
    be "now": it is taken from SOURCE_DATE_EPOCH when set (the reproducible-builds convention),
    otherwise from the HEAD commit date, and only as a last resort from the clock.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI"], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return utc_now()


def cli_reports() -> List[Dict[str, Any]]:
    """Latest provenance-wrapped reports the CLI wrote, if any are committed.

    Only files carrying a provenance envelope count. Tool verdicts (`links.json`,
    `site_data_check.json`, `tests_summary.json`) live in the same directory but are written by the
    checks themselves - listing them here would make this payload depend on the order the tools ran
    in, which is exactly the kind of coupling that makes a "reproducible" data file a lie.
    """
    reports: List[Dict[str, Any]] = []
    for path in sorted((ROOT / "reports").glob("*.json")):
        if path.name in {"links.json", "tests_summary.json", "site_data_check.json"}:
            continue
        try:
            payload = json.loads(path.read_text())
        except Exception:
            continue
        wrapped = payload.get("provenance") or payload.get("_provenance")
        if not wrapped:
            continue
        reports.append(
            {
                "file": path.name,
                "keys": sorted(payload.keys())[:12],
                "provenance": wrapped,
                "kind": wrapped.get("command") or path.stem,
            }
        )
    reports.sort(key=lambda item: (item["provenance"].get("generated_at_utc") or "", item["file"]))
    return reports[-8:]


def test_summary() -> Optional[Dict[str, Any]]:
    """CI writes reports/tests_summary.json; include it verbatim when it exists."""
    path = ROOT / "reports" / "tests_summary.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def limitations() -> List[Dict[str, str]]:
    """The LIMITATIONS.md headings and their first paragraph.

    Rendered on the site at build time so the page cannot quietly omit the uncomfortable parts.
    """
    path = ROOT / "LIMITATIONS.md"
    if not path.exists():
        return []
    items: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            if current:
                items.append(current)
            current = {"heading": line[3:].strip(), "body": ""}
            continue
        if current is None or line.startswith("#"):
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("|") or stripped.startswith("*") is False and False:
            continue
        if stripped.startswith(("|", "```")):
            continue
        if not current["body"] and not stripped.startswith("**"):
            current["body"] = stripped
    if current:
        items.append(current)
    for item in items:
        body = item["body"]
        if len(body) > 320:
            item["body"] = body[:320].rsplit(" ", 1)[0] + " …"
        if not body:
            item["body"] = "See LIMITATIONS.md for the full text."
    return items


def build(out_path: Optional[Path] = None, n_sims: int = 1000) -> Path:
    registry = Registry()
    sources = [
        {
            "id": source.id,
            "url": source.url,
            "title": source.title,
            "publisher": source.publisher,
            "provides": source.what_it_provides,
            "licence": source.licence_or_terms,
            "free": source.free,
            "key_required": source.key_required,
            "official": source.official,
            "verification": source.verification,
        }
        for source in registry.sources
    ]
    claims = []
    for claim in registry.claims:
        source = registry.get(claim["source_id"]) if claim.get("source_id") else None
        claims.append(
            {
                "id": claim.get("id"),
                "claim": claim.get("claim"),
                "quote": claim.get("quote"),
                "status": claim.get("status"),
                "relevance": claim.get("relevance"),
                "source_id": claim.get("source_id"),
                "source_url": getattr(source, "url", None),
                "source_title": getattr(source, "title", None),
            }
        )
    payload: Dict[str, Any] = {
        "meta": {
            "version": __version__,
            "generated_at": build_timestamp(),
            "git_revision": git_revision(),
            "synthetic_reference": synthetic_reference_note(),
        },
        "status": {
            "registry_problems": registry.validate(),
            "rules_problems": verify_rules(),
            "tests": test_summary(),
        },
        "sources": sources,
        "claims": claims,
        "removed_or_downgraded": registry.raw.get("removed_or_downgraded", []),
        "rules": rules_summary(),
        "demo": engine_demo(n_sims=n_sims),
        "reports": cli_reports(),
        "limitations": limitations(),
        "test_summary": test_summary(),
    }
    target = out_path or (ROOT / "docs" / "assets" / "data.js")
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "window.STOKENGINEER_DATA = " + json.dumps(payload, indent=1) + ";\n"
    target.write_text(body)
    # a machine-readable copy as well, so CI and reviewers can diff it without parsing JS
    json_target = ROOT / "docs" / "data" / "site_data.json"
    json_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.write_text(json.dumps(payload, indent=1) + "\n")
    return target


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="path to write data.js to")
    parser.add_argument("--n-sims", type=int, default=1000)
    args = parser.parse_args(argv)
    path = build(Path(args.out) if args.out else None, n_sims=args.n_sims)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
