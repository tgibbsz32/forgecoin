"""Selected October 26 FRG ports across active clients and service integration.

Historical docs and archived prior_chains are intentionally not treated as live
endpoints. The frozen native consensus build is staged separately in PR #185.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
NATIVE = {"p2p": 39480, "daemon_rpc": 39481, "zmq_rpc": 39482}


def src(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class SelectedPorts(unittest.TestCase):
    def test_frozen_manifest_ports_match_public_spec(self):
        for path in ("config/mainnet.identity.json", "docs/mainnet.identity.json"):
            with self.subTest(path=path):
                manifest = json.loads(src(path))
                self.assertEqual(manifest["ports"], NATIVE)
                self.assertEqual(manifest["genesis_nonce"], 20261026)
                self.assertEqual(
                    manifest["address_prefixes"],
                    {"standard": 190, "integrated": 191, "subaddress": 192},
                )
                self.assertIs(manifest["release_authorized"], False)
                old = manifest["prior_chains"]["development"]
                self.assertEqual(old["classification"], "archive_only")
                self.assertEqual(old["p2p_port"], 19480)
                self.assertEqual(old["rpc_port"], 19481)

    def test_native_compatibility_guards_and_pooled_rpc(self):
        pool = src("services/official_pool/jtgrassie/pool.conf")
        server = src("services/official_pool/jtgrassie/src/pool.c")
        compat = src("services/official_pool/jtgrassie/src/xmr.cpp")
        self.assertIn("rpc-port = 39481", pool)
        self.assertIn("config.rpc_port = 39481", server)
        self.assertIn("config.rpc_port != 39481", server)
        for token in ("P2P_DEFAULT_PORT == 39480",
                      "RPC_DEFAULT_PORT == 39481",
                      "ZMQ_RPC_DEFAULT_PORT == 39482"):
            self.assertIn(token, compat)
        # The native main branch is still legacy; PR #185 integrates the
        # frozen daemon. No false assertion that main's binary is ready.

    def test_android_and_explorer_use_selected_node_ports(self):
        android = src("apps/android/app/src/main/java/org/forgecoin/p2ptest/NodeService.java")
        explorer = src("apps/explorer/app.py")
        self.assertIn('s += ":39480"', android)
        self.assertIn("optionally followed by :39480", android)
        self.assertNotIn("19480", android)
        self.assertIn("http://127.0.0.1:39481", explorer)
        self.assertIn("expected_daemon_rpc_port=39481", explorer)
        self.assertNotIn("19481", explorer)

    def test_windows_apps_keep_native_and_local_services_separate(self):
        classic = src("apps/desktop/Program.cs")
        tauri = src("apps/desktop-tauri/src-tauri/src/engine.rs")
        ui = src("apps/desktop-tauri/src/App.tsx")
        for legacy in ("19480", "19481", "19482"):
            self.assertNotIn(legacy, classic)
            self.assertNotIn(legacy, ui)
        self.assertIn("--rpc-bind-port 39484", classic)
        self.assertIn("127.0.0.1:39484/json_rpc", classic)
        self.assertIn('"--http-port", "39483"', classic)
        self.assertIn("127.0.0.1:39483/2/summary", classic)
        self.assertIn('daemon_url: "http://127.0.0.1:39481".into()', tauri)
        self.assertIn("peer: String::new()", tauri)
        self.assertIn('settings.peer.trim().ends_with(":19480")', tauri)
        self.assertIn('peer.port() == Some(19480)', tauri)
        self.assertIn('u.port() == Some(19481)', tauri)

    def test_website_and_current_docs_reflect_distinct_local_ports(self):
        spec = src("docs/CURRENT_MAINNET.md")
        page = src("docs/current-mainnet.html")
        contract = src("docs/NETWORK_PORTS.md")
        for val in ("39480", "39481", "39482", "39483", "39484"):
            with self.subTest(port=val):
                self.assertIn(val, contract)
        self.assertIn("Windows Forms wallet RPC **127.0.0.1:39484**", spec)
        self.assertIn("Wallet RPC 39484; XMRig statistics 39483", page)
        self.assertIn("NETWORK_PORTS.md", page)
        self.assertIn("Tauri wallet RPC", contract)
        self.assertIn("19480", contract)  # archived use specifically identified
        self.assertIn("archive_only", contract)


if __name__ == "__main__":
    unittest.main()
