"""Free, keyless data ingest with provenance.

Every fetcher here points at a source declared in ``src/data/sources_verified.json`` and
writes the raw response to ``data/cache/`` next to a ``.meta.json`` sidecar recording the URL,
status, byte count, SHA-256 and UTC timestamp. Reports quote those sidecars, so a number can
always be traced back to the exact bytes it came from.

Design constraints agreed for this project: free, no premium tiers, no trials, no
subscriptions, and no API keys required. That rules out the paid odds feeds and premium stats
providers, and it is why the keyless ESPN scoreboard (odds) and the official MLB Stats API are
the defaults. Optional key-based sources are listed in the registry but never called by the
default pipeline.

Sandboxes without egress raise :class:`OfflineError` with the URL that failed, instead of
returning empty data that would quietly become a zero projection.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import CACHE_DIR
from .provenance import Registry, sha256_bytes, utc_now
from .rules import implied_team_total

USER_AGENT = "StokEngineer/0.4 (+https://github.com/buffedlizard55-lab/StokEngineer) research"
DEFAULT_TIMEOUT = 25
DEFAULT_RETRIES = 3


class OfflineError(RuntimeError):
    """Raised when the sandbox/CI cannot reach an external source."""


@dataclass
class FetchRecord:
    """Provenance for one HTTP fetch."""

    url: str
    source_id: str
    status: int
    bytes: int
    sha256: str
    fetched_at_utc: str
    cached_path: str
    from_cache: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Fetcher:
    """Minimal HTTP client with caching, retries and provenance."""

    cache_dir: Path = field(default_factory=lambda: Path(CACHE_DIR))
    timeout: int = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES
    records: List[FetchRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_paths(self, source_id: str, suffix: str) -> Tuple[Path, Path]:
        return (
            self.cache_dir / f"{source_id}{suffix}",
            self.cache_dir / f"{source_id}{suffix}.meta.json",
        )

    def get_bytes(
        self, url: str, source_id: str, suffix: str = ".bin", use_cache: bool = True
    ) -> bytes:
        payload_path, meta_path = self._cache_paths(source_id, suffix)
        if use_cache and payload_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self.records.append(FetchRecord(**{**meta, "from_cache": True}))
            return payload_path.read_bytes()

        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
        )
        last_error: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = response.read()
                    status = response.getcode()
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                last_error = exc
                if attempt == self.retries:
                    raise OfflineError(
                        f"could not fetch {url} (source id {source_id!r}) after "
                        f"{self.retries} attempts: {exc}. This environment appears to have no "
                        f"outbound network; run the ingest step in GitHub Actions "
                        f"(.github/workflows/forward-test.yml) or supply a CSV instead."
                    ) from exc
                time.sleep(1.5 * attempt)
        else:  # pragma: no cover - loop always breaks or raises
            raise OfflineError(str(last_error))

        record = FetchRecord(
            url=url,
            source_id=source_id,
            status=status,
            bytes=len(body),
            sha256=sha256_bytes(body),
            fetched_at_utc=utc_now(),
            cached_path=str(payload_path),
        )
        payload_path.write_bytes(body)
        meta_path.write_text(json.dumps(record.as_dict(), indent=2))
        self.records.append(record)
        return body

    def get_json(
        self, url: str, source_id: str, suffix: str = ".json", use_cache: bool = True
    ) -> Any:
        return json.loads(
            self.get_bytes(url, source_id, suffix=suffix, use_cache=use_cache).decode("utf-8")
        )

    def provenance(self) -> List[Dict[str, Any]]:
        return [record.as_dict() for record in self.records]


# ---------------------------------------------------------------------------
# MLB Stats API (official, keyless) - source id mlb_statsapi
# ---------------------------------------------------------------------------
MLB_BASE = "https://statsapi.mlb.com/api/v1"


def mlb_schedule(fetcher: Fetcher, date: str) -> Dict[str, Any]:
    url = f"{MLB_BASE}/schedule?sportId=1&date={date}&hydrate=team,linescore"
    return fetcher.get_json(url, source_id="mlb_schedule", suffix=f"-{date}.json")


def mlb_final_games(schedule: Mapping[str, Any]) -> List[Dict[str, Any]]:
    games: List[Dict[str, Any]] = []
    for block in schedule.get("dates", []):
        for game in block.get("games", []):
            state = (game.get("status") or {}).get("abstractGameState")
            if state == "Final":
                games.append(game)
    return games


def mlb_boxscore(fetcher: Fetcher, game_pk: int) -> Dict[str, Any]:
    url = f"{MLB_BASE}/game/{game_pk}/boxscore"
    return fetcher.get_json(url, source_id="mlb_boxscore", suffix=f"-{game_pk}.json")


def mlb_season_stats(fetcher: Fetcher, season: int, group: str = "hitting") -> Dict[str, Any]:
    """League-wide season stats in one request (group='hitting' or 'pitching')."""
    url = (
        f"{MLB_BASE}/stats?stats=season&group={group}&sportId=1&season={season}"
        f"&limit=2000&playerPool=ALL"
    )
    return fetcher.get_json(url, source_id=f"mlb_season_stats_{group}", suffix=f"-{season}.json")


def boxscore_stat_lines(boxscore: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Per-player actual stat lines from a box score, in this engine's stat-key vocabulary.

    Mapping is explicit (not a loop over every field) so that a change in the feed cannot
    silently alter which stats get scored.
    """
    rows: List[Dict[str, Any]] = []
    for side in ("away", "home"):
        team_block = boxscore["teams"][side]
        team_abbr = team_block["team"].get("abbreviation") or team_block["team"]["name"]
        other = "home" if side == "away" else "away"
        for key, entry in team_block.get("players", {}).items():
            person = entry.get("person", {})
            stats = entry.get("stats", {})
            position = (entry.get("position") or {}).get("abbreviation", "")
            batting = stats.get("batting") or {}
            pitching = stats.get("pitching") or {}
            if not batting and not pitching:
                continue
            row: Dict[str, Any] = {
                "player_id": person.get("id"),
                "name": person.get("fullName"),
                "team": team_abbr,
                "opponent": boxscore["teams"][other]["team"].get("abbreviation", ""),
                "position": position,
                "batting": batting,
                "pitching": pitching,
                "stats": {},
            }
            # plate appearances and outs are context for the forward test (removing the
            # predicted game from season totals). They are kept out of ``stats`` on purpose:
            # ``stats`` is scored by the rules engine, which rejects unknown keys.
            plate_appearances = (
                int(batting.get("plateAppearances", 0) or 0)
                or int(batting.get("atBats", 0) or 0)
                + int(batting.get("baseOnBalls", 0) or 0)
                + int(batting.get("hitByPitch", 0) or 0)
                + int(batting.get("sacFlies", 0) or 0)
                + int(batting.get("sacBunts", 0) or 0)
            )
            row["game_context"] = {
                "pa": float(plate_appearances) if batting else 0.0,
                "outs": float(int(pitching.get("outs", 0))) if pitching else 0.0,
            }
            if batting:
                singles = (
                    int(batting.get("hits", 0))
                    - int(batting.get("doubles", 0))
                    - int(batting.get("triples", 0))
                    - int(batting.get("homeRuns", 0))
                )
                row["stats"] = {
                    "single": singles,
                    "double": int(batting.get("doubles", 0)),
                    "triple": int(batting.get("triples", 0)),
                    "hr": int(batting.get("homeRuns", 0)),
                    "rbi": int(batting.get("rbi", 0)),
                    "run": int(batting.get("runs", 0)),
                    "bb": int(batting.get("baseOnBalls", 0)),
                    "hbp": int(batting.get("hitByPitch", 0)),
                    "sb": int(batting.get("stolenBases", 0)),
                }
            if pitching:
                outs = int(pitching.get("outs", 0))
                row["stats"] = {
                    "ip": outs / 3.0,
                    "so": int(pitching.get("strikeOuts", 0)),
                    "win": int(pitching.get("wins", 0)),
                    "er": int(pitching.get("earnedRuns", 0)),
                    "hit_against": int(pitching.get("hits", 0)),
                    "bb_against": int(pitching.get("baseOnBalls", 0)),
                    "hit_batsman": int(pitching.get("hitBatsmen", 0)),
                    "complete_game": float(pitching.get("completeGames", 0) or 0),
                    "complete_game_shutout": float(
                        pitching.get("shutouts", 0) or 0
                    ),
                    "no_hitter": 0.0,  # not exposed directly; derived below when applicable
                }
                # a shutout with zero hits allowed in a complete game is a no-hitter
                if (
                    float(row["stats"]["complete_game_shutout"]) > 0
                    and int(pitching.get("hits", 0)) == 0
                ):
                    row["stats"]["no_hitter"] = 1.0
            rows.append(row)
    return rows


