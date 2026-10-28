#!/usr/bin/env python3
import copy
import unittest
from mfrg_phase32_readiness import REQUIRED,evaluate
def manifest():
    return {"version":1,"evidence":{name:{"reviewed":False,"reference":""} for name in REQUIRED}}
class Tests(unittest.TestCase):
    def test_all_missing_holds(self):
        r=evaluate(manifest())
        self.assertEqual(len(r["missing_evidence"]),len(REQUIRED))
        self.assertFalse(r["minting_authorized"])
    def test_all_declared_still_no_release(self):
        m=manifest()
        for item in m["evidence"].values():item.update(reviewed=True,reference="operator-claimed-public-reference")
        r=evaluate(m)
        self.assertEqual(r["missing_evidence"],[])
        self.assertFalse(r["production_readiness_cryptographically_proven"])
        self.assertFalse(r["presale_authorized"])
    def test_missing_key(self):
        m=manifest();m["evidence"].pop(REQUIRED[0])
        with self.assertRaises(ValueError):evaluate(m)
    def test_unknown_key(self):
        m=manifest();m["evidence"]["bypass"]={"reviewed":True,"reference":"x"}
        with self.assertRaises(ValueError):evaluate(m)
    def test_boolean_as_version(self):
        m=manifest();m["version"]=True
        with self.assertRaises(ValueError):evaluate(m)
    def test_missing_reference(self):
        m=manifest();m["evidence"][REQUIRED[0]]["reviewed"]=True
        with self.assertRaises(ValueError):evaluate(m)
    def test_string_as_boolean(self):
        m=manifest();m["evidence"][REQUIRED[0]]["reviewed"]="true"
        with self.assertRaises(ValueError):evaluate(m)
    def test_wrong_record(self):
        m=manifest();m["evidence"][REQUIRED[0]]={}
        with self.assertRaises(ValueError):evaluate(m)
if __name__=="__main__":unittest.main()
