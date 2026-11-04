/* ForgeCoin canonical payout batch reservation (OFFLINE / NO WALLET RPC).
 *
 * A reviewed future payout coordinator must prove every credited source,
 * chain anchor, confirmation depth, payout address and fee budget BEFORE
 * calling this function. We bind the existing deterministic manifest to
 * the durable LMDB intent journal in ONE serialized write transaction.
 *
 * This module never calls a wallet, debits balances, clears a journal,
 * marks a batch settled or enables FRG_TESTED_WALLET_PAYOUTS.
 *
 * All prepared/ambiguous/candidate states stay held across restart.
 */
#ifndef FRG_PAYOUT_BATCH_RESERVATION_H
#define FRG_PAYOUT_BATCH_RESERVATION_H

#include <errno.h>
#include <lmdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "frg_payout_manifest.h"
#include "frg_payout_intent_journal.h"

/* Frozen 20261026 MAINNET UUID: bd936359-09e4-4fdb-8ec0-12fa9d6ef090.
 * Testnet/stagenet batches require a separately reviewed domain.
 */
static const uint8_t FRG_PAYOUT_FROZEN_CHAIN_ID[16] = {
    0xbd, 0x93, 0x63, 0x59, 0x09, 0xe4, 0x4f, 0xdb,
    0x8e, 0xc0, 0x12, 0xfa, 0x9d, 0x6e, 0xf0, 0x90
};

/* Caller must open the journal database in a committed LMDB transaction
 * before using its db handle. Output parameters are changed ONLY after a
 * committed and verified intent survives a full synchronous flush.
 *
 * Holding ANY earlier intent, including an unrelated source-credit batch
 * or a malformed journal record, rejects all new reservations. This is
 * intentional until a separately reviewed, canonical settlement path can
 * prove each earlier payment and release its hold without replays.
 */
static inline int
frg_payout_batch_reserve(
    MDB_env *env, MDB_dbi intent_db,
    const uint8_t chain_uuid[16],
    const uint8_t credited_sources_sha256[32],
    const uint8_t anchor_hash[32], uint64_t anchor_height,
    const frg_payout_recipient_t *recipients, size_t count,
    uint64_t max_fee_atomic,
    uint8_t out_batch_id[32],
    uint8_t out_manifest_sha256[32],
    uint64_t *out_total_atomic)
{
    if (!env || !chain_uuid || !credited_sources_sha256 ||
        !anchor_hash || !recipients || !out_batch_id ||
        !out_manifest_sha256 || !out_total_atomic ||
        memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16) != 0)
        return EINVAL;

    /* Unsafe LMDB modes cannot constitute durable pre-send evidence. */
    unsigned flags = 0;
    int rc = mdb_env_get_flags(env, &flags);
    if (rc) return rc;
    if (flags & (MDB_NOSYNC | MDB_NOMETASYNC | MDB_WRITEMAP |
                 MDB_MAPASYNC))
        return EACCES;

    uint8_t batch_id[32] = {0};
    uint8_t manifest[32] = {0};
    uint64_t amount = 0;
    rc = frg_payout_manifest_hash(
        chain_uuid, credited_sources_sha256, anchor_hash, anchor_height,
        recipients, count, max_fee_atomic, batch_id, manifest, &amount);
    if (rc) return rc;

    MDB_txn *txn = NULL;
    rc = mdb_txn_begin(env, NULL, 0, &txn);
    if (rc) return rc;

    /* Serializes the global hold check and the put with every writer.
     * Do not trust a separate prior readonly check (TOCTOU).
     */
    bool held = true;
    rc = frg_payout_intent_held(txn, intent_db, &held);
    if (rc || held)
    {
        mdb_txn_abort(txn);
        return rc ? rc : EBUSY;
    }

    rc = frg_payout_intent_prepare(txn, intent_db, batch_id, manifest,
                                   anchor_hash, anchor_height, amount,
                                   max_fee_atomic);
    if (rc)
    {
        mdb_txn_abort(txn);
        return rc;
    }
    rc = mdb_txn_commit(txn);
    if (rc) return rc; /* LMDB owns txn after commit attempt. */

    /* On a flush or post-write verification error, do NOT clear the
     * intent or return an approval to call a wallet. A future process
     * will see the held record and require manual reconciliation.
     */
    rc = mdb_env_sync(env, 1);
    if (rc) return rc;
    rc = mdb_txn_begin(env, NULL, MDB_RDONLY, &txn);
    if (rc) return rc;

    frg_payout_intent_record_t record;
    rc = frg_payout_intent_read(txn, intent_db, batch_id, &record);
    if (!rc &&
        (record.state != FRG_PAYOUT_INTENT_PREPARED ||
         record.anchor_height != anchor_height ||
         record.amount_atomic != amount ||
         record.max_fee_atomic != max_fee_atomic ||
         memcmp(record.anchor_hash, anchor_hash, 32) ||
         memcmp(record.manifest_sha256, manifest, 32)))
        rc = EPROTO;
    mdb_txn_abort(txn);
    if (rc) return rc;

    memcpy(out_batch_id, batch_id, 32);
    memcpy(out_manifest_sha256, manifest, 32);
    *out_total_atomic = amount;
    return 0;
}

#endif /* FRG_PAYOUT_BATCH_RESERVATION_H */
