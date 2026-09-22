"""
top_stacks.py — Top Stacks tool reproduction
Verified:
- Top Stacks scores whole teams instead of individuals — https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data
- For each team shows projected stack total, stack ownership, how often stack in optimal lineups — same source
- Baseball is correlated game (when team bats around, four hitters cash together) — same source
- Stacks tool is MLB-specific edge — https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data
- NFL: QB+pass-catcher stacks and bring-backs naturally because sims reward correlation — https://www.stokastic.com/articles/nfl-dfs/stokastic-review
"""
from dataclasses import dataclass
from typing import List, Dict
import itertools

@dataclass
class HitterForStack:
    name: str
    team: str
    salary: int
    projection: float
    ownership: float
    order: int

class TopStacksEngine:
    def __init__(self, hitters: List[HitterForStack]):
        self.hitters = hitters

    def generate_stacks(self, stack_size=4) -> List[Dict]:
        teams={}
        for h in self.hitters:
            teams.setdefault(h.team, []).append(h)
        stacks=[]
        for team, players in teams.items():
            # Sort by order (lineup order 1-9 matters — verified https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data)
            players_sorted = sorted(players, key=lambda x: x.order)
            # Take top 5 batters for potential stacks
            top5 = players_sorted[:5]
            if len(top5) < stack_size:
                continue
            # Generate all combinations of stack_size
            for combo in itertools.combinations(top5, stack_size):
                total_proj = sum(p.projection for p in combo)
                # Stack ownership approximated as product? Actually field stacks less correlated than product
                # Simplified: avg ownership of players * correlation discount
                avg_own = sum(p.ownership for p in combo)/len(combo)
                # Stack ownership typically lower than individual avg because field doesn't stack perfectly
                stack_own = avg_own * 0.7  # heuristic, flagged as inference
                stacks.append({
                    "Team": team,
                    "Stack": "+".join(p.name for p in combo),
                    "Stack Size": stack_size,
                    "Projected Stack Total": round(total_proj,2),
                    "Avg Player Ownership": round(avg_own,1),
                    "Projected Stack Ownership": round(stack_own,1),
                    "Optimal% Proxy": round(total_proj / 10,1),  # proxy: higher projection => more often optimal
                    "Correlation Note": "When team bats around, four hitters cash together — verified https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data",
                    "Verification": "Top Stacks definition verified https://www.stokastic.com/articles/mlb-dfs/how-to-use-mlb-dfs-data"
                })
        return sorted(stacks, key=lambda x: x["Projected Stack Total"], reverse=True)

    def nfl_stacks(self, qbs, wrs, tes):
        """
        NFL stacks: QB+WR, QB+WR+WR, QB+WR+bring-back
        Verified: Builds QB plus pass-catcher stacks and bring-backs naturally, because sims reward correlation — https://www.stokastic.com/articles/nfl-dfs/stokastic-review
        """
        stacks=[]
        for qb in qbs:
            same_team_wrs = [w for w in wrs if w.team==qb.team]
            same_team_tes = [t for t in tes if t.team==qb.team]
            opp_wrs = [w for w in wrs if w.team!=qb.team]
            for wr in same_team_wrs[:3]:
                total = qb.projection + wr.projection
                stacks.append({
                    "Stack": f"{qb.name}+{wr.name}",
                    "Type": "QB+WR",
                    "Total Proj": round(total,2),
                    "Team": qb.team,
                    "Correlation": "0.6 QB-WR same team — heuristic flagged as inference, principle verified https://www.stokastic.com/articles/nfl-dfs/stokastic-review"
                })
                # Bring-back
                for opp in opp_wrs[:2]:
                    total2 = total + opp.projection
                    stacks.append({
                        "Stack": f"{qb.name}+{wr.name}+{opp.name} (bring-back)",
                        "Type": "QB+WR+Opp WR bring-back",
                        "Total Proj": round(total2,2),
                        "Team": qb.team,
                        "Correlation": "Bring-back 0.15 — verified concept https://www.stokastic.com/articles/nfl-dfs/stokastic-review"
                    })
        return sorted(stacks, key=lambda x: x["Total Proj"], reverse=True)

if __name__ == "__main__":
    hitters=[
        HitterForStack(name="Judge", team="NYY", salary=5500, projection=14, ownership=22, order=2),
        HitterForStack(name="Soto", team="NYY", salary=5300, projection=13.5, ownership=20, order=3),
        HitterForStack(name="Stanton", team="NYY", salary=4800, projection=11, ownership=12, order=4),
        HitterForStack(name="Torres", team="NYY", salary=4200, projection=9, ownership=8, order=5),
        HitterForStack(name="Rizzo", team="NYY", salary=4000, projection=8.5, ownership=6, order=6),
    ]
    eng=TopStacksEngine(hitters)
    print(eng.generate_stacks(4)[:3])
