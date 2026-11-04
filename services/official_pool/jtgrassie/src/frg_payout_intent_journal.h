/* ForgeCoin native pool durable payout INTENT ledger — research-only.
 *
 * This is deliberately NOT a payout sender or a settlement engine.
 * Records prove only a locally persisted intent / ambiguous-wallet state.
 * NO function in this file transfers funds, debits miner balances,
 * authorizes wallet RPC, or allows an intent to be deleted or settled.
 *
 * Issue #210: Before network-side signing, record a canonical payout batch
 * with exactly-once source accounting, fee limits and independently verified
 * chain anchors. Those final controls are still NOT implemented here.
 */
#ifndef FRG_PAYOUT_INTENT_JOURNAL_H
#define FRG_PAYOUT_INTENT_JOURNAL_H

#include <lmdb.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define FRG_PAYOUT_INTENT_DB "frg_payout_intents_v1"
#define FRG_PAYOUT_INTENT_VERSION UINT32_C(1)
#define FRG_PAYOUT_INTENT_PREPARED UINT32_C(1)
#define FRG_PAYOUT_INTENT_AMBIGUOUS UINT32_C(2)
#define FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED UINT32_C(3)
#define FRG_PAYOUT_INTENT_ID_LENGTH 32

/* A 32-byte opaque key identifies the immutable logical batch.
 * The 32-byte manifest hash must bind sorted recipients, amounts, source
 * reward IDs, fee budget, chain identity, and lock/reorg policy. This library
 * CANNOT validate its contents: upstream review/commitment remains required.
 * The versioned record contains NO wallet address, password, private key or
 * seed. Its fixed layout is 128 bytes on the supported 64-bit Linux targets.
 */
typedef struct frg_payout_intent_record
{
    uint32_t version;
    uint32_t state;
    uint64_t amount_atomic;
    uint64_t max_fee_atomic;
    uint64_t anchor_height;
    uint8_t manifest_sha256[32];
    uint8_t anchor_hash[32];
    uint8_t candidate_txid[32];
} frg_payout_intent_record_t;

_Static_assert(sizeof(frg_payout_intent_record_t) == 128,
               "FRG payout intent v1 on-disk record layout changed");

static inline bool
frg_payout_bytes_nonzero(const uint8_t *ptr, size_t count)
{
    if (!ptr) return false;
    uint8_t bits = 0;
    for (size_t i = 0; i < count; ++i) bits |= ptr[i];
    return bits != 0;
}

/* Open only inside a writable LMDB transaction; caller MUST commit it.
 * Never use MDB_NOSYNC or MDB_NOMETASYNC for a payout journal.
 */
static inline int
frg_payout_intent_open(MDB_txn *txn, MDB_dbi *db)
{
    if (!txn || !db) return EINVAL;
    return mdb_dbi_open(txn, FRG_PAYOUT_INTENT_DB, MDB_CREATE, db);
}

static inline int
frg_payout_intent_read(MDB_txn *txn, MDB_dbi db,
                       const uint8_t batch_id[FRG_PAYOUT_INTENT_ID_LENGTH],
                       frg_payout_intent_record_t *out)
{
    if (!txn || !batch_id || !out ||
        !frg_payout_bytes_nonzero(batch_id, FRG_PAYOUT_INTENT_ID_LENGTH))
        return EINVAL;
    memset(out, 0, sizeof(*out));
    MDB_val key = { FRG_PAYOUT_INTENT_ID_LENGTH, (void *)batch_id };
    MDB_val val = { 0, NULL };
    int rc = mdb_get(txn, db, &key, &val);
    if (rc) return rc;
    if (val.mv_size != sizeof(*out) || !val.mv_data)
        return MDB_BAD_VALSIZE;
    frg_payout_intent_record_t record;
    memcpy(&record, val.mv_data, sizeof(record));
    if (record.version != FRG_PAYOUT_INTENT_VERSION ||
        (record.state != FRG_PAYOUT_INTENT_PREPARED &&
         record.state != FRG_PAYOUT_INTENT_AMBIGUOUS &&
         record.state != FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED) ||
        !record.amount_atomic ||
        !frg_payout_bytes_nonzero(record.manifest_sha256, 32) ||
        !frg_payout_bytes_nonzero(record.anchor_hash, 32) ||
        (record.state == FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED &&
         !frg_payout_bytes_nonzero(record.candidate_txid, 32)) ||
        (record.state != FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED &&
         frg_payout_bytes_nonzero(record.candidate_txid, 32)))
        return EPROTO;
    *out = record;
    return 0;
}

/* Write a pre-send intent with no mutable secrets. A duplicate key MUST
 * fail, even if the requested fields match. Caller MUST commit BEFORE
 * any external wallet RPC call. A successful mdb_put is NOT persistence
 * until the transaction is committed to durable storage.
 */
