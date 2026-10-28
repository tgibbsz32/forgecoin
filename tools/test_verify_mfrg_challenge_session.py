#!/usr/bin/env python3
"""Synthetic Step 21 tests, no live RPC."""
import copy
import datetime as dt
import unittest
from test_verify_mfrg_control_challenges import sample
from verify_mfrg_control_challenges import fingerprint,ReconciliationError
from verify_mfrg_challenge_session import check_session

NOW=dt.datetime(2026,10,28,17,0,tzinfo=dt.timezone.utc)
def fixture():
    m,t,e=sample()
    s={"session_id":"abc"*12,"created_utc":"2026-10-28T16:59:00Z","expires_utc":"2026-10-28T17:05:00Z",
       "mint":m["mint"],"initialization_signature":m["initialization_signature"],"slot":e["slot"],
       "nonces":{e["challenges"][0]["claim"]["token_account"]:e["challenges"][0]["claim"]["nonce"]}}
    return m,t,e,s
class SessionTests(unittest.TestCase):
    def test_valid_is_not_live_proof(self):
        m,t,e,s=fixture();r,add=check_session(m,t,fingerprint(t),e,s,{"sessions":[],"nonces":[]},NOW)
        self.assertFalse(r["live_chain_ownership_verified"])
        self.assertEqual(len(add["nonces"]),1)
    def blocked(self,edit,used=None,now=NOW):
        m,t,e,s=fixture();edit(m,t,e,s)
        with self.assertRaises((ReconciliationError,ValueError,TypeError)):
            check_session(m,t,fingerprint(t),e,s,used or {"sessions":[],"nonces":[]},now)
    def test_expired(self):self.blocked(lambda m,t,e,s:None,now=NOW+dt.timedelta(minutes=6))
    def test_future(self):self.blocked(lambda m,t,e,s:None,now=NOW-dt.timedelta(minutes=2))
    def test_long_ttl(self):self.blocked(lambda m,t,e,s:s.update(expires_utc="2026-10-28T18:00:00Z"))
    def test_session_replay(self):self.blocked(lambda m,t,e,s:None,used={"sessions":["abc"*12],"nonces":[]})
    def test_nonce_replay(self):self.blocked(lambda m,t,e,s:None,used={"sessions":[],"nonces":["a"*64]})
    def test_changed_nonce(self):self.blocked(lambda m,t,e,s:s["nonces"].update({"C"*43:"b"*64}))
    def test_wrong_slot(self):self.blocked(lambda m,t,e,s:s.update(slot=1))
    def test_wrong_mint(self):self.blocked(lambda m,t,e,s:s.update(mint="D"*43))
    def test_wrong_init(self):self.blocked(lambda m,t,e,s:s.update(initialization_signature="E"*88))
    def test_utc(self):self.blocked(lambda m,t,e,s:s.update(created_utc="2026-10-28T16:59:00+00:00"))
    def test_extra_field(self):self.blocked(lambda m,t,e,s:s.update(untrusted=True))
    def test_short_id(self):self.blocked(lambda m,t,e,s:s.update(session_id="short"))
if __name__=="__main__":unittest.main()
