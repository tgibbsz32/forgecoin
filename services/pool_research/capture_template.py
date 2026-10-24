"""Explicit offline/devnet template capture tool.

No automatic wallet access or daemon startup. Only localhost RPC.
Requires an explicitly provided disposable wallet address. Never print address.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener
from .template_adapter import validate_template
from .mining_work import prepare_work

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("RPC redirects are forbidden")

def local_opener():
    return build_opener(ProxyHandler({}), NoRedirect())

def capture(url, wallet_address, output, timeout=5):
    parsed=urlsplit(url)
    if parsed.scheme!="http" or parsed.hostname not in ("127.0.0.1","localhost","::1"):
        raise ValueError("only loopback HTTP RPC is supported")
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("","/json_rpc"):
        raise ValueError("unexpected RPC URL")
    if not wallet_address or not isinstance(wallet_address,str) or len(wallet_address)>256:
        raise ValueError("invalid address")
    body=json.dumps({"jsonrpc":"2.0","id":"local-template","method":"get_block_template",
                     "params":{"wallet_address":wallet_address,"reserve_size":8}}).encode()
    req=Request(url,body,{"Content-Type":"application/json"},method="POST")
    with local_opener().open(req,timeout=timeout) as res:
        if res.status != 200:raise ValueError("daemon RPC non-200 response")
        payload=res.read(1024*1024+1)
    if len(payload)>1024*1024:raise ValueError("RPC response too large")
    response=json.loads(payload)
    if (not isinstance(response, dict) or response.get("jsonrpc") != "2.0"
            or response.get("id") != "local-template" or "result" not in response):
        raise ValueError("invalid or mismatched JSON-RPC template reply")
    result=validate_template(response,8)
    work=prepare_work(result)
    # Capture only non-address public block-template metadata; blobs might encode miner wallet keys.
    summary={"height":result.height,"difficulty":result.difficulty,"expected_reward":result.expected_reward,
             "seed_hash":result.seed_hash.hex(),"blocktemplate_bytes":len(result.blocktemplate_blob),
             "hashing_bytes":len(result.blockhashing_blob),"reserved_offset":result.reserved_offset,
             "nonce_offset":work.header.nonce_offset,"transaction_count":work.transaction_count,
             "major_version":work.header.major,"previous_hash":work.header.previous_hash.hex()}
    Path(output).write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(description="Read one template from explicitly selected isolated loopback daemon")
    p.add_argument("--rpc",default="http://127.0.0.1:39481/json_rpc")
    p.add_argument("--wallet-address",required=True,help="Disposable test wallet address; not logged")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    r=capture(args.rpc,args.wallet_address,args.output)
    print("Validated isolated template at height",r["height"],"and saved sanitized summary.")
if __name__=="__main__":main()
