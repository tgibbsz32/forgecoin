/* ForgeCoin local credited-block source commitment (RESEARCH / NO SENDER).
 *
 * Derives the payout source digest directly from the official pool's LMDB
 * blocks database. It does not trust a supplied arbitrary 32-byte digest.
 *
 * IMPORTANT: A saved, unlocked pool block is NOT independent proof of
 * canonical chain membership, correct PPLNS credit, available wallet balance
 * or spendable reward. This is only a deterministic local ledger fingerprint.
 * A payout executor still requires fresh native canonical-header/maturity
 * evidence, a validated recipient list and balance/fee reconciliation.
 */
#ifndef FRG_PAYOUT_CREDITED_SOURCES_H
#define FRG_PAYOUT_CREDITED_SOURCES_H

#include <errno.h>
#include <limits.h>
#include <lmdb.h>
#include <openssl/evp.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "frg_payout_batch_reservation.h"
#include "frg_credited_ledger_scan.h"

#define FRG_PAYOUT_REWARD_MATURITY UINT64_C(60)

static inline int frg_source_hex_nibble(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static inline bool frg_source_hash_bytes(const char hex[64], uint8_t bytes[32])
{
    if (!hex || !bytes) return false;
    for (size_t i = 0; i < 32; ++i) {
        int hi = frg_source_hex_nibble(hex[i * 2]);
        int lo = frg_source_hex_nibble(hex[i * 2 + 1]);
        if (hi < 0 || lo < 0) return false;
        bytes[i] = (uint8_t)((hi << 4) | lo);
    }
    return true;
}

/* Must scan every row (including locked/orphaned) under a live pool LMDB
 * transaction. Only UNIQUE unlocked heights contribute to the source set.
 * Reversed/non-numeric height ordering fails closed: production block DB
 * uses compare_uint64. The source digest is independent of anchor height,
 * so changing only the tip cannot change a batch's source identity.
 *
 * Invalid rows, duplicate unlocked heights, zero rewards, unconfirmed
 * unlocked blocks, corrupted hashes, overflows and an empty eligible source
 * set return errors. Nothing is written or authorized by this function.
 */
static inline int
frg_payout_credited_sources_digest(
    MDB_txn *txn, MDB_dbi db_blocks,
    const uint8_t chain_uuid[16], uint64_t anchor_height,
    uint8_t out_sha256[32], uint64_t *out_count,
    uint64_t *out_reward_atomic)
{
    if (!txn || !chain_uuid || !out_sha256 || !out_count ||
        !out_reward_atomic ||
        memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16) != 0 ||
        anchor_height < FRG_PAYOUT_REWARD_MATURITY)
        return EINVAL;
    MDB_cursor *cursor = NULL;
    int rc = mdb_cursor_open(txn, db_blocks, &cursor);
    if (rc) return rc;

    EVP_MD_CTX *digest = EVP_MD_CTX_new();
    if (!digest) {
        mdb_cursor_close(cursor);
        return ENOMEM;
    }

    static const char domain[] = "FRG.PAYOUT.CREDITED.SOURCES.V1";
    bool ok = EVP_DigestInit_ex(digest, EVP_sha256(), NULL) == 1 &&
        frg_payout_digest_write(digest, domain, sizeof domain - 1) &&
        frg_payout_digest_write(digest, chain_uuid, 16);
    rc = ok ? 0 : EIO;
    uint64_t count = 0, reward_sum = 0, previous_height = 0;
    MDB_val key = {0, NULL}, val = {0, NULL};
    MDB_cursor_op op = MDB_FIRST;
    while (rc == 0 && (rc = mdb_cursor_get(cursor, &key, &val, op)) == 0) {
        op = MDB_NEXT;
        if (!key.mv_data || !val.mv_data ||
            key.mv_size != sizeof(uint64_t) ||
            val.mv_size != sizeof(frg_history_saved_t)) {
            rc = EPROTO;
            break;
        }
        frg_history_saved_t block = {0};
        uint64_t key_height = 0;
        memcpy(&block, val.mv_data, sizeof block);
        memcpy(&key_height, key.mv_data, sizeof key_height);
        uint8_t hash[32] = {0}, parent[32] = {0};
        if (key_height != block.height ||
            block.status > FRG_HISTORY_ORPHANED ||
            !frg_source_hash_bytes(block.hash, hash) ||
            !frg_source_hash_bytes(block.prev_hash, parent)) {
            rc = EPROTO;
            break;
        }
        if (block.status != FRG_HISTORY_UNLOCKED) continue;

        if (!block.height || block.height <= previous_height ||
            !block.difficulty || !block.reward ||
            block.height > anchor_height ||
            anchor_height - block.height < FRG_PAYOUT_REWARD_MATURITY ||
            count == UINT64_MAX || reward_sum > UINT64_MAX - block.reward) {
            rc = EPROTO;
            break;
        }
        if (!frg_payout_digest_u64(digest, block.height) ||
            !frg_payout_digest_write(digest, hash, 32) ||
            !frg_payout_digest_write(digest, parent, 32) ||
            !frg_payout_digest_u64(digest, block.difficulty) ||
            !frg_payout_digest_u64(digest, block.reward)) {
            rc = EIO;
            break;
        }
        previous_height = block.height;
        count++;
        reward_sum += block.reward;
    }
    if (rc == MDB_NOTFOUND) rc = 0;
    if (rc == 0 && count == 0) rc = ENODATA;

    uint8_t result[32] = {0};
    unsigned len = 0;
    if (!rc && (!frg_payout_digest_u64(digest, count) ||
                EVP_DigestFinal_ex(digest, result, &len) != 1 ||
                len != 32))
        rc = EIO;
    EVP_MD_CTX_free(digest);
    mdb_cursor_close(cursor);
    if (rc) return rc;

    memcpy(out_sha256, result, sizeof result);
    *out_count = count;
    *out_reward_atomic = reward_sum;
    return 0;
}

