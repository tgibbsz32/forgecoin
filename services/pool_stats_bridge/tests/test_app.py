"""No wallets, daemon, mining, Internet, or upstream pool needed."""
import json
import threading
import unittest
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest.mock import patch

from services.pool_stats_bridge.app import (
    PreviewHandler, StatsBridgeError, fetch_stats, normalize_stats,
    public_payload, validate_upstream, SITE_DIR,
)


STATS = {
    "pool_hashrate": 35678,
    "network_hashrate": 5000000,
    "network_difficulty": 600000000,
    "network_height": 12345,
    "connected_miners": 9,
    "pool_blocks_found": 23,
    "round_hashes": 987654321,
    "last_block_found": 1760000000,
    "last_template_fetched": 1760000032,
    "pool_fee": .01,
    "miner_balance": 12000.55,  # PRIVATE/account-bound field must never propagate
    "miner_hashrate": 3000,
    "worker_count": 1,
    "pool_port": 3333,
}


class StatsValidationTests(unittest.TestCase):
    def test_correct_upstream_contract_and_fee_fraction(self):
        data = normalize_stats(STATS)
        self.assertEqual(data["poolHashrate"], 35678)
        self.assertEqual(data["networkHeight"], 12345)
        self.assertEqual(data["poolFeePercent"], 1.0)
        self.assertEqual(data["roundHashes"], 987654321)
        self.assertEqual(len(data), 10)
        self.assertNotIn("miner_balance", data)
        self.assertNotIn("miner_hashrate", data)
        self.assertNotIn("pool_port", data)

    def test_refuse_remote_upstreams_credentials_path_and_query(self):
        bad = [
            "http://example.com:4243/stats",
            "https://127.0.0.1:4243/stats",
            "http://localhost:4243/stats",
            "http://127.0.0.1:4243/admin",
            "http://127.0.0.1:4243/stats?wa=secret",
            "http://u:p@127.0.0.1:4243/stats",
            "http://127.0.0.1:4243/stats#test",
            "http://127.0.0.1/stats",
            "http://127.0.0.1:99999/stats",
            "file:///etc/passwd",
        ]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(StatsBridgeError):
                validate_upstream(value)
        self.assertEqual(
            validate_upstream("http://127.0.0.1:4243/stats"),
            "http://127.0.0.1:4243/stats",
        )

    def test_missing_negative_nonfinite_fractional_and_boolean_metrics(self):
        for key in [
            "pool_hashrate", "network_height", "network_difficulty",
            "round_hashes", "pool_blocks_found",
        ]:
            with self.subTest(key=key):
                bad = dict(STATS)
                bad.pop(key)
                with self.assertRaises(StatsBridgeError):
                    normalize_stats(bad)
        bad_values = [-1, 1.2, False, None, "5", 2**64, float("inf")]
        for value in bad_values:
            with self.subTest(value=value):
                bad = dict(STATS, network_height=value)
                with self.assertRaises(StatsBridgeError):
                    normalize_stats(bad)
        for fee in (-.1, 1.5, "1", None, float("nan"), float("inf"), True):
            with self.subTest(fee=fee):
                with self.assertRaises(StatsBridgeError):
                    normalize_stats(dict(STATS, pool_fee=fee))

    def test_no_upstream_or_invalid_source_never_reports_live(self):
        code, result = public_payload(None)
        self.assertEqual(code, 503)
        self.assertEqual(result["state"], "not_connected")
        self.assertFalse(result["launchApproved"])
        self.assertNotIn("stats", result)

        code, result = public_payload("http://127.0.0.1:4243/stats",
                                      fetcher=lambda url: (_ for _ in ()).throw(OSError("offline")))
        self.assertEqual(code, 503)
        self.assertEqual(result["state"], "unavailable")
        self.assertNotIn("stats", result)

    def test_real_data_is_labelled_unverified_not_launched(self):
        code, data = public_payload(
            "http://127.0.0.1:4243/stats", fetcher=lambda url: normalize_stats(STATS)
        )
        self.assertEqual(code, 200)
        self.assertEqual(data["state"], "backend_observed_unverified")
        self.assertFalse(data["launchApproved"])
        self.assertEqual(data["stats"]["connectedMiners"], 9)
        self.assertNotIn("miner_balance", str(data))

    def test_real_local_fixture_stats_source_no_external_requests(self):
        from http.server import BaseHTTPRequestHandler
        class FixtureHandler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                if self.path != "/stats":
                    self.send_error(404)
                    return
                body = json.dumps(STATS).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        source = HTTPServer(("127.0.0.1", 0), FixtureHandler)
        thread = threading.Thread(target=source.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{source.server_port}/stats"
            result = fetch_stats(url)
            self.assertEqual(result["poolBlocksFound"], 23)
            self.assertEqual(result["poolFeePercent"], 1.0)
            self.assertNotIn("miner_balance", result)
            code, payload = public_payload(url)
            self.assertEqual(code, 200)
            self.assertFalse(payload["launchApproved"])
        finally:
            source.shutdown()
            thread.join(timeout=3)
            source.server_close()

    def test_http_response_malformed_json_and_large_body_fail_closed(self):
        class FakeResponse:
            status = 200
            def __init__(self, value):
                self.value = value
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, n):
                return self.value[:n]

        from services.pool_stats_bridge.app import build_opener
        for data in [b"", b"[]", b"{}", b'{"network_height":NaN}',
                     b"x" * (65536 + 1)]:
            with self.subTest(prefix=data[:25]), patch(
                "services.pool_stats_bridge.app.build_opener"
            ) as opener:
                opener.return_value.open.return_value = FakeResponse(data)
                with self.assertRaises((StatsBridgeError, ValueError)):
                    fetch_stats("http://127.0.0.1:4243/stats")


class HttpPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), PreviewHandler)
        cls.url = "http://127.0.0.1:" + str(cls.server.server_port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=3)
        cls.server.server_close()

    def get(self, path):
        try:
            with urlopen(self.url + path, timeout=3) as response:
                return response.status, response.headers, response.read()
        except HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_offline_stats_are_not_fabricated(self):
        status, headers, body = self.get("/api/pool-stats")
        self.assertEqual(status, 503)
        data = json.loads(body)
        self.assertFalse(data["launchApproved"])
        self.assertEqual(data["state"], "not_connected")
        self.assertNotIn("stats", data)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])

    def test_dashboard_and_assets_work_without_any_backend(self):
        for path in ["/", "/dashboard.html", "/dashboard.css",
                     "/dashboard.js", "/assets/forgecoin-logo.png"]:
            with self.subTest(path=path):
                status, _, data = self.get(path)
                self.assertEqual(status, 200)
                self.assertGreater(len(data), 20)
        _, _, body = self.get("/dashboard.html")
        self.assertIn(b"Mining pool", body)

    def test_no_wallet_rpc_or_path_traversal(self):
        for path in ["/json_rpc", "/workers", "/stats",
                     "/.env", "/README.md", "/../../etc/passwd",
                     "/api/miner-balance", "/api/withdraw"]:
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 404)


if __name__ == "__main__":
    unittest.main()
