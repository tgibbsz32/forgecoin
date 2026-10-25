"""Offline SQLite reward ledger prototype; NEVER sign or initiate payouts."""
import sqlite3
from .model import allocate_reward

class RewardLedger:
    def __init__(self, path):
        self.db=sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS blocks(
          block_hash TEXT PRIMARY KEY, height INTEGER NOT NULL, reward INTEGER NOT NULL,
          maturity_height INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('immature','mature','orphaned'))
        );
        CREATE TABLE IF NOT EXISTS allocations(
          block_hash TEXT NOT NULL REFERENCES blocks(block_hash),
          miner TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>=0),
          PRIMARY KEY(block_hash,miner)
        );
        CREATE TABLE IF NOT EXISTS fees(
          block_hash TEXT PRIMARY KEY REFERENCES blocks(block_hash), amount INTEGER NOT NULL
        );
        """)
        self.db.commit()

    def record_block(self, block_hash, height, reward_atomic, maturity_height, shares):
        """Record an independently verified canonical candidate only; no chain verification here."""
        if not isinstance(block_hash,str) or len(block_hash)!=64 or any(c not in '0123456789abcdef' for c in block_hash):
            raise ValueError("lowercase hexadecimal 32-byte block hash required")
        if type(height)!=int or height<0 or type(maturity_height)!=int or maturity_height<=height:
            raise ValueError("invalid height/maturity")
        alloc=allocate_reward(reward_atomic,shares)
        with self.db:
            old=self.db.execute("SELECT height,reward,maturity_height FROM blocks WHERE block_hash=?",(block_hash,)).fetchone()
            if old:
                if old!=(height,reward_atomic,maturity_height):
                    raise ValueError("block hash reuse with conflicting metadata")
                previous=dict(self.db.execute("SELECT miner,amount FROM allocations WHERE block_hash=?",(block_hash,)))
                fee=self.db.execute("SELECT amount FROM fees WHERE block_hash=?",(block_hash,)).fetchone()[0]
                if previous!=alloc.miner_atomic or fee!=alloc.fee_atomic:
                    raise ValueError("conflicting allocations")
                return False
            self.db.execute("INSERT INTO blocks VALUES (?,?,?,?,?)",(block_hash,height,reward_atomic,maturity_height,'immature'))
            self.db.execute("INSERT INTO fees VALUES (?,?)",(block_hash,alloc.fee_atomic))
            self.db.executemany("INSERT INTO allocations VALUES (?,?,?)",[(block_hash,k,v) for k,v in alloc.miner_atomic.items()])
        return True

    def reconcile_chain(self, canonical_by_height, tip_height):
        """Reconcile an externally verified, height-indexed chain snapshot.

        The caller must read one coherent canonical view from a trusted node,
        including the tip and every recorded block height at or below that tip.
        Missing observations are errors, never evidence of an orphan. This does
        not verify headers, chain identity, ancestry or spending authority.
        """
        if type(tip_height) is not int or tip_height < 0:
            raise ValueError("invalid tip")
        if type(canonical_by_height) is not dict:
            raise ValueError("height-indexed canonical snapshot required")
        canonical = canonical_by_height.copy()
        for height, hash_ in canonical.items():
            if type(height) is not int or not 0 <= height <= tip_height:
                raise ValueError("invalid canonical height")
            if (not isinstance(hash_, str) or len(hash_) != 64
                    or any(c not in '0123456789abcdef' for c in hash_)):
                raise ValueError("invalid canonical identifier")
        if tip_height not in canonical:
            raise ValueError("canonical tip observation required")
        if len(set(canonical.values())) != len(canonical):
            raise ValueError("canonical hash reused at multiple heights")
        with self.db:
            # Lock before reading so a concurrent writer cannot add an unchecked
            # block between the coverage check and state updates.
            self.db.execute("BEGIN IMMEDIATE")
            rows = self.db.execute(
                "SELECT block_hash,height,maturity_height,state FROM blocks"
            ).fetchall()
            missing = {height for _, height, _, _ in rows
                       if height <= tip_height and height not in canonical}
            if missing:
                raise ValueError("incomplete canonical snapshot")
            changes = []
            for hash_, height, maturity, state in rows:
                if height > tip_height or canonical[height] != hash_:
                    target = 'orphaned'
                else:
                    target = 'mature' if maturity <= tip_height else 'immature'
                if state == 'orphaned' and target != 'orphaned':
                    raise ValueError("orphan revival requires independent review")
                changes.append((target, hash_))
            self.db.executemany(
                "UPDATE blocks SET state=? WHERE block_hash=?", changes
            )

    def balances(self):
        return dict(self.db.execute("""
          SELECT miner,SUM(amount) FROM allocations
          JOIN blocks USING (block_hash) WHERE state='mature'
          GROUP BY miner ORDER BY miner
        """))

    def close(self):
        self.db.close()
