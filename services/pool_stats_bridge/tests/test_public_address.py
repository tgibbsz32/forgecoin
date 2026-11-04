"""Native C pool public-address lookup: read-only, local-only, no balances."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from services.pool_stats_bridge.app import (
    PreviewHandler, StatsBridgeError, fetch_miner_stats,
    normalize_miner_stats, public_miner_payload, validate_public_address,
)

ADDRESS = "4" + "A" * 94
PRIVATE_FIELDS = {
    "miner_hashrate": 54000,
    "miner_hashrate_stats": [54000, 53000, 51000, 45000, 20000, 10000],
    "worker_count": 3,
    "miner_balance": 987654321.12345678,
    "payment_threshold": 0.8,
    "pool_port": 12345,
    "wallet_private_key": "FAKE_SECRET_DO_NOT_ECHO",
}

class AddressContractTests(unittest.TestCase):
    def test_strict_base58_syntax_only(self):
        self.assertEqual(validate_public_address(ADDRESS), ADDRESS)
        for invalid in (None, 1, "", "4" * 89, "4" * 141,
                        "4" * 94 + "0", "4" * 94 + "I",
                        "4" * 94 + "O", "4" * 94 + "l",
                        "4" * 95 + "\n", "4" * 94 + ";",
                        "4" * 94 + "=", "seed phrase here",
                        "4" * 94 + "\u00e9"):
            with self.subTest(value=str(invalid)[:16]), self.assertRaises(StatsBridgeError):
                validate_public_address(invalid)

    def test_no_monetary_or_secret_data_forwarded(self):
        public = normalize_miner_stats(PRIVATE_FIELDS)
        self.assertEqual(public, {
            "hashrate": 54000, "workers": 3,
            "hashrateWindows": [54000, 53000, 51000, 45000, 20000, 10000],
        })
        for secret in ("miner_balance", "wallet_private_key", "pool_port",
                       "payment_threshold", "FAKE_SECRET"):
            self.assertNotIn(secret, json.dumps(public))

    def test_invalid_metrics_fail_closed(self):
        for key, value in (
            ("miner_hashrate", -1), ("miner_hashrate", True),
            ("worker_count", 2.3), ("worker_count", 2**64),
            ("miner_hashrate_stats", [1, 2]),
            ("miner_hashrate_stats", ["3"] * 6),
            ("miner_hashrate_stats", [True] * 6),
        ):
            with self.subTest(key=key, value=str(value)[:30]):
                with self.assertRaises(StatsBridgeError):
                    normalize_miner_stats(dict(PRIVATE_FIELDS, **{key: value}))

    def test_preview_never_claims_launch_or_payout(self):
        self.assertEqual(public_miner_payload(None, ADDRESS)[0], 503)
        self.assertEqual(public_miner_payload(None, "not an address")[0], 400)
        code, payload = public_miner_payload(
            "http://127.0.0.1:4243/stats", ADDRESS,
            fetcher=lambda endpoint, addr: normalize_miner_stats(PRIVATE_FIELDS))
        self.assertEqual(code, 200)
        self.assertFalse(payload["launchApproved"])
        self.assertEqual(payload["state"], "backend_observed_unverified")
        self.assertEqual(payload["stats"]["workers"], 3)
        self.assertNotIn(ADDRESS, json.dumps(payload))
        self.assertNotIn("miner_balance", json.dumps(payload))
        self.assertEqual(public_miner_payload(
            "http://127.0.0.1:4243/stats", ADDRESS,
            fetcher=lambda endpoint, addr: (_ for _ in ()).throw(OSError("offline"))
        )[0], 503)


class PoolAddressHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seen = []
        class PoolFixture(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_GET(self):
                cls.seen.append((self.path, self.headers.get("Cookie")))
                body = json.dumps(PRIVATE_FIELDS).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        cls.pool = HTTPServer(("127.0.0.1", 0), PoolFixture)
        cls.pool_thread = threading.Thread(target=cls.pool.serve_forever, daemon=True)
        cls.pool_thread.start()
        cls.upstream = "http://127.0.0.1:{}/stats".format(cls.pool.server_port)
        Handler = type("TestHandler", (PreviewHandler,), {"upstream": cls.upstream})
        cls.bridge = HTTPServer(("127.0.0.1", 0), Handler)
        cls.bridge_thread = threading.Thread(target=cls.bridge.serve_forever, daemon=True)
        cls.bridge_thread.start()
        cls.url = "http://127.0.0.1:{}".format(cls.bridge.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()
        cls.pool.shutdown()
        cls.bridge_thread.join(timeout=3)
        cls.pool_thread.join(timeout=3)
        cls.bridge.server_close()
        cls.pool.server_close()

    def get(self, path):
        try:
            with urlopen(self.url + path, timeout=3) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()

    def test_local_cookie_lookup_proxies_only_nonmonetary_stats(self):
        raw = fetch_miner_stats(self.upstream, ADDRESS)
        self.assertEqual(raw["hashrate"], 54000)
        self.assertEqual(raw["workers"], 3)
        self.assertEqual(self.seen[-1], ("/stats", "wa=" + ADDRESS))
        code, headers, body = self.get("/api/miner-stats?address=" + quote(ADDRESS))
        self.assertEqual(code, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        data = json.loads(body)
        self.assertEqual(data["stats"]["hashrateWindows"][0], 54000)
        self.assertFalse(data["launchApproved"])
        self.assertNotIn("miner_balance", body.decode())
        self.assertNotIn("FAKE_SECRET", body.decode())
        self.assertEqual(self.seen[-1], ("/stats", "wa=" + ADDRESS))

    def test_malformed_or_duplicate_query_never_contacts_pool(self):
        for query in ("", "?address=a", "?address=" + ADDRESS + "&address=" + ADDRESS,
                      "?address=" + ADDRESS + "&secret=x",
                      "?a=" + ADDRESS, "?address=%0D" + ADDRESS,
                      "?address=" + ADDRESS + "%3Babc",
                      "?address=" + "A" * 300):
            before = len(self.seen)
            code, _, body = self.get("/api/miner-stats" + query)
            self.assertEqual(code, 400, query)
            self.assertEqual(len(self.seen), before, query)
            self.assertFalse(json.loads(body)["launchApproved"])

    def test_no_miner_payout_admin_route(self):
        for path in ("/api/payout", "/api/miner-balance", "/api/miner-stats/../payout",
                     "/api/miner-stats?foo=bar"):
            self.assertIn(self.get(path)[0], (400, 404))


if __name__ == "__main__":
    unittest.main()
