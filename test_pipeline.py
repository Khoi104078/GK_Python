"""
test_pipeline.py - Kiểm thử tự động. Chạy: python -m unittest -v

Bao gồm các tình huống lỗi của YÊU CẦU 10 (API lỗi, JSON sai định dạng, dữ liệu rỗng,
file hỏng...) được giả lập bằng mock nên không cần mạng.
"""
import os
import tempfile
import unittest
from unittest import mock

import requests

import bonus_sql
import clean
import config
import fetch_data
import sample_data
import search
import stats
import storage
from fetch_data import FetchError
from storage import StorageError


def demo_matches():
    matches, rejects = clean.clean_matches(sample_data.generate_sample_matches())
    return matches, rejects


class TestClean(unittest.TestCase):
    def test_counts_and_reasons(self):
        matches, rejects = demo_matches()
        self.assertEqual(len(matches), 56)        # 56 trận gốc (kể cả 2 trận "bẩn nhưng cứu được")
        self.assertEqual(len(rejects), 9)         # 9 bản ghi lỗi cài sẵn
        reasons = " | ".join(r["reason"] for r in rejects)
        for expected in ["trùng id", "thiếu tỷ số", "thiếu tên đội nhà", "ngày sai định dạng",
                         "không phải số", "tỷ số âm", "trạng thái lạ", "thiếu hoặc sai 'id'",
                         "đội nhà trùng đội khách"]:
            self.assertIn(expected, reasons)

    def test_normalization(self):
        raw = sample_data.generate_sample_matches()
        matches, _ = clean.clean_matches(raw)
        by_id = {m.match_id: m for m in matches}
        dirty = raw["matches"][1]                                    # id 1001: tên thừa khoảng trắng, tỷ số là chuỗi
        self.assertEqual(by_id[1001].home_team, dirty["homeTeam"]["name"])      # gộp khoảng trắng
        self.assertIsInstance(by_id[1001].home_score, int)                       # "2" -> 2
        self.assertIsInstance(by_id[1001].away_score, int)
        self.assertEqual(by_id[1002].status, "FINISHED")                         # "finished " -> "FINISHED"

    def test_unfinished_have_no_score(self):
        matches, _ = demo_matches()
        scheduled = [m for m in matches if m.status == "SCHEDULED"]
        self.assertTrue(scheduled)
        self.assertTrue(all(m.home_score is None and m.total_goals is None for m in scheduled))

    def test_bad_top_level(self):
        with self.assertRaises(ValueError):
            clean.clean_matches({"oops": 1})
        with self.assertRaises(ValueError):
            clean.clean_matches([1, 2, 3])


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.matches, _ = demo_matches()

    def tearDown(self):
        self.tmp.cleanup()

    def test_csv_roundtrip(self):
        path = storage.save_csv(self.matches, os.path.join(self.tmp.name, "m.csv"))
        loaded = storage.load_csv(path)
        self.assertEqual([m.to_dict() for m in loaded], [m.to_dict() for m in self.matches])

    def test_json_roundtrip(self):
        path = storage.save_json(self.matches, os.path.join(self.tmp.name, "m.json"))
        loaded = storage.load_json(path)
        self.assertEqual([m.to_dict() for m in loaded], [m.to_dict() for m in self.matches])

    def test_missing_and_broken_files(self):
        with self.assertRaises(StorageError):
            storage.load_csv(os.path.join(self.tmp.name, "khong_ton_tai.csv"))
        bad_json = os.path.join(self.tmp.name, "bad.json")
        with open(bad_json, "w", encoding="utf-8") as f:
            f.write("{không phải json")
        with self.assertRaises(StorageError):
            storage.load_json(bad_json)

    def test_missing_columns(self):
        path = os.path.join(self.tmp.name, "thieu_cot.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("a,b\n1,2\n")
        with self.assertRaises(StorageError):
            storage.load_csv(path)

    def test_bad_rows_are_skipped(self):
        path = storage.save_csv(self.matches[:3], os.path.join(self.tmp.name, "m.csv"))
        with open(path, "a", encoding="utf-8") as f:
            f.write("xyz,1,ngay-sai,A,B,FINISHED,1,0,H,1\n")
        loaded = storage.load_csv(path)
        self.assertEqual(len(loaded), 3)


class TestSearchSort(unittest.TestCase):
    def setUp(self):
        self.matches, _ = demo_matches()

    def test_filter_team_case_insensitive(self):
        found = search.filter_matches(self.matches, team="  SAO vàng ")
        self.assertTrue(found)
        self.assertTrue(all("sao vàng" in (m.home_team + m.away_team).lower() for m in found))

    def test_filter_combined(self):
        found = search.filter_matches(self.matches, status="finished", min_goals=4, matchday=None)
        self.assertTrue(all(m.is_finished and m.total_goals >= 4 for m in found))
        none = search.filter_matches(self.matches, team="không có đội này")
        self.assertEqual(none, [])

    def test_sort(self):
        by_goals = search.sort_matches(search.filter_matches(self.matches, status="FINISHED"), "goals", True)
        goals = [m.total_goals for m in by_goals]
        self.assertEqual(goals, sorted(goals, reverse=True))
        by_date = search.sort_matches(self.matches, "date")
        self.assertEqual([m.match_date for m in by_date], sorted(m.match_date for m in by_date))
        with self.assertRaises(ValueError):
            search.sort_matches(self.matches, "khong_co")


class TestStats(unittest.TestCase):
    def setUp(self):
        self.matches, _ = demo_matches()

    def test_standings_consistency(self):
        finished = [m for m in self.matches if m.is_finished]
        table = stats.standings(self.matches)
        self.assertEqual(sum(r["played"] for r in table), 2 * len(finished))
        self.assertEqual(sum(r["gf"] for r in table), sum(r["ga"] for r in table))
        for r in table:
            self.assertEqual(r["played"], r["won"] + r["draw"] + r["lost"])
            self.assertEqual(r["points"], 3 * r["won"] + r["draw"])

    def test_home_advantage_sums_to_100(self):
        ha = stats.home_advantage(self.matches)
        self.assertAlmostEqual(ha["home_win_pct"] + ha["draw_pct"] + ha["away_win_pct"], 100, delta=0.2)

    def test_empty_input(self):
        self.assertEqual(stats.standings([]), [])
        self.assertEqual(stats.home_advantage([])["matches"], 0)

    def test_python_standings_match_sql_standings(self):
        """Hai cách tính độc lập (Python vs SQL) phải ra cùng kết quả."""
        with tempfile.TemporaryDirectory() as tmp:
            conn = bonus_sql.build_database(self.matches, os.path.join(tmp, "t.db"))
            sql_rows = conn.execute(bonus_sql.STANDINGS_SQL).fetchall()
            conn.close()
        py_rows = stats.standings(self.matches)
        self.assertEqual([(r["team"], r["points"], r["gd"]) for r in py_rows],
                         [(r["team"], r["points"], r["gd"]) for r in sql_rows])


def fake_response(status=200, json_data=None, json_error=False, headers=None):
    resp = mock.Mock()
    resp.status_code = status
    resp.headers = headers or {}
    if json_error:
        resp.json.side_effect = ValueError("not json")
    else:
        resp.json.return_value = json_data
    return resp


@mock.patch("fetch_data.time.sleep", lambda s: None)
@mock.patch.object(config, "API_KEY", "key-gia")
class TestFetchErrors(unittest.TestCase):
    GOOD = {"matches": [{"id": 1}]}

    def test_no_api_key(self):
        with mock.patch.object(config, "API_KEY", ""):
            with self.assertRaises(FetchError) as ctx:
                fetch_data.fetch_matches("PL")
        self.assertIn("API key", str(ctx.exception))

    @mock.patch("fetch_data.requests.get")
    def test_success(self, get):
        get.return_value = fake_response(200, self.GOOD)
        self.assertEqual(fetch_data.fetch_matches("PL"), self.GOOD)

    @mock.patch("fetch_data.requests.get")
    def test_auth_and_not_found_do_not_retry(self, get):
        for status in (401, 403, 404):
            get.reset_mock()
            get.return_value = fake_response(status)
            with self.assertRaises(FetchError):
                fetch_data.fetch_matches("PL")
            self.assertEqual(get.call_count, 1)

    @mock.patch("fetch_data.requests.get")
    def test_rate_limit_then_success(self, get):
        get.side_effect = [fake_response(429, headers={"Retry-After": "1"}), fake_response(200, self.GOOD)]
        self.assertEqual(fetch_data.fetch_matches("PL"), self.GOOD)
        self.assertEqual(get.call_count, 2)

    @mock.patch("fetch_data.requests.get")
    def test_timeout_exhausts_retries(self, get):
        get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(FetchError) as ctx:
            fetch_data.fetch_matches("PL")
        self.assertEqual(get.call_count, config.MAX_RETRIES)
        self.assertIn("hết thời gian", str(ctx.exception))

    @mock.patch("fetch_data.requests.get")
    def test_ssl_error_message(self, get):
        get.side_effect = requests.exceptions.SSLError("cert")
        with self.assertRaises(FetchError) as ctx:
            fetch_data.fetch_matches("PL")
        self.assertIn("SSL", str(ctx.exception))

    @mock.patch("fetch_data.requests.get")
    def test_server_error_retries(self, get):
        get.return_value = fake_response(503)
        with self.assertRaises(FetchError):
            fetch_data.fetch_matches("PL")
        self.assertEqual(get.call_count, config.MAX_RETRIES)

    @mock.patch("fetch_data.requests.get")
    def test_bad_payloads(self, get):
        cases = [fake_response(200, json_error=True),            # không phải JSON
                 fake_response(200, ["a", "list"]),              # sai kiểu
                 fake_response(200, {"khong_co": 1}),            # thiếu 'matches'
                 fake_response(200, {"matches": "abc"}),         # 'matches' sai kiểu
                 fake_response(200, {"matches": []})]            # rỗng
        for resp in cases:
            get.return_value = resp
            with self.assertRaises(FetchError):
                fetch_data.fetch_matches("PL")


if __name__ == "__main__":
    unittest.main()
