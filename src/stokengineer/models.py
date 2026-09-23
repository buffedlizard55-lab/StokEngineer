"""Per-sport projection models.

Design
------
Each model takes projected **opportunity** (minutes, attempts, targets, plate appearances,
...) and converts it into full simulated **stat lines**, which :mod:`stokengineer.rules`
then scores with the official DraftKings/FanDuel table. Two reasons for simulating stat
lines instead of projecting a single fantasy-point number:

* DraftKings NBA pays double-double and triple-double bonuses and DraftKings NFL pays
  300/100-yard bonuses. Averaging stats first and scoring the average understates the value
  of exactly the players GPPs are won with.
* Ceiling/floor/Boom%/Bust% are percentiles of a distribution. Stokastic publishes those as
  first-class columns (claims c07, c08), so the engine has to carry the distribution.

What is sourced vs assumed
--------------------------
* Opportunity -> stat conversion uses per-unit rates supplied per player (from the slate
  file, which in production comes from nflverse/MLB StatsAPI/NBA endpoints or the user's CSV
  export). Those inputs are not invented by this file.
* The *dispersion* of each rate around its mean is a documented prior in
  :class:`SimulationConfig`, and :meth:`SimulationConfig.from_history` re-estimates it from
  real game logs. Every report records which config was used.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import DATA_DIR
from .correlation import (
    MLB_OFFENSE,
    NBA_PACE,
    TEAM_SCORING,
    TEAM_VOLUME,
    LatentSpec,
    team_latent_factors,
)
from .rules import applicable_stat_keys, score_array

SUPPORTED_SPORTS = ("nfl", "nba", "mlb")


# ---------------------------------------------------------------------------
# slate containers
# ---------------------------------------------------------------------------
@dataclass
class PlayerProjection:
    """One player on a slate: identity, salary, and the inputs the model needs."""

    id: str
    name: str
    team: str
    opponent: str
    positions: Tuple[str, ...]
    salary: float
    props: Dict[str, float] = field(default_factory=dict)
    game_id: str = ""
    #: Target correlation between two teammates' fantasy scores, imposed as a post-processing
    #: calibration (see :func:`apply_teammate_correlation`). The verified sources say the sims
    #: must respect correlation within a game ("correlations hold", claim c03) and none of them
    #: publish a number, so this is a *documented prior*, not a measurement. It is the single
    #: biggest lever on how much a stack is worth, and LIMITATIONS.md tracks calibrating it
    #: against free historical data as outstanding work.
    target_teammate_correlation: float = 0.12

    notes: str = ""

    @staticmethod
    def from_dict(raw: Mapping[str, Any]) -> "PlayerProjection":
        positions = raw.get("positions")
        if positions is None:
            positions = [raw["position"]] if raw.get("position") else []
        return PlayerProjection(
            id=str(raw.get("id") or raw.get("name")),
            name=str(raw["name"]),
            team=str(raw.get("team", "")),
            opponent=str(raw.get("opponent", "")),
            positions=tuple(str(p) for p in positions),
            salary=float(raw.get("salary", 0) or 0),
            props={k: float(v) for k, v in (raw.get("props") or {}).items()},
            game_id=str(raw.get("game_id") or ""),
            notes=str(raw.get("notes", "")),
        )

    def as_validation_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "salary": self.salary,
            "positions": list(self.positions),
            "team": self.team,
            "opponent": self.opponent,
            "game_id": self.game_id or (self.team, self.opponent),
        }


@dataclass
class Slate:
    sport: str
    site: str
    players: List[PlayerProjection]
    date: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)
    games: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def from_dict(raw: Mapping[str, Any]) -> "Slate":
        sport = str(raw["sport"]).lower()
        if sport not in SUPPORTED_SPORTS:
            raise ValueError(f"sport must be one of {SUPPORTED_SPORTS}, got {sport!r}")
        site = str(raw.get("site", "draftkings")).lower()
        players = [PlayerProjection.from_dict(p) for p in raw["players"]]
        return Slate(
            sport=sport,
            site=site,
            players=players,
            date=str(raw.get("date", "")),
            provenance=dict(
                raw.get("_provenance") or raw.get("provenance") or raw.get("_meta") or {}
            ),
            games=list(raw.get("games") or []),
        )

    @staticmethod
    def load(path: Path | str) -> "Slate":
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict) and "_meta" in data and "players" not in data:
            # sample files keep their metadata separate from the payload
            payload = dict(data)
            payload["_provenance"] = data.get("_meta", {})
            return Slate.from_dict(payload)
        return Slate.from_dict(data)

    def index(self) -> Dict[str, int]:
        return {p.id: i for i, p in enumerate(self.players)}

    def teams(self) -> List[str]:
        return [p.team for p in self.players if p.team]

    def validate(self) -> List[str]:
        problems: List[str] = []
        if not self.players:
            problems.append("slate has no players")
        ids = [p.id for p in self.players]
        if len(set(ids)) != len(ids):
            problems.append("duplicate player ids")
        for p in self.players:
            if not p.positions:
                problems.append(f"{p.name}: no positions")
            if p.salary <= 0:
                problems.append(f"{p.name}: salary must be positive")
        return problems


# ---------------------------------------------------------------------------
# simulation configuration (documented priors + calibration entry point)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SimulationConfig:
    """Dispersion settings.

    ``*_sd_scale`` multiply the model's per-stat standard deviations; ``team_*`` are the
    log-sigmas of the shared team factors. Defaults are priors chosen to look like real DFS
    distributions (a stud's score is roughly 35-45% as variable as their mean), and
    :meth:`from_history` replaces them with values measured from game logs.
    """

    volume_sd_scale: float = 1.0
    efficiency_sd_scale: float = 1.0
    minutes_sd_scale: float = 1.0
    team_volume_sigma: float = TEAM_VOLUME.sigma
    team_scoring_sigma: float = TEAM_SCORING.sigma
    nba_pace_sigma: float = NBA_PACE.sigma
    mlb_offense_sigma: float = MLB_OFFENSE.sigma
    #: Target correlation between two teammates' fantasy scores, imposed as a post-processing
    #: calibration (see :func:`apply_teammate_correlation`). The verified sources say the sims
    #: must respect correlation within a game ("correlations hold", claim c03) and none of them
    #: publish a number, so this is a *documented prior*, not a measurement. It is the biggest
    #: lever on how much a stack is worth, and LIMITATIONS.md tracks calibrating it against
    #: free historical data as outstanding work.
    target_teammate_correlation: float = 0.12
    notes: str = "prior defaults (uncalibrated)"

    @staticmethod
    def from_history(rows: Sequence[Mapping[str, Any]]) -> "SimulationConfig":
        """Estimate dispersion scales from real per-player game logs.

        ``rows`` needs ``{"sport", "position", "mean", "actual"}`` per player-game. The
        estimator compares the coefficient of variation of the residuals around each
        player's own mean with the model's assumed CV, and returns a multiplicative scale.
        This is intentionally simple and inspectable rather than a black box.
        """
        by_group: Dict[Tuple[str, str], List[Tuple[float, float]]] = {}
        for row in rows:
            key = (str(row["sport"]).lower(), str(row.get("position", "")).upper())
            mean = float(row["mean"])
            if mean <= 0:
                continue
            by_group.setdefault(key, []).append((mean, float(row["actual"])))

        scales: Dict[str, float] = {}
        for (sport, position), pairs in by_group.items():
            means = np.array([m for m, _ in pairs])
            actual = np.array([a for _, a in pairs])
            resid = (actual - means) / means
            cv = float(np.std(resid, ddof=1)) if resid.size > 2 else float("nan")
            scales[position] = cv if math.isfinite(cv) else 1.0

        if not scales:
            return SimulationConfig()
        typical = float(np.median([v for v in scales.values() if v > 0])) or 1.0
        return SimulationConfig(
            volume_sd_scale=typical,
            efficiency_sd_scale=typical,
            minutes_sd_scale=typical,
            notes=(
                f"estimated from {len(rows)} player-games; median residual CV={typical:.3f} "
                f"across groups {sorted(k[0] + ':' + k[1] for k in by_group)}"
            ),
        )

    def latent_specs(self, sport: str) -> List[LatentSpec]:
        if sport == "nfl":
            return [
                replace(TEAM_VOLUME, sigma=self.team_volume_sigma),
                replace(TEAM_SCORING, sigma=self.team_scoring_sigma),
            ]
        if sport == "nba":
            return [replace(NBA_PACE, sigma=self.nba_pace_sigma)]
        if sport == "mlb":
            return [replace(MLB_OFFENSE, sigma=self.mlb_offense_sigma)]
        raise ValueError(f"no latents for sport {sport!r}")


# ---------------------------------------------------------------------------
# sampling helpers
# ---------------------------------------------------------------------------
def _poisson(mean: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    return rng.poisson(np.clip(mean, 0.0, None)).astype(float)


def _normal(mean: np.ndarray, sd: np.ndarray, rng: np.random.Generator,
            low: float = 0.0, high: Optional[float] = None) -> np.ndarray:
    out = rng.normal(mean, np.clip(sd, 1e-9, None))
    out = np.maximum(out, low)
    if high is not None:
        out = np.minimum(out, high)
    return out


def _beta_like(mean: np.ndarray, sd: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Bounded [0,1] draws with a target mean and sd, from a moment-matched Beta.

    Used for per-attempt probabilities (completion rate, catch rate), where a normal would
    occasionally produce values below 0 or above 1.
    """
    mean = np.clip(mean, 1e-6, 1 - 1e-6)
    var = np.clip(np.asarray(sd, dtype=float) ** 2, 1e-9, mean * (1 - mean) - 1e-9)
    kappa = mean * (1 - mean) / var - 1.0
    kappa = np.clip(kappa, 0.1, 1e6)
    alpha = mean * kappa
    beta = (1 - mean) * kappa
    return rng.beta(alpha, beta)


# ---------------------------------------------------------------------------
# sport models
# ---------------------------------------------------------------------------
def _nfl_stat_lines(
    player: PlayerProjection,
    latents: Dict[str, np.ndarray],
    n_sims: int,
    rng: np.random.Generator,
    cfg: SimulationConfig,
) -> Dict[str, np.ndarray]:
    """NFL stat-line simulation for one player.

    Volume (attempts/targets/carries) is drawn around the player's projection scaled by the
    team's shared volume factor, so a game in which the whole passing offence is up lifts the
    QB and his receivers together. Touchdowns are drawn per opportunity scaled by the team's
    shared scoring factor. That is the "correlations hold" mechanic described in
    ``sk_nfl_review``, generated rather than hard-coded.
    """
    p = player.props
    vol = latents["team_volume"]
    scor = latents["team_scoring"]
    out: Dict[str, np.ndarray] = {}
    pos = set(player.positions)

    if "QB" in pos:
        attempts = _poisson(p.get("pass_att", 0.0) * vol, rng)
        comp_rate = _beta_like(
            np.full(n_sims, p.get("comp_rate", 0.63)),
            np.full(n_sims, 0.04 * cfg.efficiency_sd_scale),
            rng,
        )
        completions = rng.binomial(attempts.astype(int), comp_rate).astype(float)
        ypa = _normal(
            np.full(n_sims, p.get("pass_yd_per_att", 7.1)),
            np.full(n_sims, 0.9 * cfg.efficiency_sd_scale),
            rng,
            low=0.0,
        )
        pass_yd = completions * 0.0 + attempts * ypa
        pass_td = _poisson(p.get("pass_td_per_att", 0.045) * attempts * scor, rng)
        pass_int = _poisson(p.get("int_per_att", 0.022) * attempts, rng)
        rush_att = _poisson(p.get("rush_att", 0.0) * vol, rng)
        rush_yd = rush_att * _normal(
            np.full(n_sims, p.get("rush_yd_per_att", 4.2)),
            np.full(n_sims, 1.4 * cfg.efficiency_sd_scale),
            rng,
            low=0.0,
        )
        rush_td = _poisson(p.get("rush_td_per_att", 0.03) * rush_att * scor, rng)
        out.update(
            pass_yd=pass_yd,
            pass_td=pass_td,
            pass_int=pass_int,
            rush_yd=rush_yd,
            rush_td=rush_td,
            fumble_lost=_poisson(np.full(n_sims, 0.15), rng),
            two_pt=_poisson(np.full(n_sims, 0.03), rng),
        )
        return out

    if "RB" in pos:
        carries = _poisson(p.get("rush_att", 0.0) * vol, rng)
        rush_yd = carries * _normal(
            np.full(n_sims, p.get("rush_yd_per_att", 4.3)),
            np.full(n_sims, 1.5 * cfg.efficiency_sd_scale),
            rng,
            low=0.0,
        )
        rush_td = _poisson(p.get("rush_td_per_att", 0.035) * carries * scor, rng)
        targets = _poisson(p.get("targets", 0.0) * vol, rng)
        rec = rng.binomial(targets.astype(int), np.clip(p.get("catch_rate", 0.75), 0, 1)).astype(float)
        rec_yd = rec * _normal(
            np.full(n_sims, p.get("rec_yd_per_rec", 7.5)),
            np.full(n_sims, 3.0 * cfg.efficiency_sd_scale),
            rng,
            low=0.0,
        )
        rec_td = _poisson(p.get("rec_td_per_target", 0.02) * targets * scor, rng)
        out.update(
            rush_yd=rush_yd,
            rush_td=rush_td,
            rec=rec,
            rec_yd=rec_yd,
            rec_td=rec_td,
            fumble_lost=_poisson(np.full(n_sims, 0.12), rng),
            two_pt=_poisson(np.full(n_sims, 0.02), rng),
        )
        return out

    if pos & {"WR", "TE"}:
        targets = _poisson(p.get("targets", 0.0) * vol, rng)
        catch_rate = _beta_like(
            np.full(n_sims, p.get("catch_rate", 0.65)),
            np.full(n_sims, 0.05 * cfg.efficiency_sd_scale),
            rng,
        )
        rec = rng.binomial(targets.astype(int), catch_rate).astype(float)
        rec_yd = rec * _normal(
            np.full(n_sims, p.get("rec_yd_per_rec", 12.0)),
            np.full(n_sims, 4.5 * cfg.efficiency_sd_scale),
            rng,
            low=0.0,
        )
        rec_td = _poisson(p.get("rec_td_per_target", 0.055) * targets * scor, rng)
        out.update(
            rec=rec,
            rec_yd=rec_yd,
            rec_td=rec_td,
            fumble_lost=_poisson(np.full(n_sims, 0.05), rng),
            two_pt=_poisson(np.full(n_sims, 0.01), rng),
        )
        return out

    if "DST" in pos:
        out.update(
            dst_sack=_poisson(np.full(n_sims, p.get("dst_sack", 2.4)), rng),
            dst_int=_poisson(np.full(n_sims, p.get("dst_int", 0.85)), rng),
            dst_fum_rec=_poisson(np.full(n_sims, p.get("dst_fum_rec", 0.7)), rng),
            dst_ret_td=_poisson(np.full(n_sims, p.get("dst_ret_td", 0.12)), rng),
            dst_safety=_poisson(np.full(n_sims, 0.05), rng),
            dst_blocked_kick=_poisson(np.full(n_sims, 0.08), rng),
            dst_pa=np.clip(
                _normal(
                    np.full(n_sims, p.get("dst_pa", 22.0)),
                    np.full(n_sims, 9.0 * cfg.efficiency_sd_scale),
                    rng,
                    low=0.0,
                ),
                0.0,
                None,
            ),
        )
        return out

    return {}


def _nba_stat_lines(
    player: PlayerProjection,
    latents: Dict[str, np.ndarray],
    n_sims: int,
    rng: np.random.Generator,
    cfg: SimulationConfig,
) -> Dict[str, np.ndarray]:
    """NBA stat-line simulation: minutes first, then per-minute rates.

    "Minutes come first. No minutes, no production." (source id ``sk_nba_projections``,
    claim c10). The shared team factor is deliberately small, because Stokastic states that
    in basketball player-to-player correlation barely matters (claim c11).
    """
    p = player.props
    pace = latents["nba_pace"]
    proj_min = p.get("minutes", 24.0)
    min_sd = p.get("minutes_sd", max(2.0, proj_min * 0.18)) * cfg.minutes_sd_scale
    minutes = _normal(
        np.full(n_sims, proj_min) * pace,
        np.full(n_sims, min_sd),
        rng,
        low=0.0,
        high=48.0,
    )
    scale = cfg.volume_sd_scale

    def rate(key: str, fallback: float, sd_fraction: float) -> np.ndarray:
        mean = np.full(n_sims, p.get(key, fallback))
        sd = np.full(n_sims, max(1e-6, p.get(key, fallback) * sd_fraction) * scale)
        return _normal(mean, sd, rng, low=0.0)

    return {
        "pts": _poisson(rate("pts_per_min", 0.55, 0.28) * minutes, rng),
        "reb": _poisson(rate("reb_per_min", 0.20, 0.35) * minutes, rng),
        "ast": _poisson(rate("ast_per_min", 0.16, 0.40) * minutes, rng),
        "fg3m": _poisson(rate("fg3m_per_min", 0.07, 0.45) * minutes, rng),
        "stl": _poisson(rate("stl_per_min", 0.035, 0.55) * minutes, rng),
        "blk": _poisson(rate("blk_per_min", 0.025, 0.60) * minutes, rng),
        "to": _poisson(rate("to_per_min", 0.075, 0.45) * minutes, rng),
        "minutes": minutes,
    }


def _mlb_hitter_stat_lines(
    player: PlayerProjection,
    latents: Dict[str, np.ndarray],
    n_sims: int,
    rng: np.random.Generator,
    cfg: SimulationConfig,
) -> Dict[str, np.ndarray]:
    """MLB hitter: a multinomial over plate-appearance outcomes, then runs and RBI.

    The team offence factor is shared by every hitter in the lineup, which reproduces the
    correlation that makes stacking worth something ("when a team bats around, four hitters
    cash together"). Runs and RBI are drawn with per-PA propensities that scale with the
    team's implied run environment rather than being modelled jointly at inning level - that
    limitation is recorded in LIMITATIONS.md.
    """
    p = player.props
    offence = latents["mlb_offense"]
    pa = _poisson(p.get("pa", 4.2) * (0.5 + 0.5 * offence), rng)
    pa_int = pa.astype(int)

    def prob(key: str, fallback: float, exponent: float = 0.5) -> np.ndarray:
        """Per-PA probability, nudged by the team offence factor (a hot team hits a bit more)."""
        base = np.full(n_sims, p.get(key, fallback), dtype=float)
        return np.clip(base * (offence**exponent), 1e-6, 0.6)

    p_single = prob("p_single", 0.145)
    p_double = prob("p_double", 0.045)
    p_triple = prob("p_triple", 0.004)
    p_hr = prob("p_hr", 0.035)
    p_bb = prob("p_bb", 0.085)
    p_hbp = prob("p_hbp", 0.010)
    p_out = np.clip(
        1.0 - (p_single + p_double + p_triple + p_hr + p_bb + p_hbp), 0.05, 1.0
    )

    # Per-plate-appearance multinomial draw, fully vectorised:
    # category = the number of cumulative thresholds the uniform draw exceeds.
    max_pa = int(pa_int.max()) if pa_int.size and pa_int.max() > 0 else 1
    draws = rng.random((n_sims, max_pa))
    cumulative = np.cumsum(
        np.stack([p_out, p_single, p_double, p_triple, p_hr, p_bb, p_hbp], axis=1), axis=1
    )  # [n_sims, 7]
    valid = np.arange(max_pa)[None, :] < pa_int[:, None]  # only real plate appearances count
    category = (draws[:, :, None] >= cumulative[:, None, :]).sum(axis=2)  # [n_sims, max_pa]
    counts = np.stack(
        [((category == k) & valid).sum(axis=1).astype(float) for k in range(7)]
    )  # [7, n_sims]

    hits = counts[1] + counts[2] + counts[3] + counts[4]
    on_base = hits + counts[5] + counts[6]
    # Runs and RBI propensity rises with the team's implied run environment.
    run_rate = np.clip(p.get("run_per_on_base", 0.32) * offence, 0.0, 0.8)
    rbi_rate = np.clip(p.get("rbi_per_on_base", 0.28) * offence, 0.0, 0.8)
    return {
        "single": counts[1],
        "double": counts[2],
        "triple": counts[3],
        "hr": counts[4],
        "bb": counts[5],
        "hbp": counts[6],
        "run": rng.binomial(on_base.astype(int), run_rate).astype(float),
        "rbi": rng.binomial(on_base.astype(int), rbi_rate).astype(float),
        "sb": _poisson(np.full(n_sims, p.get("sb_rate", 0.08)), rng),
    }


def _mlb_pitcher_stat_lines(
    player: PlayerProjection,
    latents: Dict[str, np.ndarray],
    n_sims: int,
    rng: np.random.Generator,
    cfg: SimulationConfig,
) -> Dict[str, np.ndarray]:
    """MLB pitcher: outs recorded, then strikeouts / baserunners / runs allowed.

    The opponent's shared offence factor is applied in reverse, which is what creates the
    negative pitcher-versus-opposing-hitters relationship the simulator needs in order to
    price a stack against the arm it is facing.
    """
    p = player.props
    opp = latents.get("mlb_offense")
    if opp is None:
        opp = np.ones(n_sims)
    outs = _poisson(np.full(n_sims, p.get("outs", 16.5)), rng)
    outs = np.minimum(outs, 27.0)
    ip = outs / 3.0
    so = _poisson(outs * np.full(n_sims, p.get("so_per_out", 0.28)), rng)
    bb_against = _poisson(
        outs * np.full(n_sims, p.get("bb_per_out", 0.085)) * (0.6 + 0.4 * opp), rng
    )
    hit_against = _poisson(
        outs * np.full(n_sims, p.get("hit_per_out", 0.28)) * (0.6 + 0.4 * opp), rng
    )
    runs = _poisson(
        outs * np.full(n_sims, p.get("run_per_out", 0.13)) * opp * cfg.efficiency_sd_scale, rng
    )
    er = np.minimum(runs, _poisson(outs * np.full(n_sims, p.get("er_per_out", 0.115)) * opp, rng))
    win_prob = np.clip(p.get("win_prob", 0.35), 0.0, 1.0)
    win = rng.binomial(1, win_prob, size=n_sims).astype(float)
    quality_start = ((ip >= 6.0) & (er <= 3.0)).astype(float)
    complete_game = (outs >= 27.0).astype(float)
    complete_game_shutout = ((outs >= 27.0) & (runs == 0)).astype(float)
    no_hitter = ((outs >= 27.0) & (hit_against == 0)).astype(float)

    return {
        "ip": ip,
        "so": so,
        "win": win,
        "er": er,
        "hit_against": hit_against,
        "bb_against": bb_against,
        "hit_batsman": _poisson(outs * np.full(n_sims, p.get("hbp_per_out", 0.01)), rng),
        "quality_start": quality_start,
        "complete_game": complete_game,
        "complete_game_shutout": complete_game_shutout,
        "no_hitter": no_hitter,
        "outs_recorded": outs,
        "runs_allowed": runs,
    }


def _latents_for_player(
    player: PlayerProjection,
    factor_table: Dict[str, Dict[str, np.ndarray]],
    n_sims: int,
    sport: str,
) -> Dict[str, np.ndarray]:
    """Team latents for this player (opponent latents where the sport needs them).

    For MLB the choice matters and is easy to get wrong: a *hitter* is driven by his own
    team's offence (that is what puts men on base in front of him), while a *pitcher* is
    driven by the offence of the team he is facing. Getting this backwards would invert the
    stack-versus-arm relationship the simulator exists to price.
    """
    team = factor_table.get(player.team, {})
    opp = factor_table.get(player.opponent, {})
    ones = np.ones(n_sims)

    if sport == "nfl":
        return {
            "team_volume": team.get("team_volume", ones),
            "team_scoring": team.get("team_scoring", ones),
        }
    if sport == "nba":
        return {"nba_pace": team.get("nba_pace", ones)}
    if sport == "mlb":
        is_pitcher = bool(set(player.positions) & {"P", "SP", "RP"})
        source = opp if is_pitcher else team
        return {"mlb_offense": source.get("mlb_offense", ones)}
    return {}


# ---------------------------------------------------------------------------
# slate-level driver
# ---------------------------------------------------------------------------
def simulate_stat_lines(
    slate: Slate,
    n_sims: int,
    rng: np.random.Generator,
    config: Optional[SimulationConfig] = None,
) -> Dict[str, Dict[str, np.ndarray]]:
    """Simulate a full slate of stat lines, keyed by player id."""
    cfg = config or SimulationConfig()
    factors = team_latent_factors(
        slate.teams(), cfg.latent_specs(slate.sport), n_sims, rng
    )
    out: Dict[str, Dict[str, np.ndarray]] = {}
    for player in slate.players:
        latents = _latents_for_player(player, factors, n_sims, slate.sport)
        if slate.sport == "nfl":
            lines = _nfl_stat_lines(player, latents, n_sims, rng, cfg)
        elif slate.sport == "nba":
            lines = _nba_stat_lines(player, latents, n_sims, rng, cfg)
        else:
            if set(player.positions) & {"P", "SP", "RP", "RP"}:
                lines = _mlb_pitcher_stat_lines(player, latents, n_sims, rng, cfg)
            else:
                lines = _mlb_hitter_stat_lines(player, latents, n_sims, rng, cfg)
        out[player.id] = lines
    return out


def simulate_fantasy_points(
    slate: Slate,
    n_sims: int,
    seed: Optional[int] = None,
    config: Optional[SimulationConfig] = None,
    site: Optional[str] = None,
) -> Tuple[np.ndarray, Dict[str, Dict[str, np.ndarray]]]:
    """Fantasy points for every player on the slate, ``[n_sims, n_players]``.

    Stat lines are scored with the official rules for ``site`` (defaults to the slate's
    site), so the same simulation can be priced for DraftKings and FanDuel without changing
    the model.
    """
    scoring_site = site or slate.site
    rng = np.random.default_rng(seed)
    stat_lines = simulate_stat_lines(slate, n_sims, rng, config)
    matrix = np.zeros((n_sims, len(slate.players)))
    for idx, player in enumerate(slate.players):
        lines = stat_lines[player.id]
        if not lines:
            continue
        allowed = applicable_stat_keys(scoring_site, slate.sport, player.positions)
        arrays = {
            k: v
            for k, v in lines.items()
            if k in allowed or k in {"complete_game", "complete_game_shutout", "no_hitter",
                                     "quality_start", "dst_pa"}
        }
        arrays = {k: v for k, v in arrays.items() if k in allowed or k == "dst_pa"}
        matrix[:, idx] = score_array(
            arrays, scoring_site, slate.sport, positions=player.positions, size=n_sims
        )
    cfg = config or SimulationConfig()
    if cfg.target_teammate_correlation > 0:
        matrix = apply_teammate_correlation(
            matrix,
            [player.team for player in slate.players],
            target=cfg.target_teammate_correlation,
            rng=rng,
        )
    return matrix, stat_lines


def apply_teammate_correlation(
    matrix: np.ndarray,
    teams: Sequence[str],
    target: float,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Re-shape each player's variance into a shared team component plus a private one.

    Why this exists: the per-stat simulation already shares a team volume/scoring factor
    between teammates, but the independent noise in each stat line dominates it, so the
    measured teammate correlation came out around 0.09 - far too low for a stack to be worth
    anything. This calibration decomposes each player's z-score into the team's common
    component and the player's own component and recombines them at the target correlation:

        z_new = sqrt(rho) * z_team + sqrt(1 - rho) * z_private

    Marginals are preserved (the result is re-standardised to each player's original mean and
    standard deviation), so ceilings, floors and boom rates do not move - only the *joint*
    structure does, which is exactly what a stack is betting on. ``rho`` is a documented prior
    (see :class:`SimulationConfig`), not a measurement.
    """
    if not 0.0 <= target < 1.0:
        raise ValueError("target teammate correlation must be in [0, 1)")
    rng = rng or np.random.default_rng(0)
    out = matrix.copy()
    by_team: Dict[str, List[int]] = {}
    for index, team in enumerate(teams):
        by_team.setdefault(team, []).append(index)
    for _team, indexes in by_team.items():
        if len(indexes) < 2:
            continue
        block = matrix[:, indexes]
        mean = block.mean(axis=0)
        sd = block.std(axis=0)
        sd_safe = np.where(sd > 0, sd, 1.0)
        z = (block - mean) / sd_safe
        # team component: the average standardised deviation of the group in each simulation
        z_team = z.mean(axis=1, keepdims=True)
        z_team = (z_team - z_team.mean()) / (z_team.std() or 1.0)
        private = z - z.mean(axis=0, keepdims=True)
        private = private / np.where(private.std(axis=0) > 0, private.std(axis=0), 1.0)
        combined = np.sqrt(target) * z_team + np.sqrt(1.0 - target) * private
        # re-standardise per player so this changes the JOINT structure only: ceilings, floors
        # and boom rates are functions of the marginals and must not move
        combined_sd = combined.std(axis=0)
        combined = (combined - combined.mean(axis=0)) / np.where(combined_sd > 0, combined_sd, 1.0)
        out[:, indexes] = mean + combined * sd_safe
    return out


def load_sample_slate(name: str) -> Slate:
    """Load a bundled sample slate from ``src/data/samples``.

    Sample slates are synthetic on purpose (see each file's ``_meta``) and are labelled
    ``synthetic`` so a report can never be mistaken for a real-slate result.
    """
    path = Path(DATA_DIR) / "samples" / name
    if not path.exists():
        raise FileNotFoundError(
            f"sample slate {name!r} not found in {path.parent}. Available: "
            f"{sorted(p.name for p in path.parent.glob('*.json'))}"
        )
    return Slate.load(path)
