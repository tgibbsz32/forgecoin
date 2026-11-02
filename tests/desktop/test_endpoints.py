"""Selected FRG 20261026 desktop network/loopback preflight.

These guard source and configuration, not native wallet/payout validation.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class DesktopIdentityPreflight(unittest.TestCase):
    def test_windows_forms_wallet_rpc_is_not_zmq_or_miner_api(self):
        code = source("apps/desktop/Program.cs")
        self.assertNotIn("19482", code)
        self.assertIn("--rpc-bind-ip 127.0.0.1 --rpc-bind-port 39484", code)
        self.assertIn("--daemon-address 127.0.0.1:39481", code)
        self.assertIn('Rpc("http://127.0.0.1:39484/json_rpc", "transfer"', code)
        self.assertIn('"--http-host", "127.0.0.1", "--http-port", "39483"', code)
        self.assertIn('HttpGetJson("http://127.0.0.1:39483/2/summary")', code)
        self.assertNotIn('Rpc("http://127.0.0.1:39483/json_rpc"', code)
        self.assertIn('"--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", "39480"', code)
        self.assertIn('"--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", "39481"', code)

    def test_tauri_defaults_require_explicit_peer_and_selected_ports(self):
        back = source("apps/desktop-tauri/src-tauri/src/engine.rs")
        front = source("apps/desktop-tauri/src/App.tsx")
        self.assertIn('daemon_url: "http://127.0.0.1:39481".into()', back)
        self.assertIn('peer: String::new()', back)
        self.assertIn('daemonUrl: "http://127.0.0.1:39481", peer: ""', front)
        self.assertNotIn('150.136.209.227:19480', front)
        self.assertIn('placeholder="trusted-node.example.org:39480"', front)
        self.assertIn('"--p2p-bind-ip",', back)
        self.assertIn('''"--p2p-bind-ip",
                            "127.0.0.1",
                            "--p2p-bind-port",
                            "39480",''', back)
        self.assertIn('''"--rpc-bind-ip",
                            "127.0.0.1",
                            "--rpc-bind-port",
                            "39481",''', back)
        self.assertIn('if self.settings.peer.is_empty()', back)

    def test_tauri_migrates_saved_old_endpoint_without_reactivating_it(self):
        back = source("apps/desktop-tauri/src-tauri/src/engine.rs")
        self.assertIn('settings.peer.trim().ends_with(":19480")', back)
        self.assertIn('settings.peer.clear();', back)
        self.assertIn('settings.daemon_url.trim_end_matches(\'/\') == "http://127.0.0.1:19481"', back)
        self.assertIn('settings.daemon_url = Settings::default().daemon_url;', back)
        self.assertIn('serde_json::to_vec_pretty(&settings)', back)
        self.assertIn('peer.port() == Some(19480)', back)
        self.assertIn('u.port() == Some(19481)', back)
        self.assertIn('Retired ForgeCoin daemon RPC port 19481', back)

    def test_docs_no_longer_mix_wallet_rpc_and_xmrig(self):
        for path in ("apps/desktop/INSTALL.md", "apps/desktop/README.txt"):
            document = source(path)
            self.assertIn("wallet RPC uses localhost39484", document)
            self.assertIn("XMRig stats use 39483", document)
            self.assertIn("NOT LAUNCHED", document)
        validation = source("apps/desktop/VALIDATION.md")
        self.assertIn("127.0.0.1:39484", validation)
        self.assertIn("127.0.0.1:39483", validation)
        self.assertNotIn("P2P listens on TCP 19480", validation)


if __name__ == "__main__":
    unittest.main()
