"""No live daemon, wallet, miner, block submission or payout in these tests."""
from dataclasses import replace
import io
import json
import secrets
import unittest
from unittest.mock import patch

from .daemon_job_source import (
    DaemonJobError, DaemonJobSource, LoopbackDaemonRpc
)

TIP = "ab" * 32
OTHER_TIP = "cd" * 32
GENESIS = "aa" * 32
SEED = "42" * 32


class FakeDaemon:
    def __init__(self):
        self.tip = TIP
        self.height = 17
        self.nettype = "testnet"
        self.sync = True
        self.genesis = GENESIS
        self.calls = []
        self.extra_nonce_return_override = None
        self.seed = SEED
        self.status = "OK"
        self.after_template_tip = None
        self.header_wrong = False
        self.timestamp_varint = b"\x80\x80\x80\x80\x01"

    def __call__(self, method, params=None):
        self.calls.append((method, params))
        if method == "get_info":
            return {
                "height": self.height, "top_block_hash": self.tip,
                "nettype": self.nettype, "synchronized": self.sync,
                "busy_syncing": False,
            }
        if method == "get_block_header_by_height":
            if params != {"height": 0}:
                raise AssertionError("unexpected header lookup")
            return {"block_header": {"height": 0, "hash": self.genesis}}
        if method != "get_block_template":
            raise AssertionError("unexpected daemon method")
        if not params or "extra_nonce" not in params or "reserve_size" in params:
            raise AssertionError("wrong RPC extra_nonce mode")
        extra = bytes.fromhex(params["extra_nonce"])
        reserve = (self.extra_nonce_return_override if self.extra_nonce_return_override
                   is not None else extra)
        # Serialized CryptoNote header: major, minor, timestamp(varint), prev, nonce.
        prev = bytes.fromhex(OTHER_TIP if self.header_wrong else self.tip)
        # Use a five-byte CryptoNote timestamp varint: standard XMRig rx/0
        # places the nonce at byte 39 (2 version bytes + 5 timestamp + 32).
        header = b"\x11\x11" + self.timestamp_varint + prev + bytes(4)
        # The daemon mining blob contains a merkle root derived from the miner
        # transaction, so changing coinbase extra_nonce must change this root.
        from hashlib import sha256
        hashing = header + sha256(b"fixture-miner-tx" + reserve).digest() + b"\x01"
        block = header + b"\x55" * 40 + reserve + b"\x66" * 16
        result = {
            "status": self.status, "height": self.height, "difficulty": 500000,
            "expected_reward": 2384185222, "seed_hash": self.seed,
            "blocktemplate_blob": block.hex(), "blockhashing_blob": hashing.hex(),
            "reserved_offset": len(header) + 40, "prev_hash": self.tip,
        }
        if self.after_template_tip is not None:
            self.tip = self.after_template_tip
        return result


