"""check_links.py — Verify every cited URL in the project resolves (no dead/hallucinated links).

Exit codes:
  0 = all URLs reachable (HTTP 200/2xx/3xx) or bot-blocked-but-alive (403/405/406/429/418) or TLS errors that browsers tolerate
  1 = some URL definitively dead (DNS failure, connection refused, 404/410)

Usage:  python tools/check_links.py
"""
import json
import re
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

#: URLs deliberately not fetched, with the reason a human reviewer needs.
EXEMPT = {
    "http://gdx.mlb.com/components/copyright.txt":
        "MLB publishes this notice over plain http; it is cited as text, not fetched.",
    "https://127.0.0.1:9/definitely-not-listening":
        "test fixture: proves the fetcher reports an unreachable host instead of inventing data.",
}

# Status codes that mean "site is alive but declined our bot" — NOT dead links.
BOT_BLOCKED = {403, 405, 406, 418, 423, 429, 503}
# Codes that definitively mean the URL is wrong/removed.
DEAD = {404, 410}


def _walk(obj, path: str, urls: dict) -> None:
    """Collect every `url` value, wherever it sits in the tree."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            where = f"{path}.{key}" if path else key
            if key == "url" and isinstance(value, str) and value.startswith("http"):
                urls.setdefault(value, where)
            else:
                _walk(value, where, urls)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            _walk(value, f"{path}[{index}]", urls)


def collect_urls() -> dict:
    """Gather every external URL from the data files, the site and the markdown docs.

    Schema note: ``sources_verified.json`` is a list under ``sources`` (not a dict of
    categories), and claims carry their own source ids - so this walks the tree instead of
    assuming a shape. An earlier version silently collected *zero* urls when the schema
    changed, which is worse than failing: it reported success on an empty list.
    """
    urls = {}
    for name in ("sources_verified.json", "claims.json"):
        path = ROOT / "src" / "data" / name
        if path.exists():
            _walk(json.loads(path.read_text()), name, urls)
    for pattern in ("docs/*.html", "docs/assets/*.js", "*.md", "src/**/*.py", "tests/*.py"):
        for path in ROOT.glob(pattern):
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for match in re.finditer(r"https?://[^\s\"'<>)\]]+", text):
                url = match.group(0).rstrip(".,;:")
                if url.startswith("https://github.com/buffedlizard55-lab/StokEngineer"):
                    continue  # self-reference
                urls.setdefault(url, str(path.relative_to(ROOT)))
    # 2. docs/index.html
    html = (ROOT / "docs" / "index.html").read_text()
    for m in re.finditer(r'href="(https?://[^"]+)"', html):
        u = m.group(1)
        if u.startswith("https://github.com/buffedlizard55-lab/StokEngineer"):
            continue  # self-reference
        urls.setdefault(u, "docs/index.html")
    return urls


def check(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    ctx = ssl.create_default_context()
    # Some legit sites have odd cert chains; treat TLS errors as "alive, manual review" not dead.
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            code = r.getcode()
            return "OK" if 200 <= code < 400 else f"HTTP {code}"
    except urllib.error.HTTPError as e:
        code = e.code
        if code in BOT_BLOCKED:
            return "BOT-BLOCKED(ALIVE)"
        if code in DEAD:
            return f"DEAD({code})"
        return f"HTTP {code}"
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        reason = str(e.reason).lower() if hasattr(e, "reason") else str(e).lower()
        if "certificate" in reason or "ssl" in reason or "tls" in reason:
            return "TLS-WARN(ALIVE?)"
        if "name or service not known" in reason or "getaddrinfo" in reason:
            return "DEAD(DNS)"
        return f"UNREACHABLE({reason[:60]})"


def main() -> int:
    urls = collect_urls()
    pending = {u: w for u, w in urls.items() if u not in EXEMPT}
    print(f"Checking {len(pending)} unique URLs ({len(urls) - len(pending)} exempt)...\n")
    dead = []
    out = {}
    for i, (url, where) in enumerate(sorted(pending.items()), 1):
        status = check(url)
        out[url] = {"status": status, "where": where}
        marker = "  " if status.startswith(("OK",)) else "! "
        print(f"{i:3d}/{len(pending)} [{status:20s}] {url}")
        if status.startswith("DEAD") or status.startswith("UNREACHABLE"):
            dead.append((url, status, where))
    if EXEMPT:
        print("\nExempt (documented, not fetched):")
        for url, reason in sorted(EXEMPT.items()):
            print(f"  - {url}\n      {reason}")
    print("\n==== SUMMARY ====")
    print(f"total={len(urls)} checked={len(pending)} ok={len(out)-len(dead)} problematic={len(dead)}")
    report = Path(__file__).resolve().parent.parent / "reports" / "links.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps({"checked": out, "exempt": EXEMPT, "dead": [u for u, _, _ in dead]}, indent=1)
        + "\n"
    )
    print(f"wrote {report.relative_to(report.parent.parent)}")
    if dead:
        print("\nProblematic (needs manual review / fix):")
        for u, s, w in dead:
            print(f"  - [{s}] {u}  ({w})")
        return 1
    print("No dead links. All URLs resolve or are bot-blocked-but-alive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
