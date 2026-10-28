"""Offline-only PPLNS window and atomic conservation regression tests."""
from dataclasses import replace
import unittest

from services.pool_research.pplns import (
    VerifiedShare, allocate_pplns, snapshot, MAX_SQLITE_INT,
)


class PPLNSTests(unittest.TestCase):
    def setUp(self):
        self.history = [
            VerifiedShare(10, "share-A1", "minerA", 8),
            VerifiedShare(11, "share-B1", "minerB", 7),
            VerifiedShare(12, "share-A2", "minerA", 5),
        ]

    def test_partial_oldest_share_and_one_percent_fee(self):
        result = allocate_pplns(10000, self.history, 5)
        self.assertEqual(result.window.target_work, 10)
        self.assertEqual(result.window.observed_work, 10)
        self.assertEqual(result.window.miner_work, {"minerA": 5, "minerB": 5})
        self.assertEqual((result.window.first_sequence,
                          result.window.last_sequence), (11, 12))
        self.assertTrue(result.window.partial_first_share)
        self.assertEqual(result.reward.fee_atomic, 100)
        self.assertEqual(result.reward.miner_atomic, {"minerA": 4950, "minerB": 4950})

    def test_partial_boundary_spans_older_share(self):
        window = snapshot(self.history, 7)
        self.assertEqual(window.miner_work, {"minerA": 7, "minerB": 7})
        self.assertEqual(window.observed_work, 14)
        self.assertEqual(window.first_sequence, 10)
        self.assertTrue(window.partial_first_share)

    def test_short_history_does_not_invent_work(self):
        window = snapshot(self.history, 100)
        self.assertEqual(window.target_work, 200)
        self.assertEqual(window.observed_work, 20)
        self.assertEqual(window.miner_work, {"minerA": 13, "minerB": 7})
        self.assertFalse(window.partial_first_share)

    def test_exact_window_and_tiny_atomic_rounding(self):
        window = snapshot(self.history, 10)
        self.assertEqual(window.observed_work, 20)
        self.assertFalse(window.partial_first_share)
        result = allocate_pplns(7, self.history, 5)
        self.assertEqual(result.reward.fee_atomic, 0)
        self.assertEqual(result.reward.miner_atomic, {"minerA": 4, "minerB": 3})
        self.assertEqual(result.reward.fee_atomic
                         + sum(result.reward.miner_atomic.values()), 7)

    def test_history_immutable_and_repeatable(self):
        before = list(self.history)
        x = allocate_pplns(901, self.history, 5)
        y = allocate_pplns(901, self.history, 5)
        self.assertEqual(x, y)
        self.assertEqual(self.history, before)

    def test_offline_ledger_maturity_and_orphan_simulation(self):
        """Composition check only; chain authority and signing are absent."""
        import tempfile
        from pathlib import Path
        from services.pool_research.ledger import RewardLedger

        result = allocate_pplns(10000, self.history, 5)
        with tempfile.TemporaryDirectory() as folder:
            ledger = RewardLedger(Path(folder) / "simulation.sqlite")
            try:
                block_hash = "ab" * 32
                self.assertTrue(ledger.record_block(
                    block_hash, 1, 10000, 61, result.window.miner_work))
                self.assertEqual(ledger.balances(), {})
                ledger.reconcile_chain([block_hash], 60)
                self.assertEqual(ledger.balances(), {})
                ledger.reconcile_chain([block_hash], 61)
                self.assertEqual(ledger.balances(), result.reward.miner_atomic)
                ledger.reconcile_chain([], 62)
                self.assertEqual(ledger.balances(), {})
                with self.assertRaisesRegex(ValueError, "revival"):
                    ledger.reconcile_chain([block_hash], 63)
            finally:
                ledger.close()

    def test_rejects_corrupt_history(self):
        base = self.history
        cases = (
            list(reversed(base)),
            [base[0], replace(base[1], sequence=10), base[2]],
            [base[0], replace(base[1], share_id="share-A1"), base[2]],
            [replace(base[0], difficulty=0), *base[1:]],
            [replace(base[0], difficulty=True), *base[1:]],
            [replace(base[0], difficulty=MAX_SQLITE_INT + 1), *base[1:]],
            [replace(base[0], miner="a\nb"), *base[1:]],
            [replace(base[0], share_id="bad identity"), *base[1:]],
            [replace(base[0], sequence=True), *base[1:]],
            [("not a share"), *base[1:]],
            [],
        )
        for sample in cases:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                snapshot(sample, 5)

    def test_rejects_unsafe_targets_and_rewards(self):
        for diff, mult in ((0, 2), (True, 2), (5, True), (5, 0),
                           (5, 17), (MAX_SQLITE_INT, 2)):
            with self.subTest(diff=diff, multiplier=mult):
                with self.assertRaises(ValueError):
                    snapshot(self.history, diff, multiplier=mult)
        for reward in (-1, True, 1.0, MAX_SQLITE_INT + 1):
            with self.subTest(reward=reward), self.assertRaises(ValueError):
                allocate_pplns(reward, self.history, 5)


if __name__ == "__main__":
    unittest.main()
