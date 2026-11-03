"""The reorg acceptance runner must never create mainnet or public peers.

These tests run without a daemon, wallet, network connection, or files on Oracle.
The real fork/sync/reorg runtime is separately exercised by native CI.
"""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import smoke_regtest_reorg as reorg


class DisposableReorgSafety(unittest.TestCase):
    def test_standalone_regtest_launch_isolated_and_mining_fixture_only(self):
        with tempfile.TemporaryDirectory() as folder:
            node = Path(folder) / "node"
            with patch.object(reorg.subprocess, "Popen") as launch:
                reorg.launch(Path(folder) / "forged", node, 49700, 49701, None, offline=True)
                args = launch.call_args.args[0]
        self.assertIn("--regtest", args)
        self.assertIn("--keep-fakechain", args)
        self.assertIn("--fixed-difficulty", args)
        self.assertEqual(args[args.index("--fixed-difficulty") + 1], "1")
        self.assertIn("--disable-dns-checkpoints", args)
        self.assertIn("--no-igd", args)
        self.assertIn("--no-zmq", args)
        self.assertEqual(args[args.index("--p2p-bind-ip") + 1], "127.0.0.1")
        self.assertEqual(args[args.index("--rpc-bind-ip") + 1], "127.0.0.1")
        self.assertEqual(args[args.index("--out-peers") + 1], "0")
        self.assertEqual(args[args.index("--in-peers") + 1], "2")
        self.assertNotIn("--add-exclusive-node", args)
        self.assertNotIn("--testnet", args)
        self.assertNotIn("--stagenet", args)
        self.assertIn("--offline", args)  # independent forks mine with no P2P synchronization
        self.assertNotIn("0.0.0.0", args)

    def test_reconnecting_node_uses_one_explicit_local_peer_only(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(reorg.subprocess, "Popen") as launch:
                reorg.launch(Path(folder) / "forged", Path(folder) / "node",
                             49702, 49703, None, peer=49700)
                args = launch.call_args.args[0]
        self.assertEqual(args[args.index("--out-peers") + 1], "1")
        self.assertEqual(args[args.index("--in-peers") + 1], "0")
        self.assertEqual(args[args.index("--add-exclusive-node") + 1], "127.0.0.1:49700")
        self.assertNotIn("--offline", args)

    def test_no_peer_connection_while_offline_mining(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(AssertionError, "offline"):
                reorg.launch(Path(folder) / "forged", Path(folder) / "node",
                             49702, 49703, None, peer=49700, offline=True)

    def test_deep_fork_requires_more_than_reward_maturity_window(self):
        self.assertGreaterEqual(reorg.FORK_A_BLOCKS, 61)
        self.assertGreater(reorg.FORK_B_BLOCKS, reorg.FORK_A_BLOCKS)
        self.assertLessEqual(reorg.MINE_BATCH, 10)
        source = (ROOT / "tools/smoke_regtest_reorg.py").read_text(encoding="utf-8")
        self.assertIn("header(a_rpc, FORK_A_BLOCKS - 1)", source)
        self.assertIn("a_old_deep", source)
        self.assertIn("b_deep", source)
        self.assertIn("Old deep block survived reorg", source)
        self.assertIn("mine_in_batches(a_rpc, address, FORK_A_BLOCKS, 13)", source)
        self.assertIn("mine_in_batches(b_rpc, address, FORK_B_BLOCKS, 456)", source)

    def test_chunked_regtest_mining_checks_each_native_height(self):
        address = "test-public-address-only"
        with patch.object(reorg, "mine", side_effect=lambda port, addr, n, nonce: ["a" * 64] * n) as mined:
            with patch.object(reorg, "info", side_effect=[
                {"height": 11}, {"height": 21}, {"height": 23},
            ]) as heights:
                reorg.mine_in_batches(19481, address, 22, 15)
        self.assertEqual([call.args[2] for call in mined.call_args_list], [10, 10, 2])
        self.assertEqual([call.args[3] for call in mined.call_args_list], [15, 20495, 40975])
        self.assertEqual(heights.call_count, 3)

    def test_chunked_regtest_mining_rejects_wrong_native_height(self):
        with patch.object(reorg, "mine", return_value=["a" * 64] * 10):
            with patch.object(reorg, "info", return_value={"height": 10}):
                with self.assertRaisesRegex(AssertionError, "height mismatch"):
                    reorg.mine_in_batches(19481, "test-only", 10, 15)

    def test_fork_test_never_contains_external_oracle_endpoint(self):
        source = (ROOT / "tools/smoke_regtest_reorg.py").read_text(encoding="utf-8")
        self.assertNotIn("150.136.209.227", source)
        self.assertIn("TemporaryDirectory(prefix=\"frg-fakechain-fork-\")", source)
        self.assertIn("manifest.get(\"release_authorized\") is not False", source)
        self.assertIn("manifest.get(\"mined_blocks_permitted_before_launch\") != 0", source)
        self.assertIn("header(a_rpc, 1)", source)
        self.assertIn("header(b_rpc, 1)", source)
        self.assertIn("a_old_first == b_first", source)
        self.assertIn("header(a_rpc, FORK_B_BLOCKS)", source)
        self.assertIn("a_old_tip", source)


if __name__ == "__main__":
    unittest.main()
