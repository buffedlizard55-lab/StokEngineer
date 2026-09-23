"""StokEngineer - an open, source-verified DFS projection / optimisation / simulation engine.

Design rule of this package: every number that comes from an external source carries a
source id that exists in ``src/data/sources_verified.json``. Nothing is invented, and
anything that is a modelling prior rather than a sourced fact says so in its docstring.

Modules
-------
``rules``       DraftKings / FanDuel scoring + roster rules, loaded from verified JSON.
``models``      Bottom-up per-sport projection models (NBA, NFL, MLB).
``ownership``   Field/ownership model plus ownership-weighted field lineup generation.
``optimizer``   Lineup construction (MILP with a documented greedy fallback).
``simulate``    Contest-level Monte Carlo simulation with real payout structures.
``evaluate``    Backtest / forward-test metrics and reporting.
``ingest``      Free, keyless data plumbing (with provenance sidecars).
"""

from pathlib import Path

__version__ = "0.4.0"

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "src" / "data"
REPORTS_DIR = ROOT / "reports"
CACHE_DIR = ROOT / "data" / "cache"

__all__ = ["__version__", "ROOT", "DATA_DIR", "REPORTS_DIR", "CACHE_DIR"]
