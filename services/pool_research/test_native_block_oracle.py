"""Fail-closed unit tests for the offline native block serialization oracle."""
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from services.pool_research.native_block_oracle import NativeBlockError, native_hashing_blob


class NativeBlockOracleTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__)
        self.full = bytes(range(50))
        self.hashing = bytes(range(76))
        self.valid = subprocess.CompletedProcess([], 0,
            stdout=self.full.hex() + "\n" + self.hashing.hex() + "\n",
            stderr="")

    @patch("services.pool_research.native_block_oracle.subprocess.run")
    def test_exact_canonical_round_trip(self, run):
        run.return_value = self.valid
        self.assertEqual(native_hashing_blob(self.path, self.full), self.hashing)
        self.assertEqual(run.call_args.kwargs["input"], self.full.hex() + "\n")
        self.assertFalse(run.call_args.kwargs["check"])
        self.assertEqual(run.call_args.kwargs["timeout"], 15)

    @patch("services.pool_research.native_block_oracle.subprocess.run")
    def test_modified_source_serialization_fails_closed(self, run):
        changed = bytearray(self.full)
        changed[12] ^= 0x10
        run.return_value = subprocess.CompletedProcess([], 0,
            stdout=bytes(changed).hex() + "\n" + self.hashing.hex() + "\n",
            stderr="")
        with self.assertRaisesRegex(NativeBlockError, "serialization differs"):
            native_hashing_blob(self.path, self.full)

    @patch("services.pool_research.native_block_oracle.subprocess.run")
    def test_invalid_native_output_never_accepted(self, run):
        outputs = ("", "garbage\n", self.full.hex() + "\n", "ff\n" + self.hashing.hex() + "\n",
                   self.full.hex() + "\nGG\n",
                   self.full.hex() + "\n" + ("00" * 39) + "\n",
                   self.full.hex() + "\n" + self.hashing.hex() + "\nextra\n")
        for stdout in outputs:
            with self.subTest(stdout=stdout[:30]):
                run.return_value = subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")
                with self.assertRaises(NativeBlockError):
                    native_hashing_blob(self.path, self.full)

    @patch("services.pool_research.native_block_oracle.subprocess.run")
    def test_nonzero_or_timeout_rejected(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, stdout="", stderr="rejected")
        with self.assertRaises(NativeBlockError):
            native_hashing_blob(self.path, self.full)
        run.side_effect = subprocess.TimeoutExpired("oracle", 15)
        with self.assertRaises(NativeBlockError):
            native_hashing_blob(self.path, self.full)

    def test_invalid_inputs_fail_before_process(self):
        for blob in (b"", "not bytes", None, b"x" * 262145):
            with self.subTest(blob_type=type(blob).__name__), self.assertRaises(NativeBlockError):
                native_hashing_blob(self.path, blob)
        with self.assertRaises(NativeBlockError):
            native_hashing_blob(self.path, self.full, timeout=0)


if __name__ == "__main__":
    unittest.main()
