"""SQLite-backed governance eligibility and decision audit log (development only)."""
import os
import sqlite3
import time
from pathlib import Path

ROLES = frozenset(("staking", "miner", "developer", "community", "chamber"))
SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
 wallet TEXT PRIMARY KEY,
 created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS role_decisions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 wallet TEXT NOT NULL REFERENCES members(wallet),
 role TEXT NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('approve','revoke')),
 reviewer TEXT NOT NULL,
 rationale TEXT NOT NULL,
 created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS role_history ON role_decisions(wallet, role, id);
"""

def db_path():
    return Path(os.environ.get("FORGECOIN_GOVERNANCE_DB", "governance-dev.sqlite3"))

class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

def connect():
    conn = sqlite3.connect(db_path(), timeout=10, factory=ClosingConnection)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.executescript(SCHEMA)
    return conn

def register(wallet: str):
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO members(wallet, created_at) VALUES (?,?)", (wallet, int(time.time())))

def roles_for(wallet: str):
    """Current authorized categories are last audited decisions per category."""
    with connect() as conn:
        rows = conn.execute("""
            SELECT d.role, d.action
            FROM role_decisions d
            INNER JOIN (
                SELECT role, MAX(id) AS last_id
                FROM role_decisions WHERE wallet=? GROUP BY role
            ) latest ON latest.last_id=d.id
            WHERE d.wallet=?
        """, (wallet,wallet)).fetchall()
    return {role for role, action in rows if action == "approve"}

def decide(wallet: str, role: str, action: str, reviewer: str, rationale: str):
    """Restricted local administrator operation; never exposed to HTTP."""
    if role not in ROLES or action not in ("approve", "revoke"):
        raise ValueError("invalid role decision")
    if not reviewer.strip() or not rationale.strip():
        raise ValueError("reviewer and rationale required")
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO members(wallet, created_at) VALUES (?,?)", (wallet, int(time.time())))
        conn.execute(
            "INSERT INTO role_decisions(wallet, role, action, reviewer, rationale, created_at) VALUES (?,?,?,?,?,?)",
            (wallet, role, action, reviewer, rationale, int(time.time()))
        )

def history(wallet: str):
    with connect() as conn:
        rows = conn.execute("SELECT role,action,reviewer,rationale,created_at FROM role_decisions WHERE wallet=? ORDER BY id", (wallet,)).fetchall()
    return [dict(zip(("role","action","reviewer","rationale","created_at"), row)) for row in rows]
