"""
sample_data.py - Sinh dữ liệu GIẢ LẬP có cấu trúc giống hệt JSON của football-data.org.

Dùng khi chưa có API key / không vào được trang web (chạy: python main.py all --demo)
và để minh họa bước làm sạch: cuối danh sách có cài sẵn các bản ghi LỖI.
Tên đội là tên hư cấu, kết quả sinh ngẫu nhiên (seed cố định nên lần nào cũng giống nhau).
"""
import random
from datetime import date, timedelta

TEAMS = ["Sao Vàng FC", "Hải Âu United", "Phượng Hoàng City", "Rồng Xanh",
         "Bão Tố FC", "Thiên Long", "Sóng Biển", "Lửa Đỏ"]


def _round_robin(teams):
    """Xếp lịch vòng tròn (circle method): mỗi vòng mỗi đội đá đúng 1 trận."""
    arr, n, rounds = teams[:], len(teams), []
    for _ in range(n - 1):
        rounds.append([(arr[i], arr[n - 1 - i]) for i in range(n // 2)])
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    return rounds


def _team(name):
    return {"id": TEAMS.index(name.strip()) + 1 if name.strip() in TEAMS else 99,
            "name": name, "shortName": name}


def generate_sample_matches(finished_matchdays: int = 10) -> dict:
    rng = random.Random(42)
    first_half = _round_robin(TEAMS)
    second_half = [[(a, h) for h, a in rnd] for rnd in first_half]  # lượt về đảo sân
    start = date(2026, 8, 1)

    matches, mid = [], 1000
    for md, pairs in enumerate(first_half + second_half, start=1):
        for home, away in pairs:
            finished = md <= finished_matchdays
            hs, as_ = (rng.choice([0, 0, 1, 1, 1, 2, 2, 3, 4]),
                       rng.choice([0, 0, 1, 1, 2, 2, 3])) if finished else (None, None)
            matches.append({
                "id": mid, "matchday": md,
                "utcDate": f"{start + timedelta(days=7 * (md - 1))}T15:00:00Z",
                "status": "FINISHED" if finished else "SCHEDULED",
                "homeTeam": _team(home), "awayTeam": _team(away),
                "score": {"fullTime": {"home": hs, "away": as_}},
            })
            mid += 1

    # ---------- 2 trận "bẩn nhưng cứu được": làm bẩn TẠI CHỖ, không thêm trận mới ----------
    m1 = matches[1]                                   # id 1001: tên thừa khoảng trắng + tỷ số dạng chuỗi
    m1["homeTeam"]["shortName"] = "  " + m1["homeTeam"]["name"].replace(" ", "   ") + "  "
    ft = m1["score"]["fullTime"]
    ft["home"], ft["away"] = str(ft["home"]), str(ft["away"])
    matches[2]["status"] = "finished "                # id 1002: sai hoa/thường + khoảng trắng

    # ---------- 9 bản ghi LỖI cài sẵn (sẽ bị loại khi làm sạch) ----------
    d = "2026-08-02T15:00:00Z"
    ok = lambda i, **kw: {"id": i, "matchday": 3, "utcDate": d, "status": "FINISHED",
                          "homeTeam": _team(TEAMS[0]), "awayTeam": _team(TEAMS[1]),
                          "score": {"fullTime": {"home": 1, "away": 0}}, **kw}
    matches += [
        dict(matches[0]),                                                  # 1. trùng id
        ok(9001, score={"fullTime": {"home": None, "away": None}}),        # 2. FINISHED nhưng thiếu tỷ số
        ok(9002, homeTeam={"id": 1, "name": "   ", "shortName": ""}),      # 3. thiếu tên đội nhà
        ok(9003, utcDate="31/13/2026"),                                    # 4. ngày sai định dạng
        ok(9004, score={"fullTime": {"home": "abc", "away": 2}}),          # 5. tỷ số không phải số
        ok(9005, score={"fullTime": {"home": -1, "away": 0}}),             # 6. tỷ số âm
        ok(9006, status="WEIRD_STATUS"),                                   # 7. trạng thái lạ
        ok(None),                                                          # 8. thiếu id
        ok(9008, awayTeam=_team(TEAMS[0])),                                # 9. đội nhà trùng đội khách
    ]

    return {
        "competition": {"id": 0, "code": "DEMO", "name": "Giải mẫu (dữ liệu giả lập)"},
        "matches": matches,
    }
