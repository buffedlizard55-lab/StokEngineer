"""Check the committed site payload against a fresh build of the same payload.

What this can and cannot guarantee, stated plainly:

* **Claims must match exactly.** The sources registry, the claim ledger, the rules tables, the
  limitations rendered from ``LIMITATIONS.md`` and the integrity status are compared byte for byte
  (ignoring only the build timestamp and revision). If any of those drifted, the site would be
  claiming something the repository no longer says - which is the failure this project exists to
  prevent, so it fails the build.
* **A live engine run cannot be reproducible to the last digit.** The demo section is the output of
  a real simulation: optimisation ties, floating-point reductions and BLAS kernels differ between
  machines, and a different tie can pick a different player. CI therefore *reports* demo drift as a
  warning (with the numbers), so a human can re-run the builder and commit the result, but it does
  not pretend the digits are portable.

Exit code 1 only when a claim-level section differs or the demo loses its structure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
COMMITTED = ROOT / "docs" / "data" / "site_data.json"

#: compared exactly (after removing volatile meta fields)
STRICT_SECTIONS = ("sources", "claims", "removed_or_downgraded", "rules", "limitations", "status")
VOLATILE = (("meta", "generated_at"), ("meta", "git_revision"))
#: the live engine run: structure is checked, digits are reported
DEMO_KEYS = ("sample", "sport", "site", "field_size", "n_sims", "payout_source")


def _strip(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.loads(json.dumps(payload))
    for section, key in VOLATILE:
        payload.get(section, {}).pop(key, None)
    payload.pop("demo", None)
    payload.pop("test_summary", None)
    return payload


def _first_difference(a: Any, b: Any, path: str = "") -> str:
    if type(a) is not type(b):
        return f"{path or '<root>'}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a:
                return f"{path}.{key}: missing from the committed payload"
            if key not in b:
                return f"{path}.{key}: missing from the freshly built payload"
            diff = _first_difference(a[key], b[key], f"{path}.{key}")
            if diff:
                return diff
        return ""
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: {len(a)} committed entries vs {len(b)} freshly built"
        for index, (left, right) in enumerate(zip(a, b)):
            diff = _first_difference(left, right, f"{path}[{index}]")
            if diff:
                return diff
        return ""
    if a != b:
        return f"{path}: committed {a!r} vs built {b!r}"
    return ""


def _check_demo(committed: List[Dict[str, Any]], built: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if len(committed) != len(built):
        errors.append(f"demo: {len(committed)} committed entries vs {len(built)} built")
        return errors, warnings
    for index, (old, new) in enumerate(zip(committed, built)):
        name = old.get("sample", f"demo[{index}]")
        for key in DEMO_KEYS:
            if old.get(key) != new.get(key):
                errors.append(f"demo[{index}] ({name}).{key}: {old.get(key)!r} vs {new.get(key)!r}")
        old_rows = {row["name"]: row for row in old.get("projection_table", [])}
        new_rows = {row["name"]: row for row in new.get("projection_table", [])}
        for player, row in old_rows.items():
            if player not in new_rows:
                errors.append(f"demo[{index}] ({name}): player {player} disappeared from the table")
            elif row["salary"] != new_rows[player]["salary"]:
                errors.append(
                    f"demo[{index}] ({name}): {player} salary {row['salary']} vs "
                    f"{new_rows[player]['salary']}"
                )
        for field, label in (
            ("roi_pct", "ROI"),
            ("cash_rate_pct", "cash rate"),
        ):
            old_values = [lineup[field] for lineup in old.get("lineups", [])]
            new_values = [lineup[field] for lineup in new.get("lineups", [])]
            if len(old_values) != len(new_values):
                errors.append(f"demo[{index}] ({name}): lineup count changed")
                continue
            drift = max(
                (abs(a - b) for a, b in zip(old_values, new_values)), default=0.0
            )
            if drift > 1e-9:
                warnings.append(
                    f"demo[{index}] ({name}): {label} drifted by up to {drift:.1f} points between "
                    f"the committed run and this one ({old_values} -> {new_values})"
                )
        old_players = [player["name"] for lineup in old.get("lineups", []) for player in lineup["players"]]
        new_players = [player["name"] for lineup in new.get("lineups", []) for player in lineup["players"]]
        if sorted(old_players) != sorted(new_players):
            warnings.append(
                f"demo[{index}] ({name}): the optimiser chose different players in this "
                "environment (optimisation ties are not portable)"
            )
    return errors, warnings


def _report(ok: bool, errors: List[str], warnings: List[str]) -> None:
    """Write the verdict next to the other reports, and annotate a GitHub Actions run.

    A failed check is only useful if the reason is readable: the run's log API is not reachable
    from every environment, so the reason is written to reports/site_data_check.json (uploaded as
    a CI artifact) and, in Actions, emitted as a check annotation.
    """
    path = ROOT / "reports" / "site_data_check.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"ok": ok, "errors": errors, "warnings": warnings}, indent=1) + "\n"
    )
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for message in errors:
            escaped = f"Site payload stale: {message}".replace("%", "%25").replace("\n", "%0A")
            print(f"::error title=Site payload::{escaped}")


def main() -> int:
    if not COMMITTED.exists():
        print(f"missing {COMMITTED.relative_to(ROOT)} - run python tools/build_site_data.py")
        return 1
    committed = json.loads(COMMITTED.read_text())
    committed_bytes = COMMITTED.read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "data.js"
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_site_data.py"), "--out", str(target)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("the builder itself failed:\n" + result.stdout[-2000:] + result.stderr[-2000:])
            return 1
        built = json.loads(COMMITTED.read_text())
    COMMITTED.write_bytes(committed_bytes)  # leave the working tree exactly as we found it

    errors: List[str] = []
    warnings: List[str] = []
    difference = _first_difference(_strip(committed), _strip(built))
    if difference:
        errors.append("claim-level drift: " + difference)
    demo_errors, demo_warnings = _check_demo(committed.get("demo", []), built.get("demo", []))
    errors.extend(demo_errors)
    warnings.extend(demo_warnings)

    for warning in warnings:
        print("warning: " + warning)
    if errors:
        print("\nSITE PAYLOAD IS STALE - the site would publish something the code no longer says:")
        for error in errors:
            print("  - " + error)
        print("\nrun: python tools/build_site_data.py && git add docs/data docs/assets/data.js")
        _report(False, errors, warnings)
        return 1
    if warnings:
        print(
            "\nclaim-level sections match exactly; the demo section drifted as described above.\n"
            "Re-run tools/build_site_data.py and commit if the new numbers should be published."
        )
    else:
        print("site payload matches the builder output (claims and demo digits)")
    _report(True, [], warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
