"""OFFLINE-only state machine tests; use fake tx hashes and no actual RPCs."""
import importlib.util
import json
import pathlib
import sqlite3
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location(
    "settlement_qa",ROOT/"services/pool_settlement/ledger.py")
mod=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)
Journal=mod.Journal
SettlementError=mod.SettlementError

# Known QA addresses, not private keys or production spend addresses.
A="YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA"
B="YnJPKnrv2fk6MdHkvvAxDbe1L3Dv7WgtrjPBHnP3NokU1Zri6a8da9SfoDiF9SpQxP4Xn18BT2bBNLnVtCPqXTvr1UTsca4Z4"
RECIPIENTS=((A,9_900_000),(B,100_000))
BLOCK="1"*64
TX1="2"*64
TX2="3"*64
SIGNED_META="beef"*30
BATCH="minedblock-0000001-payout"
OTHER="minedblock-0000002-payout"

def proofs(confirmations=22,*,txids=(TX1,),all_destinations=RECIPIENTS):
    return [mod.ConfirmedTx(
       txid=x,wallet_type="out",wallet_destinations=(tuple(all_destinations) if len(txids)==1 else (all_destinations[i],)),
       wallet_confirmations=confirmations,wallet_height=12,
       wallet_double_spend=False,daemon_in_pool=False,
       daemon_block_height=12,daemon_block_hash="f"*64,
       canonical_block_hash="f"*64,daemon_block_includes_tx=True)
       for i,x in enumerate(txids)]

class SettlementJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="frg-payout-journal-qa-")
        self.path=pathlib.Path(self.tmp.name)/"settlements.sqlite"
        self.j=Journal(self.path,qa_mode=True)
        self.j.credit_verified_mature_reward(BLOCK,RECIPIENTS,verified_canonical=True)
    def tearDown(self):
        self.j.close()
        self.tmp.cleanup()
    def prepared(self):
        self.assertEqual(self.j.reserve(BATCH,RECIPIENTS),"RESERVED")
        self.assertTrue(self.j.get_do_not_relay_parameters(BATCH)["do_not_relay"])
        self.j.record_signed(BATCH,[TX1],[SIGNED_META])
        self.j.record_relay_result(BATCH,acknowledged_txids=[TX1])

    def test_two_miner_exact_1pct_fee_wallet_and_unspent_credit(self):
        self.assertEqual(self.j.balance(A),(9_900_000,0))
        self.assertEqual(self.j.balance(B),(100_000,0))
        self.assertEqual(sum(v for _,v in RECIPIENTS),10_000_000)
        self.assertEqual(RECIPIENTS[1][1]*100,10_000_000)
    def test_canonical_reward_credit_requires_proof(self):
        with self.assertRaises(SettlementError):
            self.j.credit_verified_mature_reward("4"*64,RECIPIENTS)
    def test_reward_idempotent_same_hash_and_allocation(self):
        self.assertFalse(self.j.credit_verified_mature_reward(BLOCK,RECIPIENTS,verified_canonical=True))
        self.assertEqual(self.j.balance(B),(100_000,0))
    def test_reward_hash_cannot_replay_different_amounts(self):
        with self.assertRaises(SettlementError):
            self.j.credit_verified_mature_reward(BLOCK,((A,8_000_000),(B,2_000_000)),
                                                verified_canonical=True)
    def test_uint64_rejects_float_negative_and_bool(self):
        for x in (1.0,-1,True,(1<<64)):
            with self.assertRaises(SettlementError):mod.amount(x)
    def test_atomic_reservation_insufficient_balance(self):
        with self.assertRaises(SettlementError):
            self.j.reserve(BATCH,((A,9_900_000),(B,200_000)))
        self.assertEqual(self.j.balance(A),(9_900_000,0))
        self.assertEqual(self.j.balance(B),(100_000,0))
    def test_reserved_balances_not_double_spendable(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.assertEqual(self.j.balance(A),(0,9_900_000))
        self.assertEqual(self.j.balance(B),(0,100_000))
        with self.assertRaises(SettlementError):self.j.reserve(OTHER,RECIPIENTS)
        self.assertEqual(self.j.balance(A),(0,9_900_000))
    def test_same_intent_is_idempotent(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.assertEqual(self.j.reserve(BATCH,RECIPIENTS),"RESERVED")
        with self.assertRaises(SettlementError):
            self.j.reserve(BATCH,((A,9_900_000),))
    def test_cannot_create_transfer_after_signed(self):
        self.prepared()
        with self.assertRaises(SettlementError):self.j.get_do_not_relay_parameters(BATCH)
    def test_transfer_is_not_relayed_until_signed_metadata_persisted(self):
        self.j.reserve(BATCH,RECIPIENTS)
        with self.assertRaises(SettlementError):self.j.relay_metadata(BATCH)
        self.j.record_signed(BATCH,[TX1],[SIGNED_META])
        self.assertEqual(self.j.relay_metadata(BATCH),[(TX1,SIGNED_META)])
    def test_metadata_and_txids_are_immutable(self):
        self.prepared()
        with self.assertRaises(SettlementError):
            self.j.record_signed(BATCH,[TX2],[SIGNED_META])
    def test_record_signed_rollback_on_bad_metadata(self):
        self.j.reserve(BATCH,RECIPIENTS)
        with self.assertRaises(SettlementError):
            self.j.record_signed(BATCH,[TX1],["not-hex!"])
        self.assertEqual(self.j.snapshot(BATCH)["state"],"RESERVED")
    def test_txid_global_uniqueness(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.record_signed(BATCH,[TX1],[SIGNED_META])
        self.j.credit_verified_mature_reward("4"*64,RECIPIENTS,verified_canonical=True)
        self.j.reserve(OTHER,RECIPIENTS)
        with self.assertRaises(SettlementError):
            self.j.record_signed(OTHER,[TX1],[SIGNED_META])
    def test_repeated_broadcast_receipt_idempotent(self):
        self.prepared()
        self.assertFalse(self.j.record_relay_result(BATCH,acknowledged_txids=[TX1]))
        self.assertEqual(self.j.snapshot(BATCH)["state"],"BROADCAST")
    def test_relay_failure_never_marks_transmitted(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.record_signed(BATCH,[TX1],[SIGNED_META])
        with self.assertRaises(SettlementError):
            self.j.record_relay_result(BATCH,acknowledged_txids=[])
        self.assertEqual(self.j.snapshot(BATCH)["state"],"SIGNED")
    def test_confirmation_threshold(self):
        self.prepared()
        with self.assertRaises(SettlementError):
            self.j.record_observations(BATCH,proofs(confirmations=19))
        self.assertEqual(self.j.snapshot(BATCH)["state"],"BROADCAST")
        self.assertEqual(self.j.balance(A),(0,9_900_000))
    def test_reorg_canonical_mismatch(self):
        self.prepared()
        p=proofs()
        bad=[mod.ConfirmedTx(**{**p[0].__dict__,"canonical_block_hash":"e"*64})]
        with self.assertRaises(SettlementError):self.j.record_observations(BATCH,bad)
        self.assertEqual(self.j.snapshot(BATCH)["state"],"BROADCAST")
    def test_double_spend_and_mempool_reject(self):
        self.prepared()
        for key,val in [("wallet_double_spend",True),("daemon_in_pool",True),
                        ("daemon_block_includes_tx",False),("wallet_type","in")]:
            x=mod.ConfirmedTx(**{**proofs()[0].__dict__,key:val})
            with self.assertRaises(SettlementError):self.j.record_observations(BATCH,[x])
    def test_destination_amount_mismatch_refused(self):
        self.prepared()
        bad=mod.ConfirmedTx(**{**proofs()[0].__dict__,
                               "wallet_destinations":((A,10_000_000),)})
        with self.assertRaises(SettlementError):self.j.record_observations(BATCH,[bad])
    def test_missing_one_of_multiple_txids(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.record_signed(BATCH,[TX1,TX2],[SIGNED_META,SIGNED_META])
        self.j.record_relay_result(BATCH,acknowledged_txids=[TX1,TX2])
        with self.assertRaises(SettlementError):self.j.record_observations(BATCH,proofs())
        self.assertTrue(self.j.record_observations(BATCH,proofs(txids=(TX1,TX2))))
    def test_accepted_confirmation_and_settlement_exact_once(self):
        self.prepared()
        self.j.record_observations(BATCH,proofs())
        self.assertTrue(self.j.commit_observed(BATCH))
        self.assertFalse(self.j.commit_observed(BATCH))
        self.assertEqual(self.j.balance(A),(0,0))
        self.assertEqual(self.j.balance(B),(0,0))
        self.assertEqual(self.j.db.execute("SELECT COUNT(*) FROM payments").fetchone()[0],2)
    def test_crash_restart_after_reservation_does_not_release_hold(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.close()
        self.j=Journal(self.path,qa_mode=True)
        self.assertEqual(self.j.snapshot(BATCH)["state"],"RESERVED")
        self.assertEqual(self.j.balance(A),(0,9_900_000))
    def test_crash_restart_after_signed_preserves_relay_bytes(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.record_signed(BATCH,[TX1],[SIGNED_META])
        self.j.close()
        self.j=Journal(self.path,qa_mode=True)
        self.assertEqual(self.j.relay_metadata(BATCH),[(TX1,SIGNED_META)])
        with self.assertRaises(SettlementError):self.j.cancel_before_signing(BATCH)
    def test_crash_restart_after_confirmed_before_settle(self):
        self.prepared()
        self.j.record_observations(BATCH,proofs())
        self.j.close()
        self.j=Journal(self.path,qa_mode=True)
        self.assertTrue(self.j.commit_observed(BATCH))
        self.assertFalse(self.j.commit_observed(BATCH))
    def test_crash_restart_after_settlement_does_not_debit_twice(self):
        self.prepared();self.j.record_observations(BATCH,proofs())
        self.j.commit_observed(BATCH)
        self.j.close();self.j=Journal(self.path,qa_mode=True)
        self.assertFalse(self.j.commit_observed(BATCH))
        self.assertEqual(self.j.db.execute("SELECT COUNT(*) FROM payments").fetchone()[0],2)
    def test_cancel_only_unsigned_intent(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.assertTrue(self.j.cancel_before_signing(BATCH))
        self.assertFalse(self.j.cancel_before_signing(BATCH))
        self.assertEqual(self.j.balance(A),(9_900_000,0))
    def test_default_production_journal_cannot_mint_or_settle(self):
        live_path=pathlib.Path(self.tmp.name)/"production-hold.sqlite"
        live=Journal(live_path)
        try:
            with self.assertRaises(SettlementError):
                live.credit_verified_mature_reward("f"*64,RECIPIENTS,verified_canonical=True)
            with self.assertRaises(SettlementError):
                live.commit_observed(BATCH)
        finally:live.close()

    def test_reject_reuse_of_qa_database_as_production_journal(self):
        with self.assertRaises(SettlementError):
            Journal(self.path)

    def test_partial_split_relay_ack_cannot_mark_entire_batch_broadcast(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.record_signed(BATCH,[TX1,TX2],[SIGNED_META,SIGNED_META])
        with self.assertRaises(SettlementError):
            self.j.record_relay_result(BATCH,acknowledged_txids=[TX1])
        self.assertEqual(self.j.snapshot(BATCH)["state"],"SIGNED")
        self.assertTrue(self.j.record_relay_result(BATCH,acknowledged_txids=[TX1,TX2]))

    def test_invalid_chain_identity_refused(self):
        with self.assertRaises(SettlementError):Journal(self.path,genesis="0"*64)
    def test_cannot_settle_unverified_wallet_ack(self):
        self.prepared()
        with self.assertRaises(SettlementError):self.j.commit_observed(BATCH)
    def test_reject_duplicate_address_and_invalid_precision(self):
        for dest in (((A,1),(A,2)),((A,0),),((A,1.0),)):
            with self.assertRaises(SettlementError):mod.validate_destinations(dest)
    def test_signed_metadata_and_txids_survive_wallet_RPC_unknown_response(self):
        self.j.reserve(BATCH,RECIPIENTS)
        self.j.record_signed(BATCH,[TX1],[SIGNED_META])
        self.j.close();self.j=Journal(self.path,qa_mode=True)
        self.assertEqual(self.j.snapshot(BATCH)["state"],"SIGNED")
        self.assertEqual(self.j.relay_metadata(BATCH),[(TX1,SIGNED_META)])

if __name__=="__main__":unittest.main()
