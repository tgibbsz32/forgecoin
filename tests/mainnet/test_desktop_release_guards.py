import json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2]
M=json.loads((R/"config/mainnet.identity.json").read_text())
def src(name):return (R/name).read_text(encoding="utf-8")
class DesktopPrelaunchGuards(unittest.TestCase):
 def test_genesis_pinned_and_three_windows_binaries(self):
  self.assertEqual(M["genesis_hash"],"4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c")
  self.assertEqual(M["stage"],"genesis-frozen")
  self.assertFalse(M["release_authorized"])
  binaries=M["windows_prelaunch_binaries_sha256"]
  self.assertEqual(set(binaries),{"forged.exe","forge-wallet-rpc.exe","forge-wallet-cli.exe"})
  for sha in binaries.values():self.assertRegex(sha,r"^[0-9a-f]{64}$")
 def test_explorer_has_hash_and_nonce_guards(self):
  ex=src("apps/explorer/app.py")
  self.assertIn("EXPECTED_GENESIS_HASH = '"+M["genesis_hash"]+"'",ex)
  self.assertIn("genesis.get('hash') != EXPECTED_GENESIS_HASH",ex)
  self.assertIn("genesis.get('nonce') != EXPECTED_GENESIS_NONCE",ex)
 def test_wallet_bundle_checks_native_hashes(self):
  b=src("apps/desktop/build.ps1")
  for x in ("windows_prelaunch_binaries_sha256","Get-FileHash","Wrong network, stale build or tampered executable",
            "mainnet.identity.json","forge-wallet-cli.exe","TREASURY-WALLET.md"):
   self.assertIn(x,b)
 def test_wallet_creation_available_but_both_mining_modes_locked(self):
  c=src("apps/desktop/Program.cs")
  t=src("apps/desktop-tauri/src-tauri/src/engine.rs")
  for x in ("New mainnet has not launched. Solo mining","New mainnet has not launched. Pool mining","private void CreateWallet","wallets-mainnet-20261026"):
   self.assertIn(x,c)
  for x in ("Fresh mainnet has not launched: solo mining","Fresh mainnet has not launched: pool mining","wallets-mainnet-20261026"):
   self.assertIn(x,t)
 def test_case_insensitive_windows_crypto_assembler(self):
  c=src("src/crypto/CMakeLists.txt")
  r=src("external/randomx/CMakeLists.txt")
  self.assertIn("FORGE_CRYPTO_ARCH_ID",c)
  self.assertIn("RANDOMX_TARGET_ARCH",r)
  self.assertIn("CryptonightR_template.S",c)
  self.assertIn("jit_compiler_x86_static.S",r)
 def test_wallet_rpc_never_serves_treasury_methods_without_auth(self):
  gui=src("apps/desktop/Program.cs")
  self.assertNotIn("--disable-rpc-login",gui)
  self.assertIn("--rpc-login",gui)
  self.assertIn("RandomNumberGenerator.Create()",gui)
  self.assertIn("new NetworkCredential",gui)
  self.assertIn('"Digest"',gui)
  self.assertIn("http.Credentials = cache",gui)
  self.assertIn("127.0.0.1:39483",gui)
 def test_owner_fee_wallet_secret_not_necessary_for_pool(self):
  docs=src("apps/desktop/TREASURY-WALLET.md")
  self.assertIn("You alone retain",docs)
  self.assertIn("public FRG receiving address",docs)
  self.assertIn("No server needs your seed",docs)
  p=src("services/official_pool/jtgrassie/src/pool.c")
  self.assertIn("Missing pool-fee-wallet",p)
  self.assertIn("fee_nettype != nettype",p)
if __name__=="__main__":unittest.main()
