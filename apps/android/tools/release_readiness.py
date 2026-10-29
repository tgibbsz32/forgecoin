#!/usr/bin/env python3
"""Fail-closed static gate. A passing code check does not grant release approval."""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
SRC = ROOT / "app/src/main"
EVIDENCE = ROOT / "release_evidence.json"

def audit(root=ROOT):
    root = Path(root)
    manifest = (root / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    activity = (root / "app/src/main/java/org/forgecoin/p2ptest/MainActivity.java").read_text(encoding="utf-8")
    evidence_file = root / "release_evidence.json"
    evidence = json.loads(evidence_file.read_text(encoding="utf-8")) if evidence_file.exists() else {}
    binary = root / "app/src/main/jniLibs/arm64-v8a/libforged.so"
    checks = {
        "private_app_backup_disabled": 'android:allowBackup="false"' in manifest,
        "native_fr g_binary_present".replace(" ", ""): binary.is_file() and binary.stat().st_size > 100000,
        "native_consensus_acceptance_signed_off": bool(evidence.get("native_consensus_acceptance_signed_off", False)),
        "native_25_word_wallet_create_restore_verified": bool(evidence.get("native_25_word_wallet_create_restore_verified", False)),
        "native_wallet_signing_broadcast_verified": bool(evidence.get("native_wallet_signing_broadcast_verified", False)),
        "arm64_randomx_solo_pool_acceptance_verified": bool(evidence.get("arm64_randomx_solo_pool_acceptance_verified", False)),
        "foreground_mining_thermal_safety_verified": bool(evidence.get("foreground_mining_thermal_safety_verified", False)),
        "physical_arm64_test_evidence": bool(evidence.get("physical_arm64_test_evidence", False)),
        "device_authentication_verified": bool(evidence.get("device_authentication_verified", False)),
        "independent_security_review_signed": bool(evidence.get("independent_security_review_signed", False)),
        "release_wallet_operations_enabled": '"Create FRG wallet — unavailable"' not in activity,
    }
    # Never auto-certify a release from claims in a JSON file: this script
    # reports missing claims only and a separate human evidence review is mandatory.
    return checks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-release", action="store_true")
    args = parser.parse_args()
    checks = audit()
    for name, success in checks.items():
        print("{} {}".format("PASS" if success else "BLOCK", name))
    ready = all(checks.values())
    print("RELEASE_READINESS={}".format("EVIDENCE_REQUIRED" if ready else "BLOCKED"))
    if args.require_release and not ready:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
