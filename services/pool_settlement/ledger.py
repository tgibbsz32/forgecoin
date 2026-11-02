"""ForgeCoin pool settlement journal: durable OFFLINE state machine.

No network transport and NO wallet spending methods are present in this
module. Recording a wallet RPC response does not constitute confirmation.
Native pool.c remains the authoritative LMDB reward ledger; this journal is
not wired to that ledger and MUST NOT be enabled for public payments.

The intended safe flow is: reserve existing mature credits, have a separately
reviewed wallet transport construct a transaction with do_not_relay=true,
persist signed metadata+TXIDs, relay precisely those bytes, independently
verify canonical chain inclusion and wallet-owned outputs, then settle.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import pathlib
import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable

GENESIS = "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c"
FRG_ATOMIC=100_000_000
MAX_ATOMIC=(1 << 64)-1
TXID=re.compile(r"^[0-9a-f]{64}$")
HEX=re.compile(r"^[0-9a-fA-F]+$")
ADDRESS=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{90,130}$")
TRANSIENT=frozenset(("RESERVED","SIGNED","BROADCAST","HOLD"))
MIN_CONF=20

class SettlementError(ValueError):
    pass

def amount(value):
    if isinstance(value,bool) or not isinstance(value,int) or value < 0 or value>MAX_ATOMIC:
        raise SettlementError("atomic amount must be unsigned uint64")
    return value

def validate_destinations(destinations):
    """Reject duplicates, invalid amounts and noncanonical ordering."""
    if not isinstance(destinations,(tuple,list)) or not 1<=len(destinations)<=128:
        raise SettlementError("expected 1-128 recipients")
    clean=[]
    for item in destinations:
        if not isinstance(item,(tuple,list)) or len(item)!=2:
            raise SettlementError("expected (address, integer atomic amount)")
        addr,units=item
        if not isinstance(addr,str) or not ADDRESS.fullmatch(addr):
            raise SettlementError("recipient address format invalid")
        units=amount(units)
        if units<=0:raise SettlementError("zero-value destination")
        clean.append((addr,units))
    clean.sort(key=lambda pair:pair[0])
    if len(set(addr for addr,_ in clean))!=len(clean):
        raise SettlementError("duplicate recipient address")
    if sum(units for _,units in clean)>MAX_ATOMIC:
        raise SettlementError("total amount overflow")
    return tuple(clean)

def canonical_json(obj):
    return json.dumps(obj,separators=(",",":"),sort_keys=True,ensure_ascii=True)

@dataclass(frozen=True)
class ConfirmedTx:
    txid:str
    wallet_type:str
    wallet_destinations:tuple[tuple[str,int],...]
    wallet_confirmations:int
    wallet_height:int
    wallet_double_spend:bool
    daemon_in_pool:bool
    daemon_block_height:int
    daemon_block_hash:str
    canonical_block_hash:str
    daemon_block_includes_tx:bool

def verify_observation(tx:ConfirmedTx,required:int):
    """Check that a caller-provided *independent* wallet/daemon observation
    is internally consistent. RPC origin/authenticity must be handled by a
    future transport. This alone is NOT cryptographic proof of payment.
    """
    if not isinstance(tx,ConfirmedTx) or not TXID.fullmatch(tx.txid):
        raise SettlementError("invalid transaction observation")
    if tx.wallet_type!="out" or tx.wallet_double_spend or tx.daemon_in_pool:
        raise SettlementError("wallet transfer is not confirmed outgoing")
    if not isinstance(tx.wallet_confirmations,int) or tx.wallet_confirmations<required:
        raise SettlementError("insufficient chain confirmations")
    if not isinstance(tx.wallet_height,int) or tx.wallet_height<1:
        raise SettlementError("invalid wallet mined height")
    if tx.daemon_block_height!=tx.wallet_height:
        raise SettlementError("wallet and daemon disagree on block height")
    if not TXID.fullmatch(tx.daemon_block_hash) or tx.daemon_block_hash!=tx.canonical_block_hash:
        raise SettlementError("transaction block is not canonical")
    if tx.daemon_block_includes_tx is not True:
        raise SettlementError("transaction not included in canonical block")
    return validate_destinations(tx.wallet_destinations)

class Journal:
    """No production spending, remote RPC or native pool ledger mutation."""
    def __init__(self,filepath,*,genesis=GENESIS,minimum_confirmations=MIN_CONF,qa_mode=False):
        if genesis!=GENESIS:raise SettlementError("unexpected ForgeCoin mainnet identity")
        if (not isinstance(minimum_confirmations,int) or isinstance(minimum_confirmations,bool)
            or minimum_confirmations<10 or minimum_confirmations>200):
            raise SettlementError("confirmation threshold outside audited bounds")
        if not isinstance(qa_mode,bool):raise SettlementError("explicit QA boolean required")
        self.qa_mode=qa_mode
        self.path=pathlib.Path(filepath)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.confirmations=minimum_confirmations
        self.db=sqlite3.connect(str(self.path),timeout=30,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS balance(
            address TEXT PRIMARY KEY, available TEXT NOT NULL, held TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS batches(
            batch_id TEXT PRIMARY KEY, intent_sha256 TEXT NOT NULL,
            recipients_json TEXT NOT NULL, state TEXT NOT NULL,
            txids_json TEXT, metadata_json TEXT, note TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS batch_txids(
            txid TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES batches(batch_id));
        CREATE TABLE IF NOT EXISTS payments(
            batch_id TEXT NOT NULL REFERENCES batches(batch_id),
            address TEXT NOT NULL, amount TEXT NOT NULL,
            PRIMARY KEY(batch_id,address));
        """)
        try:
            with self.tx():
                existing=self.db.execute("SELECT value FROM meta WHERE key='genesis'").fetchone()
                if existing is None:
                    self.db.execute("INSERT INTO meta(key,value) VALUES('genesis',?)",(GENESIS,))
                elif existing["value"]!=GENESIS:
                    raise SettlementError("journal identity mismatch")
                mode=self.db.execute("SELECT value FROM meta WHERE key='qa_mode'").fetchone()
                expected="true" if self.qa_mode else "false"
                if mode is None:
                    self.db.execute("INSERT INTO meta(key,value) VALUES('qa_mode',?)",(expected,))
                elif mode["value"]!=expected:
                    raise SettlementError("QA/production journal reuse forbidden")
        except BaseException:
            self.db.close()
            raise

    @contextlib.contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()
    def snapshot(self,batch_id):
        row=self.db.execute("SELECT * FROM batches WHERE batch_id=?",(batch_id,)).fetchone()
        if row is None:raise SettlementError("unknown payout intent")
        return dict(row)
    def balance(self,address):
        row=self.db.execute("SELECT * FROM balance WHERE address=?",(address,)).fetchone()
        return (int(row["available"]),int(row["held"])) if row else (0,0)

    def _write_balance(self,address,available,held):
        amount(available);amount(held)
        if available+held>MAX_ATOMIC:raise SettlementError("aggregate available/held overflows")
        self.db.execute("INSERT INTO balance(address,available,held) VALUES(?,?,?) "
                        "ON CONFLICT(address) DO UPDATE SET available=excluded.available,held=excluded.held",
                        (address,str(available),str(held)))

    def credit_verified_mature_reward(self,block_key,allocations,*,verified_canonical=False):
        """Research-only injection API. The verified flag is caller-controlled;
        NOT connected to native LMDB and NOT proof of mining a real block.
        Test fixture uses it to exercise reservation behavior.
        """
        if not self.qa_mode:
            raise SettlementError("NO direct crediting: live pool LMDB integration not reviewed")
        if not verified_canonical:raise SettlementError("canonical maturity proof absent")
        if not isinstance(block_key,str) or not TXID.fullmatch(block_key):
            raise SettlementError("block hash required")
        recipients=validate_destinations(allocations)
        marker="block:"+block_key
        digest=hashlib.sha256(canonical_json(recipients).encode()).hexdigest()
        with self.tx():
            old=self.db.execute("SELECT value FROM meta WHERE key=?",(marker,)).fetchone()
            if old:
                if old["value"]!=digest:raise SettlementError("conflicting maturity replay")
                return False
            for addr,units in recipients:
                avail,held=self.balance(addr)
                self._write_balance(addr,avail+units,held)
            self.db.execute("INSERT INTO meta(key,value) VALUES(?,?)",(marker,digest))
        return True

    def reserve(self,batch_id,destinations):
        if not isinstance(batch_id,str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{8,90}",batch_id):
            raise SettlementError("invalid stable payout batch ID")
        pairs=validate_destinations(destinations)
        payload=canonical_json(pairs)
        digest=hashlib.sha256((GENESIS+batch_id+payload).encode()).hexdigest()
        with self.tx():
            old=self.db.execute("SELECT * FROM batches WHERE batch_id=?",(batch_id,)).fetchone()
            if old:
                if old["intent_sha256"]!=digest:raise SettlementError("payout ID reused for different recipients")
                return old["state"]
            for addr,units in pairs:
                available,held=self.balance(addr)
                if available<units:raise SettlementError("insufficient unlocked pool credits")
                self._write_balance(addr,available-units,held+units)
            self.db.execute("INSERT INTO batches(batch_id,intent_sha256,recipients_json,state) VALUES(?,?,?,'RESERVED')",
                            (batch_id,digest,payload))
        return "RESERVED"

    def get_do_not_relay_parameters(self,batch_id):
        row=self.snapshot(batch_id)
        if row["state"]!="RESERVED":
            raise SettlementError("cannot build new signed transfer after submission")
        pairs=json.loads(row["recipients_json"])
        return {"destinations":[{"address":addr,"amount":units} for addr,units in pairs],
                "do_not_relay":True,"get_tx_metadata":True,"get_tx_hex":False,
                "priority":0}

    def record_signed(self,batch_id,txids,metadata):
        if (not isinstance(txids,(tuple,list)) or not isinstance(metadata,(tuple,list)) or
            not 1<=len(txids)==len(metadata)<=128):
            raise SettlementError("invalid signed transfer split result")
        hashes=[]
        for x in txids:
            if not isinstance(x,str) or not TXID.fullmatch(x):
                raise SettlementError("invalid 64-hex transaction hash")
            hashes.append(x)
        if len(set(hashes))!=len(hashes):raise SettlementError("duplicate transaction hashes")
        if any(not isinstance(x,str) or not 8<=len(x)<=4_000_000 or not HEX.fullmatch(x)
               for x in metadata):
            raise SettlementError("missing or invalid signed relay metadata")
        hjson=canonical_json(hashes)
        mjson=canonical_json(metadata)
        with self.tx():
            row=self._batch(batch_id)
            if row["state"]=="SIGNED" and row["txids_json"]==hjson and row["metadata_json"]==mjson:
                return False
            if row["state"]!="RESERVED":
                raise SettlementError("cannot sign again or mutate already-signed transaction")
            for x in hashes:
                if self.db.execute("SELECT 1 FROM batch_txids WHERE txid=?",(x,)).fetchone():
                    raise SettlementError("transaction hash belongs to another payout batch")
            self.db.executemany("INSERT INTO batch_txids(txid,batch_id) VALUES(?,?)",
                                [(h,batch_id) for h in hashes])
            self.db.execute("UPDATE batches SET state='SIGNED',txids_json=?,metadata_json=? WHERE batch_id=?",
                            (hjson,mjson,batch_id))
        return True

    def _batch(self,batch_id):
        row=self.db.execute("SELECT * FROM batches WHERE batch_id=?",(batch_id,)).fetchone()
        if not row:raise SettlementError("unknown payout batch")
        return row

    def relay_metadata(self,batch_id):
        row=self.snapshot(batch_id)
        if row["state"] not in ("SIGNED","BROADCAST","HOLD"):
            raise SettlementError("only signed immutable transactions may be relayed")
        return list(zip(json.loads(row["txids_json"]),json.loads(row["metadata_json"])))

    def record_relay_result(self,batch_id,*,acknowledged_txids):
        # Unknown status is deliberately not treated as a failure; before
        # retrying, inspect the existing pool/chain for these same TXIDs.
        if (not isinstance(acknowledged_txids,(tuple,list)) or
            not all(isinstance(v,str) and TXID.fullmatch(v) for v in acknowledged_txids)):
            raise SettlementError("unverified relay acknowledgment hashes")
        with self.tx():
            row=self._batch(batch_id)
            if row["state"] not in ("SIGNED","BROADCAST"):
                raise SettlementError("payout not in signed state")
            expected=json.loads(row["txids_json"])
            if sorted(acknowledged_txids)!=sorted(expected):
                raise SettlementError("wallet has not acknowledged every signed payout TXID")
            if row["state"]=="BROADCAST":return False
            self.db.execute("UPDATE batches SET state='BROADCAST' WHERE batch_id=?",(batch_id,))
        return True

    def record_observations(self,batch_id,observations):
        if not isinstance(observations,(list,tuple)) or not observations:
            raise SettlementError("no transaction proofs supplied")
        with self.tx():
            row=self._batch(batch_id)
            if row["state"] not in ("SIGNED","BROADCAST","HOLD"):
                raise SettlementError("only signed/pending payments may be observed")
            hashes=json.loads(row["txids_json"])
            if sorted(x.txid for x in observations)!=sorted(hashes):
                raise SettlementError("every journalled txid must be independently observed")
            destinations=[]
            for observation in observations:
                destinations.extend(verify_observation(observation,self.confirmations))
            if validate_destinations(destinations)!=validate_destinations(json.loads(row["recipients_json"])):
                raise SettlementError("wallet's confirmed recipients/amounts mismatch immutable intent")
            self.db.execute("UPDATE batches SET state='OBSERVED',note='confirmed-by-caller; awaiting local ledger settlement' WHERE batch_id=?",(batch_id,))
        return True

    def commit_observed(self,batch_id):
        """Marks the *standalone* journal settled; no writes to native pool LMDB.
        This API cannot release production FRG. Integration remains blocked.
        """
        if not self.qa_mode:
            raise SettlementError("NO production settlement: native pool LMDB integration not implemented")
        with self.tx():
            row=self._batch(batch_id)
            if row["state"]=="SETTLED":return False
            if row["state"]!="OBSERVED":raise SettlementError("not fully confirmed against canonical chain")
            pairs=validate_destinations(json.loads(row["recipients_json"]))
            for addr,units in pairs:
                avail,held=self.balance(addr)
                if held<units:raise SettlementError("held funds already released/corrupt")
                self._write_balance(addr,avail,held-units)
                self.db.execute("INSERT INTO payments(batch_id,address,amount) VALUES(?,?,?)",
                                (batch_id,addr,str(units)))
            self.db.execute("UPDATE batches SET state='SETTLED',note='journal-only; native pool LMDB not integrated' WHERE batch_id=?",
                            (batch_id,))
        return True

    def cancel_before_signing(self,batch_id):
        with self.tx():
            row=self._batch(batch_id)
            if row["state"]=="CANCELLED":return False
            if row["state"]!="RESERVED":
                raise SettlementError("cannot release reserved funds after signing/broadcast")
            for addr,units in json.loads(row["recipients_json"]):
                avail,held=self.balance(addr)
                if held<units:raise SettlementError("insufficient held reservation")
                self._write_balance(addr,avail+units,held-units)
            self.db.execute("UPDATE batches SET state='CANCELLED' WHERE batch_id=?",(batch_id,))
        return True