def season_rates(
    season_stats: Mapping[str, Any], group: str = "hitting"
) -> Dict[int, Dict[str, float]]:
    """Per-player season rates, used to build model inputs for a forward test.

    Returns ``{player_id: {...rates...}}``. For hitters the rates are per plate appearance
    (single/double/triple/HR/BB/HBP/out), for pitchers they are per out recorded. Plate
    appearances are derived as ``plateAppearances`` when present.
    """
    out: Dict[int, Dict[str, float]] = {}
    for split in season_stats.get("stats", [{}])[0].get("splits", []):
        stat = split.get("stat", {})
        pid = (split.get("player") or {}).get("id")
        if pid is None:
            continue
        if group == "hitting":
            pa = float(stat.get("plateAppearances", 0) or 0)
            if pa <= 0:
                continue
            hits = float(stat.get("hits", 0) or 0)
            doubles = float(stat.get("doubles", 0) or 0)
            triples = float(stat.get("triples", 0) or 0)
            home_runs = float(stat.get("homeRuns", 0) or 0)
            bb = float(stat.get("baseOnBalls", 0) or 0)
            hbp = float(stat.get("hitByPitch", 0) or 0)
            out[pid] = {
                "pa": pa,
                # totals (needed to remove the predicted game before computing rates)
                "hits_total": hits,
                "doubles_total": doubles,
                "triples_total": triples,
                "hr_total": home_runs,
                "bb_total": bb,
                "hbp_total": hbp,
                "runs_total": float(stat.get("runs", 0) or 0),
                "rbi_total": float(stat.get("rbi", 0) or 0),
                "sb_total": float(stat.get("stolenBases", 0) or 0),
                "p_single": max(0.0, (hits - doubles - triples - home_runs) / pa),
                "p_double": doubles / pa,
                "p_triple": triples / pa,
                "p_hr": home_runs / pa,
                "p_bb": bb / pa,
                "p_hbp": hbp / pa,
                "run_per_on_base": float(stat.get("runs", 0) or 0) / max(1.0, hits + bb + hbp),
                "rbi_per_on_base": float(stat.get("rbi", 0) or 0) / max(1.0, hits + bb + hbp),
                "sb_rate": float(stat.get("stolenBases", 0) or 0)
                / max(1.0, float(stat.get("gamesPlayed", 1) or 1)),
                "games": float(stat.get("gamesPlayed", 0) or 0),
                "plate_appearances": pa,
                "team_id": (split.get("team") or {}).get("id"),
                "name": (split.get("player") or {}).get("fullName", ""),
            }
        else:
            outs = float(stat.get("outs", 0) or 0)
            if outs <= 0:
                continue
            games_played = max(1.0, float(stat.get("gamesPlayed", 1) or 1))
            out[pid] = {
                # outs per appearance: what a single-game start projection needs
                "outs": outs / games_played,
                "so_per_out": float(stat.get("strikeOuts", 0) or 0) / outs,
                "bb_per_out": float(stat.get("baseOnBalls", 0) or 0) / outs,
                "hit_per_out": float(stat.get("hits", 0) or 0) / outs,
                "run_per_out": float(stat.get("runs", 0) or 0) / outs,
                "er_per_out": float(stat.get("earnedRuns", 0) or 0) / outs,
                "hbp_per_out": float(stat.get("hitBatsmen", 0) or 0) / outs,
                "hits_total": float(stat.get("hits", 0) or 0),
                "bb_total": float(stat.get("baseOnBalls", 0) or 0),
                "so_total": float(stat.get("strikeOuts", 0) or 0),
                "er_total": float(stat.get("earnedRuns", 0) or 0),
                "runs_total": float(stat.get("runs", 0) or 0),
                "hbp_total": float(stat.get("hitBatsmen", 0) or 0),
                "wins_total": float(stat.get("wins", 0) or 0),
                "games": float(stat.get("gamesPlayed", 0) or 0),
                "outs_total": outs,
                "team_id": (split.get("team") or {}).get("id"),
                "name": (split.get("player") or {}).get("fullName", ""),
            }
    return out