/* New source-bound reservation path: derive digest and journal the intent
 * inside the SAME write transaction. No TOCTOU between a separate readonly
 * source scan and an external writer changing block credit records.
 *
 * The caller must independently establish canonical chain/maturity,
 * balances, native address validity and fee constraints before any wallet
 * execution; this function is NOT authorization to call wallet RPC.
 */
static inline int
frg_payout_batch_reserve_from_credited_lmdb(
    MDB_env *env, MDB_dbi blocks_db, MDB_dbi intent_db,
    const uint8_t chain_uuid[16], const uint8_t anchor_hash[32],
    uint64_t anchor_height, const frg_payout_recipient_t *recipients,
    size_t count, uint64_t max_fee_atomic,
    uint8_t out_batch_id[32], uint8_t out_manifest_sha256[32],
    uint64_t *out_total_atomic)
{
    if (!env || !chain_uuid || !anchor_hash || !recipients ||
        !out_batch_id || !out_manifest_sha256 || !out_total_atomic ||
        out_batch_id == out_manifest_sha256 ||
        memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16) != 0 ||
        !frg_payout_bytes_nonzero(anchor_hash, 32))
        return EINVAL;

    unsigned flags = 0;
    int rc = mdb_env_get_flags(env, &flags);
    if (rc) return rc;
    if (flags & (MDB_NOSYNC | MDB_NOMETASYNC | MDB_WRITEMAP |
                 MDB_MAPASYNC))
        return EACCES;

    MDB_txn *txn = NULL;
    rc = mdb_txn_begin(env, NULL, 0, &txn);
    if (rc) return rc;

    bool held = true;
    rc = frg_payout_intent_held(txn, intent_db, &held);
    if (rc || held) {
        mdb_txn_abort(txn);
        return rc ? rc : EBUSY;
    }

    uint8_t sources[32] = {0};
    uint64_t source_count = 0, source_rewards = 0;
    rc = frg_payout_credited_sources_digest(
        txn, blocks_db, chain_uuid, anchor_height, sources,
        &source_count, &source_rewards);
    if (rc) {
        mdb_txn_abort(txn);
        return rc;
    }
    /* A source-record total is NOT the available balance and does not
     * prove that PPLNS fees and previously paid credits reconcile. */
    (void)source_count;
    (void)source_rewards;

    uint8_t batch_id[32] = {0}, manifest[32] = {0};
    uint64_t amount = 0;
    rc = frg_payout_manifest_hash(
        chain_uuid, sources, anchor_hash, anchor_height, recipients, count,
        max_fee_atomic, batch_id, manifest, &amount);
    if (rc) {
        mdb_txn_abort(txn);
        return rc;
    }

    rc = frg_payout_intent_prepare(
        txn, intent_db, batch_id, manifest, anchor_hash, anchor_height,
        amount, max_fee_atomic);
    if (rc) {
        mdb_txn_abort(txn);
        return rc;
    }
    rc = mdb_txn_commit(txn);
    if (rc) return rc;

    rc = mdb_env_sync(env, 1);
    if (rc) return rc;
    rc = mdb_txn_begin(env, NULL, MDB_RDONLY, &txn);
    if (rc) return rc;
    frg_payout_intent_record_t record;
    rc = frg_payout_intent_read(txn, intent_db, batch_id, &record);
    if (!rc &&
        (record.state != FRG_PAYOUT_INTENT_PREPARED ||
         record.amount_atomic != amount ||
         record.max_fee_atomic != max_fee_atomic ||
         record.anchor_height != anchor_height ||
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

#endif /* FRG_PAYOUT_CREDITED_SOURCES_H */
