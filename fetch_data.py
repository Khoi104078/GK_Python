"""
fetch_data.py - Thu thập dữ liệu trận đấu từ football-data.org.

>>> YÊU CẦU 1 : thu thập từ nguồn trực tuyến (API football-data.org)
>>> YÊU CẦU 10: xử lý khi API không trả dữ liệu / trả sai định dạng
    - thiếu API key, hết thời gian chờ, mất mạng / lỗi SSL
    - 401/403 (key sai), 404 (sai mã giải), 429 (quá giới hạn), 5xx (lỗi server)
    - phản hồi không phải JSON, thiếu khóa "matches", danh sách trận rỗng
"""
import json
import os
import time

import requests

import config


class FetchError(Exception):
    """Lỗi khi lấy dữ liệu (thông báo đã viết sẵn cho người dùng đọc)."""


def raw_path(competition: str) -> str:
    return os.path.join(config.RAW_DIR, f"matches_{competition}.json")


def _validate_payload(data) -> None:
    """>>> YÊU CẦU 10: kiểm tra dữ liệu API trả về có đúng định dạng và không rỗng."""
    if not isinstance(data, dict):
        raise FetchError("API trả về dữ liệu sai định dạng (không phải đối tượng JSON).")
    if "matches" not in data or not isinstance(data["matches"], list):
        raise FetchError("Phản hồi thiếu danh sách 'matches' (sai định dạng).")
    if len(data["matches"]) == 0:
        raise FetchError("API trả về danh sách trận đấu RỖNG (giải/mùa này chưa có dữ liệu).")


def save_raw(data: dict, competition: str) -> str:
    os.makedirs(config.RAW_DIR, exist_ok=True)
    path = raw_path(competition)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_raw(competition: str) -> dict:
    """Đọc lại JSON thô đã lưu (dùng cho bước làm sạch hoặc khi không có mạng)."""
    path = raw_path(competition)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FetchError(f"Chưa có dữ liệu thô: {path}. Hãy chạy 'python main.py fetch' trước.")
    except json.JSONDecodeError as e:
        raise FetchError(f"File dữ liệu thô bị hỏng ({path}): {e}")
    _validate_payload(data)
    return data


def fetch_matches(competition: str = config.DEFAULT_COMPETITION, season: int = None) -> dict:
    """Gọi API lấy toàn bộ trận của 1 giải; thử lại khi lỗi tạm thời. Trả về dict JSON thô."""
    if not config.API_KEY:
        raise FetchError(
            "Chưa có API key. Đăng ký tại football-data.org rồi chạy:\n"
            '    $env:FOOTBALL_API_KEY="key_cua_ban"      (PowerShell)\n'
            "Hoặc chạy thử không cần key: python main.py all --demo"
        )

    url = f"{config.BASE_URL}/competitions/{competition}/matches"
    params = {"season": season} if season else {}
    headers = {"X-Auth-Token": config.API_KEY}
    last_error = "không rõ nguyên nhân"

    for attempt in range(1, config.MAX_RETRIES + 1):
        wait = config.RETRY_WAIT * attempt
        try:
            resp = requests.get(url, headers=headers, params=params,
                                timeout=config.REQUEST_TIMEOUT)
        except requests.exceptions.SSLError as e:
            last_error = f"lỗi chứng chỉ SSL (kiểm tra giờ hệ thống / VPN / antivirus): {e}"
        except requests.exceptions.Timeout:
            last_error = f"hết thời gian chờ ({config.REQUEST_TIMEOUT}s)"
        except requests.exceptions.ConnectionError as e:
            last_error = f"không kết nối được mạng/máy chủ: {e}"
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Lỗi request không xác định: {e}")
        else:
            code = resp.status_code
            if code == 200:
                try:
                    data = resp.json()
                except ValueError:
                    raise FetchError("API trả về nội dung KHÔNG phải JSON (sai định dạng).")
                _validate_payload(data)
                return data
            if code in (401, 403):
                raise FetchError(f"HTTP {code}: API key sai hoặc không có quyền với giải '{competition}'.")
            if code == 404:
                raise FetchError(f"HTTP 404: không tìm thấy giải '{competition}' (sai mã giải?).")
            if code == 429:
                last_error = "HTTP 429: vượt giới hạn số request (free tier ~10 request/phút)"
                try:
                    wait = max(wait, int(resp.headers.get("Retry-After", 0)))
                except ValueError:
                    pass
            elif 500 <= code < 600:
                last_error = f"HTTP {code}: lỗi phía máy chủ"
            else:
                raise FetchError(f"HTTP {code}: phản hồi không mong đợi.")

        if attempt < config.MAX_RETRIES:
            print(f"[fetch] Lần {attempt}/{config.MAX_RETRIES} lỗi ({last_error}); thử lại sau {wait}s...")
            time.sleep(wait)

    raise FetchError(f"Thất bại sau {config.MAX_RETRIES} lần thử: {last_error}")


def fetch_and_save(competition: str = config.DEFAULT_COMPETITION) -> dict:
    data = fetch_matches(competition)
    path = save_raw(data, competition)
    print(f"[fetch] Đã lấy {len(data['matches'])} bản ghi thô -> {path}")
    return data
