"""
storage.py - Lưu và đọc lại dữ liệu ĐÃ LÀM SẠCH.

>>> YÊU CẦU 5 : lưu CSV và JSON (save_csv, save_json)
>>> YÊU CẦU 6 : đọc lại từ file về list[Match] (load_csv, load_json)
>>> YÊU CẦU 10: file thiếu / rỗng / hỏng / có dòng sai định dạng -> báo lỗi rõ ràng,
              dòng hỏng bị bỏ qua và đếm lại thay vì làm chương trình văng
"""
import csv
import json
import os

import config
from models import FIELDS, Match


class StorageError(Exception):
    """Lỗi đọc/ghi file (thông báo viết sẵn cho người dùng)."""


def processed_path(competition: str, ext: str) -> str:
    return os.path.join(config.PROCESSED_DIR, f"matches_{competition}.{ext}")


# ----------------------------- GHI -----------------------------
def save_csv(matches: list, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:   # utf-8-sig: Excel đọc đúng tiếng Việt
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for m in matches:
            writer.writerow({k: ("" if v is None else v) for k, v in m.to_dict().items()})
    return path


def save_json(matches: list, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([m.to_dict() for m in matches], f, ensure_ascii=False, indent=2)
    return path


def save_rejects(rejects: list, path: str) -> str:
    """Ghi nhật ký các bản ghi bị loại khi làm sạch (để chứng minh bước làm sạch)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rejects, f, ensure_ascii=False, indent=2)
    return path


# ----------------------------- ĐỌC -----------------------------
def _rows_to_matches(rows, source: str):
    matches, bad = [], 0
    for i, row in enumerate(rows, start=1):
        try:
            matches.append(Match.from_dict(row))
        except (ValueError, TypeError) as e:
            bad += 1
            print(f"[storage] Bỏ qua dòng {i} của {os.path.basename(source)}: {e}")
    if not matches:
        raise StorageError(f"File {source} không có dòng dữ liệu hợp lệ nào.")
    if bad:
        print(f"[storage] Cảnh báo: {bad} dòng hỏng đã bị bỏ qua.")
    return matches


def load_csv(path: str) -> list:
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            missing = set(FIELDS[:8]) - set(reader.fieldnames or [])
            if missing:
                raise StorageError(f"File CSV thiếu cột: {sorted(missing)}")
            return _rows_to_matches(list(reader), path)
    except FileNotFoundError:
        raise StorageError(f"Không tìm thấy file: {path}. Hãy chạy 'python main.py clean' trước.")
    except (csv.Error, UnicodeDecodeError) as e:
        raise StorageError(f"File CSV bị hỏng ({path}): {e}")


def load_json(path: str) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise StorageError(f"Không tìm thấy file: {path}. Hãy chạy 'python main.py clean' trước.")
    except json.JSONDecodeError as e:
        raise StorageError(f"File JSON bị hỏng ({path}): {e}")
    if not isinstance(data, list):
        raise StorageError(f"File JSON sai định dạng (cần một danh sách): {path}")
    return _rows_to_matches(data, path)
