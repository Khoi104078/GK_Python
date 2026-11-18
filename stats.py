"""
stats.py - Thống kê trên list[Match] bằng Python thuần (dict, Counter, sorted).

>>> YÊU CẦU 9: 5 thống kê có ý nghĩa (đề yêu cầu tối thiểu 3)
    1. standings()       - bảng xếp hạng tính từ kết quả
    2. team_form()       - phong độ N trận gần nhất của mỗi đội
    3. home_advantage()  - lợi thế sân nhà: tỷ lệ H/D/A + trung bình bàn thắng
    4. home_away_split() - mỗi đội ghi bàn sân nhà vs sân khách
    5. top_matches()     - các trận nhiều bàn thắng nhất / cách biệt lớn nhất
"""
from collections import Counter, defaultdict


def _finished(matches):
    return [m for m in matches if m.is_finished]


# 1. Bảng xếp hạng -----------------------------------------------------------
def standings(matches: list) -> list:
    table = defaultdict(lambda: {"played": 0, "won": 0, "draw": 0, "lost": 0,
                                 "gf": 0, "ga": 0})
    for m in _finished(matches):
        for team, gf, ga in ((m.home_team, m.home_score, m.away_score),
                             (m.away_team, m.away_score, m.home_score)):
            row = table[team]
            row["played"] += 1
            row["gf"] += gf
            row["ga"] += ga
            if gf > ga:
                row["won"] += 1
            elif gf == ga:
                row["draw"] += 1
            else:
                row["lost"] += 1

    rows = []
    for team, r in table.items():
        rows.append({"team": team, **r, "gd": r["gf"] - r["ga"],
                     "points": 3 * r["won"] + r["draw"]})
    rows.sort(key=lambda r: (-r["points"], -r["gd"], -r["gf"], r["team"]))
    for i, r in enumerate(rows, start=1):
        r["pos"] = i
    return rows


# 2. Phong độ ----------------------------------------------------------------
def team_form(matches: list, n: int = 5) -> list:
    history = defaultdict(list)                          # team -> [(ngày, id, W/D/L)]
    for m in _finished(matches):
        hr = "W" if m.result == "H" else "D" if m.result == "D" else "L"
        ar = "W" if m.result == "A" else "D" if m.result == "D" else "L"
        history[m.home_team].append((m.match_date, m.match_id, hr))
        history[m.away_team].append((m.match_date, m.match_id, ar))

    rows = []
    for team, games in history.items():
        last = [g[2] for g in sorted(games)[-n:]]        # n trận gần nhất, cũ -> mới
        pts = sum(3 if x == "W" else 1 if x == "D" else 0 for x in last)
        rows.append({"team": team, "form": "".join(last), "points": pts, "games": len(last)})
    rows.sort(key=lambda r: (-r["points"], r["team"]))
    return rows


# 3. Lợi thế sân nhà ---------------------------------------------------------
def home_advantage(matches: list) -> dict:
    done = _finished(matches)
    if not done:
        return {"matches": 0}
    c = Counter(m.result for m in done)
    total = len(done)
    return {
        "matches": total,
        "home_win_pct": round(100 * c["H"] / total, 1),
        "draw_pct": round(100 * c["D"] / total, 1),
        "away_win_pct": round(100 * c["A"] / total, 1),
        "avg_goals_per_match": round(sum(m.total_goals for m in done) / total, 2),
        "avg_home_goals": round(sum(m.home_score for m in done) / total, 2),
        "avg_away_goals": round(sum(m.away_score for m in done) / total, 2),
    }


# 4. Sân nhà vs sân khách của từng đội --------------------------------------
def home_away_split(matches: list) -> list:
    acc = defaultdict(lambda: {"hg": 0, "hn": 0, "ag": 0, "an": 0})
    for m in _finished(matches):
        acc[m.home_team]["hg"] += m.home_score
        acc[m.home_team]["hn"] += 1
        acc[m.away_team]["ag"] += m.away_score
        acc[m.away_team]["an"] += 1
    rows = []
    for team, a in acc.items():
        home_avg = a["hg"] / a["hn"] if a["hn"] else 0.0
        away_avg = a["ag"] / a["an"] if a["an"] else 0.0
        rows.append({"team": team, "home_avg_goals": round(home_avg, 2),
                     "away_avg_goals": round(away_avg, 2),
                     "diff": round(home_avg - away_avg, 2)})
    rows.sort(key=lambda r: -r["diff"])
    return rows


# 5. Trận đáng chú ý ---------------------------------------------------------
def top_matches(matches: list, by: str = "goals", n: int = 5) -> list:
    done = _finished(matches)
    if by == "goals":
        key = lambda m: m.total_goals
    elif by == "margin":
        key = lambda m: abs(m.home_score - m.away_score)
    else:
        raise ValueError("by phải là 'goals' hoặc 'margin'")
    return sorted(done, key=key, reverse=True)[:n]
