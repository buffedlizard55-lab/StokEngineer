"""Ownership (field) modelling.

What Stokastic publishes about ownership (claim c21-era quote, source ``sk_mlb_ownership``):
projected ownership is a forecast of the percentage of tournament entries that will roster a
player - i.e. a forecast of *other people's behaviour*. The undisclosed part is how they get
there, and claim ``c24`` records that the coefficients are not public.

How this module does it, without pretending to have their model:

1. Players get a **weight** from a linear score over interpretable features (projection,
   value over salary baseline, salary, team implied total, positional scarcity, news bump).
2. A field of lineups is *simulated* by sampling from those weights subject to the real
   roster rules (via :mod:`stokengineer.optimizer` feasibility), then
3. **Projected ownership is the empirical frequency** of each player in that simulated field.

Step 3 is what makes the numbers internally consistent: ownership sums to
``roster_size * 100`` across the pool automatically, and a player who cannot fit in a legal
lineup cannot be projected at 40%. The feature weights are documented priors until
:meth:`OwnershipModel.calibrate` is run against real ownership (a free source for that is the
user's own contest-results export, which contains actual ownership).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .models import PlayerProjection, Slate
from .optimizer import LineupConstraints, fast_lineup
from .rules import PITCHER_POSITIONS, SiteRules, get_site_rules, pts_per_dollar, value


@dataclass(frozen=True)
class OwnershipWeights:
    """Prior feature weights (log-linear). Replaced by :meth:`OwnershipModel.calibrate`.

    Signs are the interesting part and they are all defensible from public writing: high
    projection and high value draw ownership, expensive players draw less ownership per
    point of value, and a team with a big implied total drags its skill players up
    (``sk_mlb_ownership``: chalk follows Vegas over/unders and implied totals).
    """

    bias: float = -2.0
    projection: float = 0.12
    value: float = 0.30
    salary: float = -0.00012
    implied_total: float = 0.06
    position_scarcity: float = 0.05
    news_boost: float = 0.35

    def vector(self) -> np.ndarray:
        return np.array(
            [
                self.bias,
                self.projection,
                self.value,
                self.salary,
                self.implied_total,
                self.position_scarcity,
                self.news_boost,
            ],
            dtype=float,
        )


FEATURE_NAMES = (
    "bias",
    "projection",
    "value",
    "salary",
    "implied_total",
    "position_scarcity",
    "news_boost",
)


@dataclass
class OwnershipModel:
    weights: OwnershipWeights = field(default_factory=OwnershipWeights)
    fitted_on: str = "prior (uncalibrated)"

    # -- feature construction -------------------------------------------------
    def features(
        self,
        slate: Slate,
        projections: Mapping[str, float],
        news_boost: Optional[Mapping[str, float]] = None,
    ) -> Tuple[np.ndarray, List[str]]:
        """Design matrix for the field weights, one row per player."""
        rows: List[List[float]] = []
        ids: List[str] = []
        implied = _implied_totals_from_slate(slate)

        # positional scarcity: 1 / (number of players sharing the position group)
        position_counts: Dict[str, int] = {}
        for player in slate.players:
            key = _primary_position(player)
            position_counts[key] = position_counts.get(key, 0) + 1

        for player in slate.players:
            proj = float(projections.get(player.id, 0.0))
            salary = float(player.salary or 0.0)
            val = float(value(proj, salary)) if salary else 0.0
            pos_key = _primary_position(player)
            scarcity = 1.0 / max(1, position_counts.get(pos_key, 1))
            boost = float((news_boost or {}).get(player.id, 0.0))
            rows.append(
                [
                    1.0,
                    proj,
                    val,
                    salary,
                    implied.get(player.team, 0.0),
                    scarcity,
                    boost,
                ]
            )
            ids.append(player.id)
        return np.array(rows, dtype=float), ids

    def _log_weights(self, features: np.ndarray) -> np.ndarray:
        return features @ self.weights.vector()

    def raw_weights(
        self,
        slate: Slate,
        projections: Mapping[str, float],
        news_boost: Optional[Mapping[str, float]] = None,
    ) -> Dict[str, float]:
        features, ids = self.features(slate, projections, news_boost)
        logits = self._log_weights(features)
        logits = logits - logits.max()
        w = np.exp(logits)
        return {pid: float(v) for pid, v in zip(ids, w)}

    # -- calibration ----------------------------------------------------------
    def calibrate(
        self,
        features: np.ndarray,
        actual_ownership: np.ndarray,
        iterations: int = 4000,
        step: float = 0.05,
        l2: float = 1e-4,
    ) -> "OwnershipModel":
        """Fit the weights to observed ownership with gradient descent on log-ownership.

        Ownership is modelled as ``softmax(features @ theta)`` scaled to the pool, so the
        gradient is the familiar ``X.T @ (p_hat - p_actual)``. Coordinate scale differs by
        feature, so the step is divided by the feature's standard deviation - plain, fast,
        and inspectable, with no dependency on scikit-learn.
        """
        x = np.asarray(features, dtype=float)
        y = np.asarray(actual_ownership, dtype=float)
        if x.ndim != 2 or y.shape[0] != x.shape[0]:
            raise ValueError("features must be [n, k] and actual_ownership [n]")
        if np.any(y < 0):
            raise ValueError("ownership cannot be negative")

        target = np.clip(y, 1e-9, None)
        scale = np.where(x.std(axis=0) > 0, x.std(axis=0), 1.0)
        theta = self.weights.vector().copy()

        for _ in range(iterations):
            logits = x @ theta
            logits = logits - logits.max()
            p_hat = np.exp(logits)
            p_hat = p_hat / p_hat.sum()
            p_actual = target / target.sum()
            grad = x.T @ (p_hat - p_actual) / len(x)
            grad = grad + l2 * theta
            theta = theta - step * grad / scale

        names = FEATURE_NAMES
        fitted = OwnershipWeights(**{name: float(v) for name, v in zip(names, theta)})
        return OwnershipModel(weights=fitted, fitted_on=f"{len(x)} player-ownership pairs")


def _primary_position(player: PlayerProjection) -> str:
    return player.positions[0] if player.positions else "?"


def _implied_totals_from_slate(slate: Slate) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for game in slate.games:
        home = str(game.get("home_team", ""))
        away = str(game.get("away_team", ""))
        if "home_implied_total" in game:
            totals[home] = float(game["home_implied_total"])
        if "away_implied_total" in game:
            totals[away] = float(game["away_implied_total"])
    return totals


# ---------------------------------------------------------------------------
# field simulation
# ---------------------------------------------------------------------------
@dataclass
class FieldLineup:
    player_ids: List[str]
    weight: float = 0.0


def generate_field_lineups(
    slate: Slate,
    weights: Mapping[str, float],
    n_entries: int,
    rng: np.random.Generator,
    site: Optional[str] = None,
    stack_rate: float = 0.0,
    bring_back_rate: float = 0.0,
    projections: Optional[Mapping[str, float]] = None,
    noise: float = 0.25,
    sharp_share: float = 0.35,
    sharp_noise: float = 0.08,
    jitter_multiplier: float = 0.02,
    max_attempts_per_entry: int = 40,
    max_player_share: Optional[float] = 0.5,
    strategy_weights: Optional[Mapping[str, float]] = None,
    strong_share: float = 0.0,
    strong_node_budget: int = 1500,
) -> List[List[int]]:
    """Sample a legal field of lineups.

    Two modes, and the difference matters for how believable a simulated ROI is:

    * **projection mode** (``projections`` supplied) - each entry draws a *noisy* copy of the
      projections and drafts a legal, near-optimal lineup under that view (the same search the
      optimizer uses, in fast first-fit mode).
      A share of entries (``sharp_share``) are treated as sharp players: they use a much smaller
      error (``sharp_noise``), which is what stops a simulated field from being a field of
      pushovers and therefore stops simulated ROI from being fictional. ``noise`` (0.25) and
      ``sharp_share`` (0.35) are documented priors, not measured values - they are the single
      biggest lever on the ROI a report shows, and every report names them.
    * **weights mode** (no projections) - players are drawn proportional to their ownership
      weight. This is the fallback, and it is the honest one to use when only ownership is
      known (a user-supplied ownership CSV, for example).

    Either way, salary cap, slot eligibility and any stack/bring-back requirement are enforced
    on the finished lineup, and entries that cannot be completed legally are dropped rather
    than quietly patched.
    """
    rules = get_site_rules(site or slate.site, slate.sport)
    strategy_weights = dict(
        strategy_weights or {"projection": 0.55, "value": 0.2, "contrarian": 0.15, "ceiling": 0.1}
    )
    total_weight = sum(strategy_weights.values())
    if total_weight <= 0:
        raise ValueError("strategy_weights must sum to a positive number")
    strategy_weights = {k: v / total_weight for k, v in strategy_weights.items()}
    ids = [p.id for p in slate.players]
    positions = [list(p.positions) for p in slate.players]
    salaries = np.array([float(p.salary) for p in slate.players])
    teams = [p.team for p in slate.players]
    opponents = [p.opponent for p in slate.players]
    n = len(ids)

    game_ids = [p.game_id or (p.team, p.opponent) for p in slate.players]
    raw = np.array([max(0.0, float(weights.get(pid, 0.0))) for pid in ids])
    probs = raw / raw.sum() if raw.sum() > 0 else np.ones(n) / n
    proj = np.array([float((projections or {}).get(pid, 0.0)) for pid in ids])
    use_projection_mode = projections is not None and proj.max() > 0

    groups: List[List[str]] = []
    for eligible, count in rules.slot_groups():
        groups.extend([list(eligible)] * count)

    def eligible_index(eligible: Sequence[str]) -> List[int]:
        return [i for i in range(n) if any(pos in eligible for pos in positions[i])]

    eligible_by_group = [eligible_index(eligible) for eligible in groups]

    def legal(indices: Sequence[int]) -> bool:
        """Full legality, not just salary: slots, salary cap and the multi-game rule.

        The stack / bring-back rewrites below swap players in and out, and a swap is exactly
        where a field generator quietly produces lineups a site would reject. Every rewritten
        lineup is re-checked here before it is allowed into the field.
        """
        if len(indices) != rules.roster_size:
            return False
        if float(salaries[list(indices)].sum()) > rules.salary_cap:
            return False
        if rules.assign_slots([positions[i] for i in indices]) is None:
            return False
        if rules.min_games > 1:
            games = {game_ids[i] for i in indices}
            if len(games) < rules.min_games:
                return False
        if rules.max_hitters_per_team:
            per_team: Dict[str, int] = {}
            for i in indices:
                if any(pos in PITCHER_POSITIONS for pos in positions[i]):
                    continue
                per_team[teams[i]] = per_team.get(teams[i], 0) + 1
            if any(count > rules.max_hitters_per_team for count in per_team.values()):
                return False
        return True

    def search_by_view(
        view: np.ndarray, attempt: int, node_budget: int = 0
    ) -> Optional[List[int]]:
        """A legal near-optimal lineup under ``view``, via the optimizer's fast search.

        A field of naive greedy lineups is a field of pushovers, and beating pushovers is not
        an edge. Real entrants mostly use an optimiser with imperfect projections, so the field
        is built the same way: a fast first-fit search (with a small random tilt so entries
        differ) under each entry's own noisy view.
        """
        view_map = {ids[i]: float(view[i]) for i in range(n)}
        lineup = fast_lineup(
            slate,
            view_map,
            site=site or slate.site,
            constraints=LineupConstraints(),
            seed=int(rng.integers(0, 2**31 - 1)),
            jitter=max(jitter_multiplier, 0.03),
            # Fast first-fit unless this entry is one of the `strong_share` that solve the
            # problem properly. A field made only of first-fit drafters is a field of pushovers,
            # and beating pushovers is not an edge; a field where nobody solves properly is the
            # opposite mistake and nearly as unrealistic. Both are documented priors.
            node_budget=node_budget,
        )
        if lineup is None:
            return None
        position_of = {pid: index for index, pid in enumerate(ids)}
        return [position_of[pid] for pid in lineup.player_ids]

    def greedy_by_view(view: np.ndarray) -> Optional[List[int]]:
        """Fill each slot group with the best available player under ``view``."""
        chosen: List[int] = []
        used: set[int] = set()
        for gi, eligible in enumerate(groups):
            candidates = [i for i in eligible_by_group[gi] if i not in used]
            if not candidates:
                return None
            remaining_groups = groups[gi + 1 :]
            best: Optional[int] = None
            for i in sorted(candidates, key=lambda x: -view[x]):
                salary_used = float(salaries[chosen].sum()) if chosen else 0.0
                if salary_used + float(salaries[i]) > rules.salary_cap:
                    continue
                # can the remaining slots still be afforded?
                min_remaining = 0.0
                blocked = used | {i}
                for later in remaining_groups:
                    options = [salaries[j] for j in eligible_index(later) if j not in blocked]
                    if not options:
                        min_remaining = float("inf")
                        break
                    min_remaining += float(min(options))
                if salary_used + float(salaries[i]) + min_remaining > rules.salary_cap:
                    continue
                best = i
                break
            if best is None:
                return None
            chosen.append(best)
            used.add(best)
        return chosen

    out: List[List[int]] = []
    appearances: np.ndarray = np.zeros(n, dtype=int)
    share_cap = (
        max(1, int(np.ceil(max_player_share * n_entries))) if max_player_share else None
    )
    for _entry in range(n_entries):
        for _attempt in range(max_attempts_per_entry):
            if use_projection_mode:
                sigma = sharp_noise if rng.random() < sharp_share else noise
                view = proj * (1.0 + rng.normal(0.0, sigma, size=n))
                # Real fields are not one strategy repeated N times. Simulating them as if they
                # were makes a lineup that differs from the crowd look far better than it is,
                # because a homogeneous field all fails together. These are the four strategies
                # every DFS field actually contains, with documented (uncalibrated) weights:
                #   projection-greedy, points-per-dollar, contrarian (low ownership), and a
                #   ceiling-chasing mix. `strategy_weights` is the knob to calibrate.
                strategy = rng.random()
                normalized_own = probs * n / max(probs.sum(), 1e-9)
                if strategy < strategy_weights["projection"]:
                    pass
                elif strategy < strategy_weights["projection"] + strategy_weights["value"]:
                    view = view / np.maximum(salaries, 1.0) * 1000.0
                elif (
                    strategy
                    < strategy_weights["projection"]
                    + strategy_weights["value"]
                    + strategy_weights["contrarian"]
                ):
                    view = view * (1.0 + 0.6 * (1.0 - normalized_own))
                else:
                    view = view * (1.0 + 0.4 * (1.0 - normalized_own)) * (
                        1.0 + rng.normal(0.0, 0.15, size=n)
                    )
                if share_cap is not None:
                    # a field where one lineup shape dominates is not a field, it is a queue of
                    # clones: cap how often any player can appear, the way real fields spread out
                    over_used = appearances >= share_cap
                    view = np.where(over_used, -np.inf, view)
                # ownership still tilts who people pick, but far less than in weights mode
                view = view * (0.75 + 0.25 * (probs * n / max(probs.sum(), 1e-9)))
                entry_budget = strong_node_budget if rng.random() < strong_share else 0
                chosen = search_by_view(view, _attempt, entry_budget)
            else:
                # ownership-weighted drawing, the honest path when only ownership is known
                chosen = _weighted_draw(rules, positions, salaries, probs, groups, rng)
            if chosen is None or not legal(chosen):
                continue
            if stack_rate > 0 and slate.sport == "nfl" and rng.random() < stack_rate:
                stacked = _apply_nfl_stack(
                    chosen, ids, {pid: i for i, pid in enumerate(ids)}, positions, teams,
                    opponents, probs, rng,
                )
                if stacked is None or not legal(stacked):
                    continue
                chosen = stacked
            if (
                bring_back_rate > 0
                and slate.sport == "nfl"
                and stack_rate > 0
                and rng.random() < bring_back_rate
            ):
                brought = _apply_bring_back(chosen, ids, positions, teams, opponents, probs, rng)
                if brought is None or not legal(brought):
                    continue
                chosen = brought
            out.append(chosen)
            for i in chosen:
                appearances[i] += 1
            break
    return out


def _weighted_draw(
    rules: SiteRules,
    positions: Sequence[Sequence[str]],
    salaries: np.ndarray,
    probs: np.ndarray,
    groups: Sequence[Sequence[str]],
    rng: np.random.Generator,
) -> Optional[List[int]]:
    """Ownership-weighted draw with a salary-aware preference once the cap gets tight."""
    chosen: List[int] = []
    salary_used = 0.0
    for slot_index, eligible in enumerate(groups):
        candidates = [
            i
            for i in range(len(positions))
            if i not in chosen and any(pos in eligible for pos in positions[i])
        ]
        if not candidates:
            return None
        cand_p = probs[candidates]
        if cand_p.sum() <= 0:
            cand_p = np.ones(len(candidates))
        cand_p = cand_p / cand_p.sum()
        slots_left = len(groups) - slot_index
        room = rules.salary_cap - salary_used
        need_avg = room / slots_left
        adjusted = cand_p * np.where(salaries[candidates] <= need_avg * 1.6, 1.0, 0.35)
        adjusted = adjusted / adjusted.sum()
        pick = int(rng.choice(candidates, p=adjusted))
        chosen.append(pick)
        salary_used += float(salaries[pick])
    return chosen


def _apply_nfl_stack(
    chosen: List[int],
    ids: Sequence[str],
    index: Mapping[str, int],
    positions: Sequence[Sequence[str]],
    teams: Sequence[str],
    opponents: Sequence[str],
    probs: np.ndarray,
    rng: np.random.Generator,
) -> Optional[List[int]]:
    """Force a QB plus a teammate pass catcher, keeping the lineup's size and positions."""
    qb_positions = [i for i in chosen if "QB" in positions[i]]
    if not qb_positions:
        return list(chosen)
    qb = qb_positions[0]
    team = teams[qb]
    teammates = [
        i
        for i, p in enumerate(positions)
        if teams[i] == team and any(x in p for x in ("WR", "TE")) and i not in chosen
    ]
    if not teammates:
        return None
    teammate_probs = probs[teammates] ** 0.5
    teammate_probs = teammate_probs / teammate_probs.sum()
    new_pick = int(rng.choice(teammates, p=teammate_probs))
    # replace a non-QB, non-DST slot player so the position structure stays legal
    replaceable = [i for i in chosen if "QB" not in positions[i] and "DST" not in positions[i]]
    if not replaceable:
        return None
    victim = int(rng.choice(replaceable))
    return [new_pick if i == victim else i for i in chosen]


