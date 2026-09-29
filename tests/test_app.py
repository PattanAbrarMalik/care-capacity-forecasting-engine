"""Meaningful formula and REST checks using a disposable working database."""

import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analytics
import app
import store


class AnalyticsTests(unittest.TestCase):
    def test_gaps_flow_and_stock_are_distinct(self):
        rows = analytics.enriched([
            {"date": "2025-01-01", "cbp_custody": 10, "hhs_care": 100, "transfers": 8, "discharges": 3},
            {"date": "2025-01-04", "cbp_custody": 7, "hhs_care": 104, "transfers": 0, "discharges": 5},
        ])
        self.assertEqual(rows[1]["total_load"], 111)
        self.assertEqual(rows[1]["net_flow"], -5)
        self.assertIsNone(rows[1]["offset_ratio"])
        self.assertEqual(analytics.quality(rows)["unobserved_calendar_days"], 2)
        self.assertEqual(analytics.monthly(rows)[0]["average_load"], 110.5)

    def test_input_validation(self):
        valid = {"date": "2025-01-01", **dict.fromkeys(store.COLUMNS, 0)}
        self.assertEqual(store.validate(valid), valid)
        for changed in ({"hhs_care": -1}, {"hhs_care": 1.5}, {"hhs_care": True}, {"date": "2025-02-30"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                store.validate({**valid, **changed})


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db = store.DB
        store.DB = Path(cls.temp.name) / "test.sqlite3"
        store.initialize()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        store.DB = cls.old_db
        cls.temp.cleanup()

    def call(self, path, method="GET", payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base + path, data=body, method=method,
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request) as result:
                return result.status, json.load(result)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_live_routes_and_crud(self):
        self.assertEqual(self.call("/api/health")[1]["status"], "ok")
        status, initial = self.call("/api/observations?start=2025-12-21&end=2025-12-21")
        self.assertEqual((status, initial["summary"]["count"]), (200, 1))
        payload = {"date": "2026-03-01", **dict.fromkeys(store.COLUMNS, 1)}
        status, created = self.call("/api/observations", "POST", payload)
        self.assertEqual(status, 201)
        row_id = created["id"]
        self.assertEqual(self.call(f"/api/observations/{row_id}")[1]["date"], payload["date"])
        self.assertEqual(self.call("/api/observations", "POST", payload)[0], 409)
        status, updated = self.call(f"/api/observations/{row_id}", "PUT", {**payload, "hhs_care": 9})
        self.assertEqual((status, updated["hhs_care"]), (200, 9))
        self.assertEqual(self.call(f"/api/observations/{row_id}", "DELETE")[0], 200)
        self.assertEqual(self.call(f"/api/observations/{row_id}")[0], 404)
        self.assertEqual(self.call("/api/observations?start=bad")[0], 400)
        self.assertEqual(self.call("/api/forecast?days=14")[0], 200)
        status, research = self.call("/api/research")
        self.assertEqual(status, 200)
        self.assertTrue(research["matches_source"])
        self.assertTrue(research["models"]["available"])
        with urlopen(self.base) as result:
            self.assertIn(b"Understand the load", result.read())


if __name__ == "__main__":
    unittest.main()
