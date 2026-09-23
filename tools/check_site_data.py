"""Fail if the committed site payload does not match what the builder produces now.

The payload is generated from the registry, the claim ledger and a real engine run, so it is the
one file on the site that a reviewer must be able to trust. A stale payload would mean the site
claims something the code no longer does - exactly the failure mode this repository exists to avoid.

Volatile fields (the build timestamp and the revision it was built from) are ignored: everything
else - sources, claims, rules, demo numbers, limitations - must match byte for byte.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMITTED = ROOT / "docs" / "data" / "site_data.json"
VOLATILE = (("meta", "generated_at"), ("meta", "git_revision"))


def _strip(payload: dict) -> dict:
    payload = json.loads(json.dumps(payload))
    for section, key in VOLATILE:
        payload.get(section, {}).pop(key, None)
    return payload


def _first_difference(a, b, path: str = "") -> str:
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


def main() -> int:
    if not COMMITTED.exists():
        print(f"missing {COMMITTED.relative_to(ROOT)} - run python tools/build_site_data.py")
        return 1
    committed = json.loads(COMMITTED.read_text())
    committed_path = COMMITTED.read_bytes()
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
        # `--out` writes the JS payload; the builder always refreshes docs/data/site_data.json too,
        # so keep a copy of the fresh JSON before restoring the committed file.
        fresh_json = json.loads(COMMITTED.read_text())
    COMMITTED.write_bytes(committed_path)  # leave the working tree exactly as we found it
    difference = _first_difference(_strip(committed), _strip(fresh_json))
    if difference:
        print("site payload is stale: " + difference)
        print("run: python tools/build_site_data.py && git add docs/data docs/assets/data.js")
        return 1
    print("site payload matches the builder output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
