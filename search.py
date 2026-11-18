"""
search.py - Tìm kiếm / lọc / sắp xếp trên list[Match].

>>> YÊU CẦU 7: filter_matches() - lọc theo đội, trạng thái, khoảng ngày, vòng đấu, số bàn tối thiểu
>>> YÊU CẦU 8: sort_matches()   - sắp xếp theo 5 tiêu chí, tăng hoặc giảm
"""
from datetime import date
from typing import Optional


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def filter_matches(matches: list, team: Optional[str] = None, status: Optional[str] = None,
                   date_from: Optional[date] = None, date_to: Optional[date] = None,
                   matchday: Optional[int] = None, min_goals: Optional[int] = None) -> list:
    """Các điều kiện kết hợp bằng AND; điều kiện nào = None thì bỏ qua."""
    result = matches
    if team:
        key = _norm(team)   # tìm không phân biệt hoa/thường, khớp một phần tên
        result = [m for m in result if key in _norm(m.home_team) or key in _norm(m.away_team)]
    if status:
        result = [m for m in result if m.status == status.upper()]
    if date_from:
        result = [m for m in result if m.match_date >= date_from]
    if date_to:
        result = [m for m in result if m.match_date <= date_to]
    if matchday is not None:
        result = [m for m in result if m.matchday == matchday]
    if min_goals is not None:
        result = [m for m in result if m.total_goals is not None and m.total_goals >= min_goals]
    return list(result)


SORT_KEYS = {
    "date":     lambda m: (m.match_date, m.match_id),
    "matchday": lambda m: (m.matchday if m.matchday is not None else 0, m.match_id),
    "goals":    lambda m: m.total_goals if m.total_goals is not None else -1,
    "margin":   lambda m: abs(m.home_score - m.away_score) if m.is_finished else -1,
    "home":     lambda m: m.home_team.lower(),
}


def sort_matches(matches: list, by: str = "date", descending: bool = False) -> list:
    if by not in SORT_KEYS:
        raise ValueError(f"Tiêu chí sắp xếp không hợp lệ: {by!r}. Chọn một trong {sorted(SORT_KEYS)}")
    return sorted(matches, key=SORT_KEYS[by], reverse=descending)
