"""Deterministic offline ledger safety checks; no native daemon involved."""
import tempfile
import unittest
from pathlib import Path
from services.pool_research.ledger import RewardLedger

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.path=Path(self.dir.name)/"pool.sqlite"
        self.ledger=RewardLedger(self.path)
        self.h="ab"*32
        self.shares={"minerA":3,"minerB":1}
    def tearDown(self):
        self.ledger.close()
        self.dir.cleanup()
    def test_maturity_idempotence_and_persistence(self):
        self.assertTrue(self.ledger.record_block(self.h,100,10000,160,self.shares))
        self.assertFalse(self.ledger.record_block(self.h,100,10000,160,self.shares))
        self.ledger.reconcile_chain({100:self.h,159:"ef"*32},159)
        self.assertEqual(self.ledger.balances(),{})
        self.ledger.close()
        self.ledger=RewardLedger(self.path)
        self.ledger.reconcile_chain({100:self.h,160:"ef"*32},160)
        self.assertEqual(self.ledger.balances(),{"minerA":7425,"minerB":2475})
    def test_orphan_reversal_and_no_automatic_revival(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.reconcile_chain({100:self.h,160:"ef"*32},160)
        self.ledger.reconcile_chain({100:"cd"*32,161:"ef"*32},161)
        self.assertEqual(self.ledger.balances(),{})
        with self.assertRaisesRegex(ValueError,"revival"):
            self.ledger.reconcile_chain({100:self.h,162:"ef"*32},162)
    def test_conflicting_duplicate_rejected(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        with self.assertRaisesRegex(ValueError,"conflicting"):
            self.ledger.record_block(self.h,100,10000,160,{"minerA":1})
    def test_invalid_inputs(self):
        for args in [("bad",100,10000,160,self.shares),(self.h,-1,10000,160,self.shares),(self.h,100,10000,100,self.shares)]:
            with self.assertRaises(ValueError):self.ledger.record_block(*args)
    def states(self):
        return list(self.ledger.db.execute("SELECT block_hash,state FROM blocks ORDER BY height"))

    def test_partial_chain_view_cannot_reverse_rewards(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.reconcile_chain({100:self.h,160:"ef"*32},160)
        before=self.states()
        for view in [{160:"ef"*32}, {}, [self.h], {100:self.h}]:
            with self.subTest(view=view), self.assertRaises(ValueError):
                self.ledger.reconcile_chain(view,160)
            self.assertEqual(self.states(),before)
            self.assertEqual(self.ledger.balances(),{"minerA":7425,"minerB":2475})

    def test_hash_at_wrong_height_cannot_mature_reward(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.reconcile_chain({99:self.h,100:"cd"*32,160:"ef"*32},160)
        self.assertEqual(self.states(),[(self.h,"orphaned")])
        self.assertEqual(self.ledger.balances(),{})

    def test_reorg_to_shorter_chain_orphans_blocks_above_tip(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.reconcile_chain({100:self.h,160:"ef"*32},160)
        self.ledger.reconcile_chain({99:"cd"*32},99)
        self.assertEqual(self.states(),[(self.h,"orphaned")])
        self.ledger.close()
        self.ledger=RewardLedger(self.path)
        self.assertEqual(self.ledger.balances(),{})
        self.assertEqual(self.states(),[(self.h,"orphaned")])

    def test_tip_rollback_demotes_mature_reward(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.reconcile_chain({100:self.h,160:"ef"*32},160)
        self.ledger.reconcile_chain({100:self.h,159:"ef"*32},159)
        self.assertEqual(self.states(),[(self.h,"immature")])
        self.assertEqual(self.ledger.balances(),{})

    def test_conflicting_candidates_at_same_height(self):
        other="cd"*32
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.record_block(other,100,20000,160,self.shares)
        self.ledger.reconcile_chain({100:self.h,160:"ef"*32},160)
        self.assertEqual(dict(self.states()),{self.h:"mature",other:"orphaned"})
        self.assertEqual(self.ledger.balances(),{"minerA":7425,"minerB":2475})

    def test_failed_revival_rolls_back_other_state_changes(self):
        other="cd"*32
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        self.ledger.record_block(other,101,10000,161,self.shares)
        self.ledger.reconcile_chain({100:self.h,101:"aa"*32,160:"ef"*32},160)
        before=self.states()
        with self.assertRaisesRegex(ValueError,"revival"):
            self.ledger.reconcile_chain({100:"aa"*32,101:other,161:"ef"*32},161)
        self.assertEqual(self.states(),before)

    def test_invalid_snapshot_is_atomic(self):
        self.ledger.record_block(self.h,100,10000,160,self.shares)
        before=self.states()
        views=[{100:self.h,160:"z"*64},{100:self.h,160:self.h},
               {True:self.h,160:"ef"*32},{-1:self.h,160:"ef"*32},
               {100:self.h,161:"cd"*32,160:"ef"*32},
               {100:self.h,160:"EF"*32},{"100":self.h,160:"ef"*32}]
        for view in views:
            with self.subTest(view=view), self.assertRaises(ValueError):
                self.ledger.reconcile_chain(view,160)
            self.assertEqual(self.states(),before)

if __name__=="__main__":
    unittest.main()