def subtract_game_from_season(
    season_row: Mapping[str, float], game_context: Mapping[str, float]
) -> Dict[str, float]:
    """Season-to-date totals with the predicted game removed - no look-ahead.

    Using full-season rates to "predict" a game that is already inside the season leaks the
    answer, and on a season-to-date feed it leaks *almost the entire* answer late in the year.
    This returns the totals and per-game rates a modeller would have had before first pitch.

    ``game_context`` carries the game's own plate appearances / outs recorded (see
    :func:`boxscore_stat_lines`).
    """
    prior = dict(season_row)
    games = float(prior.get("games", 0) or 0)
    games_before = max(0.0, games - 1.0)
    prior["games_before"] = games_before
    if "hits_total" in prior:  # hitter row
        pa_before = max(0.0, float(prior.get("pa", 0.0)) - float(game_context.get("pa", 0.0)))
        prior["pa_before"] = pa_before
        prior["pa_per_game_before"] = pa_before / games_before if games_before else 0.0
    if "outs_total" in prior:  # pitcher row
        outs_before = max(
            0.0, float(prior.get("outs_total", 0.0)) - float(game_context.get("outs", 0.0))
        )
        prior["outs_before"] = outs_before
        prior["outs_per_game_before"] = outs_before / games_before if games_before else 0.0
    return prior


