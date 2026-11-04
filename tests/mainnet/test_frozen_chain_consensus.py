"""Frozen 20261026 consensus source and prelaunch lock checks.

Static source preflight only; not a native daemon build or consensus audit.
"""
import gzip
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def read(p):
    return (ROOT / p).read_text(encoding="utf-8")

class FrozenMainnetIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(read("config/mainnet.identity.json"))
        cls.network = read("src/cryptonote_config.h")
        cls.diff = read("src/cryptonote_basic/forgecoin_difficulty.h")
        cls.forks = read("src/hardforks/hardforks.cpp")
        cls.chain = read("src/cryptonote_core/blockchain.cpp")
        cls.core = read("src/cryptonote_core/cryptonote_core.cpp")
        cls.miner = read("src/cryptonote_basic/miner.cpp")

    def test_frozen_genesis_and_ports(self):
        m = self.manifest
        self.assertEqual(m["stage"], "genesis-frozen")
        self.assertFalse(m["release_authorized"])
        self.assertEqual(m["genesis_nonce"], 20261026)
        self.assertEqual(m["genesis_hash"], "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c")
        self.assertEqual(m["network_uuid"], "bd936359-09e4-4fdb-8ec0-12fa9d6ef090")
        self.assertEqual(m["ports"], {"p2p":39480,"daemon_rpc":39481,"zmq_rpc":39482})
        self.assertEqual(m["address_prefixes"], {"standard":190,"integrated":191,"subaddress":192})
        self.assertIn("GENESIS_NONCE = 20261026", self.network)
        self.assertIn(m["genesis_tx_hex"], self.network)
        for token in (
            "P2P_DEFAULT_PORT = 39480", "RPC_DEFAULT_PORT = 39481",
            "ZMQ_RPC_DEFAULT_PORT = 39482",
            "CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX = 190",
            "CRYPTONOTE_PUBLIC_INTEGRATED_ADDRESS_BASE58_PREFIX = 191",
            "CRYPTONOTE_PUBLIC_SUBADDRESS_BASE58_PREFIX = 192",
        ):
            self.assertIn(token, self.network)
        self.assertNotIn("GENESIS_NONCE = 10000", self.network)

    def test_startup_and_lwma_consensus(self):
        self.assertIn("{ 19, 1, 0, 1 }", self.forks)
        for token in (
            "FORGE_STARTUP_INITIAL_DIFFICULTY = 500000",
            "FORGE_MINIMUM_DIFFICULTY = 400000",
            "FORGE_STARTUP_FIXED_LAST_HEIGHT = 15",
            "FORGE_LWMA_HEIGHT = 16",
            "FORGE_LWMA_WINDOW = 90",
        ):
            self.assertIn(token, self.diff)
        self.assertIn("forgecoin_lwma_window(", self.diff)
        self.assertIn("start_top_height == 0", self.chain)

    def test_prelaunch_consensus_is_not_a_manifest_toggle(self):
        self.assertEqual(self.manifest["consensus_guard_stage"], "draft-unbuilt")
        self.assertFalse(self.manifest["release_authorized"])
        guard = read("src/cryptonote_basic/forgecoin_prelaunch.h")
        self.assertIn("return !mainnet || height == 0;", guard)
        self.assertIn("return !mainnet || creation_height != 0;", guard)
        self.assertIn("return !mainnet;", guard)
        self.assertIn("forgecoin_prelaunch::mining_allowed(m_prelaunch_nettype == MAINNET)", self.miner)
        self.assertEqual(self.core.count("forgecoin_prelaunch::mining_allowed(get_nettype() == MAINNET)"),3)
        self.assertIn("forgecoin_prelaunch::output_allowed(m_nettype == MAINNET, output_index.height)",self.chain)
        self.assertIn("forgecoin_prelaunch::block_allowed(m_nettype == MAINNET, block_height)",self.chain)
        self.assertIn("forgecoin_prelaunch::block_allowed(m_nettype == MAINNET, m_db->height())",self.chain)

    def test_genesis_maturity_does_not_automatically_become_spendable(self):
        self.assertEqual(self.manifest["currency"]["genesis_output_atomic"],1192092895)
        # Consensus forbids rings referencing height-zero outputs, irrespective
        # of ordinary coinbase unlock time.
        guard = read("src/cryptonote_basic/forgecoin_prelaunch.h")
        self.assertRegex(guard,r"output_allowed\(bool mainnet, std::uint64_t creation_height\)")
        self.assertIn("creation_height != 0",guard)
        self.assertIn("scan_outputkeys_for_indexes",self.chain)

    def test_historical_height2_chain_fixture_is_byte_exact(self):
        fixtures = ROOT / "tests/mainnet/fixtures"
        m = json.loads((fixtures / "pre_guard_20261026_height2_lmdb.json").read_text(encoding="utf-8"))
        self.assertEqual(m["genesis_hash"], self.manifest["genesis_hash"])
        self.assertEqual(m["chain_height"], 2)
        self.assertEqual(m["accepted_block1_hash"], "9755a4f129f97b7865e5897e79abf5fea89dec2ba776d53fb9d01942b9f7ba9e")
        packed = (fixtures / "pre_guard_20261026_height2_data.mdb.gz").read_bytes()
        self.assertEqual(len(packed), 2613)
        self.assertEqual(len(packed), m["compressed_size"])
        self.assertEqual(hashlib.sha256(packed).hexdigest(), m["compressed_sha256"])
        db = gzip.decompress(packed)
        self.assertEqual(len(db), 126976)
        self.assertEqual(len(db), m["uncompressed_size"])
        self.assertEqual(hashlib.sha256(db).hexdigest(), m["uncompressed_sha256"])

if __name__ == "__main__":
    unittest.main()
