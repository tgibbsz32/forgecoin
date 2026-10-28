#!/usr/bin/env python3
import concurrent.futures
import copy
import datetime as dt
import os
import tempfile
import unittest
from test_mfrg_integrated_challenge_verifier import setup,NOW
from verify_mfrg_control_challenges import fingerprint
from mfrg_integrated_challenge_verifier import reserve_verified_issuer
from mfrg_idempotent_verification import verify_persist
from mfrg_signed_challenge_issuer import IssuerError
def bundle():
    m,t,e,env,key=setup()
    return m,t,e,env,key,fingerprint(t)
class Tests(unittest.TestCase):
    def test_retry_same_result(self):
        m,t,e,env,key,pin=bundle()
        with tempfile.TemporaryDirectory() as d:
            db=os.path.join(d,"data.sqlite");reserve_verified_issuer(env,key,db,NOW)
            x=verify_persist(m,t,pin,e,env,key,db,NOW)
            y=verify_persist(m,t,pin,e,env,key,db,NOW)
            self.assertEqual(x,y)
            self.assertFalse(y["live_chain_custody_verified"])
    def test_parallel_retries_only_one_result(self):
        m,t,e,env,key,pin=bundle()
        with tempfile.TemporaryDirectory() as d:
            db=os.path.join(d,"data.sqlite");reserve_verified_issuer(env,key,db,NOW)
            def run(_):return verify_persist(m,t,pin,e,env,key,db,NOW)
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                output=list(pool.map(run,range(12)))
            self.assertTrue(all(x==output[0] for x in output))
    def test_payload_change_denied(self):
        m,t,e,env,key,pin=bundle()
        with tempfile.TemporaryDirectory() as d:
            db=os.path.join(d,"data.sqlite");reserve_verified_issuer(env,key,db,NOW)
            verify_persist(m,t,pin,e,env,key,db,NOW)
            altered=copy.deepcopy(e);altered["slot"]+=1
            with self.assertRaises(IssuerError):verify_persist(m,t,pin,altered,env,key,db,NOW)
    def test_invalid_does_not_consume(self):
        m,t,e,env,key,pin=bundle()
        with tempfile.TemporaryDirectory() as d:
            db=os.path.join(d,"data.sqlite");reserve_verified_issuer(env,key,db,NOW)
            with self.assertRaises(ValueError):verify_persist(m,t,"0"*64,e,env,key,db,NOW)
            self.assertTrue(verify_persist(m,t,pin,e,env,key,db,NOW)["session_consumed"])
    def test_missing_reservation(self):
        m,t,e,env,key,pin=bundle()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(IssuerError):verify_persist(m,t,pin,e,env,key,os.path.join(d,"db"),NOW)
if __name__=="__main__":unittest.main()