static inline int
frg_payout_intent_prepare(MDB_txn *txn, MDB_dbi db,
                          const uint8_t batch_id[32],
                          const uint8_t manifest_sha256[32],
                          const uint8_t anchor_hash[32],
                          uint64_t anchor_height,
                          uint64_t amount_atomic, uint64_t max_fee_atomic)
{
    if (!txn || !batch_id || !manifest_sha256 || !anchor_hash ||
        !frg_payout_bytes_nonzero(batch_id, 32) ||
        !frg_payout_bytes_nonzero(manifest_sha256, 32) ||
        !frg_payout_bytes_nonzero(anchor_hash, 32) ||
        !amount_atomic || max_fee_atomic > amount_atomic)
        return EINVAL;
    frg_payout_intent_record_t record;
    memset(&record, 0, sizeof(record));
    record.version = FRG_PAYOUT_INTENT_VERSION;
    record.state = FRG_PAYOUT_INTENT_PREPARED;
    record.amount_atomic = amount_atomic;
    record.max_fee_atomic = max_fee_atomic;
    record.anchor_height = anchor_height;
    memcpy(record.manifest_sha256, manifest_sha256, 32);
    memcpy(record.anchor_hash, anchor_hash, 32);
    MDB_val key = { 32, (void *)batch_id };
    MDB_val val = { sizeof(record), &record };
    return mdb_put(txn, db, &key, &val, MDB_NOOVERWRITE);
}

/* Wallet failures, timeouts and process recovery are always ambiguous.
 * Mark and retain the intent. NO automatic retry is permitted.
 * This does not assert a real transaction has been sent.
 */
static inline int
frg_payout_intent_mark_ambiguous(MDB_txn *txn, MDB_dbi db,
                                const uint8_t batch_id[32])
{
    if (!txn) return EINVAL;
    frg_payout_intent_record_t record;
    int rc = frg_payout_intent_read(txn, db, batch_id, &record);
    if (rc) return rc;
    if (record.state != FRG_PAYOUT_INTENT_PREPARED)
        return EALREADY;
    record.state = FRG_PAYOUT_INTENT_AMBIGUOUS;
    MDB_val key = { 32, (void *)batch_id };
    MDB_val val = { sizeof(record), &record };
    return mdb_put(txn, db, &key, &val, 0);
}

/* Store an externally reported transaction ID as UNVERIFIED evidence, not
 * as settlement. Verified canonical chain/output reconciliation must be a
 * separately reviewed module; this API cannot approve or debit a payment.
 */
static inline int
frg_payout_intent_note_candidate(MDB_txn *txn, MDB_dbi db,
                                 const uint8_t batch_id[32],
                                 const uint8_t candidate_txid[32])
{
    if (!txn || !candidate_txid ||
        !frg_payout_bytes_nonzero(candidate_txid, 32))
        return EINVAL;
    frg_payout_intent_record_t record;
    int rc = frg_payout_intent_read(txn, db, batch_id, &record);
    if (rc) return rc;
    if (record.state != FRG_PAYOUT_INTENT_PREPARED &&
        record.state != FRG_PAYOUT_INTENT_AMBIGUOUS)
        return EALREADY;
    record.state = FRG_PAYOUT_INTENT_CANDIDATE_UNVERIFIED;
    memcpy(record.candidate_txid, candidate_txid, 32);
    MDB_val key = { 32, (void *)batch_id };
    MDB_val val = { sizeof(record), &record };
    return mdb_put(txn, db, &key, &val, 0);
}

/* Always fail closed when ANY intent exists: none of these states is proof
 * of final payment. A damaged entry must never be treated as an empty DB.
 * No auto-clear or "settled" state is provided until #210 is complete.
 */
static inline int
frg_payout_intent_held(MDB_txn *txn, MDB_dbi db, bool *held)
{
    if (!txn || !held) return EINVAL;
    *held = true;
    MDB_cursor *cursor = NULL;
    int rc = mdb_cursor_open(txn, db, &cursor);
    if (rc) return rc;
    MDB_val key = { 0, NULL }, val = { 0, NULL };
    rc = mdb_cursor_get(cursor, &key, &val, MDB_FIRST);
    if (rc == MDB_NOTFOUND) {
        *held = false;
        rc = 0;
    } else if (rc == 0) {
        if (key.mv_size != 32 || !key.mv_data ||
            !frg_payout_bytes_nonzero(key.mv_data, 32) ||
            val.mv_size != sizeof(frg_payout_intent_record_t) ||
            !val.mv_data) {
            rc = MDB_BAD_VALSIZE;
        } else {
            frg_payout_intent_record_t record;
            rc = frg_payout_intent_read(txn, db, key.mv_data, &record);
        }
    }
    mdb_cursor_close(cursor);
    return rc;
}

#endif
