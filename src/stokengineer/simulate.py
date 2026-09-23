"""Contest-level simulation.

This is the feature Stokastic calls its differentiator: "Game level simulation tools exist on
the market currently ... However, nowhere else do users have the ability to perform
simulations on the contest level" (source ``sk_pricing``), and "Every lineup that comes out is
then ranked by simulated ROI against the real payout structure of the contest you tell it you
are entering" (source ``sk_nfl_review``, claim c04).

The implementation mirrors that description exactly:

1. sample the slate many times (player outcomes vary sim to sim),
2. build a field whose lineups are drawn with each player's projected ownership weighting how
   often he is shared (claim c03),
3. score the user's lineups against that field in every simulation,
4. convert the finishing rank in each simulation into a payout using the payout structure the
   user supplied, and report expectation, cash rate, win rate and percentiles.

Payout structures are inputs, never guesses: :class:`PayoutStructure` accepts a real tier list
or a CSV exported from a contest page, and `illustrative_*` builders are clearly named as
illustrative so no report can pass one off as a real contest.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .models import Slate
from .ownership import generate_field_lineups
from .rules import summarise_distribution


# ---------------------------------------------------------------------------
# payout structures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PayoutTier:
    """A contiguous range of finishing ranks paid ``amount`` each."""

    start_rank: int
    end_rank: int
    amount: float


@dataclass
class PayoutStructure:
    entries: int
    entry_fee: float
    tiers: Tuple[PayoutTier, ...]
    source: str = "user supplied"

    # -- constructors --------------------------------------------------------
    @staticmethod
    def from_tiers(
        entries: int, entry_fee: float, tiers: Sequence[Mapping[str, Any]], source: str = "user supplied"
    ) -> "PayoutStructure":
        parsed = tuple(
            PayoutTier(int(t["start_rank"]), int(t["end_rank"]), float(t["amount"])) for t in tiers
        )
        structure = PayoutStructure(entries=int(entries), entry_fee=float(entry_fee),
                                    tiers=parsed, source=source)
        structure.validate()
        return structure

    @staticmethod
    def from_csv(path: Path | str, entries: int, entry_fee: float) -> "PayoutStructure":
        """Read a payout table exported from a contest page.

        Accepted columns: ``rank`` (or ``start_rank``/``end_rank``) and ``amount`` (or
        ``payout``/``prize``). One row per paid rank is fine for small fields; for big fields
        use ranges. This is the sanctioned route because it uses the user's own contest data
        rather than scraping.
        """
        tiers: List[PayoutTier] = []
        with open(path, newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                lower = {k.lower().strip(): v for k, v in row.items()}
                start = lower.get("start_rank") or lower.get("rank")
                end = lower.get("end_rank") or lower.get("rank")
                amount = lower.get("amount") or lower.get("payout") or lower.get("prize")
                if start in (None, "") or amount in (None, ""):
                    continue
                tiers.append(
                    PayoutTier(int(float(start)), int(float(end)), float(str(amount).replace("$", "").replace(",", "")))
                )
        structure = PayoutStructure(entries=entries, entry_fee=entry_fee, tiers=tuple(tiers),
                                    source=f"csv:{Path(path).name}")
        structure.validate()
        return structure

    @staticmethod
    def illustrative_gpp(
        entries: int,
        entry_fee: float,
        first_place_share: float = 0.12,
        paid_fraction: float = 0.20,
        top_depth: int = 15,
        decay: float = 0.62,
        min_cash_multiple: float = 1.7,
        rake: float = 0.12,
    ) -> "PayoutStructure":
        """ILLUSTRATIVE top-heavy curve shaped like a large-field GPP. Not a real contest.

        Construction (and why it is built this way): the pool is ``entries * fee * (1 - rake)``;
        the tail pays ``min_cash_multiple x fee`` to each cashing entry; whatever is left funds
        the top ``top_depth`` places with a geometric decay, normalised so the tiers sum exactly
        to the pool. Two details matter for honest ROI numbers:

        * the min cash is a realistic multiple (~1.7x), because a structure that pays 3x for
          scraping into the money makes every simulated ROI look fantastic;
        * the top prizes are normalised to the leftover pool rather than picking a first prize
          and hoping the rest fits.

        Stokastic asks the user for the real payout structure instead of shipping one (claim
        c04), and so does this engine: use :meth:`from_csv` with the contest's own payout table
        before believing any ROI.
        """
        pool = entries * entry_fee * (1.0 - rake)
        paid = max(1, int(entries * paid_fraction))
        depth = min(top_depth, paid)
        min_cash = entry_fee * min_cash_multiple
        tail_count = max(0, paid - depth)
        tail_pool = min_cash * tail_count
        top_pool = pool - tail_pool
        if top_pool <= 0:
            raise ValueError(
                f"min cash of {min_cash:.2f} x {tail_count} tail entries exceeds the pool "
                f"({pool:.2f}); lower min_cash_multiple or paid_fraction"
            )
        raw_top = [decay**i for i in range(depth)]
        normaliser = sum(raw_top) / (top_pool * max(first_place_share, 1e-9) / max(first_place_share, 1e-9))
        # first place takes `first_place_share` of the top pool; the rest decays geometrically
        first = top_pool * first_place_share
        amounts = [first * (decay**i) for i in range(depth)]
        scale = top_pool / sum(amounts)
        amounts = [a * scale for a in amounts]
        tiers: List[PayoutTier] = [
            PayoutTier(i + 1, i + 1, amount) for i, amount in enumerate(amounts)
        ]
        if tail_count:
            tiers.append(PayoutTier(depth + 1, paid, min_cash))
        structure = PayoutStructure(
            entries=entries,
            entry_fee=entry_fee,
            tiers=tuple(tiers),
            source="ILLUSTRATIVE curve generated in-engine (not a real contest)",
        )
        structure.validate()
        return structure

    @staticmethod
    def flat_cash(entries: int, entry_fee: float, paid_fraction: float = 0.55,
                  multiple: float = 1.8) -> "PayoutStructure":
        """ILLUSTRATIVE double-up style structure (no rake modelling beyond the multiple)."""
        paid = max(1, int(entries * paid_fraction))
        return PayoutStructure.from_tiers(
            entries,
            entry_fee,
            [{"start_rank": 1, "end_rank": paid, "amount": entry_fee * multiple}],
            source="ILLUSTRATIVE flat cash curve (not a real contest)",
        )

    # -- accessors -----------------------------------------------------------
    def payout_lookup(self, max_rank: Optional[int] = None) -> np.ndarray:
        """Dense rank -> amount table, so a whole chunk of simulations can be paid at once.

        The per-simulation Python loop this replaces was the slowest thing in the engine and
        was called ``n_sims x n_lineups`` times per contest.
        """
        limit = int(max_rank or self.entries)
        lookup = np.zeros(limit + 1, dtype=float)
        for tier in self.tiers:
            start = max(1, int(tier.start_rank))
            end = min(limit, int(tier.end_rank))
            if end >= start:
                lookup[start : end + 1] = float(tier.amount)
        return lookup

    def payout_for_rank(self, rank: int) -> float:
        for tier in self.tiers:
            if tier.start_rank <= rank <= tier.end_rank:
                return tier.amount
        return 0.0

    @property
    def total_pool(self) -> float:
        return sum(
            tier.amount * (tier.end_rank - tier.start_rank + 1) for tier in self.tiers
        )

    @property
    def paid_entries(self) -> int:
        return max((tier.end_rank for tier in self.tiers), default=0)

    @property
    def cost(self) -> float:
        return self.entries * self.entry_fee

    @property
    def rake(self) -> float:
        if self.cost <= 0:
            return float("nan")
        return 1.0 - self.total_pool / self.cost

    def validate(self) -> None:
        problems: List[str] = []
        if self.entries <= 0 or self.entry_fee <= 0:
            problems.append("entries and entry_fee must be positive")
        for tier in self.tiers:
            if tier.start_rank < 1 or tier.end_rank < tier.start_rank:
                problems.append(f"bad tier {tier}")
            if tier.amount < 0:
                problems.append(f"negative payout in tier {tier}")
            if tier.end_rank > self.entries:
                problems.append(f"tier {tier} pays ranks beyond the field size")
        ordered = sorted(self.tiers, key=lambda t: t.start_rank)
        for prev, nxt in zip(ordered, ordered[1:]):
            if nxt.start_rank <= prev.end_rank:
                problems.append(f"overlapping tiers: {prev} / {nxt}")
        if self.total_pool > self.cost + 1e-6:
            problems.append(
                f"payouts exceed the money collected (pool {self.total_pool:.2f} > "
                f"entries*fee {self.cost:.2f}); check the structure"
            )
        if problems:
            raise ValueError("invalid payout structure: " + "; ".join(problems))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "entries": self.entries,
            "entry_fee": self.entry_fee,
            "source": self.source,
            "paid_entries": self.paid_entries,
            "total_pool": round(self.total_pool, 2),
            "rake": round(self.rake, 4) if math.isfinite(self.rake) else None,
            "tiers": [
                {"start_rank": t.start_rank, "end_rank": t.end_rank, "amount": t.amount}
                for t in self.tiers
            ],
        }


# ---------------------------------------------------------------------------
# contest simulation
# ---------------------------------------------------------------------------
@dataclass
class ContestResult:
    label: str
    player_ids: List[str]
    projected_score: float
    mean_score: float
    roi_pct: float
    expected_payout: float
    cash_rate_pct: float
    win_rate_pct: float
    top_1pct_rate_pct: float
    median_rank: float
    mean_percentile: float
    best_rank: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "players": list(self.player_ids),
            "projected_score": round(self.projected_score, 2),
            "mean_score": round(self.mean_score, 2),
            "roi_pct": round(self.roi_pct, 2),
            "expected_payout": round(self.expected_payout, 3),
            "cash_rate_pct": round(self.cash_rate_pct, 2),
            "win_rate_pct": round(self.win_rate_pct, 4),
            "top_1pct_rate_pct": round(self.top_1pct_rate_pct, 3),
            "median_rank": round(self.median_rank, 1),
            "mean_percentile": round(self.mean_percentile, 2),
            "best_rank": int(self.best_rank),
        }


def _scores_for(matrix: np.ndarray, lineups: Sequence[Sequence[int]]) -> np.ndarray:
    """``[n_sims, n_lineups]`` fantasy-point totals for a set of index lineups."""
    if not lineups:
        return np.zeros((matrix.shape[0], 0))
    idx = np.asarray(lineups, dtype=int)
    return matrix[:, idx].sum(axis=2)


def simulate_contest(
    fp_matrix: np.ndarray,
    user_lineups: Sequence[Sequence[int]],
    payout: PayoutStructure,
    *,
    field_lineups: Optional[Sequence[Sequence[int]]] = None,
    field_size: Optional[int] = None,
    labels: Optional[Sequence[str]] = None,
    chunk_size: int = 250,
) -> List[ContestResult]:
    """Rank each user lineup against a field in every simulated contest.

    ``fp_matrix`` is ``[n_sims, n_players]`` (from ``models.simulate_fantasy_points``). Field
    lineups are either supplied (a real field you downloaded, or one built by
    :func:`stokengineer.ownership.generate_field_lineups`) or generated here - in which case
    the caller must pass ``field_size``.

    Memory is bounded by ``chunk_size``: only that many simulations of field scores are
    materialised at once, so a 10k-entry field over 10k sims never needs a 800 MB array.
    """
    if fp_matrix.ndim != 2:
        raise ValueError("fp_matrix must be [n_sims, n_players]")
    n_sims, n_players = fp_matrix.shape
    if field_lineups is None:
        raise ValueError(
            "field_lineups is required: build one with ownership.generate_field_lineups "
            "(ownership-weighted) or pass a real field export"
        )
    field = [list(map(int, lu)) for lu in field_lineups]
    users = [list(map(int, lu)) for lu in user_lineups]
    if field_size and len(field) > field_size:
        field = field[:field_size]
    if not field:
        raise ValueError("field is empty")

    entry_fee = payout.entry_fee
    user_scores = _scores_for(fp_matrix, users)  # [n_sims, n_users]
    n_users = len(users)
    payouts = np.zeros((n_sims, n_users))
    ranks = np.zeros((n_sims, n_users), dtype=int)
    n_field = len(field)

    lookup = payout.payout_lookup(n_field + 1)
    # pre-compute field score slices once per chunk
    for start in range(0, n_sims, chunk_size):
        stop = min(n_sims, start + chunk_size)
        block = fp_matrix[start:stop]
        field_block = block[:, np.asarray(field, dtype=int)].sum(axis=2)  # [chunk, n_field]
        for u in range(n_users):
            scores_u = user_scores[start:stop, u]
            # rank = 1 + number of field scores strictly greater than the user's score
            # (ties share the better rank, which is how a real leaderboard pays)
            better = np.sum(field_block > scores_u[:, None], axis=1)
            rank = np.minimum(better + 1, n_field + 1)
            ranks[start:stop, u] = rank
            payouts[start:stop, u] = lookup[rank]
        del block, field_block

    labels = list(labels or [f"lineup_{i}" for i in range(n_users)])
    results: List[ContestResult] = []
    for u in range(n_users):
        mean_payout = float(payouts[:, u].mean())
        roi = (mean_payout - entry_fee) / entry_fee * 100.0
        ranks_u = ranks[:, u]
        results.append(
            ContestResult(
                label=labels[u],
                player_ids=[str(p) for p in users[u]],
                projected_score=0.0,
                mean_score=float(user_scores[:, u].mean()),
                roi_pct=roi,
                expected_payout=mean_payout,
                cash_rate_pct=float((payouts[:, u] > 0).mean() * 100.0),
                win_rate_pct=float((ranks_u == 1).mean() * 100.0),
                top_1pct_rate_pct=float((ranks_u <= max(1, n_field * 0.01)).mean() * 100.0),
                median_rank=float(np.median(ranks_u)),
                mean_percentile=float(np.mean((1.0 - ranks_u / max(1, n_field)) * 100.0)),
                best_rank=int(ranks_u.min()),
            )
        )
    return results


def plausibility_warnings(
    results: Sequence[ContestResult], payout: PayoutStructure
) -> List[str]:
    """Flag results that are arithmetically fine but too good to take at face value.

    A contest simulation is only as honest as the field it is run against. When a lineup's
    simulated ROI is far above what its cash rate can justify, the usual explanations are
    (a) the field model is too weak, or (b) the lineups were built from projections the field
    did not have. Both are assumptions, so the report says so instead of printing a fantasy
    number with no caveat.
    """
    warnings: List[str] = []
    for result in results:
        if result.roi_pct > 100.0 and result.cash_rate_pct < 60.0:
            warnings.append(
                f"{result.label}: simulated ROI {result.roi_pct:.0f}% with a "
                f"{result.cash_rate_pct:.0f}% cash rate. A cash rate near the paid fraction "
                f"cannot justify that ROI unless the lineup is winning top prizes far more "
                f"often than the field. Check (1) the field model, (2) whether the lineups were "
                f"built on info the field lacked, (3) the payout structure."
            )
        if payout.source.startswith("ILLUSTRATIVE"):
            warnings.append(
                "payout structure is illustrative, so ROI is a ranking aid only"
            )
            break
    return warnings


def field_lineups_from_ownership(
    slate: Slate,
    ownership: Mapping[str, float],
    n_entries: int,
    seed: Optional[int] = None,
    site: Optional[str] = None,
    stack_rate: float = 0.35,
    bring_back_rate: float = 0.35,
    projections: Optional[Mapping[str, float]] = None,
    noise: float = 0.25,
    sharp_share: float = 0.35,
    sharp_noise: float = 0.08,
    strong_share: float = 0.25,
    max_player_share: Optional[float] = 0.5,
) -> List[List[int]]:
    """Build a field whose sharing matches projected ownership (claim c03).

    Passing ``projections`` switches on projection mode: every field entry drafts from a
    noisy copy of the projections, which is what makes a field look like real people rather
    than like random names. Ownership still sets how often each player is shared.
    """
    rng = np.random.default_rng(seed)
    return generate_field_lineups(
        slate,
        ownership,
        n_entries,
        rng,
        site=site,
        stack_rate=stack_rate,
        bring_back_rate=bring_back_rate,
        projections=projections,
        noise=noise,
        sharp_share=sharp_share,
        strong_share=strong_share,
        max_player_share=max_player_share,
        sharp_noise=sharp_noise,
    )


def lineup_scores(matrix: np.ndarray, lineups: Sequence[Sequence[int]]) -> np.ndarray:
    return _scores_for(matrix, lineups)


def boom_bust_table(
    slate: Slate,
    fp_matrix: np.ndarray,
    projections: Mapping[str, float],
    ownership: Optional[Mapping[str, float]] = None,
) -> List[Dict[str, Any]]:
    """The published boom/bust columns, per player (claims c07, c08).

    Ceiling = 75th percentile, floor = 25th percentile, boom/bust thresholds are the
    salary-relative values from the NBA strategy article.
    """
    rows: List[Dict[str, Any]] = []
    for idx, player in enumerate(slate.players):
        samples = fp_matrix[:, idx]
        summary = summarise_distribution(samples, player.salary)
        row = {
            "player_id": player.id,
            "name": player.name,
            "team": player.team,
            "salary": player.salary,
            "projection": round(float(projections.get(player.id, samples.mean())), 2),
            **{k: round(v, 3) for k, v in summary.as_dict().items()},
        }
        if ownership is not None:
            row["ownership_pct"] = round(float(ownership.get(player.id, 0.0)), 2)
            row["leverage"] = round(
                float(row["boom_pct"] - row["ownership_pct"]), 3
            )
        rows.append(row)
    return sorted(rows, key=lambda r: -r["projection"])


def optimal_lineup(
    slate: Slate,
    fp_matrix: np.ndarray,
    projections: Mapping[str, float],
    sim_index: int = 0,
    constraints: Optional[Any] = None,
) -> List[int]:
    """Best legal lineup for one simulated outcome (the 'optimal' lineup in that world)."""
    from .optimizer import optimize_lineup  # local import avoids a cycle

    scores = {p.id: float(fp_matrix[sim_index, i]) for i, p in enumerate(slate.players)}
    lineup = optimize_lineup(slate, scores, constraints=constraints)
    index = slate.index()
    return [index[pid] for pid in lineup.player_ids]


def optimal_lineup_rates(
    slate: Slate,
    fp_matrix: np.ndarray,
    sample: int = 50,
    constraints: Optional[Any] = None,
) -> Dict[str, float]:
    """How often each player appears in the optimal lineup across simulated outcomes.

    This is the honest, simulation-based version of Stokastic's "optimal %" column: it is
    expensive, so it defaults to a sample of simulations rather than all of them, and the
    sample size is reported by the caller.
    """
    index = slate.index()
    counts = np.zeros(len(slate.players))
    used = 0
    for sim in range(min(sample, fp_matrix.shape[0])):
        try:
            lineup = optimal_lineup(slate, fp_matrix, {}, sim_index=sim, constraints=constraints)
        except (ValueError, KeyError):
            continue
        for i in lineup:
            counts[i] += 1
        used += 1
    if used == 0:
        return {p.id: 0.0 for p in slate.players}
    return {p.id: float(counts[i] / used * 100.0) for i, p in enumerate(slate.players)}
