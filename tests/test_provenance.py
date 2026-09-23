"""Provenance tests: the repo must not be able to cite something it never declared."""
import json
from pathlib import Path

import pytest

from src.stokengineer.provenance import Registry, read_payload, write_json_with_provenance


def test_registry_is_internally_sound():
    assert Registry().validate() == []


def test_unknown_source_id_raises():
    with pytest.raises(KeyError):
        Registry().get("definitely_not_a_source")


def test_every_claim_has_a_quote_and_a_declared_source():
    registry = Registry()
    claims = registry.claims
    assert claims, "claim ledger is empty"
    for claim in claims:
        assert claim["source_id"] in {s.id for s in registry.sources}
        assert claim["quote"].strip()
        assert claim["status"] in {"verified", "flagged", "not_verified"}


def test_flagged_claims_explain_themselves():
    for claim in Registry().claims:
        if claim["status"] == "flagged":
            assert claim.get("flag"), claim["id"]


def test_unverified_status_is_explicit_not_silent():
    """Anything we could not verify must be labelled, not quietly omitted."""
    unverified = [c for c in Registry().claims if c["status"] == "not_verified"]
    assert unverified, "expected at least one explicitly unverified item (undisclosed internals)"
    for claim in unverified:
        assert claim.get("flag")


def test_envelope_round_trip(tmp_path: Path):
    registry = Registry()
    path = tmp_path / "report.json"
    write_json_with_provenance(
        path, {"hello": 1}, registry=registry, source_ids=["dk_rules_nfl"], command="test"
    )
    data = json.loads(path.read_text())
    assert data["_provenance"]["sources"][0]["id"] == "dk_rules_nfl"
    assert data["_provenance"]["payload_sha256"]
    assert read_payload(path) == {"hello": 1}


def test_write_refuses_undeclared_source(tmp_path: Path):
    with pytest.raises(KeyError):
        write_json_with_provenance(
            tmp_path / "x.json", {"a": 1}, registry=Registry(), source_ids=["nope"]
        )
