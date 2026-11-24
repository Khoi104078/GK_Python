Football Tracker
Chương trình Python thu thập dữ liệu trận đấu bóng đá từ API công khai, làm sạch, lưu ra file CSV/JSON, rồi tìm kiếm, sắp xếp và thống kê.
---
1. Mô tả
Bài toán
Dữ liệu bóng đá có sẵn trên mạng nhưng ở dạng JSON thô, lồng nhau và đôi khi sai định dạng. Chương trình này giải quyết bài toán: lấy dữ liệu từ nguồn trực tuyến → làm sạch → lưu thành dữ liệu có cấu trúc → đọc lại để tìm kiếm và thống kê.
```
Web/API → Thu thập → Xử lý → Dữ liệu có cấu trúc → File → Thống kê
```
Đầu vào / đầu ra
	Nội dung
Nguồn dữ liệu	API football-data.org (v4), endpoint `/competitions/{mã giải}/matches`
Đầu vào	JSON thô các trận đấu của một giải (mặc định Premier League `PL`; hỗ trợ `PD`, `SA`, `BL1`, `CL`)
Đầu ra	`data/raw/*.json` (thô), `data/processed/*.csv` và `*.json` (sạch), `rejected_*.json` (bản ghi bị loại), bảng tìm kiếm và 5 thống kê in ra màn hình
Mỗi bản ghi (1 trận đấu) có 10 thuộc tính
Thuộc tính	Ý nghĩa	Loại
`match_id`	Mã trận	gốc
`matchday`	Vòng đấu	gốc
`match_date`	Ngày thi đấu (`YYYY-MM-DD`)	gốc
`home_team` / `away_team`	Đội nhà / đội khách	gốc
`status`	Trạng thái (FINISHED, SCHEDULED, ...)	gốc
`home_score` / `away_score`	Tỷ số đội nhà / đội khách	gốc
`result`	`H` đội nhà thắng, `D` hòa, `A` đội khách thắng	suy ra
`total_goals`	Tổng số bàn thắng của trận	suy ra
Cần những gì để chạy
Python 3.8 trở lên
Thư viện `requests`
API key miễn phí từ football-data.org (không bắt buộc nếu chạy chế độ `--demo`)
Thư viện `matplotlib` (tùy chọn, chỉ để vẽ biểu đồ)
---
2. Cài đặt và cách chạy
Bước 1: Cài thư viện
```powershell
pip install -r requirements.txt     # chỉ cần requests
pip install matplotlib              # (tùy chọn) nếu muốn vẽ biểu đồ
```
Bước 2: Chạy thử ngay, không cần API key hay mạng
```powershell
python main.py all --demo
```
Chế độ `--demo` dùng dữ liệu giả lập đúng cấu trúc API, có cài sẵn 9 bản ghi lỗi để thấy bước làm sạch hoạt động.
Bước 3: Chạy với dữ liệu thật
Đăng ký tài khoản và lấy API key miễn phí tại https://www.football-data.org/client/register
Đặt key bằng biến môi trường (PowerShell):
```powershell
$env:FOOTBALL_API_KEY="key_cua_ban"
python main.py all                  # giải mặc định: PL
python main.py all --comp PD        # đổi sang La Liga
```
Chạy từng bước riêng lẻ
Lệnh	Việc làm	Kết quả
`python main.py fetch`	Thu thập từ API	`data/raw/matches_<giải>.json`
`python main.py clean`	Làm sạch, lưu file	`data/processed/matches_<giải>.csv`, `.json`, `rejected_<giải>.json`
`python main.py stats`	Đọc lại CSV, in 5 thống kê	In ra màn hình
`python main.py search ...`	Tìm kiếm, lọc, sắp xếp	Bảng kết quả
`python main.py sql`	(bonus) Nạp CSV vào SQLite, chạy SQL	In ra màn hình
`python main.py charts`	(bonus) Vẽ biểu đồ	`output/*.png`
Thêm `--demo` vào bất kỳ lệnh nào để dùng dữ liệu giả lập. Thêm `--comp <mã>` để đổi giải.
Ví dụ tìm kiếm
```powershell
python main.py search --team "sao" --status FINISHED --sort goals --desc --limit 5
```
```
Tìm thấy 10/56 trận (sắp xếp theo 'goals', giảm dần):

Ngày        Vòng  Đội nhà      Tỷ số  Đội khách    Trạng thái  Tổng bàn
----------  ----  -----------  -----  -----------  ----------  --------
2026-08-15  3     Sao Vàng FC  4-2    Thiên Long   FINISHED    6
2026-08-08  2     Sao Vàng FC  4-0    Sóng Biển    FINISHED    4
2026-09-19  8     Lửa Đỏ       1-3    Sao Vàng FC  FINISHED    4
2026-09-26  9     Sóng Biển    1-3    Sao Vàng FC  FINISHED    4
2026-08-29  5     Sao Vàng FC  2-1    Rồng Xanh    FINISHED    3
... còn 5 trận nữa (tăng --limit để xem thêm)
```
```powershell
python main.py search --from 2026-08-15 --to 2026-08-22 --sort margin --desc
```
Chạy kiểm thử tự động
```powershell
python -m unittest -v
```
24 test, không cần mạng.
---
3. Cấu trúc
```
football_tracker_v2/
├── main.py             # CLI điều phối toàn bộ pipeline
├── config.py           # Cấu hình: API key, giải đấu, timeout/retry, thư mục
├── fetch_data.py       # Thu thập từ API, xử lý lỗi nguồn dữ liệu
├── sample_data.py      # Dữ liệu giả lập (65 bản ghi, 9 bản ghi lỗi cài sẵn)
├── models.py           # dataclass Match (10 thuộc tính)
├── clean.py            # Làm sạch JSON thô → list[Match] + danh sách bị loại
├── storage.py          # Lưu / đọc lại CSV và JSON
├── search.py           # Tìm kiếm, lọc, sắp xếp
├── stats.py            # 5 thống kê bằng Python thuần
├── bonus_sql.py        # (bonus) SQLite + SQL
├── charts.py           # (bonus) Biểu đồ matplotlib
├── test_pipeline.py    # Kiểm thử tự động
├── requirements.txt
└── data/
    ├── raw/            # JSON thô từ API
    └── processed/      # CSV, JSON sạch và rejected_*.json
```
File	Vai trò
`config.py`	Cấu hình tập trung: API key (đọc từ biến môi trường), danh sách giải, `REQUEST_TIMEOUT=15`, `MAX_RETRIES=3`, `RETRY_WAIT=5`, đường dẫn thư mục
`fetch_data.py`	`fetch_matches()` gọi API và thử lại khi lỗi tạm thời; `_validate_payload()` kiểm tra định dạng; `FetchError` là lỗi riêng của bước này
`models.py`	`Match` là `dataclass`; `result` và `total_goals` là thuộc tính suy ra từ tỷ số
`clean.py`	`clean_matches()` trả về `(matches, rejects)`: bản ghi sạch và danh sách bản ghi bị loại kèm lý do
`storage.py`	`save_csv`, `save_json`, `save_rejects`, `load_csv`, `load_json`; `StorageError` là lỗi riêng của bước này
`search.py`	`filter_matches()` (lọc, các điều kiện kết hợp bằng AND) và `sort_matches()` (5 tiêu chí)
`stats.py`	5 hàm thống kê, chỉ tính trên các trận đã `FINISHED`
`main.py`	Đọc tham số dòng lệnh (`argparse`), gọi từng bước, bắt lỗi và in thông báo thân thiện
---
4. Chức năng
#	Chức năng	Mô tả	Lệnh / nơi dùng
1	Thu thập	Gọi API football-data.org, lưu JSON thô vào `data/raw/`	`main.py fetch`
2	Làm sạch	Bỏ khoảng trắng thừa, ép kiểu số nguyên, chuẩn hóa ngày về `date`, loại bản ghi trùng `id`, loại bản ghi lỗi (có ghi lý do)	`main.py clean`
3	Cấu trúc dữ liệu	Mỗi trận là một `dataclass Match`, toàn bộ dữ liệu là `list[Match]`	`models.py`
4	Lưu file	Ghi CSV (mã hóa `utf-8-sig` để Excel đọc đúng tiếng Việt) và JSON	`main.py clean`
5	Đọc lại file	Nạp CSV về `list[Match]`; dòng hỏng bị bỏ qua và đếm lại	`main.py stats`, `search`
6	Tìm kiếm / lọc	Theo tên đội (khớp một phần, không phân biệt hoa thường), trạng thái, khoảng ngày, vòng đấu, số bàn tối thiểu	`search --team --status --from --to --matchday --min-goals`
7	Sắp xếp	Theo `date`, `matchday`, `goals`, `margin`, `home`; tăng hoặc giảm dần	`search --sort <tiêu chí> [--desc]`
8	Thống kê	5 thống kê, mô tả bên dưới	`main.py stats`
5 thống kê
Hàm	Thống kê
`standings()`	Bảng xếp hạng tính từ kết quả (điểm, hiệu số bàn thắng, bàn thắng)
`team_form()`	Phong độ 5 trận gần nhất của mỗi đội (chuỗi `W`/`D`/`L`)
`home_advantage()`	Tỷ lệ đội nhà thắng, hòa, đội khách thắng và số bàn trung bình mỗi trận
`home_away_split()`	Số bàn trung bình mỗi đội ghi được khi đá sân nhà so với sân khách
`top_matches()`	Top trận nhiều bàn thắng nhất và top trận thắng cách biệt lớn nhất
Ví dụ output (dữ liệu demo):
```
=== 1. BẢNG XẾP HẠNG (tính từ kết quả) ===
#  Đội                Trận  T  H  B  BT  BB  HS  Điểm
1  Hải Âu United      10    8  2  0  20  7   13  26
2  Phượng Hoàng City  10    7  0  3  14  10  4   21
3  Sao Vàng FC        10    5  3  2  18  10  8   18
...

=== 3. LỢI THẾ SÂN NHÀ ===
Số trận đã đá: 40
Đội nhà thắng 35.0% | Hòa 17.5% | Đội khách thắng 47.5%
Trung bình 2.5 bàn/trận (đội nhà 1.15, đội khách 1.35)
```
Phần mở rộng (không bắt buộc)
`main.py sql`: nạp CSV vào SQLite, tính bảng xếp hạng bằng SQL và kiểm tra chéo với kết quả tính bằng Python (có trong test).
`main.py charts`: vẽ biểu đồ bằng matplotlib, lưu vào `output/`.
---
5. Lỗi và cách xử lý
Nguyên tắc thiết kế: dữ liệu lỗi không làm chương trình dừng đột ngột. Mọi lỗi đều được bắt, in thông báo tiếng Việt dễ hiểu kèm gợi ý, và mọi bản ghi bị loại đều có lý do được lưu lại.
5.1. Lỗi khi thu thập (`fetch_data.py`)
Tình huống	Chương trình xử lý	Bạn cần làm
Chưa đặt API key	Dừng, báo lỗi kèm lệnh đặt key và gợi ý `--demo`	Đặt `$env:FOOTBALL_API_KEY="..."`
Hết thời gian chờ (15 giây)	Thử lại tối đa 3 lần, chờ 5s, 10s, 15s	Kiểm tra mạng
Mất mạng / không kết nối được máy chủ	Thử lại tối đa 3 lần	Kiểm tra kết nối Internet
Lỗi chứng chỉ SSL	Thử lại, báo nguyên nhân có thể	Kiểm tra giờ hệ thống, VPN, antivirus
HTTP 401 / 403	Dừng ngay, báo key sai hoặc không có quyền với giải này	Kiểm tra lại key
HTTP 404	Dừng ngay, báo sai mã giải	Dùng mã hợp lệ: `PL`, `PD`, `SA`, `BL1`, `CL`
HTTP 429 (quá giới hạn)	Chờ theo header `Retry-After` rồi thử lại	Chờ khoảng 1 phút (free tier ~10 request/phút)
HTTP 5xx (lỗi máy chủ)	Thử lại tối đa 3 lần	Chạy lại sau
Phản hồi không phải JSON	Báo lỗi sai định dạng	Chạy lại hoặc dùng `--demo`
Thiếu khóa `matches` hoặc danh sách rỗng	Báo lỗi sai định dạng hoặc giải/mùa chưa có dữ liệu	Đổi giải hoặc mùa
Fetch thất bại nhưng đã có dữ liệu thô từ lần trước	Tự dùng lại file `data/raw/` cũ	Không cần làm gì
Fetch thất bại và chưa có dữ liệu cũ	Thoát với mã lỗi 1 và gợi ý `--demo`	Chạy `python main.py all --demo`
5.2. Dữ liệu sai định dạng khi làm sạch (`clean.py`)
Bản ghi lỗi bị loại, ghi lý do vào `data/processed/rejected_<giải>.json`, các bản ghi còn lại vẫn được xử lý bình thường.
Lỗi trong bản ghi	Xử lý
Thiếu hoặc sai `id`	Loại bản ghi
Trùng `id` với bản ghi trước	Loại bản ghi
Thiếu tên đội nhà / đội khách	Loại bản ghi
Đội nhà trùng đội khách	Loại bản ghi
Ngày sai định dạng	Loại bản ghi
Trạng thái lạ (không thuộc danh sách hợp lệ)	Loại bản ghi
Tỷ số không phải số nguyên, hoặc số âm	Loại bản ghi
Trận `FINISHED` nhưng thiếu tỷ số	Loại bản ghi
Vòng đấu sai định dạng	Giữ bản ghi, để trống vòng đấu (không quan trọng)
Trận chưa đá (SCHEDULED, TIMED) có tỷ số	Giữ bản ghi, xóa tỷ số
Ví dụ khi chạy `--demo` (65 bản ghi thô, 9 bản ghi lỗi):
```
[clean] Bản ghi thô: 65 | Hợp lệ: 56 | Bị loại: 9
         - 1 x trùng id với bản ghi trước
         - 1 x trận FINISHED nhưng thiếu tỷ số
         - 1 x thiếu tên đội nhà
         - 1 x ngày sai định dạng
         - 1 x tỷ số không phải số nguyên
         - 1 x tỷ số âm
         - 1 x trạng thái lạ
         - 1 x thiếu hoặc sai 'id'
         - 1 x đội nhà trùng đội khách
```
5.3. Lỗi khi đọc / ghi file (`storage.py`)
Tình huống	Chương trình xử lý	Bạn cần làm
Không tìm thấy file CSV/JSON	`StorageError`, gợi ý chạy `main.py clean` trước	Chạy `python main.py clean`
File CSV thiếu cột bắt buộc	`StorageError`, liệt kê cột thiếu	Chạy lại `clean` để tạo lại file
File hỏng / sai mã hóa	`StorageError` kèm chi tiết	Chạy lại `clean`
Một vài dòng hỏng trong file	Bỏ qua dòng đó, in cảnh báo và số dòng bị bỏ	Kiểm tra file nếu cần
Không còn dòng hợp lệ nào	`StorageError`	Chạy lại `clean`
5.4. Lỗi tham số dòng lệnh
Ngày sai định dạng (ví dụ `--from 15/08/2026`): báo "ngày phải có dạng YYYY-MM-DD".
Tiêu chí sắp xếp không hợp lệ: `argparse` chỉ chấp nhận `date`, `goals`, `home`, `margin`, `matchday`.
Mọi `FetchError`, `StorageError`, `ValueError` được bắt ở `main()`, in dạng `[LỖI] ...` và thoát với mã 1 thay vì hiện traceback.
---
Lưu ý và hạn chế
Bản ghi chưa đá (SCHEDULED, TIMED) vẫn được giữ nhưng tỷ số để trống; mọi thống kê chỉ tính trận `FINISHED`.
Với Champions League (`CL`), các trận chưa xác định đội (TBD) bị loại ở bước làm sạch vì thiếu tên đội. Đây là hành vi có chủ ý.
Free tier của football-data.org giới hạn khoảng 10 request/phút; mỗi lần chạy pipeline chỉ gọi 1 request.
Thống kê dùng Python thuần (`dict`, `Counter`, `sorted`), chưa dùng pandas.