#!/usr/bin/env python3
"""Read-only localhost collector for frozen ForgeCoin 20261026 chain.

Does not create blocks, mine, pay, sign, authenticate wallets or accept writes.
Does not treat a daemon being reachable as authority to launch mainnet.
"""
import argparse
import json
import os
import pathlib
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GENESIS_NONCE = 20261026
GENESIS_HASH = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
RPC_BASE = "http://127.0.0.1:39481"
POOL_STATS = "http://127.0.0.1:4243/stats"
MAX_BYTES = 65536
POLL_SEC = 10
STATE = {"status": "starting", "checkedAt": 0, "network": None, "pool": None, "solo": None}
LOCK = threading.Lock()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def fetch_json(url, *, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"})
    with OPENER.open(req, timeout=2.5) as response:
        if response.status != 200:
            raise ValueError("upstream non-200")
        content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError("oversized upstream")
    return json.loads(content, parse_constant=lambda s: (_ for _ in ()).throw(ValueError("non-finite number")))

def rpc(method, params=None, direct=False):
    if method not in ("get_info", "get_block_header_by_height", "get_mining_status"):
        raise ValueError("method not allowlisted")
    url = RPC_BASE + ("/"+method if direct else "/json_rpc")
    raw = fetch_json(url, method="POST", payload={} if direct else
        {"jsonrpc":"2.0", "id":"read-only-monitor", "method":method, "params":params or {}})
    if not isinstance(raw, dict) or raw.get("error"):
        raise ValueError("upstream RPC error")
    result = raw if direct else raw.get("result")
    if not isinstance(result, dict) or result.get("status") not in (None, "OK"):
        raise ValueError("invalid RPC result")
    return result

def bounded_int(v):
    return v if type(v) is int and 0 <= v <= 2**64-1 else None

def normalized_chain(info, genesis):
    header = genesis.get("block_header")
    if not isinstance(header, dict) or (info.get("nettype") != "mainnet"
        or header.get("hash") != GENESIS_HASH
        or header.get("nonce") != GENESIS_NONCE or header.get("height") != 0):
        raise ValueError("wrong network/genesis")
    height = bounded_int(info.get("height"))
    difficulty = bounded_int(info.get("difficulty"))
    peer_out = bounded_int(info.get("outgoing_connections_count"))
    peer_in = bounded_int(info.get("incoming_connections_count"))
    if height is None or height < 1:
        raise ValueError("invalid canonical height")
    return {"height":height, "topHash":info.get("top_block_hash") if
        isinstance(info.get("top_block_hash"), str) and len(info["top_block_hash"]) == 64 else None,
        "difficulty":difficulty,
        "peers": (peer_in + peer_out) if peer_in is not None and peer_out is not None else None,
        "txPoolSize":bounded_int(info.get("tx_pool_size")),
        "networkHashrateEstimate": (difficulty // 120) if difficulty is not None else None,
        "mainnetGenesis": GENESIS_HASH,
        "minedBlocks": height-1,
        "tipAge":None,
        "isSynchronized":bool(info.get("synchronized", False))}

POOL_FIELDS = {
    "pool_hashrate":"poolHashrate",
    "network_hashrate":"networkHashrate",
    "network_difficulty":"networkDifficulty",
    "network_height":"networkHeight",
    "connected_miners":"connectedMiners",
    "pool_blocks_found":"poolBlocksFound",
    "round_hashes":"roundHashes",
    "last_block_found":"lastBlockFound",
    "last_template_fetched":"lastTemplateFetched",
}
def normalized_pool(raw):
    if not isinstance(raw, dict):
        raise ValueError("bad pool stats")
    result = {}
    for incoming, outgoing in POOL_FIELDS.items():
        v = bounded_int(raw.get(incoming))
        if v is None:
            raise ValueError("missing or noninteger pool stat")
        result[outgoing] = v
    fee = raw.get("pool_fee")
    if type(fee) not in (int,float) or fee < 0 or fee > 1:
        raise ValueError("invalid fee")
    result["poolFeePercent"] = round(fee*100, 4)
    # Never forward identity, wallets, miner addresses, balances or private payout details.
    return result

def normalized_solo(raw):
    if not isinstance(raw, dict):
        raise ValueError("invalid mining status")
    active = raw.get("active")
    if type(active) is not bool:
        raise ValueError("unknown local miner activity")
    speed = bounded_int(raw.get("speed"))
    threads = bounded_int(raw.get("threads_count"))
    return {"active":active, "hashrateHps":speed if active else 0,
        "threads":threads if active else 0}

def snapshot():
    at = int(time.time())
    result = {"status":"node-unavailable","checkedAt":at,"network":None,
              "pool":None,"solo":None}
    try:
        info = rpc("get_info")
        genesis = rpc("get_block_header_by_height", {"height":0})
        result["network"] = normalized_chain(info, genesis)
        result["status"] = "genesis-verified-prelaunch"
        try:
            result["solo"] = normalized_solo(rpc("get_mining_status", direct=True))
        except (OSError, ValueError, urllib.error.URLError, TypeError):
            result["solo"] = None
        try:
            result["pool"] = normalized_pool(fetch_json(POOL_STATS))
        except (OSError, ValueError, urllib.error.URLError, TypeError, KeyError):
            result["pool"] = None
    except (OSError, ValueError, urllib.error.URLError, TypeError, KeyError):
        result["status"] = "node-unavailable-or-wrong-genesis"
    return result

def loop():
    while True:
        data = snapshot()
        with LOCK:
            STATE.update(data)
        time.sleep(POLL_SEC)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == "/healthz":
            return self.respond(200, {"status":"monitor-running", "doesNotAuthorizeLaunch":True})
        if path == "/api/monitor":
            with LOCK:
                data = dict(STATE)
            return self.respond(200 if data["network"] else 503,
               dict(data, launchApproved=False, payoutsEnabled=False, miningAuthorized=False))
        if path in ("/api/pool-stats", "/api/solo-stats"):
            with LOCK:
                data = dict(STATE)
            # Both endpoints deliberately fail closed while mainnet is not authorized.
            return self.respond(503, {"status":"prelaunch-unavailable", "launchApproved":False,
                "message":"Mainnet genesis is frozen; public mining/payouts not authorized."})
        return self.respond(404, {"error":"not_found"})

    def do_POST(self): return self.respond(405, {"error":"read_only"})
    def do_PUT(self): return self.respond(405, {"error":"read_only"})
    def do_DELETE(self): return self.respond(405, {"error":"read_only"})
    def log_message(self, fmt, *args): pass
    def respond(self, code, payload):
        b = json.dumps(payload, separators=(",",":")).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'none'")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        self.wfile.write(b)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=19810)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("nonprivileged monitoring port required")
    threading.Thread(target=loop, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.serve_forever()

if __name__ == "__main__":
    main()
