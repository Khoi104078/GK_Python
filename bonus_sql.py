"""
bonus_sql.py - PHẦN MỞ RỘNG (không bắt buộc theo đề): đưa dữ liệu đã làm sạch vào SQLite
và phân tích bằng SQL. Pipeline: CSV -> SQLite -> truy vấn SQL.

Chạy: python main.py sql [--demo]
Học được: JOIN-free CTE, UNION ALL, GROUP BY + CASE, window function ROW_NUMBER.
"""
import os
import sqlite3

import config
import storage

SCHEMA = """
DROP TABLE IF EXISTS matches;
CREATE TABLE matches (
    match_id    INTEGER PRIMARY KEY,
    matchday    INTEGER,
    match_date  TEXT NOT NULL,
    home_team   TEXT NOT NULL,
    away_team   TEXT NOT NULL,
    status      TEXT NOT NULL,
    home_score  INTEGER,
    away_score  INTEGER
);
"""

# Bảng xếp hạng bằng SQL: "duỗi phẳng" mỗi trận thành 2 dòng (góc nhìn đội nhà + đội khách)
STANDINGS_SQL = """
WITH t AS (
    SELECT home_team AS team, home_score AS gf, away_score AS ga FROM matches WHERE status = 'FINISHED'
    UNION ALL
    SELECT away_team,         away_score,       home_score       FROM matches WHERE status = 'FINISHED'
)
SELECT team,
       COUNT(*)                                             AS played,
       SUM(gf > ga)                                         AS won,
       SUM(gf = ga)                                         AS draw,
       SUM(gf < ga)                                         AS lost,
       SUM(gf)                                              AS gf,
       SUM(ga)                                              AS ga,
       SUM(gf) - SUM(ga)                                    AS gd,
       SUM(CASE WHEN gf > ga THEN 3 WHEN gf = ga THEN 1 ELSE 0 END) AS points
FROM t
GROUP BY team
ORDER BY points DESC, gd DESC, gf DESC, team
"""

# Phong độ 3 trận gần nhất bằng window function
FORM_SQL = """
WITH t AS (
    SELECT home_team AS team, match_date, match_id,
           CASE WHEN home_score > away_score THEN 3 WHEN home_score = away_score THEN 1 ELSE 0 END AS pts
    FROM matches WHERE status = 'FINISHED'
    UNION ALL
    SELECT away_team, match_date, match_id,
           CASE WHEN away_score > home_score THEN 3 WHEN away_score = home_score THEN 1 ELSE 0 END
    FROM matches WHERE status = 'FINISHED'
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY team ORDER BY match_date DESC, match_id DESC) AS rn FROM t
)
SELECT team, SUM(pts) AS form_points
FROM ranked WHERE rn <= 3
GROUP BY team ORDER BY form_points DESC, team
"""

BIGGEST_WIN_SQL = """
SELECT match_date, home_team, away_team, home_score, away_score,
       ABS(home_score - away_score) AS margin
FROM matches WHERE status = 'FINISHED'
ORDER BY margin DESC, match_date LIMIT 5
"""


def build_database(matches: list, db_path: str = config.DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(m.match_id, m.matchday, m.match_date.isoformat(), m.home_team, m.away_team,
          m.status, m.home_score, m.away_score) for m in matches])
    conn.commit()
    return conn


def _show(title: str, rows) -> None:
    print(f"\n=== {title} ===")
    for r in rows:
        print("  ".join(f"{k}={r[k]}" for k in r.keys()))


def run(csv_file: str) -> None:
    matches = storage.load_csv(csv_file)
    conn = build_database(matches)
    print(f"[sql] Đã nạp {len(matches)} trận vào {config.DB_PATH}")
    _show("SQL: BẢNG XẾP HẠNG", conn.execute(STANDINGS_SQL).fetchall())
    _show("SQL: PHONG ĐỘ 3 TRẬN GẦN NHẤT (window function)", conn.execute(FORM_SQL).fetchall())
    _show("SQL: 5 TRẬN THẮNG ĐẬM NHẤT", conn.execute(BIGGEST_WIN_SQL).fetchall())
    conn.close()
