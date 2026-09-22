"""
ownership_model.py — Rebuild Stokastic ownership projections
Verified:
- Ownership is forecast % of entries rostering player — forecast of opponents' behavior — https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections
- MLB chalk follows Vegas O/U, implied totals, ballpark, pitching matchups — same source
- Algorithm developed over years by Alex Baker — https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments
- Ownership projections sortable, heaviest concentrations float to top — https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-contrarian-strategy
- Leverage = exposure - ownership, rostering less than fair ownership when field over-piled — https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments
"""
from dataclasses import dataclass
from typing import List, Dict
import math

@dataclass
class PlayerForOwnership:
    name: str
    salary: int
    projected_fp: float
    value: float
    implied_total: float
    recency_avg: float
    news_boost: float  # 0-1 if injury bump
    position: str
    team: str

class OwnershipModel:
    """
    Gradient boosting style model — simplified for open-source.
    True Stokastic model is proprietary, trained on years of private contest data.
    We use proxy features that are verified to drive ownership per Stokastic.
    Flagged as inference where proprietary.
    """
    def __init__(self):
        self.verified_drivers = [
            "Vegas over/unders",
            "Implied team total",
            "Ballpark / matchup",
            "Salary / value",
            "Recent performance",
            "News boost",
            "Source: https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections"
        ]

    def predict_ownership(self, players: List[PlayerForOwnership]) -> List[Dict]:
        # Simple heuristic model that mimics drivers — for production, train XGBoost on historical
        raw_scores=[]
        for p in players:
            # Value drives ownership — high value => high ownership
            # Verified: value is FP - salary/1000*5, used to pick between salaries — https://www.stokastic.com/articles/nba-dfs/how-to-use-nba-dfs-projections
            score = 0
            score += p.value * 2.0
            score += p.implied_total * 0.5
            score += p.recency_avg * 0.3
            score += p.news_boost * 5.0  # injury bump huge
            # Salary: cheaper players get more ownership if value equal (more affordable)
            score += (10000 - p.salary)/1000 * 0.2
            raw_scores.append(score)

        # Convert to percentages via softmax-like, calibrated to sum ~ 8*100% per lineup? Actually ownership sums >100% because multiple players per lineup
        # For simplicity, normalize to 0-40% range typical for chalk
        min_s = min(raw_scores) if raw_scores else 0
        max_s = max(raw_scores) if raw_scores else 1
        range_s = max_s - min_s if max_s!=min_s else 1
        ownerships=[]
        for i, s in enumerate(raw_scores):
            norm = (s - min_s)/range_s  # 0-1
            # Map to 1% - 35% typical range, with exponential for chalk
            own = 1 + (norm**1.5)*34 + players[i].news_boost*10
            ownerships.append(min(45, own))

        # Sort descending — heaviest concentrations float to top — verified https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-contrarian-strategy
        result=[]
        for p, own in zip(players, ownerships):
            result.append({
                "Name": p.name,
                "Team": p.team,
                "Salary": p.salary,
                "Projected FP": p.projected_fp,
                "Value": round(p.value,2),
                "Implied Total": p.implied_total,
                "Projected Ownership %": round(own,1),
                "Leverage Signal": "High chalk if >25% — consider leverage off if optimal% lower",
                "Verification": "Ownership = forecast of opponents' behavior verified https://www.stokastic.com/articles/mlb-dfs/mlb-dfs-ownership-projections, drivers same source"
            })
        return sorted(result, key=lambda x: x["Projected Ownership %"], reverse=True)

    def leverage(self, exposure_pct: float, projected_own_pct: float) -> Dict:
        """
        Leverage = exposure - ownership — verified https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments
        Positive leverage = contrarian
        """
        lev = exposure_pct - projected_own_pct
        return {
            "exposure": exposure_pct,
            "projected_ownership": projected_own_pct,
            "leverage": round(lev,1),
            "interpretation": "Positive = over field, contrarian — you win more if player hits and field under. Negative = under field.",
            "source": "Leverage definition verified https://www.stokastic.com/articles/dfs-strategy/how-to-win-dfs-tournaments"
        }

if __name__ == "__main__":
    players=[
        PlayerForOwnership(name="Chalk OF", salary=4500, projected_fp=14, value=3.5, implied_total=5.5, recency_avg=15, news_boost=0, position="OF", team="NYY"),
        PlayerForOwnership(name="Injury Boost PG", salary=3800, projected_fp=28, value=9, implied_total=118, recency_avg=12, news_boost=1, position="PG", team="LAL"),
        PlayerForOwnership(name="Low Own P", salary=9000, projected_fp=22, value=1, implied_total=3.2, recency_avg=20, news_boost=0, position="P", team="LAD"),
    ]
    model=OwnershipModel()
    print(model.predict_ownership(players))
    print(model.leverage(10, 3.5))
