"""Android preview packaging source and negative-case tests; no device needed."""
import importlib.util
import os
from pathlib import Path
import re
import tempfile
import unittest
from zipfile import ZipFile, ZIP_STORED

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("verify_android_preview_apk", ROOT / "tools/verify_android_preview_apk.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def make_apk(path, extra=(), missing=()):
    names = {"AndroidManifest.xml", "classes.dex", *verifier.APPROVED_LIBS}
    names.difference_update(missing)
    names.update(extra)
    with ZipFile(path, "w", compression=ZIP_STORED) as z:
        for name in names:
            z.writestr(name, os.urandom(120_000) if name == "classes.dex" else b"test")


class AndroidPreviewTest(unittest.TestCase):
    def test_approved_support_libraries_without_daemon(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "app.apk"
            make_apk(p)
            r = verifier.verify(p)
            self.assertFalse(r["native_daemon_included"])
            self.assertFalse(r["mainnet_release_authorized"])

    def test_unreviewed_daemon_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "app.apk"
            make_apk(p, extra=("lib/arm64-v8a/libforged.so",))
            with self.assertRaises(ValueError):
                verifier.verify(p)

    def test_missing_randomx_support_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "app.apk"
            make_apk(p, missing=("lib/arm64-v8a/libforge_randomx.so",))
            with self.assertRaises(ValueError):
                verifier.verify(p)

    def test_seed_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "app.apk"
            make_apk(p, extra=("assets/wallet.keys",))
            with self.assertRaisesRegex(ValueError, "Forbidden"):
                verifier.verify(p)

    def test_read_only_device_safety_display_never_enables_mining(self):
        device = (ROOT / "apps/android/app/src/main/java/org/forgecoin/p2ptest/MiningDeviceStatus.java").read_text(encoding="utf-8")
        ui = (ROOT / "apps/android/app/src/main/java/org/forgecoin/p2ptest/MainActivity.java").read_text(encoding="utf-8")
        manifest = (ROOT / "apps/android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        gradle = (ROOT / "apps/android/app/build.gradle").read_text(encoding="utf-8")
        for expected in ("ACTION_BATTERY_CHANGED", "EXTRA_LEVEL", "EXTRA_SCALE",
                         "BATTERY_STATUS_CHARGING", "getCurrentThermalStatus",
                         "isPowerSaveMode", "availableProcessors"):
            self.assertIn(expected, device)
        self.assertIn("Mining OFF", device)
        self.assertNotIn("start_mining", device)
        self.assertNotIn("startMining", device)
        self.assertIn("MiningDeviceStatus.summary(MainActivity.this)", ui)
        self.assertIn('"Start solo mining — unavailable",false,mine,null', ui)
        self.assertIn('"Start pool mining — unavailable",false,mine,null', ui)
        self.assertIn('android:allowBackup="false"', manifest)
        self.assertNotIn('android:extractNativeLibs=', manifest)
        self.assertIn("JavaVersion.VERSION_17", gradle)

    def test_intensity_preferences_never_enable_native_mining(self):
        java = (ROOT / "apps/android/app/src/main/java/org/forgecoin/p2ptest")
        source = (java / "MainActivity.java").read_text(encoding="utf-8")
        policy = (java / "MiningSafetyPolicy.java").read_text(encoding="utf-8")
        self.assertIn("future-mining-intensity", source)
        self.assertIn("PREVIEW ONLY", source)
        self.assertIn("mining disabled", source)
        self.assertIn("if (!runtimeApproved)", policy)
        self.assertIn("if (!foregroundActive)", policy)
        self.assertIn("if (batterySaver)", policy)
        self.assertIn("thermalStatus >= THERMAL_SEVERE", policy)
        self.assertIn("frg", policy.lower())
        self.assertNotIn("ProcessBuilder", policy)
        self.assertNotIn("startMining(", source)
        self.assertNotIn("start_mining", policy)

    def test_source_keeps_real_controls_disabled_and_correct_status_url(self):
        s = (ROOT / "apps/android/app/src/main/java/org/forgecoin/p2ptest/MainActivity.java").read_text(encoding="utf-8")
        for caption, panel in (("Start solo mining", "mine"), ("Start pool mining", "mine"),
                               ("Create FRG wallet", "wallet"), ("Restore FRG wallet", "wallet"),
                               ("Receive / send FRG", "wallet")):
            self.assertRegex(s, r'button\("' + re.escape(caption) + r'[^"]*",false,' + panel + r',null\)')
        self.assertNotIn("https://150.136.209.227/", s)
        self.assertIn("https://tgibbsz32.github.io/forgecoin/current-mainnet.html", s)
        node = (ROOT / "apps/android/app/src/main/java/org/forgecoin/p2ptest/NodeService.java").read_text(encoding="utf-8")
        self.assertIn('s += ":39480"', node)
        self.assertIn('"--rpc-bind-ip", "127.0.0.1"', node)


if __name__ == "__main__":
    unittest.main()
