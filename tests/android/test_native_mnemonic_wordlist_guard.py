"""Native 25-word English mnemonic compatibility: byte-exact C++ word list."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
ANDROID = ROOT / "apps/android/app"
NATIVE = ROOT / "src/mnemonics/english.h"


class NativeEnglishMnemonicGuards(unittest.TestCase):
    def test_dictionary_matches_native_cpp_order_exactly(self):
        cpp = NATIVE.read_text(encoding="utf-8")
        start = cpp.index("static constexpr const char * const words[NWORDS]")
        brace = cpp.index("{", start)
        end = cpp.index("};", brace)
        actual = re.findall(r'"([a-z]+)"', cpp[brace:end])
        asset = (ANDROID / "src/main/assets/frg_english_mnemonic.txt").read_text(
            encoding="utf-8"
        )
        dictionary = [
            line.strip() for line in asset.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(1626, len(actual))
        self.assertEqual(actual, dictionary)
        self.assertEqual(1626, len({word[:3] for word in dictionary}))

    def test_validator_is_offline_and_no_key_storage(self):
        java = (ANDROID / "src/main/java/org/forgecoin/p2ptest/FrgMnemonicEnglish.java")
        source = java.read_text(encoding="utf-8")
        for token in ("CRC32", "0xffff_ffffL", "DICTIONARY_WORDS = 1626",
                      "PHRASE_WORDS = 25", "PREFIX_LENGTH = 3",
                      "checksumIndex", "MAX_UINT32"):
            self.assertIn(token, source)
        for forbidden in ("HttpURLConnection", "Socket(", "ProcessBuilder",
                          "SecretKey", "KeyStore", "transfer", "start_mining",
                          "privateSpendKey", "writeFile"):
            self.assertNotIn(forbidden, source)
        ui = (ANDROID / "src/main/java/org/forgecoin/p2ptest/MainActivity.java").read_text(
            encoding="utf-8"
        )
        self.assertIn('"Restore FRG wallet — unavailable",false,wallet,null', ui)
        self.assertNotIn("FrgMnemonicEnglish.load(", ui)


if __name__ == "__main__":
    unittest.main()
