Pipeline: **Web/API → Thu thập → Xử lý → Dữ liệu có cấu trúc → File → Thống kê**

Nguồn dữ liệu: API [football-data.org](https://www.football-data.org) (dữ liệu thể thao).

## 1. Cài đặt & chạy

```powershell
pip install -r requirements.txt            # chỉ cần requests
pip install matplotlib                     # (tùy chọn) nếu muốn vẽ biểu đồ

# Chạy thử NGAY, không cần API key / mạng (dữ liệu giả lập, có cài sẵn bản ghi lỗi):
python main.py all --demo

# Cách lấy API mới: truy cập https://www.football-data.org/client/login
# Chạy với dữ liệu thật:

$env:FOOTBALL_API_KEY="key_cua_ban"
python main.py all                         # giải mặc định PL (đổi trong config.py hoặc --comp PD)
```

Từng bước riêng lẻ: `fetch` → `clean` → `stats` → `search ...` (xem docstring đầu `main.py`).

Ví dụ tìm kiếm / lọc / sắp xếp:

```powershell
python main.py search --team "sao" --status FINISHED --sort goals --desc --limit 5
python main.py search --from 2026-08-15 --to 2026-08-22 --sort margin --desc
```

Chạy kiểm thử tự động: `python -m unittest -v` (24 test, không cần mạng).

## 2. Cấu trúc

| File | Vai trò |
|---|---|
| `config.py` | Cấu hình: API key, giải đấu, timeout/retry, thư mục dữ liệu |
| `fetch_data.py` | Thu thập từ API + xử lý mọi lỗi nguồn dữ liệu |
| `sample_data.py` | Dữ liệu giả lập đúng cấu trúc API (có 9 bản ghi lỗi cài sẵn) |
| `models.py` | `dataclass Match` (10 thuộc tính) |
| `clean.py` | Làm sạch JSON thô → `list[Match]` + danh sách bản ghi bị loại |
| `storage.py` | Lưu / đọc lại CSV và JSON |
| `search.py` | Tìm kiếm, lọc, sắp xếp |
| `stats.py` | 5 thống kê bằng Python thuần |
| `main.py` | CLI điều phối pipeline |
| `bonus_sql.py`, `charts.py` | Phần mở rộng (SQLite + SQL, biểu đồ) — không bắt buộc theo đề |
| `test_pipeline.py` | Kiểm thử tự động |

Dữ liệu sinh ra: `data/raw/` (JSON thô) → `data/processed/` (CSV + JSON sạch + `rejected_*.json` nhật ký bản ghi bị loại).

## 3. Lưu ý

- Bản ghi chưa đá (SCHEDULED/TIMED) vẫn được giữ nhưng tỷ số để trống; thống kê chỉ tính trận FINISHED.
- Với Champions League, các trận chưa xác định đội (TBD) sẽ bị loại ở bước làm sạch vì thiếu tên đội — đây là hành vi có chủ ý.
- Free tier của football-data.org giới hạn ~10 request/phút; pipeline này chỉ gọi 1 request mỗi lần chạy.
- `bonus_sql.py` kiểm tra chéo: bảng xếp hạng tính bằng SQL phải khớp bảng tính bằng Python (có trong test).