def forward_test_props(
    rate_row: Mapping[str, float],
    game_context: Mapping[str, float],
    is_pitcher: bool,
    n_games_floor: float = 1.0,
) -> Dict[str, float]:
    """Model inputs for one player that exclude the game being predicted.

    Every rate is recomputed from season totals minus that game, which is the only way the
    resulting accuracy number means anything: predicting a game using a season average that
    already contains the game is a leak, not a test (see LIMITATIONS.md).
    """
    games_before = max(
        n_games_floor, float(rate_row.get("games", 0.0) or 0.0) - 1.0
    )
    context = dict(game_context or {})
    if is_pitcher:
        outs_total = max(0.0, float(rate_row.get("outs_total", 0.0)) - float(context.get("outs", 0.0)))
        wins_total = float(rate_row.get("wins_total", 0.0) or 0.0)
        props = {
            "outs": outs_total / games_before,
            "so_per_out": float(rate_row.get("so_per_out", 0.28)),
            "bb_per_out": float(rate_row.get("bb_per_out", 0.085)),
            "hit_per_out": float(rate_row.get("hit_per_out", 0.28)),
            "run_per_out": float(rate_row.get("run_per_out", 0.13)),
            "er_per_out": float(rate_row.get("er_per_out", 0.115)),
            "hbp_per_out": float(rate_row.get("hbp_per_out", 0.01)),
            # a pitcher's win rate is its own history here; the sample is small and noisy, so
            # it is shrunk halfway to the 0.35 league prior. Documented, not hidden.
            "win_prob": 0.5 * (wins_total / max(games_before, 1.0)) + 0.5 * 0.35,
            "games_before": games_before,
        }
        # rates computed over outs are re-derived from before-the-game totals where possible
        so_total = max(0.0, float(rate_row.get("so_total", 0.0)) - float(context.get("so", 0.0)))
        if outs_total > 0 and so_total > 0:
            props["so_per_out"] = so_total / outs_total
        return props

    pa_total = float(rate_row.get("pa", 0.0) or 0.0)
    pa_before = max(0.0, pa_total - float(context.get("pa", 0.0)))
    pa_basis = max(1.0, pa_before)
    hits = max(0.0, float(rate_row.get("hits_total", 0.0)) - float(context.get("hits", 0.0)))
    doubles = max(0.0, float(rate_row.get("doubles_total", 0.0)) - float(context.get("doubles", 0.0)))
    triples = max(0.0, float(rate_row.get("triples_total", 0.0)) - float(context.get("triples", 0.0)))
    homers = max(0.0, float(rate_row.get("hr_total", 0.0)) - float(context.get("hr", 0.0)))
    walks = max(0.0, float(rate_row.get("bb_total", 0.0)) - float(context.get("bb", 0.0)))
    hit_by_pitch = max(0.0, float(rate_row.get("hbp_total", 0.0)) - float(context.get("hbp", 0.0)))
    singles = max(0.0, hits - doubles - triples - homers)
    runs = max(0.0, float(rate_row.get("runs_total", 0.0)) - float(context.get("run", 0.0)))
    rbi = max(0.0, float(rate_row.get("rbi_total", 0.0)) - float(context.get("rbi", 0.0)))
    steals = max(0.0, float(rate_row.get("sb_total", 0.0)) - float(context.get("sb", 0.0)))
    on_base = max(1.0, hits + walks + hit_by_pitch)
    return {
        "pa": pa_before / games_before if games_before else 4.2,
        "p_single": singles / pa_basis,
        "p_double": doubles / pa_basis,
        "p_triple": triples / pa_basis,
        "p_hr": homers / pa_basis,
        "p_bb": walks / pa_basis,
        "p_hbp": hit_by_pitch / pa_basis,
        "run_per_on_base": runs / on_base,
        "rbi_per_on_base": rbi / on_base,
        "sb_rate": steals / games_before if games_before else 0.08,
        "games_before": games_before,
    }


