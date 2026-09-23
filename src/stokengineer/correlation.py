"""Correlation utilities.

Two distinct things live here, and keeping them apart matters:

1. **Empirical correlation** - :func:`correlation_from_observations` computes the real
   correlation of players' fantasy scores from historical panel data (e.g. nflverse
   player_stats, source id ``nflverse_player_stats_asset``). This is how we check the
   simulator instead of asserting a made-up number.

2. **Structural correlation** - :func:`team_latent_factors` draws the shared team-level
   factors that the models multiply through a team's players. Teammates end up correlated
   because they share the same draw, which is exactly how Stokastic describes its own
   simulator ("correlations hold ... the sims reward correlation instead of needing a rule
   for it" - source id ``sk_nfl_review``).

The previous build of this repo used a hand-written matrix (0.6 QB-WR, 0.15 bring-back,
...). Those numbers were never sourced, so they are gone. A correlation number in this
project now either comes out of data or out of a documented prior with a test attached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# empirical
# ---------------------------------------------------------------------------
def correlation_from_observations(
    scores: np.ndarray,
    min_observations: int = 8,
) -> Tuple[np.ndarray, np.ndarray]:
    """Correlation matrix plus the pairwise overlap counts behind each entry.

    ``scores`` is ``[n_observations, n_players]`` (e.g. one row per team-game, columns are
    players). Missing values are allowed and are passed as ``np.nan``: ``np.corrcoef``
    cannot do pairwise-complete correlation, so it is implemented here directly.

    Returns ``(corr, counts)`` where ``corr[i, j]`` is the Pearson correlation over the rows
    where both i and j are present, and ``counts[i, j]`` is how many such rows existed. Any
    pair with fewer than ``min_observations`` shared rows is returned as ``np.nan`` rather
    than as a noisy number.
    """
    arr = np.asarray(scores, dtype=float)
    if arr.ndim != 2:
        raise ValueError("scores must be a 2-D array [n_observations, n_players]")
    n_obs, n_players = arr.shape
    corr = np.full((n_players, n_players), np.nan)
    counts = np.zeros((n_players, n_players), dtype=int)

    for i in range(n_players):
        corr[i, i] = 1.0
        counts[i, i] = int(np.sum(~np.isnan(arr[:, i])))
        for j in range(i + 1, n_players):
            mask = ~np.isnan(arr[:, i]) & ~np.isnan(arr[:, j])
            n = int(mask.sum())
            counts[i, j] = counts[j, i] = n
            if n < min_observations:
                continue
            x, y = arr[mask, i], arr[mask, j]
            sx, sy = x.std(), y.std()
            if sx == 0 or sy == 0:
                continue
            corr[i, j] = corr[j, i] = float(np.corrcoef(x, y)[0, 1])
    return corr, counts


def teammate_correlation_summary(
    scores: np.ndarray,
    teams: Sequence[str],
    positions: Optional[Sequence[str]] = None,
) -> Dict[str, float]:
    """Average realised correlation between teammates vs non-teammates.

    ``teams`` and ``positions`` are aligned with the columns of ``scores``. The result is a
    check on the simulator: teammates should correlate more than the rest of the field once
    the shared team factor is switched on.
    """
    corr, counts = correlation_from_observations(scores)
    same, other = [], []
    n = len(teams)
    for i in range(n):
        for j in range(i + 1, n):
            if np.isnan(corr[i, j]) or counts[i, j] == 0:
                continue
            if positions is not None and positions[i] == "DST" and positions[j] == "DST":
                continue
            (same if teams[i] == teams[j] else other).append(float(corr[i, j]))
    return {
        "n_teammate_pairs": float(len(same)),
        "n_other_pairs": float(len(other)),
        "mean_teammate_corr": float(np.mean(same)) if same else float("nan"),
        "mean_other_corr": float(np.mean(other)) if other else float("nan"),
    }


# ---------------------------------------------------------------------------
# structural
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LatentSpec:
    """A shared team-level draw, documented as a prior."""

    name: str
    sigma: float
    description: str

    def draw(self, n_sims: int, rng: np.random.Generator) -> np.ndarray:
        """Log-normal multiplicative factor with mean 1.0 and the given log-sigma."""
        mu = -0.5 * self.sigma**2  # so that E[exp(Z)] = 1
        return np.exp(rng.normal(mu, self.sigma, size=n_sims))


# The priors below are *documented priors*, not measured values. They exist so the
# simulator has a dispersion structure at all; tools/calibrate.py (and the forward-test
# workflow) re-estimate them from real data and the reports record which was used.
TEAM_VOLUME = LatentSpec(
    name="team_volume",
    sigma=0.15,
    description="Game-to-game swing in a team's offensive volume (attempts/carries/targets).",
)
TEAM_SCORING = LatentSpec(
    name="team_scoring",
    sigma=0.25,
    description="Game-to-game swing in how efficiently a team converts volume into touchdowns.",
)
NBA_PACE = LatentSpec(
    name="nba_pace",
    sigma=0.06,
    description=(
        "NBA team-level pace/usage swing. Small on purpose: Stokastic states that in "
        "basketball player-to-player correlation barely matters (source id sk_nba_boom_bust)."
    ),
)
MLB_OFFENSE = LatentSpec(
    name="mlb_offense",
    sigma=0.30,
    description="Game-to-game swing in a team's run scoring, which is what correlates "
    "teammates in baseball (a team that bats around takes four hitters with it).",
)


def team_latent_factors(
    teams: Iterable[str],
    specs: Sequence[LatentSpec],
    n_sims: int,
    rng: np.random.Generator,
) -> Dict[str, Dict[str, np.ndarray]]:
    """One draw per team per latent per simulation.

    Deterministic given ``rng``: every player on a team reads the same arrays, which is what
    creates teammate correlation without a hand-written correlation matrix.
    """
    out: Dict[str, Dict[str, np.ndarray]] = {}
    for team in sorted(set(teams)):
        out[str(team)] = {spec.name: spec.draw(n_sims, rng) for spec in specs}
    return out


def nearest_psd(matrix: np.ndarray) -> np.ndarray:
    """Project a symmetric matrix onto the nearest positive semi-definite correlation matrix.

    Used only for imported/external correlation matrices (e.g. an empirical matrix from a
    thin sample, or a user-supplied one): a covariance built from a non-PSD correlation
    matrix would make ``np.random.multivariate_normal`` produce nonsense silently.
    """
    arr = np.asarray(matrix, dtype=float)
    sym = (arr + arr.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(sym)
    eigvals = np.clip(eigvals, 1e-10, None)
    psd = (eigvecs * eigvals) @ eigvecs.T
    d = np.sqrt(np.clip(np.diag(psd), 1e-12, None))
    psd = psd / np.outer(d, d)
    np.fill_diagonal(psd, 1.0)
    return psd


def sample_correlated_scores(
    means: np.ndarray,
    stddevs: np.ndarray,
    correlation: np.ndarray,
    n_sims: int,
    rng: np.random.Generator,
    floor: Optional[float] = 0.0,
) -> np.ndarray:
    """Gaussian-copula-free multivariate normal sampler for external correlation input.

    The models in :mod:`stokengineer.models` usually generate correlation structurally. This
    function exists for the paths that need an explicit matrix: ``empirical`` (measured from
    history) or ``user`` (supplied by the person running the slate). Both are recorded in the
    report so a reader always knows which source of correlation produced a number.
    """
    means = np.asarray(means, dtype=float)
    stddevs = np.asarray(stddevs, dtype=float)
    corr = nearest_psd(correlation)
    cov = corr * np.outer(stddevs, stddevs)
    cov = cov + np.eye(len(means)) * 1e-10
    draws = rng.multivariate_normal(means, cov, size=n_sims)
    if floor is not None:
        draws = np.maximum(draws, floor)
    return draws
