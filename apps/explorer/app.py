"""Read-only ForgeCoin explorer. No generic RPC proxy or wallet access."""
import json
import os
import re
import time
import threading
import urllib.request
import urllib.error
from flask import Flask, jsonify, request

app = Flask(__name__, static_folder='static', static_url_path='')
RPC_URL = os.environ.get('FORGE_RPC_URL', 'http://127.0.0.1:39481').rstrip('/')
HEX = re.compile(r'^[0-9a-fA-F]{64}$')
DIGITS = re.compile(r'^(0|[1-9][0-9]{0,8})$')
cache = {}
lock = threading.Lock()

class Unavailable(Exception): pass
class Missing(Exception): pass

def cached(key, loader, ttl=5):
    with lock:
        item = cache.get(key)
        if item and time.monotonic() < item[0]: return item[1]
    result = loader()
    with lock:
        if len(cache) >= 128: cache.clear()
        cache[key] = (time.monotonic()+ttl, result)
    return result

def node(method, params=None, direct=False):
    # Call sites are fixed. User input never chooses a node RPC method or URL.
    body = params or {}
    path = '/' + method if direct else '/json_rpc'
    if not direct: body = {'jsonrpc':'2.0','id':'explorer','method':method,'params':body}
    req = urllib.request.Request(RPC_URL+path, json.dumps(body).encode(), {'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            raw = response.read(8*1024*1024+1)
        if len(raw)>8*1024*1024: raise Unavailable()
        data = json.loads(raw)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise Unavailable() from exc
    if data.get('error'):
        if data['error'].get('code') in (-2,-5): raise Missing()
        raise Unavailable()
    result = data if direct else data.get('result', {})
    if result.get('status') not in (None,'OK'): raise Unavailable()
    return result

EXPECTED_GENESIS_NONCE = 20261026
EXPECTED_GENESIS_HASH = '4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c'
def verified_info():
    state = node('get_info')
    genesis = node('get_block_header_by_height', {'height': 0}).get('block_header', {})
    if state.get('nettype') != 'mainnet' or genesis.get('nonce') != EXPECTED_GENESIS_NONCE or genesis.get('hash') != EXPECTED_GENESIS_HASH:
        raise Unavailable('RPC is not the fresh ForgeCoin mainnet')
    return state

def info(): return cached('info', verified_info)
def wide(obj, name):
    return int(obj['wide_'+name],16) if obj.get('wide_'+name) else int(obj.get(name,0))
def header(h):
    return {'height':h['height'],'hash':h['hash'],'timestamp':h['timestamp'],
        'difficulty':str(wide(h,'difficulty')),'reward_atomic':str(h['reward']),
        'tx_count':h.get('num_txes',0),'size':h.get('block_size',0),
        'major_version':h['major_version'],'prev_hash':h['prev_hash'],
        'orphan_status':h.get('orphan_status',False)}
def headers(start,end):
    return node('get_block_headers_range', {'start_height':start,'end_height':end,'fill_pow_hash':False})['headers']
def height_arg(value):
    if not DIGITS.fullmatch(value): raise ValueError('Invalid block height.')
    return int(value)

# Defensive route-wide gate: block and tx lookups must never show legacy-chain
# records even when the attacker requests a valid-looking 64-character hash.
# The unauthenticated /api/status document contains only public, frozen constants.
@app.before_request
def require_frozen_new_mainnet_identity():
    if request.path.startswith('/api/') and request.path != '/api/status':
        info()

@app.get('/api/status')
def release_status():
    try:
        info()
        verified_node = True
    except (Unavailable, Missing, KeyError, ValueError, TypeError):
        verified_node = False
    return jsonify(
        chain='forgecoin-mainnet',
        expected_genesis_nonce=EXPECTED_GENESIS_NONCE,
        expected_genesis_hash=EXPECTED_GENESIS_HASH,
        expected_daemon_rpc_port=39481,
        public_launch_authorized=False,
        native_mining_enabled=False,
        verified_native_node_connected=verified_node,
        explorer_mode='prelaunch-read-only',
        note='Native FRG mainnet is genesis-frozen; no public mining or releases are authorized.'
    )

@app.get('/')
def home(): return app.send_static_file('index.html')

@app.get('/api/overview')
def overview():
    def load():
        n=info(); tip=max(0,n['height']-1)
        hs=headers(max(0,tip-60),tip); hs.sort(key=lambda x:x['height'])
        span=hs[-1]['timestamp']-hs[0]['timestamp'] if len(hs)>1 else 0
        work=wide(hs[-1],'cumulative_difficulty')-wide(hs[0],'cumulative_difficulty') if len(hs)>1 else 0
        return {'height':n['height'],'tip_height':tip,'difficulty':str(wide(n,'difficulty')),
            'target_seconds':n['target'],'synchronized':bool(n['synchronized']),
            'peers':n.get('incoming_connections_count',0)+n.get('outgoing_connections_count',0),
            'tx_pool_size':n.get('tx_pool_size',0),'tip_hash':n['top_block_hash'],
            'latest_timestamp':hs[-1]['timestamp'],
            'observed_interval_seconds':span/(len(hs)-1) if span>0 else None,
            'estimated_hashrate':work/span if span>0 else None,
            'blocks':[header(h) for h in reversed(hs[-20:])],'fetched_at':int(time.time())}
    return jsonify(cached('overview',load,10))

@app.get('/api/blocks')
def blocks():
    before=request.args.get('before')
    end=info()['height']-1 if before is None else height_arg(before)
    if end>=info()['height']: raise Missing()
    start=max(0,end-19)
    return jsonify(cached(('blocks',end), lambda:{'blocks':[header(h) for h in reversed(headers(start,end))], 'next_before':start-1 if start else None}))

@app.get('/api/block/<identifier>')
def block(identifier):
    if HEX.fullmatch(identifier): params={'hash':identifier.lower()}
    else:
        h=height_arg(identifier)
        if h>=info()['height']: raise Missing()
        params={'height':h}
    def load():
        b=node('get_block',params); h=b['block_header']
        return {'header':header(h),'miner_tx_hash':b.get('miner_tx_hash') or h.get('miner_tx_hash'),
            'tx_hashes':b.get('tx_hashes',[]),
            'confirmations':0 if h.get('orphan_status') else max(0,info()['height']-h['height'])}
    return jsonify(cached(('block',identifier.lower()),load))

@app.get('/api/tx/<txid>')
def transaction(txid):
    if not HEX.fullmatch(txid): raise ValueError('Enter a 64-character transaction hash.')
    def load():
        result=node('get_transactions',{'txs_hashes':[txid.lower()],'decode_as_json':True,'prune':True},direct=True)
        if not result.get('txs'): raise Missing()
        tx=result['txs'][0]; data=json.loads(tx['as_json']); coinbase=any('gen' in v for v in data.get('vin',[]))
        return {'hash':txid.lower(),'in_pool':bool(tx['in_pool']),
            'block_height':None if tx['in_pool'] else tx.get('block_height'),
            'confirmations':0 if tx['in_pool'] else tx.get('confirmations',0),
            'timestamp':tx.get('received_timestamp') if tx['in_pool'] else tx.get('block_timestamp'),
            'fee_atomic':None if coinbase else (str(data['rct_signatures']['txnFee']) if 'txnFee' in data.get('rct_signatures',{}) else None),
            'version':data['version'],'unlock_time':data.get('unlock_time',0),
            'inputs':len(data.get('vin',[])),'outputs':len(data.get('vout',[])),
            'size':len(tx.get('as_hex') or tx.get('pruned_as_hex',''))//2,'coinbase':coinbase}
    return jsonify(cached(('tx',txid.lower()),load))

@app.errorhandler(ValueError)
def invalid(e): return jsonify(error=str(e)),400
@app.errorhandler(Missing)
def missing(e): return jsonify(error='Block or transaction not found.'),404
@app.errorhandler(Unavailable)
def unavailable(e): return jsonify(error='The new ForgeCoin mainnet node is offline or has an unrecognized genesis. Public launch is not authorized.'),503
@app.errorhandler(404)
def not_found(e): return jsonify(error='Page not found.'),404
@app.errorhandler(405)
def not_allowed(e): return jsonify(error='This explorer is read-only.'),405
@app.after_request
def security(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    if request.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
    return response