# ---------------------------------------------------------------------------
# nflverse (CC-BY-4.0, keyless) - source ids nflverse_*
# ---------------------------------------------------------------------------
NFLVERSE_RELEASE = "https://github.com/nflverse/nflverse-data/releases/download"


def nflverse_player_stats(fetcher: Fetcher, season: int) -> List[Dict[str, str]]:
    url = f"{NFLVERSE_RELEASE}/player_stats/player_stats_{season}.csv"
    body = fetcher.get_bytes(url, source_id="nflverse_player_stats", suffix=f"-{season}.csv")
    return list(csv.DictReader(body.decode("utf-8").splitlines()))


def nflverse_schedules(fetcher: Fetcher) -> List[Dict[str, str]]:
    url = f"{NFLVERSE_RELEASE}/schedules/games.csv"
    body = fetcher.get_bytes(url, source_id="nflverse_schedules", suffix=".csv")
    return list(csv.DictReader(body.decode("utf-8").splitlines()))


def nflverse_injuries(fetcher: Fetcher, season: int) -> List[Dict[str, str]]:
    url = f"{NFLVERSE_RELEASE}/injuries/injuries_{season}.csv"
    body = fetcher.get_bytes(url, source_id="nflverse_injuries", suffix=f"-{season}.csv")
    return list(csv.DictReader(body.decode("utf-8").splitlines()))


# ---------------------------------------------------------------------------
# ESPN scoreboard (keyless, undocumented) - source id espn_scoreboard
# ---------------------------------------------------------------------------
ESPN_SPORT_PATHS = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "mlb": "baseball/mlb",
    "nhl": "hockey/nhl",
}


def espn_scoreboard(fetcher: Fetcher, sport: str) -> Dict[str, Any]:
    path = ESPN_SPORT_PATHS.get(sport)
    if not path:
        raise ValueError(f"unsupported sport for ESPN scoreboard: {sport!r}")
    url = f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
    return fetcher.get_json(url, source_id=f"espn_scoreboard_{sport}", suffix=f"-{sport}.json")


