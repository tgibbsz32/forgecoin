#!/usr/bin/env python3
"""Read-only, single-shot ForgeCoin chain divergence/reorg observation.

This is an operational alarm, NOT majority-hashpower prevention or chain finality.
Only localhost RPC endpoints are permitted (remote nodes via reviewed SSH tunnels).
Do not point this at public daemon RPC or use it to authorize payouts/bridges.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

TARGET_SECONDS = 120
STATE_VERSION = 1


def validate_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or parts.username or parts.password:
        raise ValueError('RPC URL must be http(s) without embedded credentials')
    if parts.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Only localhost RPC allowed; tunnel independent nodes to localhost')
    if parts.path not in ('', '/', '/json_rpc') or parts.query or parts.fragment or not parts.port:
        raise ValueError('Use http://127.0.0.1:PORT/json_rpc (no query or fragment)')
    return url.rstrip('/') if parts.path.endswith('json_rpc') else url.rstrip('/') + '/json_rpc'


def rpc(url, method, params=None, timeout=5):
    payload = json.dumps({'jsonrpc': '2.0', 'id': 'risk-watch', 'method': method,
                          'params': params or {}}).encode('utf-8')
    req = Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(req, timeout=timeout) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('oversized RPC response')
    result = json.loads(data).get('result')
    if not isinstance(result, dict) or result.get('status') not in (None, 'OK'):
        raise ValueError('invalid RPC result/status for ' + method)
    return result


def parse_header(raw):
    if not isinstance(raw, dict):
        raise ValueError('header must be an object')
    h = raw.get('height')
    if not isinstance(h, int) or isinstance(h, bool) or h < 0:
        raise ValueError('invalid block height')
    block_hash, parent = raw.get('hash'), raw.get('prev_hash')
    if not isinstance(block_hash, str) or len(block_hash) != 64 or any(c not in '0123456789abcdefABCDEF' for c in block_hash):
        raise ValueError('invalid block hash')
    if not isinstance(parent, str) or len(parent) != 64 or any(c not in '0123456789abcdefABCDEF' for c in parent):
        raise ValueError('invalid parent hash')
    timestamp = raw.get('timestamp')
    if not isinstance(timestamp, int) or isinstance(timestamp, bool) or timestamp < 0:
        raise ValueError('invalid block timestamp')
    value = raw.get('wide_difficulty') or raw.get('difficulty')
    try:
        difficulty = int(value, 16) if isinstance(value, str) and value.lower().startswith('0x') else int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('invalid difficulty') from exc
    if difficulty <= 0:
        raise ValueError('non-positive difficulty')
    return {'height': h, 'hash': block_hash.lower(), 'prev_hash': parent.lower(),
            'timestamp': timestamp, 'difficulty': difficulty}


def take_snapshot(url, window=64):
    tip = parse_header(rpc(url, 'get_last_block_header')['block_header'])
    start = max(0, tip['height'] - window + 1)
    raw = rpc(url, 'get_block_headers_range', {'start_height': start,
                                                'end_height': tip['height']}).get('headers')
    if not isinstance(raw, list) or len(raw) != tip['height'] - start + 1:
        raise ValueError('incomplete block-header range')
    headers = [parse_header(h) for h in raw]
    for i, h in enumerate(headers):
        if h['height'] != start + i:
            raise ValueError('non-contiguous returned heights')
        if i and h['prev_hash'] != headers[i - 1]['hash']:
            raise ValueError('invalid parent continuity')
    if headers[-1]['hash'] != tip['hash'] or headers[-1]['difficulty'] != tip['difficulty']:
        raise ValueError('tip and range response disagree')
    return {'tip': tip, 'headers': {str(h['height']): h for h in headers}}


def assess(snapshots, previous=None, now=None, alert_depth=3, stale_seconds=900):
    """Return stable incident events plus a bounded state, without acting on the chain."""
    previous = previous or {}
    now = time.time() if now is None else now
    events = []
    current = {}
    for node, snap in snapshots.items():
        tip, headers = snap['tip'], snap['headers']
        old = previous.get(node, {})
        old_tip = old.get('tip', {})
        if old_tip and tip['height'] < old_tip['height']:
            events.append({'code': 'height_rollback', 'node': node,
                           'previous_height': old_tip['height'], 'height': tip['height']})
        if old.get('headers') and not (set(headers) & set(old['headers'])):
            events.append({'code': 'history_gap', 'node': node,
                           'message': 'prior and new observation windows do not overlap; reorg status unknown'})
        differing = [int(h) for h in set(headers) & set(old.get('headers', {}))
                     if headers[h]['hash'] != old['headers'][h]['hash']]
        if differing:
            first = min(differing)
            old_height = old_tip.get('height', first)
            events.append({'code': 'observed_reorg', 'node': node,
                           'earliest_changed_height': first,
                           'minimum_depth': max(1, old_height - first + 1),
                           'severity': 'critical' if old_height - first + 1 >= alert_depth else 'warning'})
        if now - tip['timestamp'] > stale_seconds:
            events.append({'code': 'stale_tip', 'node': node, 'age_seconds': int(now-tip['timestamp'])})
        if tip['timestamp'] > now + 7200:
            events.append({'code': 'future_timestamp', 'node': node})
        if old_tip and tip['height'] == old_tip['height'] and tip['hash'] == old_tip['hash']:
            if now - tip['timestamp'] > TARGET_SECONDS * 3:
                events.append({'code': 'no_recent_block', 'node': node})
        current[node] = snap
    names = list(current)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            aa, bb = current[a]['headers'], current[b]['headers']
            shared = set(aa) & set(bb)
            conflicts = [int(h) for h in shared if aa[h]['hash'] != bb[h]['hash']]
            if conflicts:
                events.append({'code': 'node_divergence', 'nodes': [a, b],
                               'earliest_conflict_height': min(conflicts)})
            if abs(current[a]['tip']['height'] - current[b]['tip']['height']) >= 3:
                events.append({'code': 'node_height_gap', 'nodes': [a,b],
                               'gap': abs(current[a]['tip']['height']-current[b]['tip']['height'])})
            if not shared:
                events.append({'code': 'no_overlap', 'nodes': [a, b]})
    return events, current


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', action='append', required=True, help='localhost JSON-RPC or tunnel; supply 2+')
    parser.add_argument('--state', required=True, help='persistent local JSON file (no secrets)')
    parser.add_argument('--window', type=int, default=64)
    args = parser.parse_args(argv)
    if len(args.node) < 2 or len(set(args.node)) != len(args.node):
        parser.error('at least two distinct localhost RPC tunnel endpoints are required')
    if not 8 <= args.window <= 256:
        parser.error('window must be 8..256')
    urls = {str(i): validate_url(u) for i, u in enumerate(args.node)}
    state = Path(args.state)
    try:
        prior = json.loads(state.read_text()) if state.exists() else {'version': STATE_VERSION, 'nodes': {}}
        if prior.get('version') != STATE_VERSION or not isinstance(prior.get('nodes'), dict):
            raise ValueError('unexpected state schema')
        # Persist stable URL-tunnel identifiers; no credential-bearing URLs are accepted.
        old = {u: prior['nodes'].get(u, {}) for u in urls.values()}
        observations, failures = {}, []
        for url in urls.values():
            try:
                observations[url] = take_snapshot(url, args.window)
            except Exception as exc:
                failures.append({'code': 'rpc_unavailable', 'node': url,
                                 'error': str(exc)[:160]})
        if len(observations) != len(urls):
            print(json.dumps({'status': 'UNVERIFIED', 'events': failures}, sort_keys=True))
            return 2  # Fail closed. Never save incomplete observations as a valid baseline.
        events, new_nodes = assess(observations, old)
        state.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix='.frg-risk-', dir=str(state.parent))
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump({'version': STATE_VERSION, 'nodes': new_nodes}, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, state)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        print(json.dumps({'status': 'ALERT' if events else 'OBSERVED_ONLY',
                          'events': events,
                          'tips': {k: v['tip']['height'] for k, v in observations.items()}}, sort_keys=True))
        return 1 if events else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'UNVERIFIED', 'events': [{'code':'monitor_failure','error':str(exc)[:160]}]}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
