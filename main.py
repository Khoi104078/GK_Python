"""
main.py - Điều phối pipeline:
    Web/API -> Thu thập -> Xử lý -> Dữ liệu có cấu trúc -> File -> Thống kê

Cách dùng (thêm --demo để chạy bằng dữ liệu giả lập, không cần API key/mạng):
    python main.py all --demo                   # chạy cả pipeline
    python main.py fetch [--comp PL]            # 1. thu thập -> data/raw/*.json
    python main.py clean                        # 2. làm sạch -> data/processed/*.csv, *.json
    python main.py stats                        # 3. đọc lại CSV -> thống kê
    python main.py search --team arsenal --status FINISHED --sort goals --desc --limit 10
    python main.py sql                          # (bonus) nạp CSV vào SQLite, chạy SQL
    python main.py charts                       # (bonus) vẽ biểu đồ -> output/*.png
"""
import argparse
import os
import sys
from collections import Counter
from datetime import datetime

import clean
import config
import fetch_data
import sample_data
import search
import stats
import storage
from fetch_data import FetchError
from storage import StorageError


# ----------------------------- tiện ích hiển thị -----------------------------
def format_table(rows: list, columns: list) -> str:
    """columns: [(khóa, tiêu đề)]. Căn cột theo độ dài lớn nhất."""
    if not rows:
        return "(không có dữ liệu)"
    cells = [[str(r.get(k, "")) for k, _ in columns] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) for i, (_, h) in enumerate(columns)]
    line = lambda vals: "  ".join(v.ljust(w) for v, w in zip(vals, widths))
    out = [line([h for _, h in columns]), "  ".join("-" * w for w in widths)]
    out += [line(c) for c in cells]
    return "\n".join(out)


def match_rows(matches: list) -> list:
    return [{
        "date": m.match_date.isoformat(), "md": m.matchday if m.matchday is not None else "",
        "home": m.home_team,
        "score": f"{m.home_score}-{m.away_score}" if m.is_finished else "-",
        "away": m.away_team, "status": m.status, "goals": m.total_goals if m.is_finished else "",
    } for m in matches]


MATCH_COLS = [("date", "Ngày"), ("md", "Vòng"), ("home", "Đội nhà"), ("score", "Tỷ số"),
              ("away", "Đội khách"), ("status", "Trạng thái"), ("goals", "Tổng bàn")]


def code_of(args) -> str:
    return "DEMO" if args.demo else args.comp


def csv_path(args) -> str:
    return storage.processed_path(code_of(args), "csv")


def parse_date(text: str):
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"ngày phải có dạng YYYY-MM-DD, nhận được {text!r}")


# ----------------------------- các bước pipeline -----------------------------
def step_fetch(args) -> None:
    """Bước 1 - YÊU CẦU 1 (thu thập) + 10 (xử lý lỗi nguồn dữ liệu)."""
    code = code_of(args)
    if args.demo:
        data = sample_data.generate_sample_matches()
        path = fetch_data.save_raw(data, code)
        print(f"[fetch] DEMO: đã sinh {len(data['matches'])} bản ghi thô giả lập -> {path}")
        return
    try:
        fetch_data.fetch_and_save(code)
    except FetchError as e:
        print(f"[LỖI fetch] {e}")
        if os.path.exists(fetch_data.raw_path(code)):
            print(f"[fetch] Dùng dữ liệu thô đã lưu từ lần chạy trước: {fetch_data.raw_path(code)}")
        else:
            print("[fetch] Chưa có dữ liệu cũ để dùng. Thử: python main.py all --demo")
            raise SystemExit(1)


def step_clean(args) -> list:
    """Bước 2 - YÊU CẦU 3, 4 (làm sạch -> list[Match]) và 5 (lưu CSV/JSON)."""
    code = code_of(args)
    raw = fetch_data.load_raw(code)
    matches, rejects = clean.clean_matches(raw)

    total = len(raw["matches"])
    print(f"[clean] Bản ghi thô: {total} | Hợp lệ: {len(matches)} | Bị loại: {len(rejects)}")
    for reason, n in Counter(r["reason"].split(":")[0] for r in rejects).most_common():
        print(f"         - {n} x {reason}")
    if not matches:
        raise ValueError("Không còn bản ghi hợp lệ nào sau khi làm sạch.")

    p_csv = storage.save_csv(matches, storage.processed_path(code, "csv"))
    p_json = storage.save_json(matches, storage.processed_path(code, "json"))
    p_rej = storage.save_rejects(rejects, os.path.join(config.PROCESSED_DIR, f"rejected_{code}.json"))
    print(f"[save]  CSV : {p_csv}\n[save]  JSON: {p_json}\n[save]  Nhật ký bản ghi bị loại: {p_rej}")
    return matches


def load_processed(args) -> list:
    """YÊU CẦU 6: đọc lại dữ liệu từ file CSV đã lưu."""
    matches = storage.load_csv(csv_path(args))
    print(f"[load]  Đã đọc lại {len(matches)} bản ghi từ {csv_path(args)}")
    return matches