def implied_totals_from_espn(scoreboard: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Game totals and spreads converted into implied team totals.

    ESPN publishes one spread per game, attached to the home team (negative when the home team
    is favoured) plus, on newer payloads, an explicit ``homeTeamOdds.favorite`` flag. This
    parser trusts the explicit flag when it is present and otherwise falls back to the
    documented home-team convention - it never guesses the favourite from a bare sign in a way
    that could silently hand the wrong team the larger total. The magnitude-only
    :func:`stokengineer.rules.implied_team_total` does the arithmetic (claim c23).
    """
    games: List[Dict[str, Any]] = []
    for event in scoreboard.get("events", []):
        competition = (event.get("competitions") or [{}])[0]
        odds = (competition.get("odds") or [{}])[0]
        total = odds.get("overUnder")
        spread = odds.get("spread")
        if total is None or spread is None:
            continue
        competitors = competition.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if home is None or away is None:
            continue
        explicit = (odds.get("homeTeamOdds") or {}).get("favorite")
        home_is_favourite = bool(explicit) if explicit is not None else float(spread) < 0
        favourite_total, underdog_total = implied_team_total(float(total), float(spread))
        games.append(
            {
                "event_id": event.get("id"),
                "name": event.get("name"),
                "date": event.get("date"),
                "total": float(total),
                "spread": float(spread),
                "favourite_side": "home" if home_is_favourite else "away",
                "home_team": home.get("team", {}).get("abbreviation"),
                "away_team": away.get("team", {}).get("abbreviation"),
                "home_implied_total": float(favourite_total if home_is_favourite else underdog_total),
                "away_implied_total": float(underdog_total if home_is_favourite else favourite_total),
                "source": "espn_scoreboard",
            }
        )
    return games


# ---------------------------------------------------------------------------
# CSV importers (the sanctioned, free path for salaries / ownership / results)
# ---------------------------------------------------------------------------
def _normalise(row: Mapping[str, str]) -> Dict[str, str]:
    return {(k or "").strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items()}


def import_projections_csv(path: Path | str) -> List[Dict[str, Any]]:
    """Slate file: name, team, opponent, positions (pipe separated), salary, projection, ..."""
    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            row = _normalise(raw)
            if not row.get("name"):
                continue
            positions = [
                p for p in (row.get("positions") or row.get("position") or "").replace(",", "|").split("|") if p
            ]
            props = {
                key: float(value)
                for key, value in row.items()
                if key not in {"name", "team", "opponent", "positions", "position", "salary",
                               "projection", "game_id", "notes"}
                and value not in (None, "")
                and _is_number(value)
            }
            rows.append(
                {
                    "name": row["name"],
                    "team": row.get("team", ""),
                    "opponent": row.get("opponent", ""),
                    "positions": positions,
                    "salary": float(row.get("salary") or 0),
                    "projection": float(row["projection"]) if _is_number(row.get("projection", "")) else None,
                    "game_id": row.get("game_id", ""),
                    "props": props,
                    "notes": row.get("notes", ""),
                }
            )
    if not rows:
        raise ValueError(f"{path}: no usable rows (need at least name/salary/positions)")
    return rows


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def import_actuals_csv(path: Path | str) -> Dict[str, float]:
    """Actual fantasy points per player: columns ``name`` and ``actual`` (or ``fp``/``points``)."""
    out: Dict[str, float] = {}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            row = _normalise(raw)
            value = row.get("actual") or row.get("fp") or row.get("points") or row.get("fantasy_points")
            if row.get("name") and _is_number(value or ""):
                out[row["name"]] = float(value)
    if not out:
        raise ValueError(f"{path}: no name/actual pairs found")
    return out


def import_ownership_csv(path: Path | str) -> Dict[str, float]:
    """Ownership export (e.g. downloaded from your own contest results): name + ownership %."""
    out: Dict[str, float] = {}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            row = _normalise(raw)
            value = row.get("ownership") or row.get("own") or row.get("ownership_%") or row.get("pct")
            cleaned = str(value or "").replace("%", "").replace(",", "").strip()
            if row.get("name") and _is_number(cleaned):
                out[row["name"]] = float(cleaned)
    if not out:
        raise ValueError(f"{path}: no name/ownership pairs found")
    return out


def registry_urls_for(sport: str) -> List[str]:
    """URLs the default pipeline for ``sport`` may touch. Used by tools/check_links.py."""
    registry = Registry()
    ids = ["mlb_statsapi"] if sport == "mlb" else []
    if sport == "nfl":
        ids += ["nflverse_player_stats_asset", "nflverse_schedules_asset", "nflverse_injuries_asset"]
    ids.append("espn_scoreboard")
    return [registry.get(i).url for i in ids]
