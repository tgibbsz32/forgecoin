"""FRG address validation must remain public-only and offline."""
import unittest
from pathlib import Path
J = Path(__file__).resolve().parents[2] / "apps/android/app/src/main/java/org/forgecoin/p2ptest"

class PublicAddressGuard(unittest.TestCase):
    def test_no_spend_network_or_seed_access(self):
        s=(J/"FrgPublicAddress.java").read_text(encoding="utf-8")
        for token in ("KeccakDigest(256)", "MessageDigest.isEqual",
                      "prefix = 190", "prefix = 191", "prefix = 192"):
            self.assertIn(token,s)
        for token in ("HttpURLConnection", "Socket(", "ProcessBuilder",
                      "secretKey", "privateSpendKey", "start_mining",
                      "restore_deterministic_wallet", "transfer_split"):
            self.assertNotIn(token,s)

    def test_native_wallet_is_debug_only_and_network_controls_remain_disabled(self):
        ui=(J/"MainActivity.java").read_text(encoding="utf-8")
        self.assertIn('"Validate FRG public address",BuildConfig.DEBUG',ui)
        self.assertIn("FrgPublicAddress.parse(",ui)
        self.assertIn("Public-format check only",ui)
        self.assertIn('nativeWalletReady=BuildConfig.DEBUG && NativeFrgWallet.available()',ui)
        self.assertIn('"Create native FRG wallet",nativeWalletReady,wallet',ui)
        self.assertIn('"Restore native FRG wallet",nativeWalletReady,wallet',ui)
        self.assertIn('"Send FRG — validation pending",false,wallet,null',ui)
        workflow=(J/"NativeWalletUi.java").read_text(encoding="utf-8")
        self.assertIn('if(!BuildConfig.DEBUG || !NativeFrgWallet.available()',workflow)
        self.assertIn('FLAG_SECURE',workflow)
        for token in ("HttpURLConnection", "Socket(", "ProcessBuilder", "commitTransaction", "start_mining"):
            self.assertNotIn(token,workflow)
        self.assertIn("miningQaReady=BuildConfig.DEBUG && MiningService.runtimePresent(this)",ui)

if __name__=="__main__":
    unittest.main()
