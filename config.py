"""
config.py - Cấu hình chung của project.

API key miễn phí: https://www.football-data.org/client/register
Đặt key bằng biến môi trường (PowerShell):
    $env:FOOTBALL_API_KEY="key_cua_ban"
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Nguồn dữ liệu ---
API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
BASE_URL = "https://api.football-data.org/v4"

COMPETITIONS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "CL": "Champions League",
}
DEFAULT_COMPETITION = "PL"   # đổi giải đấu ở đây (hoặc dùng --comp khi chạy)

# --- Xử lý lỗi mạng ---
REQUEST_TIMEOUT = 15   # giây chờ tối đa cho mỗi request
MAX_RETRIES = 3        # số lần thử lại khi lỗi mạng / 429 / 5xx
RETRY_WAIT = 5         # giây chờ giữa các lần thử (nhân theo số lần thử)

# --- Thư mục dữ liệu ---
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")              # JSON thô từ API
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")  # CSV/JSON đã làm sạch
OUTPUT_DIR = os.path.join(BASE_DIR, "output")                # biểu đồ, v.v.
DB_PATH = os.path.join(BASE_DIR, "data", "football.db")      # chỉ dùng cho phần SQL (bonus)