def step_stats(matches: list) -> None:
    """Bước 3 - YÊU CẦU 9: thống kê."""
    print("\n=== 1. BẢNG XẾP HẠNG (tính từ kết quả) ===")
    print(format_table(stats.standings(matches), [
        ("pos", "#"), ("team", "Đội"), ("played", "Trận"), ("won", "T"), ("draw", "H"),
        ("lost", "B"), ("gf", "BT"), ("ga", "BB"), ("gd", "HS"), ("points", "Điểm")]))

    print("\n=== 2. PHONG ĐỘ 5 TRẬN GẦN NHẤT (W=thắng, D=hòa, L=thua; cũ -> mới) ===")
    print(format_table(stats.team_form(matches, 5),
                       [("team", "Đội"), ("form", "Phong độ"), ("points", "Điểm"), ("games", "Số trận")]))

    print("\n=== 3. LỢI THẾ SÂN NHÀ ===")
    ha = stats.home_advantage(matches)
    if ha["matches"] == 0:
        print("(chưa có trận nào kết thúc)")
    else:
        print(f"Số trận đã đá: {ha['matches']}")
        print(f"Đội nhà thắng {ha['home_win_pct']}% | Hòa {ha['draw_pct']}% | Đội khách thắng {ha['away_win_pct']}%")
        print(f"Trung bình {ha['avg_goals_per_match']} bàn/trận "
              f"(đội nhà {ha['avg_home_goals']}, đội khách {ha['avg_away_goals']})")

    print("\n=== 4. GHI BÀN TRUNG BÌNH: SÂN NHÀ vs SÂN KHÁCH ===")
    print(format_table(stats.home_away_split(matches), [
        ("team", "Đội"), ("home_avg_goals", "Sân nhà"), ("away_avg_goals", "Sân khách"), ("diff", "Chênh lệch")]))

    print("\n=== 5a. 5 TRẬN NHIỀU BÀN THẮNG NHẤT ===")
    print(format_table(match_rows(stats.top_matches(matches, "goals", 5)), MATCH_COLS))
    print("\n=== 5b. 5 TRẬN THẮNG CÁCH BIỆT LỚN NHẤT ===")
    print(format_table(match_rows(stats.top_matches(matches, "margin", 5)), MATCH_COLS))


def step_search(args) -> None:
    """YÊU CẦU 7 (tìm kiếm/lọc) + 8 (sắp xếp)."""
    matches = load_processed(args)
    found = search.filter_matches(matches, team=args.team, status=args.status,
                                  date_from=args.date_from, date_to=args.date_to,
                                  matchday=args.matchday, min_goals=args.min_goals)
    found = search.sort_matches(found, by=args.sort, descending=args.desc)
    print(f"\nTìm thấy {len(found)}/{len(matches)} trận "
          f"(sắp xếp theo '{args.sort}', {'giảm' if args.desc else 'tăng'} dần):\n")
    print(format_table(match_rows(found[:args.limit]), MATCH_COLS))
    if len(found) > args.limit:
        print(f"... còn {len(found) - args.limit} trận nữa (tăng --limit để xem thêm)")


def run_all(args) -> None:
    print("[Bước 1/5] Thu thập dữ liệu (YC1, YC10)")
    step_fetch(args)
    print("\n[Bước 2/5] Làm sạch + chuyển sang cấu trúc Python + lưu file (YC3, YC4, YC5)")
    step_clean(args)
    print("\n[Bước 3/5] Đọc lại dữ liệu từ file CSV (YC6)")
    matches = load_processed(args)
    print("\n[Bước 4/5] Thống kê (YC9)")
    step_stats(matches)
    print("\n[Bước 5/5] Tìm kiếm/lọc + sắp xếp (YC7, YC8) - ví dụ: trận có ≥3 bàn, nhiều bàn nhất trước")
    found = search.sort_matches(search.filter_matches(matches, status="FINISHED", min_goals=3), "goals", True)
    print(format_table(match_rows(found[:5]), MATCH_COLS))
    print("\nHoàn tất. Thử thêm: python main.py search --team \"sao\" --sort date")


# ----------------------------- CLI -----------------------------
def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--comp", default=config.DEFAULT_COMPETITION, help="mã giải (PL, PD, SA, BL1, CL)")
    common.add_argument("--demo", action="store_true", help="dùng dữ liệu giả lập, không cần API/mạng")

    parser = argparse.ArgumentParser(description="Football Tracker - pipeline thu thập & phân tích dữ liệu bóng đá")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, helptext in [("all", "chạy toàn bộ pipeline"), ("fetch", "thu thập dữ liệu"),
                           ("clean", "làm sạch và lưu CSV/JSON"), ("stats", "thống kê từ file CSV"),
                           ("sql", "(bonus) nạp CSV vào SQLite và chạy SQL"),
                           ("charts", "(bonus) vẽ biểu đồ")]:
        sub.add_parser(name, parents=[common], help=helptext)

    s = sub.add_parser("search", parents=[common], help="tìm kiếm / lọc / sắp xếp trận đấu")
    s.add_argument("--team", help="tên đội (khớp một phần, không phân biệt hoa thường)")
    s.add_argument("--status", help="FINISHED, SCHEDULED, ...")
    s.add_argument("--from", dest="date_from", type=parse_date, help="từ ngày YYYY-MM-DD")
    s.add_argument("--to", dest="date_to", type=parse_date, help="đến ngày YYYY-MM-DD")
    s.add_argument("--matchday", type=int, help="vòng đấu")
    s.add_argument("--min-goals", type=int, help="tổng số bàn thắng tối thiểu")
    s.add_argument("--sort", default="date", choices=sorted(search.SORT_KEYS), help="tiêu chí sắp xếp")
    s.add_argument("--desc", action="store_true", help="sắp xếp giảm dần")
    s.add_argument("--limit", type=int, default=20, help="số dòng tối đa hiển thị")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "all":
            run_all(args)
        elif args.command == "fetch":
            step_fetch(args)
        elif args.command == "clean":
            step_clean(args)
        elif args.command == "stats":
            step_stats(load_processed(args))
        elif args.command == "search":
            step_search(args)
        elif args.command == "sql":
            import bonus_sql
            bonus_sql.run(csv_path(args))
        elif args.command == "charts":
            import charts
            charts.run(load_processed(args), code_of(args))
    except (FetchError, StorageError, ValueError) as e:
        print(f"[LỖI] {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
