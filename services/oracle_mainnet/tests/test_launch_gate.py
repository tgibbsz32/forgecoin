import copy
import hashlib
import importlib.util
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[3]
script=ROOT/"services/oracle_mainnet/verify_launch_gate.py"
spec=importlib.util.spec_from_file_location("forgecoin_launch_gate",script)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
BASE=json.loads((ROOT/"config/mainnet.identity.json").read_text(encoding="utf-8"))

def serialized(model):
    return json.dumps(model,sort_keys=True,separators=(",",":")).encode()
def check(model,*,sha=None,marker=None,require=False):
    return gate.verify(serialized(model),sha or gate.EXPECTED_DAEMON_SHA256,marker,require)
def marker_for(model):
    return {
        "operator_approval":"explicit",
        "genesis_hash":gate.EXPECTED_GENESIS,
        "daemon_sha256":gate.EXPECTED_DAEMON_SHA256,
        "manifest_sha256":hashlib.sha256(serialized(model)).hexdigest()
    }

class OracleLaunchSafety(unittest.TestCase):
    def test_frozen_preflight_checks_correct_binary_and_chain(self):
        status=check(BASE)
        self.assertTrue(status["binaryPinned"])
        self.assertTrue(status["genesisMatches"])
        self.assertEqual(status["configuredPoolFeePercent"],"1")
        self.assertFalse(status["canStart"])
        self.assertEqual(status["reasons"],[])
        self.assertFalse(status["releaseManifestAuthorized"])

    def test_unapproved_release_must_fail(self):
        st=check(BASE,require=True)
        self.assertFalse(st["canStart"])
        self.assertIn("release_manifest_not_authorized",st["reasons"])
        self.assertIn("operator_approval_missing_or_invalid",st["reasons"])

    def test_old_binary_never_released(self):
        st=check(BASE,sha="a"*64,require=True)
        self.assertIn("binary_sha256_mismatch",st["reasons"])
        self.assertFalse(st["canStart"])

    def test_wrong_genesis_nonce_or_hash_rejected(self):
        for k,v in [("genesis_nonce",20261020),("genesis_hash","0"*64)]:
            model=copy.deepcopy(BASE)
            model[k]=v
            self.assertIn("wrong_genesis",check(model)["reasons"])

    def test_fee_wallet_or_percent_change_requires_review(self):
        for k,v in [("operator_fee_address","A"*97),("operator_fee_fraction","0.02")]:
            model=copy.deepcopy(BASE)
            model["pool"][k]=v
            self.assertIn("fee_routing_changed",check(model)["reasons"])

    def test_bad_consensus_or_ports_rejected(self):
        model=copy.deepcopy(BASE);model["mining"]["starting_difficulty"]=1
        self.assertIn("wrong_consensus_policy",check(model)["reasons"])
        model=copy.deepcopy(BASE);model["ports"]["p2p"]=19480
        self.assertIn("wrong_network_ports",check(model)["reasons"])

    def test_tampered_currency_terms_rejected(self):
        model=copy.deepcopy(BASE)
        model["currency"]["decimals"]=12
        self.assertIn("currency_terms_changed",check(model)["reasons"])
        model=copy.deepcopy(BASE)
        model["currency"]["genesis_output_atomic"]=0
        self.assertIn("currency_terms_changed",check(model)["reasons"])

    def test_false_boolean_and_stage_no_go(self):
        model=copy.deepcopy(BASE);model["release_authorized"]="true"
        model["stage"]="released"
        self.assertIn("release_manifest_not_authorized",
                      check(model,marker=marker_for(model),require=True)["reasons"])

    def test_release_plus_valid_explicit_marker_required(self):
        model=copy.deepcopy(BASE)
        model["stage"]="released";model["release_authorized"]=True
        wrong=marker_for(model)
        wrong["manifest_sha256"]="0"*64
        self.assertIn("operator_approval_missing_or_invalid",check(model,marker=wrong,require=True)["reasons"])
        accepted=check(model,marker=marker_for(model),require=True)
        self.assertTrue(accepted["canStart"])
        self.assertEqual(accepted["reasons"],[])

    def test_marker_tamper_requires_resign(self):
        model=copy.deepcopy(BASE);model["stage"]="released";model["release_authorized"]=True
        m=marker_for(model)
        model["currency"]["decimals"]=18
        self.assertIn("operator_approval_missing_or_invalid",check(model,marker=m,require=True)["reasons"])

    def test_no_network_launch_in_service_template_without_explicit_marker(self):
        unit=(ROOT/"services/oracle_mainnet/forgecoin-mainnet-20261026.service").read_text()
        self.assertIn("ConditionPathExists=/etc/forgecoin/approved-mainnet-launch.json",unit)
        self.assertIn("ExecStartPre=/usr/bin/python3 -I /opt/forgecoin-ops/verify_launch_gate.py --require-authorized",unit)
        self.assertIn("--p2p-bind-port 39480",unit)
        self.assertIn("--rpc-bind-ip 127.0.0.1",unit)
        self.assertIn("/home/ubuntu/forgecoin-mainnet-20261026/build-release/bin/forged",unit)
        self.assertNotIn("--start-mining",unit)
        self.assertNotIn("--offline",unit)
        self.assertNotIn("monero",unit.lower())

if __name__=="__main__":unittest.main()
