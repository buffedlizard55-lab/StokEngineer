"""Provenance: the anti-hallucination layer.

Two job:

1. Load ``src/data/sources_verified.json`` and refuse to hand out a source id that is not
   declared there.
2. Record, next to every artefact the engine writes, exactly which sources and which
   command produced it, plus a SHA-256 of the payload.

``Registry`` is deliberately strict: a typo in a source id raises instead of silently
producing an unsourced number.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from . import DATA_DIR


def utc_now() -> str:
    """ISO-8601 UTC timestamp, second resolution."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


@dataclass(frozen=True)
class Source:
    """One external source, exactly as declared in sources_verified.json."""

    id: str
    url: str
    title: str
    publisher: str
    what_it_provides: str
    licence_or_terms: str
    free: bool
    key_required: bool
    official: bool
    verification: str

    @property
    def is_officially_verified(self) -> bool:
        return self.verification == "fetched_live"


SPORT_SOURCE_HINTS = {
    "nfl": ("nflverse", "espn", "dk", "draftkings", "stokastic"),
    "nba": ("nba_api", "nba", "espn", "dk", "stokastic"),
    "mlb": ("mlb", "statsapi", "espn", "dk", "stokastic", "pybaseball"),
    "nhl": ("nhl", "espn", "dk", "stokastic"),
}


class Registry:
    """Read-only view over the source registry and the claim ledger."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._sources_raw = json.loads((self.data_dir / "sources_verified.json").read_text())
        self._claims_raw = json.loads((self.data_dir / "claims.json").read_text())
        self._by_id: Dict[str, Source] = {}
        for entry in self._sources_raw.get("sources", []):
            self._by_id[entry["id"]] = Source(
                id=entry["id"],
                url=entry["url"],
                title=entry.get("title", ""),
                publisher=entry.get("publisher", ""),
                what_it_provides=entry.get("what_it_provides", ""),
                licence_or_terms=entry.get("licence_or_terms", ""),
                free=bool(entry.get("free", False)),
                key_required=bool(entry.get("key_required", False)),
                official=bool(entry.get("official", False)),
                verification=entry.get("verification", "unknown"),
            )

    # -- sources -----------------------------------------------------------------
    @property
    def sources(self) -> List[Source]:
        return list(self._by_id.values())

    def get(self, source_id: str) -> Source:
        try:
            return self._by_id[source_id]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(
                f"Unknown source id {source_id!r}. Every externally sourced number must be "
                f"declared in src/data/sources_verified.json first."
            ) from exc

    @property
    def raw(self) -> Mapping[str, Any]:
        """The registry file as written (used by the site builder for review-only sections)."""
        return self._sources_raw

    def urls(self) -> List[str]:
        return sorted({s.url for s in self.sources})

    def by_verification(self, method: str) -> List[Source]:
        return [s for s in self.sources if s.verification == method]

    # -- claims ------------------------------------------------------------------
    @property
    def claims(self) -> List[Mapping[str, Any]]:
        return list(self._claims_raw.get("claims", []))

    def claims_for(self, source_id: str) -> List[Mapping[str, Any]]:
        return [c for c in self.claims if c.get("source_id") == source_id]

    def source_ids_for_sport(self, sport: str) -> List[str]:
        """Registry ids plausibly behind a report for this sport.

        Deliberately conservative and only used to *label* reports: every id returned is one
        that exists in the registry, and a report that used a specific source names it
        explicitly instead of relying on this hint list.
        """
        hints = SPORT_SOURCE_HINTS.get(sport.lower(), ())
        return [
            source.id
            for source in self.sources
            if any(hint in source.id.lower() or hint in (source.title or "").lower() for hint in hints)
        ] or [source.id for source in self.sources]

    def validate(self) -> List[str]:
        """Return a list of problems. Empty list means the registry is internally sound.

        Checks performed:
          * every source has a unique id, an https URL and the required fields;
          * every claim points at a declared source id;
          * every claim in status ``verified`` quotes text;
          * flagged claims carry a ``flag`` explaining the caveat.
        """
        problems: List[str] = []
        seen: set[str] = set()
        required = (
            "id",
            "url",
            "title",
            "publisher",
            "what_it_provides",
            "licence_or_terms",
            "verification",
        )
        for entry in self._sources_raw.get("sources", []):
            sid = entry.get("id", "<missing id>")
            if sid in seen:
                problems.append(f"duplicate source id: {sid}")
            seen.add(sid)
            for key in required:
                if not entry.get(key):
                    problems.append(f"source {sid}: missing {key}")
            url = entry.get("url", "")
            if not url.startswith("https://"):
                problems.append(f"source {sid}: url is not https ({url!r})")
            if entry.get("verification") not in {"fetched_live", "github_api", "carried_over"}:
                problems.append(
                    f"source {sid}: verification must be one of fetched_live / github_api / "
                    f"carried_over (got {entry.get('verification')!r})"
                )
            if "official" not in entry:
                problems.append(f"source {sid}: missing official flag")
        for claim in self.claims:
            cid = claim.get("id", "<missing id>")
            source_id = claim.get("source_id")
            if source_id not in self._by_id:
                problems.append(f"claim {cid}: source_id {source_id!r} is not declared")
            if claim.get("status") == "verified" and not claim.get("quote"):
                problems.append(f"claim {cid}: status verified but no quote")
            if claim.get("status") == "flagged" and not claim.get("flag"):
                problems.append(f"claim {cid}: status flagged but no flag text")
        return problems


def environment_fingerprint() -> Dict[str, str]:
    """What produced this artefact. Recorded in every report."""
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "generated_at_utc": utc_now(),
    }


def write_json_with_provenance(
    path: Path,
    payload: Any,
    *,
    registry: Optional[Registry] = None,
    source_ids: Sequence[str] = (),
    command: str = "",
    notes: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Write ``payload`` to ``path`` wrapped in provenance metadata.

    ``source_ids`` must all exist in the registry - this is what keeps unsourced numbers
    out of published artefacts.
    """
    reg = registry or Registry()
    refs = []
    for sid in source_ids:
        src = reg.get(sid)
        refs.append({"id": src.id, "url": src.url, "publisher": src.publisher, "title": src.title})

    body = json.dumps(payload, indent=2, sort_keys=True, default=str)
    envelope = {
        "_provenance": {
            **environment_fingerprint(),
            "command": command,
            "sources": refs,
            "notes": list(notes or []),
            "payload_sha256": sha256_text(body),
            "engine_version": _engine_version(),
        },
        "payload": payload,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True, default=str) + "\n")
    return envelope


def _engine_version() -> str:
    from . import __version__

    return __version__


def read_payload(path: Path) -> Any:
    """Read an envelope written by :func:`write_json_with_provenance` (or a plain JSON file)."""
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "_provenance" in data and "payload" in data:
        return data["payload"]
    return data
