"""Lineup optimizer.

Picking a DFS lineup is a combinatorial problem: one player per roster slot, position
eligibility, a salary cap, a multi-game rule and per-team limits, maximising an objective.
This module solves it two ways and is explicit about which one ran:

* **MILP** (``pulp`` + CBC, an open-source solver that depends on nothing paid) - exact, and
  the default whenever the solver is importable. The formulation collapses slots that accept
  the same positions into one integer constraint per group, so an MLB roster is a handful of
  constraints rather than ten.
* **DFS branch and bound** - used when no solver is installed and as a fallback if the solver
  reports infeasible. It is a genuine exact-with-budget search: legal by construction, pruned
  with an augmenting-path matching check for the remaining slots, and honest that its result
  is "a good legal lineup", not "a proven optimum" (the ``method`` field says which).

Objective modes mirror the published advice (claim c12): cash builds maximise the floor, GPP
builds maximise the ceiling, and ``sim_roi`` maximises a risk-adjusted surrogate (mean minus a
variance penalty) because true ROI is a contest-level quantity - the simulator in
:mod:`stokengineer.simulate` is what actually measures it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import numpy as np

from .models import Slate
from .rules import (
    GOALIE_POSITIONS,
    PITCHER_POSITIONS,
    SiteRules,
    get_site_rules,
    validate_lineup,
)

try:  # the solver is free and open source; the engine works without it
    import pulp

    _HAS_PULP = True
except Exception:  # pragma: no cover - exercised when pulp is absent
    pulp = None  # type: ignore[assignment]
    _HAS_PULP = False


OBJECTIVE_MODES = ("median", "ceiling", "floor", "sim_roi")

#: Penalty on per-player standard deviation in the ``sim_roi`` surrogate. Documented as a
#: modelling choice, not a measured constant: cash-style builds want a small penalty, GPP
#: builds near zero. It only ever shifts which players a *single* lineup prefers.
SIM_ROI_VARIANCE_PENALTY = 0.5


@dataclass
class StackSpec:
    """Require ``count`` players from one team, optionally including that team's QB.

    Stacking is not a rule on either site; it is a strategy the simulation rewards naturally
    ("Builds QB plus pass-catcher stacks and bring-backs naturally, because the sims reward
    correlation instead of needing a rule for it" - source ``sk_nfl_review``). This lets a
    user ask for the same shape deliberately.
    """

    count: int = 2
    include_qb: bool = True
    team: Optional[str] = None


@dataclass
class LineupConstraints:
    """Everything a user can ask the optimizer to respect."""

    locked: Set[str] = field(default_factory=set)
    excluded: Set[str] = field(default_factory=set)
    min_salary: float = 0.0
    max_players_per_team: Optional[int] = None
    min_players_per_team: Optional[int] = None
    team_limits: Dict[str, int] = field(default_factory=dict)
    stack: Optional[StackSpec] = None
    bring_back: int = 0
    previous_lineups: List[Sequence[str]] = field(default_factory=list)
    max_overlap: Optional[int] = None
    min_unique: int = 0
    exposure_cap: Dict[str, int] = field(default_factory=dict)
    objective: str = "median"
    #: node budget for the DFS fallback (per lineup); the MILP path ignores it
    node_budget: int = 300_000
    time_limit_seconds: float = 5.0


@dataclass
class OptimizedLineup:
    player_ids: List[str]
    #: slot id -> player id (never a column index: indices do not survive serialisation)
    slot_assignment: Dict[str, str]
    projected: float
    salary: float
    objective_value: float
    method: str
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "player_ids": list(self.player_ids),
            "slots": {slot: player_id for slot, player_id in self.slot_assignment.items()},
            "projected": round(self.projected, 3),
            "salary": round(self.salary, 2),
            "objective_value": round(self.objective_value, 3),
            "method": self.method,
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# objectives
# ---------------------------------------------------------------------------
def score_vector(
    slate: Slate,
    projections: Mapping[str, float],
    mode: str = "median",
    ceiling: Optional[Mapping[str, float]] = None,
    floor: Optional[Mapping[str, float]] = None,
    leverage_bonus: Optional[Mapping[str, float]] = None,
    leverage_weight: float = 0.0,
    stddev: Optional[Mapping[str, float]] = None,
) -> np.ndarray:
    """Per-player objective scores for the requested build mode.

    ``median``  - straight projection (DK's own advice: value = FP - 5 x salary/1000, claim c13).
    ``ceiling`` - upper percentile (GPP builds; claim c12).
    ``floor``   - lower percentile (cash builds; claim c12).
    ``sim_roi`` - mean minus a variance penalty: a documented surrogate for ROI, because ROI
                  itself is only measurable by simulating the contest.
    """
    if mode not in OBJECTIVE_MODES:
        raise ValueError(f"mode must be one of {OBJECTIVE_MODES}, got {mode!r}")
    base = np.array([float(projections.get(p.id, 0.0)) for p in slate.players])
    if mode == "ceiling":
        if ceiling is None:
            raise ValueError("ceiling projections required for mode='ceiling'")
        base = np.array(
            [float(ceiling.get(p.id, projections.get(p.id, 0.0))) for p in slate.players]
        )
    elif mode == "floor":
        if floor is None:
            raise ValueError("floor projections required for mode='floor'")
        base = np.array(
            [float(floor.get(p.id, projections.get(p.id, 0.0))) for p in slate.players]
        )
    elif mode == "sim_roi":
        if stddev is None:
            return base
        base = base - SIM_ROI_VARIANCE_PENALTY * np.array(
            [float(stddev.get(p.id, 0.0)) for p in slate.players]
        )
    if mode != "median" and leverage_bonus and leverage_weight:
        base = base + leverage_weight * np.array(
            [float(leverage_bonus.get(p.id, 0.0)) for p in slate.players]
        )
    return base


def score_vector_from_matrix(
    slate: Slate, matrix: np.ndarray, mode: str = "median"
) -> np.ndarray:
    """Objective scores straight from the simulated fantasy-point matrix.

    Deterministic, and the only place percentiles come from: ceiling is the 75th percentile
    and floor the 25th (claim c05, matching the published boom/bust definitions).
    """
    if matrix.ndim != 2 or matrix.shape[1] != len(slate.players):
        raise ValueError(
            f"matrix must be (n_sims, {len(slate.players)}), got {matrix.shape}"
        )
    if mode == "median":
        return matrix.mean(axis=0)
    if mode == "ceiling":
        return np.percentile(matrix, 75, axis=0)
    if mode == "floor":
        return np.percentile(matrix, 25, axis=0)
    if mode == "sim_roi":
        return matrix.mean(axis=0) - SIM_ROI_VARIANCE_PENALTY * matrix.std(axis=0)
    raise ValueError(f"mode must be one of {OBJECTIVE_MODES}, got {mode!r}")


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------
def _lineup_records(slate: Slate, indices: Sequence[int]) -> List[Dict[str, Any]]:
    return [slate.players[i].as_validation_record() for i in indices]


def _team_counts(slate: Slate, indices: Sequence[int]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for i in indices:
        team = slate.players[i].team
        counts[team] = counts.get(team, 0) + 1
    return counts


def required_positions_present(slate: Slate, rules: SiteRules, constraints: LineupConstraints) -> List[str]:
    """Reasons the slate can never satisfy the constraints - checked before solving.

    Returning these instead of "no lineup found" is the difference between a solver bug and a
    user typo, and the CLI prints them verbatim.
    """
    problems: List[str] = []
    available = [p for p in slate.players if p.id not in constraints.excluded]
    if len(available) < rules.roster_size:
        problems.append(
            f"only {len(available)} available players, the roster needs {rules.roster_size}"
        )
    for eligible, count in rules.slot_groups():
        n_eligible = sum(1 for p in available if any(pos in eligible for pos in p.positions))
        if n_eligible < count:
            problems.append(f"slate has {n_eligible} players eligible for {eligible}, need {count}")
    if len(constraints.locked) > rules.roster_size:
        problems.append("more locked players than roster spots")
    known_ids = {p.id for p in slate.players}
    unknown_locked = sorted(constraints.locked - known_ids)
    if unknown_locked:
        problems.append(f"locked players not on the slate: {unknown_locked}")
    if constraints.stack is not None and constraints.stack.team:
        team_players = [p for p in available if p.team == constraints.stack.team]
        if len(team_players) < constraints.stack.count:
            problems.append(
                f"team {constraints.stack.team} has {len(team_players)} available players, "
                f"the stack needs {constraints.stack.count}"
            )
    return problems


# ---------------------------------------------------------------------------
# MILP
# ---------------------------------------------------------------------------
def _solve_milp(
    slate: Slate,
    rules: SiteRules,
    scores: np.ndarray,
    projections: Mapping[str, float],
    constraints: LineupConstraints,
) -> Optional[OptimizedLineup]:
    """Exact solve with CBC (pulp), using explicit slot-assignment variables.

    The formulation needs ``z[group, player]`` assignment variables, not just ``x[player]``:

        maximise   sum_p score_p * x_p
        s.t.       sum_{p eligible for g} z[g, p] == count_g     for every slot group g
                   sum_g z[g, p]                 == x_p          for every player p
                   sum_p salary_p * x_p          <= cap
                   plus game / team / stack / overlap constraints on x

    Summing a single ``x_p`` over a group's eligible players *looks* equivalent and is not: a
    1-player FLEX slot over the same pool as the 2 RB + 3 WR slots makes the model claim
    "exactly three RBs and three WRs and one flex player" cannot coexist, and CBC correctly
    reports the whole problem infeasible. Slot groups with identical eligibility are merged
    (``rules.slot_groups``), so an MLB roster is a handful of integer constraints.
    """
    if not _HAS_PULP:
        return None
    players = slate.players
    n = len(players)
    groups = rules.slot_groups()
    eligible_by_group = {
        eligible: [
            i for i, p in enumerate(players) if any(pos in eligible for pos in p.positions)
        ]
        for eligible, _count in groups
    }
    blocked = [
        i
        for i, player in enumerate(players)
        if player.id in constraints.excluded or constraints.exposure_cap.get(player.id, 1) <= 0
    ]

    prob = pulp.LpProblem("dfs_lineup", pulp.LpMaximize)
    x = [
        pulp.LpVariable(f"x_{i}", lowBound=0, upBound=0 if i in blocked else 1, cat="Binary")
        for i in range(n)
    ]
    z: Dict[Tuple[int, int], Any] = {}
    for gi, (eligible, _count) in enumerate(groups):
        for i in eligible_by_group[eligible]:
            if i in blocked:
                continue
            z[(gi, i)] = pulp.LpVariable(f"z_{gi}_{i}", cat="Binary")

    prob += pulp.lpSum(float(scores[i]) * x[i] for i in range(n))

    for gi, (eligible, count) in enumerate(groups):
        members = [var for (g, _i), var in z.items() if g == gi]
        if len(members) < count:
            return None  # the slate cannot fill this slot group at all
        prob += pulp.lpSum(members) == count, f"slots_{gi}"
    for i in range(n):
        assigned = pulp.lpSum(var for (_g, j), var in z.items() if j == i)
        prob += assigned == x[i], f"assign_{i}"

    prob += pulp.lpSum(players[i].salary * x[i] for i in range(n)) <= rules.salary_cap
    if constraints.min_salary > 0:
        prob += pulp.lpSum(players[i].salary * x[i] for i in range(n)) >= constraints.min_salary

    for i, player in enumerate(players):
        if player.id in constraints.locked:
            prob += x[i] == 1

    by_id = {p.id: i for i, p in enumerate(players)}
    by_team: Dict[str, List[int]] = {}
    for i, player in enumerate(players):
        by_team.setdefault(player.team, []).append(i)

    if constraints.max_players_per_team is not None:
        for _team, idxs in by_team.items():
            prob += pulp.lpSum(x[i] for i in idxs) <= constraints.max_players_per_team
    for team, limit in constraints.team_limits.items():
        prob += pulp.lpSum(x[i] for i in by_team.get(team, [])) <= limit
    if constraints.min_players_per_team is not None:
        flags = []
        for team, idxs in by_team.items():
            y = pulp.LpVariable(f"team_min_{team}", cat="Binary")
            prob += pulp.lpSum(x[i] for i in idxs) >= constraints.min_players_per_team * y
            flags.append(y)
        if flags:
            prob += pulp.lpSum(flags) >= 1

    stack = constraints.stack
    stack_flags: Dict[str, Any] = {}
    if stack is not None:
        for team, idxs in by_team.items():
            if stack.team and team != stack.team:
                continue
            if stack.include_qb and not any("QB" in players[i].positions for i in idxs):
                continue
            y = pulp.LpVariable(f"stack_{team}", cat="Binary")
            prob += pulp.lpSum(x[i] for i in idxs) >= stack.count * y
            if stack.include_qb:
                qb_idx = [i for i in idxs if "QB" in players[i].positions]
                prob += pulp.lpSum(x[i] for i in qb_idx) >= y
            stack_flags[team] = y
        if not stack_flags:
            return None
        prob += pulp.lpSum(stack_flags.values()) >= 1

    if constraints.bring_back:
        if stack is None:
            return None  # bring-back is defined relative to a stack; refuse to guess
        for team, y in stack_flags.items():
            opponents = {players[i].opponent for i in by_team.get(team, []) if players[i].opponent}
            for opponent in opponents:
                prob += (
                    pulp.lpSum(x[i] for i in by_team.get(opponent, []))
                    >= constraints.bring_back * y
                )

    for prev in constraints.previous_lineups:
        prev_idx = [by_id[pid] for pid in prev if pid in by_id]
        if not prev_idx:
            continue
        if constraints.max_overlap is not None:
            prob += pulp.lpSum(x[i] for i in prev_idx) <= constraints.max_overlap
        if constraints.min_unique:
            # "different by at least k" is the same as "overlap at most n - k"
            prob += pulp.lpSum(x[i] for i in prev_idx) <= len(prev_idx) - constraints.min_unique

    if rules.min_games > 1:
        game_ids: Dict[Any, List[int]] = {}
        for i, player in enumerate(players):
            key = player.game_id or (player.team, player.opponent)
            game_ids.setdefault(key, []).append(i)
        flags = []
        for gi, idxs in enumerate(game_ids.values()):
            b = pulp.LpVariable(f"game_{gi}", cat="Binary")
            prob += pulp.lpSum(x[i] for i in idxs) <= rules.roster_size * b
            flags.append(b)
        if flags:
            prob += pulp.lpSum(flags) >= rules.min_games

    if rules.min_skater_teams:
        flags = []
        for ti, (team, idxs) in enumerate(by_team.items()):
            skaters = [
                i for i in idxs if not any(p in GOALIE_POSITIONS for p in players[i].positions)
            ]
            b = pulp.LpVariable(f"skater_team_{ti}", cat="Binary")
            prob += pulp.lpSum(x[i] for i in skaters) <= rules.roster_size * b
            flags.append(b)
        if flags:
            prob += pulp.lpSum(flags) >= rules.min_skater_teams

    if rules.max_hitters_per_team:
        for _ti, (team, idxs) in enumerate(by_team.items()):
            hitters = [
                i for i in idxs if not any(p in PITCHER_POSITIONS for p in players[i].positions)
            ]
            prob += pulp.lpSum(x[i] for i in hitters) <= rules.max_hitters_per_team

    if required_positions_present(slate, rules, constraints):
        return None

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=constraints.time_limit_seconds)
    status = prob.solve(solver)
    if pulp.LpStatus[status] != "Optimal":
        return None

    chosen = [i for i in range(n) if x[i].value() and x[i].value() > 0.5]
    if len(chosen) != rules.roster_size:
        return None
    return _package_lineup(slate, rules, scores, projections, chosen, "milp", [])


# ---------------------------------------------------------------------------
# DFS branch and bound
# ---------------------------------------------------------------------------
class _BudgetedOut(Exception):
    """Raised when the DFS node budget or time limit is hit."""


class _Search:
    """Slot-by-slot depth-first search with matching-based pruning.

    Slots are visited most-constrained-first. Two prunes keep it tractable on real slates:

    * **salary room** - the cheapest possible completion must still fit under the cap;
    * **slot feasibility** - an augmenting-path matching (the same exact test the validator
      uses) must still be able to seat every remaining slot, which is what the earlier greedy
      fallback lacked and why it could paint itself into a corner.
    """

    def __init__(
        self,
        slate: Slate,
        rules: SiteRules,
        scores: np.ndarray,
        constraints: LineupConstraints,
        rng: np.random.Generator,
        jitter: float,
    ) -> None:
        self.slate = slate
        self.rules = rules
        self.scores = scores
        self.constraints = constraints
        self.rng = rng
        self.jitter = jitter
        self.players = slate.players
        self.n = len(self.players)
        self.salaries = np.array([float(p.salary) for p in self.players])
        self.teams = [p.team for p in self.players]
        self.opponents = [p.opponent for p in self.players]
        self.positions = [list(p.positions) for p in self.players]
        self.game_keys = [p.game_id or (p.team, p.opponent) for p in self.players]
        self.is_pitcher = [
            any(pos in PITCHER_POSITIONS for pos in self.positions[i]) for i in range(self.n)
        ]
        self.is_goalie = [
            any(pos in GOALIE_POSITIONS for pos in self.positions[i]) for i in range(self.n)
        ]
        self.locked_idx = [i for i, p in enumerate(self.players) if p.id in constraints.locked]
        self.blocked = {
            i
            for i, p in enumerate(self.players)
            if p.id in constraints.excluded or constraints.exposure_cap.get(p.id, 1) <= 0
        }
        # expand the slot groups into individual slots and visit scarce ones first
        slots: List[Tuple[str, ...]] = []
        for eligible, count in rules.slot_groups():
            slots.extend([eligible] * count)
        slots = sorted(slots, key=lambda e: (self._eligible_count(e), e))
        self.slots, locked_assignment = self._reserve_locked_slots(slots)
        self._candidates_by_slot = [self._candidates(e) for e in self.slots]
        self.sorted_candidates = [
            np.array(sorted(self._candidates_by_slot[j], key=lambda i: -float(scores[i])), dtype=int)
            for j in range(len(self.slots))
        ]
        # the VALUES are stale slot indices from the shrinking list; what matters here is
        # which players are seated, which is the KEYS
        self.chosen: List[int] = list(locked_assignment.keys())
        self.used: Set[int] = set(self.chosen)
        self.first_only = False
        self.nodes = 0
        self.deadline = time.monotonic() + constraints.time_limit_seconds
        self.best: Optional[List[int]] = None
        self.best_value = -np.inf
        self.max_players_per_team = constraints.max_players_per_team
        self.explicit_team_limits = dict(constraints.team_limits)

    # -- helpers ---------------------------------------------------------
    def _reserve_locked_slots(
        self, slots: List[Tuple[str, ...]]
    ) -> Tuple[List[Tuple[str, ...]], Dict[int, int]]:
        """Seat every locked player in a real slot and drop that slot from the search.

        A locked player is not "the first player in the list" - they occupy a specific slot,
        and which one they occupy has to stay legal for everyone else. A small backtracking
        search finds that seating; if none exists the constraints are simply impossible, and
        saying so is better than returning a lineup the validator rejects.
        """
        remaining = list(slots)
        assignment: Dict[int, int] = {}
        locked = sorted(self.locked_idx)
        if not locked:
            return remaining, assignment

        def place(position_in_locked: int) -> bool:
            if position_in_locked == len(locked):
                return True
            player = locked[position_in_locked]
            for slot_index, eligible in enumerate(remaining):
                if not any(pos in eligible for pos in self.positions[player]):
                    continue
                taken = remaining.pop(slot_index)
                assignment[player] = slot_index
                if place(position_in_locked + 1):
                    return True
                assignment.pop(player, None)
                remaining.insert(slot_index, taken)
            return False

        if not place(0):
            raise ValueError(
                "locked players cannot all be seated in legal roster slots: "
                + ", ".join(self.players[i].id for i in locked)
            )
        return remaining, assignment

    def _eligible_count(self, eligible: Tuple[str, ...]) -> int:
        return sum(1 for pos in self.positions if any(p in eligible for p in pos))

    def _candidates(self, eligible: Tuple[str, ...]) -> np.ndarray:
        idx = [
            i
            for i in range(self.n)
            if i not in self.blocked and any(p in eligible for p in self.positions[i])
        ]
        return np.array(idx, dtype=int)

    def _team_capacity(self, _team: str) -> int:
        """Per-team cap: the site sets none, so only the user's own limits bite.

        The site rules that do exist per team are the MLB hitter cap and the NHL skater-teams
        minimum, and both are counted separately because they do not apply to pitchers or
        goalies (see :func:`stokengineer.rules.validate_lineup`).
        """
        limits = [self.rules.roster_size]
        if self.max_players_per_team is not None:
            limits.append(int(self.max_players_per_team))
        if _team in self.explicit_team_limits:
            limits.append(int(self.explicit_team_limits[_team]))
        return min(limits)

    def _salary_room_ok(self, depth: int) -> bool:
        remaining_slots = len(self.slots) - depth
        used_salary = float(self.salaries[self.chosen].sum()) if self.chosen else 0.0
        cheapest = 0.0
        dearest = 0.0
        free = [i for i in range(self.n) if i not in self.used and i not in self.blocked]
        for eligible in self.slots[depth:]:
            options = [
                i for i in free if any(p in eligible for p in self.positions[i]) and i not in self.used
            ]
            if not options:
                return False
            cheapest += float(min(self.salaries[i] for i in options))
            dearest += float(max(self.salaries[i] for i in options))
        if used_salary + cheapest > self.rules.salary_cap:
            return False
        if used_salary + dearest < self.constraints.min_salary:
            return False
        return True

    def _slots_seatable(self, depth: int) -> bool:
        """Exact matching test: can the remaining slots be filled by unused players?"""
        free = [i for i in range(self.n) if i not in self.used and i not in self.blocked]
        if not free:
            return depth >= len(self.slots)
        remaining = self.slots[depth:]
        if not remaining:
            return True
        match_player_to_slot: Dict[int, int] = {}

        def augment(slot_index: int, visited: Set[int]) -> bool:
            eligible = remaining[slot_index]
            for pi in free:
                if pi in visited or not any(p in eligible for p in self.positions[pi]):
                    continue
                visited.add(pi)
                if pi not in match_player_to_slot or augment(match_player_to_slot[pi], visited):
                    match_player_to_slot[pi] = slot_index
                    return True
            return False

        for slot_index in range(len(remaining)):
            if not augment(slot_index, set()):
                return False
        return True

    def _team_limits_ok(self) -> bool:
        counts: Dict[str, int] = {}
        hitters: Dict[str, int] = {}
        for i in self.chosen:
            team = self.teams[i]
            counts[team] = counts.get(team, 0) + 1
            if not self.is_pitcher[i]:
                hitters[team] = hitters.get(team, 0) + 1
        for team, count in counts.items():
            if count > self._team_capacity(team):
                return False
        if self.rules.max_hitters_per_team:
            for team, count in hitters.items():
                if count > self.rules.max_hitters_per_team:
                    return False
        return True

    def _structural_reachable(self, depth: int, stack_depth: int) -> bool:
        """Prune on the rules that are not about positions: games and skater teams.

        Both are "at least" rules on the finished lineup, so the reachable maximum from here
        (current distinct values plus one per unfilled slot) must still clear the bar.
        """
        remaining = len(self.slots) - depth
        if self.rules.min_games > 1:
            games = {self.game_keys[i] for i in self.chosen}
            if len(games) + remaining < self.rules.min_games:
                return False
        if self.rules.min_skater_teams:
            skater_teams = {self.teams[i] for i in self.chosen if not self.is_goalie[i]}
            if len(skater_teams) + remaining < self.rules.min_skater_teams:
                return False
        return True

    def _structural_complete(self) -> bool:
        if self.rules.min_games > 1:
            if len({self.game_keys[i] for i in self.chosen}) < self.rules.min_games:
                return False
        if self.rules.min_skater_teams:
            skater_teams = {self.teams[i] for i in self.chosen if not self.is_goalie[i]}
            if len(skater_teams) < self.rules.min_skater_teams:
                return False
        return True

    def _overlap_ok(self) -> bool:
        chosen_ids = [self.players[i].id for i in self.chosen]
        for previous in self.constraints.previous_lineups:
            overlap = len(set(chosen_ids) & set(previous))
            if self.constraints.max_overlap is not None and overlap > self.constraints.max_overlap:
                return False
            if self.constraints.min_unique and overlap > len(previous) - self.constraints.min_unique:
                return False
        return True

    def _stack_reachable(self, depth: int) -> bool:
        stack = self.constraints.stack
        if stack is None:
            return True
        remaining_slots = len(self.slots) - depth
        counts: Dict[str, int] = {}
        for i in self.chosen:
            counts[self.teams[i]] = counts.get(self.teams[i], 0) + 1
        teams = {stack.team} if stack.team else {self.teams[i] for i in range(self.n)}
        for team in teams:
            current = counts.get(team, 0)
            pool = [
                i
                for i in range(self.n)
                if self.teams[i] == team and i not in self.used and i not in self.blocked
            ]
            if stack.include_qb and not any("QB" in self.positions[i] for i in pool) and not any(
                self.teams[i] == team and "QB" in self.positions[i] and i in self.chosen
                for i in range(len(self.chosen))
            ):
                continue
            seatable = 0
            for eligible in self.slots[depth:]:
                if any(any(p in eligible for p in self.positions[i]) for i in pool):
                    seatable += 1
            if current + min(len(pool), seatable, remaining_slots) >= stack.count:
                return True
        return False

    def _complete_ok(self) -> bool:
        if not self._team_limits_ok() or not self._overlap_ok():
            return False
        if not self._structural_complete():
            return False
        stack = self.constraints.stack
        if stack is not None:
            counts = _team_counts(self.slate, self.chosen)
            if stack.team:
                if counts.get(stack.team, 0) < stack.count:
                    return False
                if stack.include_qb and not any(
                    self.teams[i] == stack.team and "QB" in self.positions[i] for i in self.chosen
                ):
                    return False
                if self.constraints.bring_back:
                    opponent = next(
                        (self.opponents[i] for i in self.chosen if self.teams[i] == stack.team),
                        None,
                    )
                    brought = sum(1 for i in self.chosen if self.teams[i] == opponent)
                    if opponent and brought < self.constraints.bring_back:
                        return False
            else:
                team = max(counts, key=lambda t: counts[t])
                if counts[team] < stack.count:
                    return False
                if stack.include_qb and not any(
                    self.teams[i] == team and "QB" in self.positions[i] for i in self.chosen
                ):
                    return False
                if self.constraints.bring_back:
                    opponent = next(
                        (self.opponents[i] for i in self.chosen if self.teams[i] == team), None
                    )
                    brought = sum(1 for i in self.chosen if self.teams[i] == opponent)
                    if opponent and brought < self.constraints.bring_back:
                        return False
        if self.constraints.min_players_per_team is not None:
            counts = _team_counts(self.slate, self.chosen)
            if not any(c >= self.constraints.min_players_per_team for c in counts.values()):
                return False
        return True

    def _upper_bound(self, depth: int) -> float:
        """Admissible bound: each remaining slot takes its best still-unused player.

        Taking the best player per slot independently is a relaxation (nothing stops the same
        player being counted twice), so the bound can never cut off an optimum - which is what
        makes it safe to prune with.
        """
        total = 0.0
        for j in range(depth, len(self.slots)):
            for i in self.sorted_candidates[j]:
                if i not in self.used:
                    total += float(self.scores[i])
                    break
            else:
                return -np.inf
        return total

    def _ordered_candidates(self, depth: int) -> List[int]:
        candidates = [i for i in self._candidates_by_slot[depth] if i not in self.used]
        jitter = self.rng.normal(0.0, self.jitter, size=len(candidates)) if self.jitter else None
        order = np.argsort(
            [-(self.scores[i] + (jitter[k] if jitter is not None else 0.0))
             for k, i in enumerate(candidates)]
        )
        return [int(candidates[k]) for k in order]

    # -- search ----------------------------------------------------------
    def run(self, exhaustive: bool = True) -> List[int]:
        # locked players were seated in __init__; nothing to do here but check them
        if not self._team_limits_ok():
            raise ValueError("locked players already break the per-team limits")

        # Phase 1 - a fast first-fit walk. This guarantees a legal lineup exists to return even
        # if the improvement phase runs out of budget, which is the difference between a
        # fallback and a lottery.
        locked = list(self.used)
        self.first_only = True
        try:
            self._dfs(0)
        except _BudgetedOut:
            pass
        self.first_only = False
        if self.best is None:
            raise _BudgetedOut(
                "no legal lineup exists under these constraints (searched the whole slate)"
            )

        if not exhaustive:
            return self.best

        # Phase 2 - branch and bound from the incumbent, bounded by the node/time budget.
        # Field building passes exhaustive=False: it needs a legal, good lineup per entry, not
        # a proven optimum, and 5 seconds x 600 entries is not a field, it is a hang.
        self.chosen = list(locked)
        self.used = set(locked)
        try:
            self._dfs(0)
        except _BudgetedOut:
            pass
        return self.best

    def _dfs(self, depth: int) -> None:
        self.nodes += 1
        if self.nodes > self.constraints.node_budget or time.monotonic() > self.deadline:
            raise _BudgetedOut("DFS node budget or time limit reached")
        if depth == len(self.slots):
            if self._complete_ok():
                value = float(self.scores[self.chosen].sum())
                if value > self.best_value:
                    self.best_value = value
                    self.best = list(self.chosen)
                if self.first_only:
                    raise _BudgetedOut("first legal lineup found")
            return
        if not self.first_only and self.best is not None:
            if float(self.scores[self.chosen].sum()) + self._upper_bound(depth) <= self.best_value:
                return  # cannot beat the incumbent
        for i in self._ordered_candidates(depth):
            self.chosen.append(i)
            self.used.add(i)
            try:
                if (
                    self._team_limits_ok()
                    and self._salary_room_ok(depth + 1)
                    and self._stack_reachable(depth + 1)
                    and self._structural_reachable(depth + 1, depth + 1)
                    and self._slots_seatable(depth + 1)
                ):
                    self._dfs(depth + 1)
            finally:
                self.chosen.pop()
                self.used.discard(i)


def _solve_heuristic(
    slate: Slate,
    rules: SiteRules,
    scores: np.ndarray,
    projections: Mapping[str, float],
    constraints: LineupConstraints,
    rng: Optional[np.random.Generator] = None,
    jitter: float = 0.0,
) -> OptimizedLineup:
    search = _Search(
        slate, rules, scores, constraints, rng or np.random.default_rng(0), jitter
    )
    chosen = search.run()
    return _package_lineup(
        slate,
        rules,
        scores,
        projections,
        chosen,
        "heuristic",
        [
            "no MILP solver used (pulp not installed or prefer_milp=False): the lineup is legal "
            "and branch-and-bound searched, but optimality is not proven",
            f"{search.nodes} search nodes expanded",
        ],
    )


def _package_lineup(
    slate: Slate,
    rules: SiteRules,
    scores: np.ndarray,
    projections: Mapping[str, float],
    chosen: Sequence[int],
    method: str,
    notes: List[str],
) -> OptimizedLineup:
    records = _lineup_records(slate, chosen)
    problems = validate_lineup(records, rules.site, rules.sport)
    if problems:
        raise AssertionError(
            f"the {method} optimizer produced a lineup the validator rejects, which means the "
            f"optimizer and the rules disagree: {problems}"
        )
    assignment = rules.assign_slots([slate.players[i].positions for i in chosen]) or {}
    # expose player IDS, not column indices: an index is meaningless outside this process and
    # silently produces the wrong name in any consumer that treats it as an id
    return OptimizedLineup(
        player_ids=[slate.players[i].id for i in chosen],
        # assign_slots indexes the list it was GIVEN (the chosen players), not the slate
        slot_assignment={
            slot: slate.players[chosen[index]].id for slot, index in assignment.items()
        },
        projected=float(sum(projections.get(slate.players[i].id, 0.0) for i in chosen)),
        salary=float(sum(slate.players[i].salary for i in chosen)),
        objective_value=float(sum(scores[i] for i in chosen)),
        method=method,
        notes=list(notes),
    )


# ---------------------------------------------------------------------------
# public entry points
# ---------------------------------------------------------------------------
def optimize_lineup(
    slate: Slate,
    projections: Mapping[str, float],
    *,
    constraints: Optional[LineupConstraints] = None,
    site: Optional[str] = None,
    ceiling: Optional[Mapping[str, float]] = None,
    floor: Optional[Mapping[str, float]] = None,
    stddev: Optional[Mapping[str, float]] = None,
    leverage_bonus: Optional[Mapping[str, float]] = None,
    leverage_weight: float = 0.0,
    prefer_milp: bool = True,
    seed: Optional[int] = None,
    jitter: float = 0.0,
) -> OptimizedLineup:
    """Build the best legal lineup under the given constraints."""
    constraints = constraints or LineupConstraints()
    scoring_site = site or slate.site
    rules = get_site_rules(scoring_site, slate.sport)

    problems = required_positions_present(slate, rules, constraints)
    if problems:
        raise ValueError("; ".join(problems))

    scores = score_vector(
        slate,
        projections,
        mode=constraints.objective,
        ceiling=ceiling,
        floor=floor,
        stddev=stddev,
        leverage_bonus=leverage_bonus,
        leverage_weight=leverage_weight,
    )
    notes: List[str] = []
    rng = np.random.default_rng(seed)
    if _HAS_PULP and prefer_milp:
        result = _solve_milp(slate, rules, scores, projections, constraints)
        if result is not None:
            return result
        notes.append(
            "MILP reported no feasible lineup (or hit its time limit); fell back to the DFS "
            "search, which may relax optimality but never legality"
        )

    result = _solve_heuristic(slate, rules, scores, projections, constraints, rng=rng, jitter=jitter)
    result.notes.extend(notes)
    return result


def fast_lineup(
    slate: Slate,
    view: Mapping[str, float],
    *,
    site: Optional[str] = None,
    constraints: Optional[LineupConstraints] = None,
    seed: Optional[int] = None,
    jitter: float = 0.0,
    node_budget: int = 0,
) -> Optional[OptimizedLineup]:
    """One fast, legal, "good enough" lineup for a single view of the projections.

    Used to build simulated *fields*: a realistic field is people using a decent optimiser with
    imperfect projections, so each entry needs a legal lineup that is close to optimal under
    its own noisy view. This runs the DFS in first-fit mode (no optimality proof, no solver),
    which costs milliseconds instead of the MILP's seconds. It returns ``None`` when no legal
    lineup exists under the view rather than raising, so a field builder can retry.
    """
    constraints = constraints or LineupConstraints()
    scoring_site = site or slate.site
    rules = get_site_rules(scoring_site, slate.sport)
    if required_positions_present(slate, rules, constraints):
        return None
    scores = score_vector(slate, view, mode=constraints.objective)
    if node_budget:
        constraints = replace(constraints, node_budget=node_budget, time_limit_seconds=0.5)
    search = _Search(
        slate, rules, scores, constraints, np.random.default_rng(seed), jitter
    )
    try:
        chosen = search.run(exhaustive=bool(node_budget))
    except (_BudgetedOut, ValueError):
        return None
    try:
        return _package_lineup(
            slate, rules, scores, view, chosen, "field",
            [
                "field lineup: local branch-and-bound search under this entry's own view"
                if node_budget
                else "field lineup: fast first-fit search under this entry's own view"
            ],
        )
    except AssertionError:
        return None


def optimize_portfolio(
    slate: Slate,
    projections: Mapping[str, float],
    n_lineups: int,
    *,
    max_exposure: float = 1.0,
    min_unique: int = 1,
    max_overlap: Optional[int] = None,
    constraints: Optional[LineupConstraints] = None,
    site: Optional[str] = None,
    ceiling: Optional[Mapping[str, float]] = None,
    floor: Optional[Mapping[str, float]] = None,
    stddev: Optional[Mapping[str, float]] = None,
    seed: Optional[int] = None,
    objective: str = "median",
    jitter: float = 0.04,
    prefer_milp: bool = True,
) -> List[OptimizedLineup]:
    """Build a portfolio with exposure caps and a uniqueness floor.

    Exposure is a hard cap on how many lineups a player may appear in,
    ``ceil(max_exposure * n_lineups)``; once a player hits it, they are excluded from every
    later lineup. ``min_unique`` forces each new lineup to differ from each earlier one by at
    least that many players. Diversity comes from the exposure cap plus a small randomised
    tie-break (``jitter``), because repeatedly solving the same deterministic problem returns
    the same lineup no matter how many constraints are layered on top.
    """
    if not 0.0 < max_exposure <= 1.0:
        raise ValueError("max_exposure must be in (0, 1]")
    if n_lineups < 1:
        raise ValueError("n_lineups must be at least 1")
    base = replace(constraints or LineupConstraints(), objective=objective)
    scores = score_vector(
        slate,
        projections,
        mode=objective,
        ceiling=ceiling,
        floor=floor,
        stddev=stddev,
    )
    rng = np.random.default_rng(seed)
    cap = max(1, int(np.ceil(max_exposure * n_lineups)))
    exposure_count: Dict[str, int] = {}
    lineups: List[OptimizedLineup] = []
    seen: Set[frozenset] = set()
    attempts = 0
    max_attempts = max(12, n_lineups * 8)

    while len(lineups) < n_lineups and attempts < max_attempts:
        attempts += 1
        excluded = set(base.excluded) | {
            pid for pid, count in exposure_count.items() if count >= cap
        }
        iteration = replace(
            base,
            previous_lineups=[lineup.player_ids for lineup in lineups],
            min_unique=min_unique,
            max_overlap=max_overlap,
            excluded=excluded,
        )
        try:
            lineup = optimize_lineup(
                slate,
                projections,
                constraints=iteration,
                site=site,
                ceiling=ceiling,
                floor=floor,
                stddev=stddev,
                prefer_milp=prefer_milp,
                seed=int(rng.integers(0, 2**31 - 1)),
                jitter=jitter,
            )
        except ValueError:
            break
        signature = frozenset(lineup.player_ids)
        if signature in seen:
            continue
        lineups.append(lineup)
        seen.add(signature)
        for pid in lineup.player_ids:
            exposure_count[pid] = exposure_count.get(pid, 0) + 1
    return lineups
