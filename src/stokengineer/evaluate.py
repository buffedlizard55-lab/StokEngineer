"""Evaluation: accuracy metrics, backtesting and the forward-test harness.

The project's rule is that a model claim needs evidence. This module produces that evidence
from data anyone can fetch for free:

* **Backtest** - replay past slates where both the model inputs and the actual results are
  available. Free sources make this possible for MLB (official Stats API box scores), NFL
  (nflverse), and NBA (nba_api).
* **Forward test** - run the model for games that have just finished and compare simulated
  quantities with what actually happened. This is what the scheduled GitHub Actions workflow
  does, because it needs network access that a locked-down sandbox does not have.

Metrics are deliberately unglamorous: MAE/RMSE/bias for level accuracy, Spearman rank
correlation for ordering, top-N overlap for the thing DFS actually cares about, and a Brier
score plus reliability table for the boom/bust probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .provenance import Registry, utc_now, write_json_with_provenance
from .rules import boom_threshold


# ---------------------------------------------------------------------------
# core metrics
# ---------------------------------------------------------------------------
def mae(predicted: np.ndarray, actual: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(predicted, float) - np.asarray(actual, float))))


def rmse(predicted: np.ndarray, actual: np.ndarray) -> float:
    diff = np.asarray(predicted, float) - np.asarray(actual, float)
    return float(np.sqrt(np.mean(diff**2)))


def bias(predicted: np.ndarray, actual: np.ndarray) -> float:
    return float(np.mean(np.asarray(predicted, float) - np.asarray(actual, float)))


def spearman(predicted: np.ndarray, actual: np.ndarray) -> float:
    """Rank correlation. Implemented directly so there is no scipy dependency."""
    p = _rankdata(np.asarray(predicted, float))
    a = _rankdata(np.asarray(actual, float))
    if p.size < 2:
        return float("nan")
    p_centered = p - p.mean()
    a_centered = a - a.mean()
    denom = math_sqrt((p_centered**2).sum() * (a_centered**2).sum())
    if denom == 0:
        return float("nan")
    return float((p_centered * a_centered).sum() / denom)


def math_sqrt(value: float) -> float:
    return float(np.sqrt(max(value, 0.0)))


def _rankdata(values: np.ndarray) -> np.ndarray:
    """Average ranks for ties (equivalent to scipy.stats.rankdata)."""
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_vals = values[order]
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def r2(predicted: np.ndarray, actual: np.ndarray) -> float:
    actual = np.asarray(actual, float)
    predicted = np.asarray(predicted, float)
    ss_res = ((actual - predicted) ** 2).sum()
    ss_tot = ((actual - actual.mean()) ** 2).sum()
    if ss_tot == 0:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


def top_n_overlap(predicted: np.ndarray, actual: np.ndarray, n: int) -> float:
    """Share of the truly top-N players that the projection also put in its top N."""
    predicted = np.asarray(predicted, float)
    actual = np.asarray(actual, float)
    n = max(1, min(n, len(predicted)))
    top_pred = set(np.argsort(-predicted)[:n].tolist())
    top_actual = set(np.argsort(-actual)[:n].tolist())
    return float(len(top_pred & top_actual) / n)


def brier_score(probabilities: np.ndarray, outcomes: np.ndarray) -> float:
    p = np.asarray(probabilities, float)
    o = np.asarray(outcomes, float)
    return float(np.mean((p - o) ** 2))


def reliability_table(
    probabilities: np.ndarray, outcomes: np.ndarray, bins: int = 10
) -> List[Dict[str, float]]:
    """Predicted-versus-realised table for a probability claim (e.g. Boom%)."""
    p = np.asarray(probabilities, float)
    o = np.asarray(outcomes, float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows: List[Dict[str, float]] = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1.0 else p <= hi)
        if not mask.any():
            continue
        rows.append(
            {
                "bin_low": float(lo),
                "bin_high": float(hi),
                "n": float(mask.sum()),
                "mean_predicted": float(p[mask].mean()),
                "realised": float(o[mask].mean()),
            }
        )
    return rows


@dataclass
class ProjectionReport:
    """Everything worth reporting about one slate's projections."""

    sport: str
    site: str
    n_players: int
    metrics: Dict[str, float] = field(default_factory=dict)
    by_position: Dict[str, Dict[str, float]] = field(default_factory=dict)
    boom_brier: Optional[float] = None
    boom_reliability: List[Dict[str, float]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "sport": self.sport,
            "site": self.site,
            "n_players": self.n_players,
            "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
            "by_position": {
                pos: {k: round(v, 4) for k, v in values.items()}
                for pos, values in self.by_position.items()
            },
            "boom_brier": None if self.boom_brier is None else round(self.boom_brier, 4),
            "boom_reliability": [
                {k: round(v, 4) for k, v in row.items()} for row in self.boom_reliability
            ],
            "notes": list(self.notes),
        }