def _apply_bring_back(
    chosen: List[int],
    ids: Sequence[str],
    positions: Sequence[Sequence[str]],
    teams: Sequence[str],
    opponents: Sequence[str],
    probs: np.ndarray,
    rng: np.random.Generator,
) -> Optional[List[int]]:
    qb = next((i for i in chosen if "QB" in positions[i]), None)
    if qb is None:
        return None
    opp = opponents[qb]
    candidates = [
        i
        for i, p in enumerate(positions)
        if teams[i] == opp and any(x in p for x in ("WR", "TE", "RB")) and i not in chosen
    ]
    if not candidates:
        return None
    cand_p = probs[candidates]
    cand_p = cand_p / cand_p.sum()
    new_pick = int(rng.choice(candidates, p=cand_p))
    replaceable = [
        i
        for i in chosen
        if i != qb and "DST" not in positions[i] and not any(x in positions[i] for x in ("RB",))
    ]
    if not replaceable:
        return None
    victim = int(rng.choice(replaceable))
    return [new_pick if i == victim else i for i in chosen]


# ---------------------------------------------------------------------------
# projected ownership
# ---------------------------------------------------------------------------
def projected_ownership(
    slate: Slate,
    weights: Mapping[str, float],
    n_entries: int = 4000,
    seed: Optional[int] = None,
    site: Optional[str] = None,
    stack_rate: float = 0.35,
    bring_back_rate: float = 0.35,
) -> Dict[str, float]:
    """Ownership % per player, measured from a simulated field.

    Returns percentages (0-100). By construction ``sum(values) ~= roster_size * 100`` because
    every simulated entry rosters exactly ``roster_size`` players.
    """
    rng = np.random.default_rng(seed)
    field_lineups = generate_field_lineups(
        slate,
        weights,
        n_entries,
        rng,
        site=site,
        stack_rate=stack_rate,
        bring_back_rate=bring_back_rate,
    )
    if not field_lineups:
        raise RuntimeError("field simulation produced no legal lineups - check the slate")
    counts = np.zeros(len(slate.players))
    for lineup in field_lineups:
        counts[lineup] += 1
    return {
        player.id: float(counts[i] / len(field_lineups) * 100.0)
        for i, player in enumerate(slate.players)
    }


def blend_ownership(
    model: Mapping[str, float], manual: Mapping[str, float], model_weight: float = 0.5
) -> Dict[str, float]:
    """Blend model ownership with a user's own numbers (Stokastic supports the same idea:
    'Upload a CSV with player name, projection and ownership', source ``sk_nfl_review``)."""
    if not 0.0 <= model_weight <= 1.0:
        raise ValueError("model_weight must be between 0 and 1")
    out: Dict[str, float] = {}
    for pid, value in model.items():
        other = manual.get(pid, value)
        out[pid] = model_weight * float(value) + (1 - model_weight) * float(other)
    return out


def leverage(projected_own_pct: float, field_own_pct: float) -> float:
    """Leverage = your exposure minus the field's ownership of that player.

    Positive leverage means you own more of a player than the field, which is only +EV when
    the projection is at least as good as the field thinks (see claim c12 context and
    LIMITATIONS.md for why leverage is not free money).
    """
    return float(projected_own_pct) - float(field_own_pct)
