"""
clean.py - Làm sạch JSON thô và chuyển thành list[Match].

>>> YÊU CẦU 3 : làm sạch (chuẩn hóa chuỗi, ép kiểu, chuẩn hóa ngày, loại trùng, loại bản ghi lỗi)
>>> YÊU CẦU 4 : kết quả là list[Match] (dataclass) - cấu trúc Python phù hợp
>>> YÊU CẦU 10: dữ liệu sai định dạng KHÔNG làm chương trình văng; bản ghi lỗi bị loại
              và ghi lại lý do trong danh sách `rejects`
"""
from datetime import datetime

from models import Match

VALID_STATUS = {"SCHEDULED", "TIMED", "IN_PLAY", "PAUSED", "FINISHED",
                "POSTPONED", "SUSPENDED", "CANCELLED", "AWARDED"}


def _clean_text(value) -> str:
    """Bỏ khoảng trắng đầu/cuối và gộp khoảng trắng thừa ở giữa."""
    return " ".join(str(value or "").split())


def _clean_score(value):
    """None -> None; '2' hoặc 2 -> 2; chữ / số âm -> ValueError."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, bool):
        raise ValueError(f"tỷ số sai định dạng: {value!r}")
    try:
        number = int(str(value).strip())
    except ValueError:
        raise ValueError(f"tỷ số không phải số nguyên: {value!r}")
    if number < 0:
        raise ValueError(f"tỷ số âm: {number}")
    return number


def _team_name(team) -> str:
    if not isinstance(team, dict):
        return ""
    return _clean_text(team.get("shortName") or team.get("name"))


def _clean_one(raw: dict) -> Match:
    """Làm sạch 1 bản ghi. Raise ValueError (kèm lý do) nếu không cứu được."""
    if not isinstance(raw, dict):
        raise ValueError("bản ghi không phải đối tượng")

    # id
    try:
        match_id = int(raw["id"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("thiếu hoặc sai 'id'")

    # tên đội
    home, away = _team_name(raw.get("homeTeam")), _team_name(raw.get("awayTeam"))
    if not home:
        raise ValueError("thiếu tên đội nhà")
    if not away:
        raise ValueError("thiếu tên đội khách")
    if home.lower() == away.lower():
        raise ValueError("đội nhà trùng đội khách")

    # ngày (chuẩn hóa về kiểu date)
    try:
        match_date = datetime.strptime(str(raw["utcDate"])[:10], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        raise ValueError(f"ngày sai định dạng: {raw.get('utcDate')!r}")

    # trạng thái
    status = _clean_text(raw.get("status")).upper()
    if status not in VALID_STATUS:
        raise ValueError(f"trạng thái lạ: {raw.get('status')!r}")

    # vòng đấu
    try:
        matchday = int(raw["matchday"]) if raw.get("matchday") is not None else None
    except (TypeError, ValueError):
        matchday = None   # vòng đấu không quan trọng -> bỏ trống chứ không loại bản ghi

    # tỷ số: chỉ giữ khi trận đã kết thúc
    score = (raw.get("score") or {}).get("fullTime") or {}
    home_score, away_score = _clean_score(score.get("home")), _clean_score(score.get("away"))
    if status == "FINISHED":
        if home_score is None or away_score is None:
            raise ValueError("trận FINISHED nhưng thiếu tỷ số")
    else:
        home_score = away_score = None

    return Match(match_id, matchday, match_date, home, away, status, home_score, away_score)


def clean_matches(raw: dict):
    """
    raw: JSON thô của API.
    Trả về (matches, rejects):
        matches: list[Match] đã sạch, không trùng, sắp theo ngày
        rejects: list[dict] gồm {'match_id', 'reason'} cho từng bản ghi bị loại
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("matches"), list):
        raise ValueError("Dữ liệu thô sai định dạng: thiếu danh sách 'matches'.")

    matches, rejects, seen = [], [], set()
    for item in raw["matches"]:
        rid = item.get("id") if isinstance(item, dict) else None
        try:
            match = _clean_one(item)
            if match.match_id in seen:                      # loại trùng
                raise ValueError("trùng id với bản ghi trước")
            seen.add(match.match_id)
            matches.append(match)
        except ValueError as e:
            rejects.append({"match_id": rid, "reason": str(e)})

    matches.sort(key=lambda m: (m.match_date, m.match_id))
    return matches, rejects
