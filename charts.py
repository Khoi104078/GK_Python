"""
charts.py - PHẦN MỞ RỘNG: vẽ biểu đồ từ kết quả thống kê (cần: pip install matplotlib).
Chạy: python main.py charts [--demo]
"""
import os

import config
import stats


def run(matches: list, code: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")   # vẽ ra file, không cần cửa sổ
        import matplotlib.pyplot as plt
    except ImportError:
        print("[charts] Chưa cài matplotlib. Chạy: pip install matplotlib")
        return

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # Biểu đồ 1: điểm số theo bảng xếp hạng
    table = stats.standings(matches)
    plt.figure(figsize=(9, 5))
    plt.barh([r["team"] for r in table], [r["points"] for r in table], color="#2E86AB")
    plt.gca().invert_yaxis()
    plt.xlabel("Điểm")
    plt.title("Bảng xếp hạng")
    plt.tight_layout()
    p1 = os.path.join(config.OUTPUT_DIR, f"standings_{code}.png")
    plt.savefig(p1, dpi=150)
    plt.close()

    # Biểu đồ 2: ghi bàn trung bình sân nhà vs sân khách
    split = stats.home_away_split(matches)
    x = range(len(split))
    plt.figure(figsize=(10, 5))
    plt.bar([i - 0.2 for i in x], [r["home_avg_goals"] for r in split], 0.4, label="Sân nhà", color="#3A86FF")
    plt.bar([i + 0.2 for i in x], [r["away_avg_goals"] for r in split], 0.4, label="Sân khách", color="#FB5607")
    plt.xticks(list(x), [r["team"] for r in split], rotation=45, ha="right")
    plt.ylabel("Bàn thắng trung bình / trận")
    plt.title("Ghi bàn: sân nhà vs sân khách")
    plt.legend()
    plt.tight_layout()
    p2 = os.path.join(config.OUTPUT_DIR, f"home_away_{code}.png")
    plt.savefig(p2, dpi=150)
    plt.close()

    print(f"[charts] Đã lưu: {p1}\n[charts] Đã lưu: {p2}")
