"""
models.py - Cấu trúc dữ liệu Python cho 1 trận đấu.

>>> YÊU CẦU 2: mỗi bản ghi có 10 thuộc tính (8 thuộc tính gốc + 2 thuộc tính suy ra)
>>> YÊU CẦU 4: dùng dataclass + list[Match] thay vì dict rời rạc
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

# Thứ tự cột khi ghi CSV (cũng là 10 thuộc tính của 1 bản ghi)
FIELDS = [
    "match_id", "matchday", "match_date", "home_team", "away_team",
    "status", "home_score", "away_score", "result", "total_goals",
]


@dataclass
class Match:
    match_id: int
    matchday: Optional[int]
    match_date: date
    home_team: str
    away_team: str
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    # ----- 2 thuộc tính suy ra từ tỷ số -----
    @property
    def is_finished(self) -> bool:
        return (self.status == "FINISHED"
                and self.home_score is not None
                and self.away_score is not None)

    @property
    def result(self) -> Optional[str]:
        """'H' = đội nhà thắng, 'D' = hòa, 'A' = đội khách thắng, None = chưa đá."""
        if not self.is_finished:
            return None
        if self.home_score > self.away_score:
            return "H"
        if self.home_score < self.away_score:
            return "A"
        return "D"

    @property
    def total_goals(self) -> Optional[int]:
        return self.home_score + self.away_score if self.is_finished else None

    # ----- chuyển đổi qua lại với dict (để ghi/đọc CSV, JSON) -----
    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "matchday": self.matchday,
            "match_date": self.match_date.isoformat(),
            "home_team": self.home_team,
            "away_team": self.away_team,
            "status": self.status,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "result": self.result,
            "total_goals": self.total_goals,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Match":
        """Dựng lại Match từ dict (đọc từ CSV/JSON). Raise ValueError nếu dòng hỏng."""
        def to_int(v):
            if v is None or str(v).strip() == "":
                return None
            return int(v)

        try:
            return cls(
                match_id=int(d["match_id"]),
                matchday=to_int(d.get("matchday")),
                match_date=datetime.strptime(str(d["match_date"])[:10], "%Y-%m-%d").date(),
                home_team=str(d["home_team"]).strip(),
                away_team=str(d["away_team"]).strip(),
                status=str(d["status"]).strip(),
                home_score=to_int(d.get("home_score")),
                away_score=to_int(d.get("away_score")),
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"thiếu cột/giá trị: {e}") from e
