"""Read-only, localhost-only ForgeCoin pool UI preview and upstream stats bridge.

No Stratum socket, wallet RPC, keys, template issuance, payout, account lookup,
block submission or mining is possible here. No upstream? Return unavailable,
not illustrative figures. jfgrassie's original JSON /stats is an aggregate
interface; miner_balance is deliberately NOT proxied until FRG atomic units
and payout ownership are independently validated.

Example:
  python -m services.pool_stats_bridge.app --port 48775
Optional (only after a separately audited/isolated upstream is running):
  set FRG_POOL_STATS_UPSTREAM=http://127.0.0.1:4243/stats
"""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener

MAX_RESPONSE_BYTES = 65536
MAX_U64 = 2**64 - 1
ALLOWED_ASSETS = {
    "/dashboard.html": ("dashboard.html", "text/html; charset=utf-8"),
    "/dashboard.css": ("dashboard.css", "text/css; charset=utf-8"),
    "/dashboard.js": ("dashboard.js", "text/javascript; charset=utf-8"),
    "/assets/forgecoin-logo.png": ("assets/forgecoin-logo.png", "image/png"),
}
SITE_DIR = Path(__file__).resolve().parents[2] / "apps" / "pool-site"


class StatsBridgeError(ValueError):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_upstream(value: str) -> str:
    """No DNS, SSRF, redirects, public RPC, cookies or URL-path traversal."""
    try:
        u = urlsplit(value)
        port = u.port
    except (TypeError, ValueError) as exc:
        raise StatsBridgeError("invalid upstream URL") from exc
    if (u.scheme != "http" or u.hostname not in ("127.0.0.1", "::1")
            or port is None or not 1 <= port <= 65535
            or u.path != "/stats" or u.query or u.fragment or u.username or u.password):
        raise StatsBridgeError("explicit localhost HTTP /stats endpoint required")
    return value


def nonnegative_int(raw: dict, name: str, *, required: bool = False):
    value = raw.get(name)
    if value is None:
        if required:
            raise StatsBridgeError(f"missing {name}")
        return None
    if type(value) is not int or value < 0 or value > MAX_U64:
        raise StatsBridgeError(f"invalid {name}")
    return value


def normalize_stats(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise StatsBridgeError("unexpected upstream statistics payload")
    data = {
        "poolHashrate": nonnegative_int(raw, "pool_hashrate", required=True),
        "networkHashrate": nonnegative_int(raw, "network_hashrate", required=True),
        "networkDifficulty": nonnegative_int(raw, "network_difficulty", required=True),
        "networkHeight": nonnegative_int(raw, "network_height", required=True),
        "connectedMiners": nonnegative_int(raw, "connected_miners", required=True),
        "poolBlocksFound": nonnegative_int(raw, "pool_blocks_found", required=True),
        "roundHashes": nonnegative_int(raw, "round_hashes", required=True),
        "lastBlockFound": nonnegative_int(raw, "last_block_found", required=True),
        "lastTemplateFetched": nonnegative_int(raw, "last_template_fetched", required=True),
    }
    # Upstream expresses fee as a proportion of rewards, e.g., 0.01 is 1%.
    raw_fee = raw.get("pool_fee")
    if type(raw_fee) not in (int, float) or not 0 <= raw_fee <= 1:
        raise StatsBridgeError("invalid pool fee fraction")
    data["poolFeePercent"] = round(raw_fee * 100, 3)
    # Do not copy upstream miner_balance, miner_hashrate, account identifiers,
    # wallet cookies, payment_threshold or advertised mining ports.
    return data


def fetch_stats(url: str, *, timeout: float = 2) -> dict:
    endpoint = validate_upstream(url)
    req = Request(endpoint, method="GET", headers={"Accept": "application/json"})
    opener = build_opener(ProxyHandler({}), NoRedirects())
    with opener.open(req, timeout=timeout) as response:
        if response.status != 200:
            raise StatsBridgeError("upstream returned non-success")
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise StatsBridgeError("upstream response too large")
        if not body:
            raise StatsBridgeError("empty upstream statistics")
    try:
        raw = json.loads(body, parse_constant=lambda x: (_ for _ in ()).throw(
            StatsBridgeError("nonfinite upstream number")
        ))
    except (UnicodeError, ValueError) as exc:
        raise StatsBridgeError("invalid upstream JSON") from exc
    return normalize_stats(raw)


def public_payload(upstream: str | None, fetcher=fetch_stats) -> tuple[int, dict]:
    if not upstream:
        return 503, {
            "state": "not_connected", "launchApproved": False,
            "message": "Pool statistics backend not connected. FRG mining and payouts are not enabled by this site."
        }
    try:
        stats = fetcher(upstream)
    except Exception:
        return 503, {
            "state": "unavailable", "launchApproved": False,
            "message": "The private statistics source is unavailable or invalid; no figures are shown."
        }
    return 200, {
        "state": "backend_observed_unverified", "launchApproved": False,
        "asOf": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stats": stats,
    }


class PreviewHandler(BaseHTTPRequestHandler):
    upstream: str | None = None

    def log_message(self, fmt, *args):
        # Do not log wallet addresses; no address queries supported.
        pass

    def _headers(self, code: int, mime: str, size: int):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "img-src 'self'; connect-src 'self'; font-src 'self'; "
                         "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()

    def do_GET(self):
        route = self.path
        if route in ("/", "/dashboard.html"):
            route = "/dashboard.html"
        if route == "/api/pool-stats":
            code, data = public_payload(self.upstream)
            body = json.dumps(data, separators=(",", ":")).encode("utf-8")
            self._headers(code, "application/json; charset=utf-8", len(body))
            self.wfile.write(body)
            return
        asset = ALLOWED_ASSETS.get(route)
        if asset is None:
            body = b"Not found"
            self._headers(404, "text/plain; charset=utf-8", len(body))
            self.wfile.write(body)
            return
        file = SITE_DIR / asset[0]
        try:
            body = file.read_bytes()
        except OSError:
            body = b"Asset not available"
            self._headers(503, "text/plain; charset=utf-8", len(body))
            self.wfile.write(body)
            return
        self._headers(200, asset[1], len(body))
        self.wfile.write(body)


def serve(*, port: int, upstream: str | None):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("preview port must be unprivileged")
    if upstream:
        validate_upstream(upstream)
    handler = type("LocalPreviewHandler", (PreviewHandler,), {"upstream": upstream})
    httpd = HTTPServer(("127.0.0.1", port), handler)
    try:
        print(f"ForgeCoin READ-ONLY local UI preview: http://127.0.0.1:{port}/")
        print("Pool launch and payouts remain disabled.")
        httpd.serve_forever(poll_interval=.2)
    finally:
        httpd.server_close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Local-only, read-only FRG pool dashboard preview")
    ap.add_argument("--port", type=int, default=48775)
    args = ap.parse_args()
    serve(port=args.port, upstream=os.environ.get("FRG_POOL_STATS_UPSTREAM"))