class JobIssueTests(unittest.TestCase):
    def setUp(self):
        self.daemon = FakeDaemon()
        self.tick = 100.0
        self.issuer = DaemonJobSource(
            self.daemon, expected_genesis_hash=GENESIS, expected_nettype="testnet",
            wallet_address="DISPOSABLE_TEST_ADDRESS_1234",
            clock=lambda: self.tick, job_ttl=20, max_jobs=2,
        )

    def test_distinct_workers_receive_native_daemon_minted_work(self):
        a = self.issuer.issue("workerA", 1000)
        b = self.issuer.issue("workerB", 1000)
        self.assertNotEqual(a.job_id, b.job_id)
        self.assertNotEqual(a.hashing_blob_hex, "")
        self.assertEqual(a.height, 17)
        self.assertEqual(a.prev_hash, TIP)
        self.assertEqual(a.seed_hash, SEED)
        self.assertEqual(a.xmrig_job()["algo"], "rx/0")
        self.assertEqual(a.xmrig_job()["target"], (0xffffffff // 1000).to_bytes(4, "little").hex())
        rpc_jobs = [p for method, p in self.daemon.calls if method == "get_block_template"]
        self.assertEqual(len(rpc_jobs), 2)
        self.assertNotEqual(rpc_jobs[0]["extra_nonce"], rpc_jobs[1]["extra_nonce"])
        self.assertEqual(len(rpc_jobs[0]["extra_nonce"]), 16)
        self.assertNotIn("reserve_size", rpc_jobs[0])
        with self.assertRaisesRegex(DaemonJobError, "full"):
            self.issuer.issue("workerC", 1000)

    def test_nonce_and_digest_verified_against_native_callback(self):
        job = self.issuer.issue("workerA", 1)
        native_calls = []
        def native(seed, blob):
            native_calls.append((seed, blob))
            return bytes(32)
        result = self.issuer.inspect("workerA", job.job_id, "01020304",
                                     "00" * 32, native)
        self.assertEqual(result.status, "POW_THRESHOLD_MET_UNCREDITED")
        self.assertEqual(native_calls[0][0], bytes.fromhex(SEED))
        self.assertEqual(native_calls[0][1][39:43], bytes.fromhex("01020304"))
        self.assertEqual(len(native_calls), 1)
        with self.assertRaisesRegex(DaemonJobError, "verification failed"):
            self.issuer.inspect("workerA", job.job_id, "01020304", "00"*32, native)

    def test_cross_worker_session_mismatch_never_hashes(self):
        job = self.issuer.issue("workerA", 1)
        def must_not_hash(seed, blob): self.fail("must not hash foreign job")
        with self.assertRaisesRegex(DaemonJobError, "not assigned"):
            self.issuer.inspect("workerB", job.job_id, "01020304", "00"*32, must_not_hash)

    def test_wrong_digest_and_low_difficulty_reject(self):
        job = self.issuer.issue("workerA", 5)
        with self.assertRaisesRegex(DaemonJobError, "disagrees"):
            self.issuer.inspect("workerA", job.job_id, "01020304", "ff"*32,
                                lambda seed,blob: bytes(32))
        with self.assertRaisesRegex(DaemonJobError, "low-difficulty"):
            self.issuer.inspect("workerA", job.job_id, "05060708", "ff"*32,
                                lambda seed,blob: bytes.fromhex("ff"*32))

    def test_genesis_network_and_sync_mismatch_fail_closed(self):
        for field, value in (("genesis", OTHER_TIP), ("nettype", "mainnet"),
                             ("sync", False)):
            with self.subTest(field=field):
                fake = FakeDaemon()
                setattr(fake, field, value)
                issuer = DaemonJobSource(fake, expected_genesis_hash=GENESIS,
                    expected_nettype="testnet", wallet_address="DISPOSABLE_TEST_ADDRESS")
                with self.assertRaises(DaemonJobError):
                    issuer.issue("a", 1)
                self.assertFalse(any(method == "get_block_template" for method, _ in fake.calls))

    def test_template_reserved_region_and_header_mismatch(self):
        for field,value in (("extra_nonce_return_override", bytes.fromhex("dd"*8)),
                            ("header_wrong", True), ("status", "BUSY")):
            with self.subTest(field=field):
                fake=FakeDaemon()
                setattr(fake, field, value)
                issuer=DaemonJobSource(fake,expected_genesis_hash=GENESIS,
                    expected_nettype="testnet",wallet_address="DISPOSABLE_TEST_ADDRESS")
                with self.assertRaises(DaemonJobError):
                    issuer.issue("a", 1)

    def test_fork_race_during_template_or_hashing_is_rejected(self):
        self.daemon.after_template_tip = OTHER_TIP
        with self.assertRaisesRegex(DaemonJobError, "tip changed"):
            self.issuer.issue("workerA", 1)
        self.daemon.after_template_tip = None
        self.daemon.tip = TIP
        job = self.issuer.issue("workerA", 1)
        def forked(seed,blob):
            self.daemon.tip=OTHER_TIP
            return bytes(32)
        with self.assertRaisesRegex(DaemonJobError, "stale"):
            self.issuer.inspect("workerA", job.job_id, "01020304", "00"*32,forked)

    def test_worker_target_encoding_rejects_difficulty_over_u32(self):
        # XMRig target field is exactly four bytes in this first protocol.
        with self.assertRaisesRegex(DaemonJobError, "difficulty"):
            self.issuer.issue("workerA", 0x100000000)
        self.assertFalse(any(method == "get_block_template" for method, _ in self.daemon.calls))

    def test_expiration_and_bad_claim_fail_without_hash(self):
        job = self.issuer.issue("workerA", 1)
        def forbidden(s,b):self.fail("must not hash")
        for invalid in ("aaa", "g"*64, ""):
            with self.subTest(invalid=invalid), self.assertRaises(DaemonJobError):
                self.issuer.inspect("workerA", job.job_id,"01020304",invalid,forbidden)
        self.tick = 121
        with self.assertRaisesRegex(DaemonJobError, "expired"):
            self.issuer.inspect("workerA", job.job_id,"01020304","00"*32,forbidden)

    def test_nonstandard_nonce_offset_is_rejected_before_worker_job(self):
        self.daemon.timestamp_varint = b"\xac\x02"
        with self.assertRaisesRegex(DaemonJobError, "nonce offset"):
            self.issuer.issue("workerA", 1)

    def test_missing_verifier_does_not_consume_nonce(self):
        job = self.issuer.issue("workerA", 1)
        with self.assertRaisesRegex(DaemonJobError, "verification failed"):
            self.issuer.inspect("workerA", job.job_id,"01020304","00"*32,None)
        self.assertEqual(self.issuer.inspect("workerA",job.job_id,"01020304",
                     "00"*32,lambda s,b:bytes(32)).status,"POW_THRESHOLD_MET_UNCREDITED")


class LoopbackRpcTests(unittest.TestCase):
    def test_no_remote_dns_https_or_embedded_authority(self):
        for url in ("https://127.0.0.1:39481/json_rpc","http://localhost:39481/json_rpc",
                    "http://example.com:80/json_rpc", "http://127.0.0.1:39481/admin",
                    "http://name:secret@127.0.0.1:39481/json_rpc",
                    "http://127.0.0.1/json_rpc"):
            with self.subTest(url=url),self.assertRaises(DaemonJobError):
                LoopbackDaemonRpc(url)
        with self.assertRaises(DaemonJobError):
            LoopbackDaemonRpc("http://127.0.0.1:39481/json_rpc")("stop_daemon")

    def test_rpc_envelope_and_size_validation(self):
        rpc = LoopbackDaemonRpc("http://127.0.0.1:39481/json_rpc")
        ok = b'{"jsonrpc":"2.0","id":"frg-job-readonly","result":{"height":17}}'
        with patch.object(rpc._opener,"open",return_value=_FakeResponse(ok)):
            self.assertEqual(rpc("get_info")["height"],17)
        for invalid in (b'[]',b'{"result":{}}',b'{"id":"wrong","result":{}}',
                        b'{"id":"frg-job-readonly","result":[]}',
                        b'{"id":"frg-job-readonly","error":{"code":-1}}',
                        b'a'*(1024*1024+1)):
            with self.subTest(first=invalid[:20]),patch.object(
                    rpc._opener,"open",return_value=_FakeResponse(invalid)):
                with self.assertRaises(DaemonJobError):
                    rpc("get_info")


class _FakeResponse:
    status = 200
    def __init__(self, payload): self.buffer=io.BytesIO(payload)
    def __enter__(self):return self
    def __exit__(self,*args): self.buffer.close()
    def read(self,n):return self.buffer.read(n)


if __name__ == "__main__":
    unittest.main()
