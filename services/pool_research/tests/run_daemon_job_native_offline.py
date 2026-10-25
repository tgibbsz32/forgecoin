"""Optional real native RandomX + fixture daemon-job check; no network or funds.

From repo root: python -m services.pool_research.tests.run_daemon_job_native_offline
    --executable /trusted/compiled/randomx_worker[.exe]

The executable is supplied explicitly and not auto-downloaded or compiled.
Template bytes are synthetic and come from a LOCAL TEST CLASS, not a daemon.
"""
from argparse import ArgumentParser
from pathlib import Path

from services.pool_research.daemon_job_source import DaemonJobSource, DaemonJobError
from services.pool_research.persistent_randomx import PersistentRandomXAdapter
from services.pool_research.bound_job import _varint
from services.pool_research.test_daemon_job_source import FakeDaemon, GENESIS, SEED


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    native = PersistentRandomXAdapter(args.executable, timeout=30)
    try:
        expected = "294083824fec5947ef2cd825e2bedcb34789e4cc6ad12d7823bcf0be51178f77"
        seed = bytes.fromhex("2a91ebe3007fb301072c5b0c8e130c782d1218e4633f6a30e6c2d692b6ac5f05")
        if native(seed, b"\x11" * 76).hex() != expected:
            raise AssertionError("native RandomX reference vector mismatch")
        fake = FakeDaemon()
        source = DaemonJobSource(
            fake, expected_genesis_hash=GENESIS, expected_nettype="testnet",
            wallet_address="DISPOSABLE_TEST_ADDRESS",
        )
        worker = source.issue("worker-native", 1)
        blob = bytes.fromhex(worker.hashing_blob_hex)
        offset = 0
        for _ in range(3):
            offset = _varint(blob, offset)
        offset += 32
        nonce = "01020304"
        patched = blob[:offset] + bytes.fromhex(nonce) + blob[offset + 4:]
        claimed_digest = native(bytes.fromhex(SEED), patched).hex()
        result = source.inspect("worker-native", worker.job_id, nonce, claimed_digest, native)
        if result.status != "POW_THRESHOLD_MET_UNCREDITED" or result.digest_hex != claimed_digest:
            raise AssertionError("native RandomX job binding failed")
        try:
            source.inspect("worker-native", worker.job_id, nonce, claimed_digest, native)
        except DaemonJobError:
            pass
        else:
            raise AssertionError("duplicate native share was not rejected")
        print("PASS: native RandomX reference vector")
        print("PASS: worker-specific fixture template + native digest verification")
        print("PASS: duplicate native nonce refused; no share credited")
        print("NOTICE: fixture daemon, not production, no blockchain acceptance or payouts")
    finally:
        native.close()


if __name__ == "__main__":
    main()