def evaluate_projections(
    predicted: Mapping[str, float],
    actual: Mapping[str, float],
    salaries: Optional[Mapping[str, float]] = None,
    positions: Optional[Mapping[str, str]] = None,
    boom_probabilities: Optional[Mapping[str, float]] = None,
    sport: str = "",
    site: str = "",
    top_n: int = 20,
) -> ProjectionReport:
    """Compare projected fantasy points with what players actually scored.

    Only players present in **both** mappings are scored, and the count of dropped players is
    reported in ``notes`` - silently evaluating a different pool than the one projected is one
    of the easiest ways to publish a flattering number by accident.
    """
    common = [pid for pid in predicted if pid in actual]
    dropped = [pid for pid in predicted if pid not in actual]
    if not common:
        raise ValueError("no players appear in both predicted and actual")
    pred = np.array([float(predicted[pid]) for pid in common])
    act = np.array([float(actual[pid]) for pid in common])

    report = ProjectionReport(sport=sport, site=site, n_players=len(common))
    report.metrics = {
        "mae": mae(pred, act),
        "rmse": rmse(pred, act),
        "bias": bias(pred, act),
        "spearman": spearman(pred, act),
        "r2": r2(pred, act),
        f"top_{top_n}_overlap": top_n_overlap(pred, act, top_n),
        "mean_predicted": float(pred.mean()),
        "mean_actual": float(act.mean()),
    }
    if dropped:
        report.notes.append(f"{len(dropped)} projected players had no actual result and were excluded")

    if positions:
        groups: Dict[str, List[int]] = {}
        for i, pid in enumerate(common):
            pos = str(positions.get(pid, "?"))
            groups.setdefault(pos, []).append(i)
        for pos, idxs in groups.items():
            if len(idxs) < 5:
                continue
            idx = np.array(idxs)
            report.by_position[pos] = {
                "n": float(len(idx)),
                "mae": mae(pred[idx], act[idx]),
                "bias": bias(pred[idx], act[idx]),
                "spearman": spearman(pred[idx], act[idx]),
            }

    if boom_probabilities and salaries:
        # index the common list once: the old `common.index(pid)` inside the loop is O(n^2)
        # and called for every player on every slate
        position_of = {pid: i for i, pid in enumerate(common)}
        probs, outcomes = [], []
        for pid in common:
            salary = salaries.get(pid)
            if not salary:
                continue
            prob = boom_probabilities.get(pid)
            if prob is None:
                continue
            probs.append(float(prob) / 100.0 if prob > 1.0 else float(prob))
            outcomes.append(
                1.0 if act[position_of[pid]] >= float(boom_threshold(salary)) else 0.0
            )
        if probs:
            report.boom_brier = brier_score(np.array(probs), np.array(outcomes))
            report.boom_reliability = reliability_table(np.array(probs), np.array(outcomes))
    return report


# ---------------------------------------------------------------------------
# leakage guard
# ---------------------------------------------------------------------------
def assert_no_leakage(as_of: str, used_dates: Iterable[str]) -> None:
    """Fail if a projection used information dated after the slate it is predicting.

    Forward tests are only meaningful if this holds, and it is exactly the kind of bug that
    produces beautiful in-sample numbers, so it is a hard error rather than a warning.
    """
    cutoff = _date.fromisoformat(as_of)
    offenders = [d for d in used_dates if d and _date.fromisoformat(d) > cutoff]
    if offenders:
        raise ValueError(
            f"data leakage: projections for {as_of} used data from {sorted(offenders)}"
        )


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------
def write_report(
    path: str,
    payload: Mapping[str, Any],
    source_ids: Sequence[str],
    command: str,
    notes: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Write a report envelope, verifying every source id exists first."""
    registry = Registry()
    for sid in source_ids:
        registry.get(sid)  # raises on unknown ids
    envelope = write_json_with_provenance(
        path,
        payload,
        registry=registry,
        source_ids=source_ids,
        command=command,
        notes=notes,
    )
    return envelope


def contest_summary(results: Sequence[Any]) -> Dict[str, Any]:
    """Aggregate a list of ContestResult-ish objects into a headline block."""
    if not results:
        return {}
    rois = [r.roi_pct for r in results]
    cash = [r.cash_rate_pct for r in results]
    wins = [r.win_rate_pct for r in results]
    return {
        "n_lineups": len(results),
        "mean_roi_pct": float(np.mean(rois)),
        "median_roi_pct": float(np.median(rois)),
        "best_roi_pct": float(np.max(rois)),
        "worst_roi_pct": float(np.min(rois)),
        "mean_cash_rate_pct": float(np.mean(cash)),
        "best_win_rate_pct": float(np.max(wins)),
        "generated_at_utc": utc_now(),
    }
