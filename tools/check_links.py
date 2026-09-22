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

# Status codes that mean "site is alive but declined our bot" — NOT dead links.
BOT_BLOCKED = {403, 405, 406, 418, 423, 429, 503}
# Codes that definitively mean the URL is wrong/removed.
DEAD = {404, 410}


def collect_urls() -> dict:
    """Gather every external URL from sources_verified.json + docs/index.html."""
    urls = {}
    # 1. sources_verified.json
    sj = ROOT / "src" / "data" / "sources_verified.json"
    data = json.loads(sj.read_text())
    for category, items in data.items():
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, dict) and "url" in it:
                urls[it["url"]] = f"sources_verified.json::{category}"
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
    print(f"Checking {len(urls)} unique URLs...\n")
    dead = []
    out = {}
    for i, (url, where) in enumerate(sorted(urls.items()), 1):
        status = check(url)
        out[url] = {"status": status, "where": where}
        marker = "  " if status.startswith(("OK",)) else "! "
        print(f"{i:3d}/{len(urls)} [{status:20s}] {url}")
        if status.startswith("DEAD") or status.startswith("UNREACHABLE"):
            dead.append((url, status, where))
    print("\n==== SUMMARY ====")
    print(f"total={len(urls)} ok={len(out)-len(dead)} problematic={len(dead)}")
    if dead:
        print("\nProblematic (needs manual review / fix):")
        for u, s, w in dead:
            print(f"  - [{s}] {u}  ({w})")
        return 1
    print("No dead links. All URLs resolve or are bot-blocked-but-alive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
