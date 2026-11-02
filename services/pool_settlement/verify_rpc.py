"""Read-only native FRG wallet+daemon RPC canonical-payout verifier.

No RPC method in this file creates, signs, relays or spends transactions.
Connections are restricted to IPv4/IPv6 loopback; caller must independently
secure wallet authentication and custody. Never log RPC credentials.
"""
from __future__ import annotations
import ipaddress
import json
import urllib.parse
import urllib.request

from .ledger import ConfirmedTx,GENESIS,Journal,SettlementError,TXID,validate_destinations

WALLET_RPC="get_transfer_by_txid"
DAEMON_RPC=frozenset(("get_info","get_block_header_by_height","get_transactions","get_block"))

def loopback_only(uri):
    p=urllib.parse.urlparse(uri)
    if p.scheme!="http" or p.username or p.password or p.query or p.fragment or p.path not in ("","/","/json_rpc"):
        raise SettlementError("RPC endpoint must be uncredentialed HTTP loopback")
    try:
        if not ipaddress.ip_address(p.hostname or "").is_loopback:raise SettlementError("RPC must bind loopback")
    except ValueError:
        raise SettlementError("RPC hostname is not an IP loopback address")
    if p.port is None or not 1<=p.port<=65535:raise SettlementError("RPC port missing")
    return uri.rstrip("/").removesuffix("/json_rpc")

class ReadOnlyRPCVerifier:
    def __init__(self,daemon_url,wallet_url,*,wallet_opener=None):
        self.daemon=loopback_only(daemon_url)
        self.wallet=loopback_only(wallet_url)
        self.wallet_opener=wallet_opener or urllib.request.build_opener()

    def _rpc(self,base,method,params=None,*,wallet=False):
        if wallet:
            if method!=WALLET_RPC:raise SettlementError("wallet RPC method is not read-only approved")
        elif method not in DAEMON_RPC:
            raise SettlementError("daemon RPC method is not read-only approved")
        # Monero-derived daemon exposes get_info and get_transactions as
        # plain POST JSON endpoints, NOT /json_rpc JSON-RPC methods.
        plain_daemon=(not wallet and method in ("get_info","get_transactions"))
        endpoint=base+("/"+method if plain_daemon else "/json_rpc")
        payload=(params or {}) if plain_daemon else {
            "jsonrpc":"2.0","id":"frg-payout-readonly",
            "method":method,"params":params if params is not None else {}}
        request=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),
                                      headers={"Content-Type":"application/json"})
        with (self.wallet_opener if wallet else urllib.request.build_opener()).open(request,timeout=5) as resp:
            raw=resp.read(512_000+1)
        if len(raw)>512_000:raise SettlementError("oversized RPC response")
        reply=json.loads(raw)
        if not isinstance(reply,dict) or reply.get("error") is not None:
            raise SettlementError("wallet/daemon read-only RPC failed")
        if plain_daemon:
            if reply.get("status") not in (None,"OK"):
                raise SettlementError("daemon read-only endpoint not OK")
            return reply
        if "result" not in reply or not isinstance(reply["result"],dict):
            raise SettlementError("missing JSON-RPC result")
        return reply["result"]
    def node(self,method,params=None):
        return self._rpc(self.daemon,method,params)
    def wallet_read(self,method,params=None):
        return self._rpc(self.wallet,method,params,wallet=True)
    def identity(self):
        info=self.node("get_info")
        first=self.node("get_block_header_by_height",{"height":0})["block_header"]
        if info.get("nettype")!="mainnet" or first.get("hash")!=GENESIS or first.get("nonce")!=20261026:
            raise SettlementError("RPC node is not frozen 20261026 FRG mainnet")
        tip=int(info.get("height",0))-1
        if tip<0:raise SettlementError("invalid chain height")
        return tip

    def observation(self,txid,*,chain_tip=None):
        if not isinstance(txid,str) or not TXID.fullmatch(txid):
            raise SettlementError("invalid payout transaction hash")
        if chain_tip is None:chain_tip=self.identity()
        w=self.wallet_read(WALLET_RPC,{"txid":txid})
        transfers=w.get("transfers",[])
        transfer=w.get("transfer")
        if not isinstance(transfer,dict):
            if isinstance(transfers,list) and len(transfers)==1 and isinstance(transfers[0],dict):
                transfer=transfers[0]
            else:raise SettlementError("ambiguous wallet transfer")
        if transfer.get("txid")!=txid or transfer.get("type")!="out":
            raise SettlementError("wallet does not recognize expected outgoing payment")
        height=transfer.get("height")
        if not isinstance(height,int) or isinstance(height,bool) or height<1 or height>chain_tip:
            raise SettlementError("wallet transfer has not entered valid chain height")
        if transfer.get("locked") is True:raise SettlementError("wallet transfer locked")
        if transfer.get("double_spend_seen") is True:raise SettlementError("wallet reports double spend")
        wallet_depth=transfer.get("confirmations",0)
        if not isinstance(wallet_depth,int) or wallet_depth<0:
            raise SettlementError("wallet confirmation count invalid")
        # Never trust more confirmations than follow from the daemon's tip.
        confirmations=min(wallet_depth,chain_tip-height+1)
        destinations=transfer.get("destinations")
        if not isinstance(destinations,list) or not destinations:
            raise SettlementError("wallet cannot independently verify private payees")
        pairs=validate_destinations([(d["address"],d["amount"]) for d in destinations])
        txs=self.node("get_transactions",{"txs_hashes":[txid],"decode_as_json":False})
        entries=txs.get("txs",[]) if isinstance(txs,dict) else []
        if len(entries)!=1 or entries[0].get("tx_hash")!=txid:
            raise SettlementError("daemon did not return exactly one requested tx")
        item=entries[0]
        if item.get("in_pool") is not False or item.get("double_spend_seen") is True:
            raise SettlementError("daemon transaction is unconfirmed or double spent")
        if item.get("block_height")!=height:
            raise SettlementError("wallet and daemon disagree on mining height")
        header=self.node("get_block_header_by_height",{"height":height})["block_header"]
        block=self.node("get_block",{"height":height})
        if block.get("block_header",{}).get("hash")!=header.get("hash"):
            raise SettlementError("block body header does not match canonical tip")
        blob=block.get("json")
        if not isinstance(blob,str):raise SettlementError("canonical block tx list not available")
        details=json.loads(blob)
        included=txid in details.get("tx_hashes",[])
        if not included:raise SettlementError("payout txid absent from canonical block")
        return ConfirmedTx(
            txid=txid,wallet_type="out",wallet_destinations=pairs,
            wallet_confirmations=confirmations,wallet_height=height,
            wallet_double_spend=False,daemon_in_pool=False,
            daemon_block_height=height,
            daemon_block_hash=header["hash"],
            canonical_block_hash=block["block_header"]["hash"],
            daemon_block_includes_tx=included)

    def verify_batch(self,journal:Journal,batch_id):
        """Read-only checking only; caller must decide if safe to observe/settle.
        No writes to native pool LMDB or access to private wallet keys.
        """
        row=journal.snapshot(batch_id)
        if row["state"] not in ("SIGNED","BROADCAST","HOLD"):
            raise SettlementError("batch not in wallet-confirmable state")
        txids=json.loads(row["txids_json"])
        tip=self.identity()
        proofs=[self.observation(txid,chain_tip=tip) for txid in txids]
        journal.record_observations(batch_id,proofs)
        return len(proofs)
