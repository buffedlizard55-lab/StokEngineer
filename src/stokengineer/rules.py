"""Verified scoring and roster rules, plus the derived metrics Stokastic publishes.

Everything here is traceable:

* Scoring coefficients and roster shapes come from ``src/data/scoring_rules.json`` and
  ``src/data/roster_rules.json``, and each block names the official page it was read from.
* If the JSON ever grows a bonus rule this module does not implement, loading raises. That
  is deliberate: a silently ignored bonus would quietly understate every projection.

Derived metrics (value, pts/$, boom/bust thresholds, implied team total) are implemented
exactly as written on the cited Stokastic pages - see ``src/data/claims.json`` entries c07,
c09 and c23 for the quotes, and ``tests/test_rules.py`` for the article's worked examples.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from . import DATA_DIR

Number = Union[float, int]
ArrayLike = Union[Number, np.ndarray]

SUPPORTED_SITES = ("draftkings", "fanduel")
SUPPORTED_SPORTS = ("nfl", "nba", "mlb", "nhl")
PITCHER_POSITIONS = ("P", "SP", "RP")
GOALIE_POSITIONS = ("G",)


# ---------------------------------------------------------------------------
# config loading
# ---------------------------------------------------------------------------
def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())


@lru_cache(maxsize=1)
def _scoring_config_cached(path_str: str) -> Dict[str, Any]:
    return _read_json(Path(path_str))


@lru_cache(maxsize=1)
def _roster_config_cached(path_str: str) -> Dict[str, Any]:
    return _read_json(Path(path_str))


def scoring_config(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    path = Path(data_dir or DATA_DIR) / "scoring_rules.json"
    return _scoring_config_cached(str(path))


def roster_config(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    path = Path(data_dir or DATA_DIR) / "roster_rules.json"
    return _roster_config_cached(str(path))


def _check_site_sport(site: str, sport: str) -> Tuple[str, str]:
    site, sport = site.lower(), sport.lower()
    if site not in SUPPORTED_SITES:
        raise ValueError(f"site must be one of {SUPPORTED_SITES}, got {site!r}")
    if sport not in SUPPORTED_SPORTS:
        raise ValueError(f"sport must be one of {SUPPORTED_SPORTS}, got {sport!r}")
    return site, sport


# ---------------------------------------------------------------------------
# roster rules
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Slot:
    id: str
    eligible: Tuple[str, ...]

    def accepts(self, positions: Sequence[str]) -> bool:
        return any(p in self.eligible for p in positions)


@dataclass(frozen=True)
class SiteRules:
    """A roster configuration read from the verified roster JSON."""

    site: str
    sport: str
    salary_cap: float
    slots: Tuple[Slot, ...]
    min_games: int
    max_hitters_per_team: Optional[int]
    min_skater_teams: Optional[int]
    source: str
    verified: str

    @property
    def roster_size(self) -> int:
        return len(self.slots)

    def slot_groups(self) -> List[Tuple[Tuple[str, ...], int]]:
        """Slots aggregated by identical eligibility sets.

        Grouping matters for the MILP: two slots that accept the same positions are
        interchangeable, so a group of size *k* becomes a single integer constraint.
        """
        groups: Dict[Tuple[str, ...], int] = {}
        for slot in self.slots:
            groups[slot.eligible] = groups.get(slot.eligible, 0) + 1
        return list(groups.items())

    # -- feasibility ---------------------------------------------------------
    def assign_slots(self, positions: Sequence[Sequence[str]]) -> Optional[Dict[str, int]]:
        """Return {slot_id: player_index} if the players can legally fill every slot.

        Uses augmenting-path bipartite matching (Kuhn's algorithm). Roster sizes here are
        at most 10 slots, so the cost is irrelevant and the result is exact - which is what
        makes this usable both as a validator and as the feasibility check inside the
        greedy optimizer fallback.
        """
        if len(positions) != self.roster_size:
            return None
        match_player_to_slot: Dict[int, int] = {}

        def try_assign(slot_idx: int, visited: set[int]) -> bool:
            for player_idx in range(len(positions)):
                if player_idx in visited or not self.slots[slot_idx].accepts(positions[player_idx]):
                    continue
                visited.add(player_idx)
                if player_idx not in match_player_to_slot or try_assign(
                    match_player_to_slot[player_idx], visited
                ):
                    match_player_to_slot[player_idx] = slot_idx
                    return True
            return False

        for slot_idx in range(len(self.slots)):
            if not try_assign(slot_idx, set()):
                return None
        return {self.slots[slot_idx].id: player_idx for player_idx, slot_idx in
                match_player_to_slot.items()}


def get_site_rules(site: str, sport: str, data_dir: Optional[Path] = None) -> SiteRules:
    site, sport = _check_site_sport(site, sport)
    cfg = roster_config(data_dir)
    try:
        block = cfg[site][sport]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"no roster rules for {site}/{sport}") from exc
    return SiteRules(
        site=site,
        sport=sport,
        salary_cap=float(block["salary_cap"]),
        slots=tuple(Slot(s["id"], tuple(s["eligible"])) for s in block["slots"]),
        min_games=int(block.get("min_games") or 0),
        max_hitters_per_team=block.get("max_hitters_per_team"),
        min_skater_teams=block.get("min_skater_teams"),
        source=block.get("source", ""),
        verified=block.get("verified", "unknown"),
    )


def validate_lineup(
    players: Sequence[Mapping[str, Any]],
    site: str,
    sport: str,
    data_dir: Optional[Path] = None,
) -> List[str]:
    """Return a list of rule violations for a proposed lineup (empty list == legal).

    Each player mapping needs ``positions`` (list of position strings) and ``salary``;
    ``game_id`` (or ``team``/``opponent`` pair) is used for the multi-game requirement.
    """
    rules = get_site_rules(site, sport, data_dir)
    problems: List[str] = []

    if len(players) != rules.roster_size:
        problems.append(
            f"{site}/{sport}: lineup has {len(players)} players, rules require {rules.roster_size}"
        )

    names = [str(p.get("name", f"#{i}")) for i, p in enumerate(players)]
    if len(set(names)) != len(names):
        problems.append(f"{site}/{sport}: duplicate players in lineup: {sorted(names)}")

    salary = sum(float(p.get("salary", 0) or 0) for p in players)
    if salary > rules.salary_cap:
        problems.append(f"salary {salary:.0f} exceeds cap {rules.salary_cap:.0f}")

    positions = [tuple(p.get("positions") or ([p["position"]] if p.get("position") else []))
                 for p in players]
    if any(not pos for pos in positions):
        problems.append("every player needs at least one position")
    elif rules.assign_slots(positions) is None:
        problems.append(
            f"{site}/{sport}: positions {positions} cannot fill slots "
            f"{[(s.id, list(s.eligible)) for s in rules.slots]}"
        )

    if rules.min_games:
        games = set()
        for p in players:
            gid = p.get("game_id")
            if not gid:
                team, opp = p.get("team"), p.get("opponent")
                gid = tuple(sorted((team, opp))) if team and opp else None
            if gid:
                games.add(gid)
        if len(games) < rules.min_games:
            problems.append(
                f"lineup spans {len(games)} games; rules require at least {rules.min_games}"
            )

    if rules.max_hitters_per_team:
        per_team: Dict[str, int] = {}
        for p, pos in zip(players, positions):
            if any(x in pos for x in PITCHER_POSITIONS):
                continue  # pitchers are not hitters
            per_team[str(p.get("team", "?"))] = per_team.get(str(p.get("team", "?")), 0) + 1
        for team, count in per_team.items():
            if count > rules.max_hitters_per_team:
                problems.append(
                    f"{count} hitters from {team}; rules allow at most "
                    f"{rules.max_hitters_per_team}"
                )

    if rules.min_skater_teams:
        skater_teams = {
            str(p.get("team", "?"))
            for p, pos in zip(players, positions)
            if not any(x in pos for x in GOALIE_POSITIONS)
        }
        if len(skater_teams) < rules.min_skater_teams:
            problems.append(
                f"skaters come from {len(skater_teams)} teams; rules require "
                f"{rules.min_skater_teams}"
            )
    return problems


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------
def _points_allowed(points: ArrayLike, table: Sequence[Mapping[str, Any]]) -> ArrayLike:
    """Map points allowed to the official tier value.

    The feed reports points allowed as a whole number and the tiers are whole-number ranges,
    so continuous simulated values are rounded to the nearest integer before lookup; without
    this a simulated 34.4 would match no tier at all.
    """
    if np.isscalar(points):
        value = float(round(float(points)))  # type: ignore[arg-type]
        for row in table:
            low = row["min"]
            high = row["max"]
            if value >= low and (high is None or value <= high):
                return float(row["points"])
        raise ValueError(f"points allowed {value} does not match any tier")
    arr = np.floor(np.asarray(points, dtype=float) + 0.5)
    out = np.full(arr.shape, np.nan)
    for row in table:
        low = row["min"]
        high = row["max"]
        mask = arr >= low if high is None else (arr >= low) & (arr <= high)
        out = np.where(mask, float(row["points"]), out)
    if np.isnan(out).any():
        raise ValueError("some points-allowed values did not match a tier")
    return out


# Bonus predicates. Keyed by the ids used in src/data/scoring_rules.json; an id with no
# predicate here makes load_scoring() fail loudly rather than dropping points on the floor.
def _two_counters_at_least(statline: Mapping[str, ArrayLike], keys: Sequence[str], n: int,
                           threshold: float = 10.0) -> ArrayLike:
    total = None
    for key in keys:
        value = statline.get(key)
        if value is None:
            continue
        # cast to int: NumPy boolean addition saturates (True + True is True),
        # which would silently turn a double-double test into a single counter.
        hit = (np.asarray(value, dtype=float) >= threshold).astype(int)
        total = hit if total is None else total + hit
    if total is None:
        return False
    return total >= n


BONUS_PREDICATES = {
    "pass_300_bonus": lambda s: _ge(s, "pass_yd", 300),
    "rush_100_bonus": lambda s: _ge(s, "rush_yd", 100),
    "rec_100_bonus": lambda s: _ge(s, "rec_yd", 100),
    "double_double": lambda s: _two_counters_at_least(
        s, ("pts", "reb", "ast", "stl", "blk"), 2, 10.0
    ),
    "triple_double": lambda s: _two_counters_at_least(
        s, ("pts", "reb", "ast", "stl", "blk"), 3, 10.0
    ),
    "complete_game": lambda s: _truthy(s, "complete_game"),
    "complete_game_shutout": lambda s: _truthy(s, "complete_game_shutout"),
    "no_hitter": lambda s: _truthy(s, "no_hitter"),
    "hat_trick": lambda s: _ge(s, "goal", 3),
    "shots_5plus": lambda s: _ge(s, "sog", 5),
    "blocks_3plus": lambda s: _ge(s, "blocked_shot", 3),
    "points_3plus": lambda s: _sum_ge(s, ("goal", "assist"), 3),
    "saves_35plus": lambda s: _ge(s, "g_save", 35),
}


def _ge(statline: Mapping[str, ArrayLike], key: str, threshold: float) -> ArrayLike:
    value = statline.get(key)
    if value is None:
        return False
    return np.asarray(value, dtype=float) >= threshold


def _truthy(statline: Mapping[str, ArrayLike], key: str) -> ArrayLike:
    value = statline.get(key)
    if value is None:
        return False
    return np.asarray(value) != 0


def _sum_ge(statline: Mapping[str, ArrayLike], keys: Sequence[str], threshold: float) -> ArrayLike:
    total: Any = 0
    for key in keys:
        value = statline.get(key)
        if value is not None:
            total = total + np.asarray(value, dtype=float)
    return total >= threshold


@dataclass(frozen=True)
class Scoring:
    site: str
    sport: str
    coefficients: Mapping[str, float]
    bonus_rules: Tuple[Mapping[str, Any], ...]
    dst_points_allowed_table: Tuple[Mapping[str, Any], ...]
    source: str
    verified: str
    stat_keys: Tuple[str, ...]


def load_scoring(site: str, sport: str, data_dir: Optional[Path] = None) -> Scoring:
    """Load verified scoring for a site/sport combination."""
    site, sport = _check_site_sport(site, sport)
    cfg = scoring_config(data_dir)
    block = cfg[site][sport]

    coefficients: Dict[str, float] = {}
    for section in ("stats", "dst_stats", "pitching_stats", "goalie_stats"):
        for key, value in (block.get(section) or {}).items():
            if key in coefficients and coefficients[key] != value:
                raise ValueError(
                    f"{site}/{sport}: {key} appears twice with different values"
                )
            coefficients[key] = float(value)

    bonus_rules = tuple(block.get("bonus_rules") or ())
    pitching_bonus_rules = tuple(block.get("pitching_bonus_rules") or ())
    for rule in (*bonus_rules, *pitching_bonus_rules):
        if rule["id"] not in BONUS_PREDICATES:
            raise KeyError(
                f"scoring_rules.json declares bonus rule {rule['id']!r} for {site}/{sport} "
                f"but rules.BONUS_PREDICATES has no predicate for it. Implement it (and test "
                f"it) before publishing projections that use it."
            )

    return Scoring(
        site=site,
        sport=sport,
        coefficients=coefficients,
        bonus_rules=bonus_rules + pitching_bonus_rules,
        dst_points_allowed_table=tuple(block.get("dst_points_allowed_table") or ()),
        source=block.get("source", ""),
        verified=block.get("verified", "unknown"),
        stat_keys=tuple(sorted(coefficients)),
    )


def applicable_stat_keys(
    site: str, sport: str, positions: Sequence[str] = (), data_dir: Optional[Path] = None
) -> set:
    """Stat keys the given site/sport actually pays for, given a player's positions.

    Models use this to drop stat keys a site ignores (FanDuel MLB pays for quality starts and
    DraftKings does not) instead of having the strict scorer reject the whole stat line.
    """
    site, sport = _check_site_sport(site, sport)
    block = scoring_config(data_dir)[site][sport]
    keys: set = set()
    for section in ("stats", "dst_stats", "pitching_stats", "goalie_stats"):
        keys |= set(block.get(section) or {})
    if sport == "mlb":
        pitching = _is_pitcher(positions)
        keys = set(block.get("pitching_stats" if pitching else "stats") or {})
        for rule in (block.get("pitching_bonus_rules" if pitching else "bonus_rules") or ()):
            keys |= {k for k in ("complete_game", "complete_game_shutout", "no_hitter",
                                 "quality_start") if k == rule["id"]}
    else:
        for rule in (block.get("bonus_rules") or ()):
            pass  # non-MLB bonus ids are computed from coefficient keys already present
    return keys | {"dst_pa"}


def _is_pitcher(positions: Sequence[str]) -> bool:
    return any(p in PITCHER_POSITIONS for p in positions)


def score_statline(
    statline: Mapping[str, Number],
    site: str,
    sport: str,
    positions: Sequence[str] = (),
    data_dir: Optional[Path] = None,
    allow_unknown: bool = False,
) -> float:
    """Score one raw stat line (scalar path).

    ``positions`` matters for MLB: hitting and pitching stats do not mix, so a player with
    position ``P`` is scored with the pitching table only (official DraftKings note).
    """
    scoring = load_scoring(site, sport, data_dir)
    truthy_keys = {"complete_game", "complete_game_shutout", "no_hitter"}

    if sport == "mlb":
        block = scoring_config(data_dir)[site][sport]
        pitching = _is_pitcher(positions)
        allowed = set(block.get("pitching_stats" if pitching else "stats") or {})
        allowed |= truthy_keys | {"dst_pa"}
        applicable_bonus_ids = {
            rule["id"]
            for rule in (
                block.get("pitching_bonus_rules" if pitching else "bonus_rules") or ()
            )
        }
    else:
        allowed = set(scoring.stat_keys) | truthy_keys | {"dst_pa"}
        applicable_bonus_ids = {rule["id"] for rule in scoring.bonus_rules}

    unknown = {k for k in statline if k not in allowed}
    if unknown and not allow_unknown:
        raise ValueError(
            f"unknown stat keys for {site}/{sport}: {sorted(unknown)}. Add them to "
            f"src/data/scoring_rules.json (with a source) or pass allow_unknown=True."
        )

    if sport == "mlb":
        block = scoring_config(data_dir)[site][sport]
        coefficients = (
            block.get("pitching_stats") if _is_pitcher(positions) else block.get("stats")
        ) or {}
    else:
        coefficients = scoring.coefficients

    total = 0.0
    for key, weight in coefficients.items():
        if key in truthy_keys:
            total += float(weight) * (1.0 if statline.get(key) else 0.0)
        else:
            total += float(weight) * float(statline.get(key, 0.0) or 0.0)

    for rule in scoring.bonus_rules:
        if rule["id"] not in applicable_bonus_ids:
            continue
        if BONUS_PREDICATES[rule["id"]](statline):
            total += float(rule["points"])

    if "dst_pa" in statline:
        total += float(_points_allowed(float(statline["dst_pa"]), scoring.dst_points_allowed_table))
    return total


def score_array(
    stats: Mapping[str, ArrayLike],
    site: str,
    sport: str,
    positions: Sequence[str] = (),
    data_dir: Optional[Path] = None,
    size: Optional[int] = None,
) -> np.ndarray:
    """Vectorised sibling of :func:`score_statline` over ``n`` simulated stat lines.

    ``stats`` maps stat key -> array of length n (scalars are broadcast).
    """
    scoring = load_scoring(site, sport, data_dir)
    truthy_keys = {"complete_game", "complete_game_shutout", "no_hitter"}

    lengths = [len(np.atleast_1d(np.asarray(v))) for v in stats.values()]
    if size is None:
        size = max(lengths) if lengths else 1

    def arr(key: str) -> Optional[np.ndarray]:
        value = stats.get(key)
        if value is None:
            return None
        out = np.asarray(value, dtype=float)
        if out.ndim == 0:
            return np.full(size, float(out))
        if out.shape[0] != size:
            raise ValueError(f"stat {key!r} has length {out.shape[0]}, expected {size}")
        return out

    if sport == "mlb":
        block = scoring_config(data_dir)[site][sport]
        key = "pitching_stats" if _is_pitcher(positions) else "stats"
        coefficients = block.get(key) or {}
        bonus_ids = {
            r["id"]
            for r in (
                block.get("pitching_bonus_rules")
                if _is_pitcher(positions)
                else block.get("bonus_rules")
            )
            or ()
        }
    else:
        coefficients = scoring.coefficients
        bonus_ids = {r["id"] for r in scoring.bonus_rules}

    allowed = set(coefficients) | truthy_keys
    unknown = {k for k in stats if k not in allowed and k != "dst_pa"}
    if unknown:
        raise ValueError(
            f"unknown stat keys for {site}/{sport}: {sorted(unknown)} "
            f"(vectorised scorer is strict on purpose)"
        )

    total = np.zeros(size)
    for stat_key, weight in coefficients.items():
        values = arr(stat_key)
        if values is None:
            continue
        if stat_key in truthy_keys:
            values = (values != 0).astype(float)
        total += float(weight) * values

    for rule in scoring.bonus_rules:
        if rule["id"] not in bonus_ids:
            continue
        hit = BONUS_PREDICATES[rule["id"]](stats)
        if np.isscalar(hit):
            if hit:
                total += float(rule["points"])
        else:
            total += float(rule["points"]) * np.asarray(hit, dtype=float)

    pa = arr("dst_pa")
    if pa is not None:
        total += _points_allowed(pa, scoring.dst_points_allowed_table)  # type: ignore[arg-type]
    return total


# ---------------------------------------------------------------------------
# derived metrics (published by Stokastic, implemented exactly)
# ---------------------------------------------------------------------------
def value(fantasy_points: ArrayLike, salary: ArrayLike) -> ArrayLike:
    """Value = FP - (salary / 1000 * 5). Source: sk_nba_projections (claim c09)."""
    return np.asarray(fantasy_points, dtype=float) - (
        np.asarray(salary, dtype=float) / 1000.0 * 5.0
    )


def pts_per_dollar(fantasy_points: ArrayLike, salary: ArrayLike) -> ArrayLike:
    """Pts/$ = FP / salary * 1000. Source: sk_nba_projections (claim c09)."""
    salary_arr = np.asarray(salary, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.asarray(fantasy_points, dtype=float) / salary_arr * 1000.0
    return np.where(salary_arr > 0, out, np.nan)


def boom_threshold(salary: ArrayLike) -> ArrayLike:
    """Boom = about 5 x (salary/1000) + 10 FP. Source: sk_nba_boom_bust (claim c07)."""
    return 5.0 * (np.asarray(salary, dtype=float) / 1000.0) + 10.0


def bust_threshold(salary: ArrayLike) -> ArrayLike:
    """Bust = falling short of 5 x (salary/1000). Source: sk_nba_boom_bust (claim c07)."""
    return 5.0 * (np.asarray(salary, dtype=float) / 1000.0)


def implied_team_total(total: ArrayLike, spread: ArrayLike) -> Tuple[ArrayLike, ArrayLike]:
    """(favourite, underdog) implied team totals from a game total and a spread.

    Formula verified on sk_nfl_defense (claim c23): the favourite gets total/2 + spread/2 and
    the underdog total/2 - spread/2. The article's worked example - a 44 total with a 7-point
    favourite - returns (25.5, 18.5).

    Sign convention: only the **magnitude** of the spread is used, because feeds disagree on
    whether the favourite's spread is written -7 or +7 (ESPN writes -7 for the favourite).
    Deriving the favourite from the sign of the number is how a model quietly ends up
    projecting the wrong team, so this function never does it. Use
    :func:`implied_totals_for_side` when you know which team the spread belongs to.
    """
    total_arr = np.asarray(total, dtype=float)
    half = total_arr / 2.0
    margin = np.abs(np.asarray(spread, dtype=float)) / 2.0
    return half + margin, half - margin


def implied_totals_for_side(
    total: ArrayLike, spread: ArrayLike, is_favourite: bool
) -> Tuple[ArrayLike, ArrayLike]:
    """(home, away) implied totals for a spread attached to a known side.

    ``spread`` is that side's own spread (negative if it is the favourite, as ESPN publishes
    it). Returns ``(favourite_total, underdog_total)`` ordered as
    ``(home_total, away_total)`` according to ``is_favourite``.
    """
    favourite, underdog = implied_team_total(total, spread)
    return (favourite, underdog) if is_favourite else (underdog, favourite)


@dataclass(frozen=True)
class DistributionSummary:
    """The boom/bust view Stokastic publishes, computed from a sampled distribution."""

    mean: float
    median: float
    stddev: float
    ceiling_75: float
    floor_25: float
    ceiling_90: float
    floor_10: float
    boom_pct: float
    bust_pct: float
    boom_threshold: float
    bust_threshold: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "mean": self.mean,
            "median": self.median,
            "stddev": self.stddev,
            "ceiling_75": self.ceiling_75,
            "floor_25": self.floor_25,
            "ceiling_90": self.ceiling_90,
            "floor_10": self.floor_10,
            "boom_pct": self.boom_pct,
            "bust_pct": self.bust_pct,
            "boom_threshold": self.boom_threshold,
            "bust_threshold": self.bust_threshold,
        }


def summarise_distribution(samples: Sequence[float], salary: float) -> DistributionSummary:
    """Percentile/boom/bust summary of a simulated fantasy-point distribution.

    Ceiling = 75th percentile, floor = 25th percentile (sk_nba_boom_bust, claim c08).
    Boom% = share of sims at or above ``boom_threshold``; Bust% = share strictly below
    ``bust_threshold`` (claim c07).
    """
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        raise ValueError("no samples supplied")
    boom = float(boom_threshold(salary))
    bust = float(bust_threshold(salary))
    return DistributionSummary(
        mean=float(arr.mean()),
        median=float(np.median(arr)),
        stddev=float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        ceiling_75=float(np.percentile(arr, 75)),
        floor_25=float(np.percentile(arr, 25)),
        ceiling_90=float(np.percentile(arr, 90)),
        floor_10=float(np.percentile(arr, 10)),
        boom_pct=float((arr >= boom).mean() * 100.0),
        bust_pct=float((arr < bust).mean() * 100.0),
        boom_threshold=boom,
        bust_threshold=bust,
    )


# ---------------------------------------------------------------------------
# integrity
# ---------------------------------------------------------------------------
def verify_rules(data_dir: Optional[Path] = None) -> List[str]:
    """Structural checks over the two rules files. Empty list == OK."""
    problems: List[str] = []
    scfg = scoring_config(data_dir)
    rcfg = roster_config(data_dir)

    for site in SUPPORTED_SITES:
        if site not in scfg:
            problems.append(f"scoring_rules.json: missing site {site}")
            continue
        if site not in rcfg:
            problems.append(f"roster_rules.json: missing site {site}")
            continue
        for sport in SUPPORTED_SPORTS:
            if sport not in scfg[site]:
                problems.append(f"scoring_rules.json: missing {site}/{sport}")
                continue
            if sport not in rcfg[site]:
                problems.append(f"roster_rules.json: missing {site}/{sport}")
                continue
            for label, block in (("scoring", scfg[site][sport]), ("roster", rcfg[site][sport])):
                if not block.get("source", "").startswith("https://"):
                    problems.append(f"{label} ({site}/{sport}) has no https source")
                if not block.get("verified"):
                    problems.append(f"{label} ({site}/{sport}) has no verified marker")
                if "verified_on" not in block:
                    problems.append(f"{label} ({site}/{sport}) has no verified_on date")
            table = scfg[site][sport].get("dst_points_allowed_table")
            if table:
                ordered = sorted(table, key=lambda r: r["min"])
                if [r["min"] for r in ordered] != [r["min"] for r in table]:
                    problems.append(f"dst table ({site}/{sport}) is not ordered by min")
                if ordered[0]["min"] != 0:
                    problems.append(f"dst table ({site}/{sport}) does not start at 0")
                if ordered[-1]["max"] is not None:
                    problems.append(f"dst table ({site}/{sport}) has no open-ended top tier")
                for prev, nxt in zip(ordered, ordered[1:]):
                    if prev["max"] is None:
                        problems.append(f"dst table ({site}/{sport}) has rows after an open tier")
                    elif nxt["min"] != prev["max"] + 1:
                        problems.append(
                            f"dst table ({site}/{sport}) has a gap between "
                            f"{prev['max']} and {nxt['min']}"
                        )
            roster = rcfg[site][sport]
            if int(roster["roster_size"]) != len(roster["slots"]):
                problems.append(f"roster_rules.json {site}/{sport}: roster_size != len(slots)")
            for slot in roster["slots"]:
                if not slot.get("eligible"):
                    problems.append(f"roster_rules.json {site}/{sport}: slot {slot['id']} empty")
            # load_scoring also validates that every declared bonus rule has a predicate
            try:
                load_scoring(site, sport, data_dir)
            except KeyError as exc:
                problems.append(str(exc))
    return problems
