/* ForgeCoin two-observer historical header comparison, OFFLINE ONLY.
 *
 * Consumes two already-collected, same-tip JSON-C daemon snapshots and
 * checks EVERY eligible unlocked LMDB credit against each snapshot.
 * Proof inputs are NOT authenticated by this module. Two responses could
 * originate from one compromised process or fabricated peers. Success is
 * a provisional consistency check, NEVER canonical consensus proof, wallet
 * signing approval, or payout authorization.
 *
 * Expected snapshot format:
 * { "anchor": {native daemon header fields...},
 *   "credits": [native daemon header at each unlocked credited height...] }
 * Credits are sorted by ascending pool block height and must be complete.
 * Snapshot collection, source authentication and exact chain/fork pinning
 * must be implemented as separate, independently reviewed safeguards.
 */
#ifndef FRG_PAYOUT_HEADER_CROSSCHECK_H
#define FRG_PAYOUT_HEADER_CROSSCHECK_H

#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <lmdb.h>
#include <json-c/json.h>

#include "frg_payout_credited_sources.h"

#define FRG_PAYOUT_CROSSCHECK_MAX_CREDITS 4096u

static inline bool
frg_payout_header_anchor_matches(const struct json_object *header,
                                 uint64_t expected_height,
                                 const uint8_t expected_hash[32])
{
    struct json_object *height = NULL, *difficulty = NULL;
    struct json_object *timestamp = NULL, *reward = NULL;
    struct json_object *hash = NULL, *parent = NULL, *orphan = NULL;
    if (!header || !expected_hash || expected_height > INT64_MAX ||
        !frg_payout_bytes_nonzero(expected_hash, 32) ||
        !frg_json_member(header, "height", json_type_int, &height) ||
        !frg_json_member(header, "difficulty", json_type_int, &difficulty) ||
        !frg_json_member(header, "timestamp", json_type_int, &timestamp) ||
        !frg_json_member(header, "reward", json_type_int, &reward) ||
        !frg_json_member(header, "hash", json_type_string, &hash) ||
        !frg_json_member(header, "prev_hash", json_type_string, &parent) ||
        !frg_json_member(header, "orphan_status", json_type_boolean, &orphan))
        return false;
    if (json_object_get_int64(height) != (int64_t)expected_height ||
        json_object_get_int64(difficulty) <= 0 ||
        json_object_get_int64(timestamp) < 0 ||
        json_object_get_int64(reward) < 0 ||
        json_object_get_boolean(orphan))
        return false;
    const char *hash_text = json_object_get_string(hash);
    const char *parent_text = json_object_get_string(parent);
    uint8_t actual[32] = {0}, parent_bytes[32] = {0};
    return frg_hex_hash64(hash_text) && frg_hex_hash64(parent_text) &&
        frg_source_hash_bytes(hash_text, actual) &&
        frg_source_hash_bytes(parent_text, parent_bytes) &&
        frg_payout_bytes_nonzero(parent_bytes, 32) &&
        memcmp(actual, expected_hash, 32) == 0;
}

static inline bool
frg_payout_anchor_agreement(const struct json_object *a,
                             const struct json_object *b)
{
    if (!a || !b) return false;
    /* Exact common fields must match on both observers, regardless of
     * optional daemon-specific fields or JSON member insertion order.
     */
    const char *keys[] = {"height", "difficulty", "timestamp",
                          "reward", "hash", "prev_hash", "orphan_status"};
    for (size_t i = 0; i < sizeof keys / sizeof keys[0]; i++) {
        struct json_object *aa = NULL, *bb = NULL;
        if (!json_object_object_get_ex((struct json_object *)a, keys[i], &aa) ||
            !json_object_object_get_ex((struct json_object *)b, keys[i], &bb) ||
            !aa || !bb || !json_object_equal(aa, bb))
            return false;
    }
    return true;
}

/* Evaluates two snapshot sets against a consistent read/write LMDB
 * transaction. Caller owns evidence objects and transaction.
 *
 * Returns 0 only when every unlocked credit matches BOTH observers, both
 * agree on the exact full anchor metadata, all structural blocks pass
 * source-digest screening, source sets are complete and source maturity
 * is met. EAGAIN indicates incomplete/conflicting/untrusted observations;
 * EPROTO indicates corrupted local saved pool state. All outputs remain
 * unchanged on any failure, including database or RPC evidence error.
 */
static inline int
frg_payout_credited_headers_crosscheck(
    MDB_txn *txn, MDB_dbi blocks_db, const uint8_t chain_uuid[16],
    uint64_t anchor_height, const uint8_t anchor_hash[32],
    const struct json_object *observer_a,
    const struct json_object *observer_b,
    uint8_t out_sources_sha256[32],
    uint64_t *out_source_count, uint64_t *out_total_rewards)
{
    if (!txn || !chain_uuid || !anchor_hash || !observer_a ||
        !observer_b || observer_a == observer_b ||
        !out_sources_sha256 || !out_source_count || !out_total_rewards ||
        memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16) != 0 ||
        anchor_height < FRG_PAYOUT_REWARD_MATURITY ||
        anchor_height > INT64_MAX)
        return EINVAL;

    struct json_object *anchor_a = NULL, *anchor_b = NULL;
    struct json_object *credits_a = NULL, *credits_b = NULL;
    if (!frg_json_member(observer_a, "anchor", json_type_object, &anchor_a) ||
        !frg_json_member(observer_b, "anchor", json_type_object, &anchor_b) ||
        !frg_json_member(observer_a, "credits", json_type_array, &credits_a) ||
        !frg_json_member(observer_b, "credits", json_type_array, &credits_b) ||
        !frg_payout_header_anchor_matches(anchor_a, anchor_height, anchor_hash) ||
        !frg_payout_header_anchor_matches(anchor_b, anchor_height, anchor_hash) ||
        !frg_payout_anchor_agreement(anchor_a, anchor_b))
        return EAGAIN;

    uint8_t digest[32] = {0};
    uint64_t total = 0, rewards = 0;
    int rc = frg_payout_credited_sources_digest(
        txn, blocks_db, chain_uuid, anchor_height, digest, &total, &rewards);
    if (rc) return rc;
    if (total > FRG_PAYOUT_CROSSCHECK_MAX_CREDITS ||
        json_object_array_length(credits_a) != total ||
        json_object_array_length(credits_b) != total)
        return EAGAIN;

    MDB_cursor *cursor = NULL;
    rc = mdb_cursor_open(txn, blocks_db, &cursor);
    if (rc) return rc;
    MDB_val key = {0, NULL}, val = {0, NULL};
    MDB_cursor_op op = MDB_FIRST;
    size_t index = 0;
    while ((rc = mdb_cursor_get(cursor, &key, &val, op)) == 0) {
        op = MDB_NEXT;
        /* The digest function just validated every row in the same
         * transaction. Re-check size to avoid ever dereferencing corrupt
         * memory if an incompatible database handle is supplied.
         */
        if (!key.mv_data || !val.mv_data ||
            key.mv_size != sizeof(uint64_t) ||
            val.mv_size != sizeof(frg_history_saved_t)) {
            rc = EPROTO;
            break;
        }
        frg_history_saved_t item = {0};
        memcpy(&item, val.mv_data, sizeof item);
        if (item.status != FRG_HISTORY_UNLOCKED) continue;
        if (index >= total) {
            rc = EPROTO;
            break;
        }
        const struct json_object *a = json_object_array_get_idx(
            credits_a, (size_t)index);
        const struct json_object *b = json_object_array_get_idx(
            credits_b, (size_t)index);
        if (frg_history_compare(a, item.height, item.hash, item.prev_hash,
                                item.difficulty, item.reward) != FRG_HISTORY_MATCH ||
            frg_history_compare(b, item.height, item.hash, item.prev_hash,
                                item.difficulty, item.reward) != FRG_HISTORY_MATCH) {
            rc = EAGAIN;
            break;
        }
        index++;
    }
    mdb_cursor_close(cursor);
    if (rc == MDB_NOTFOUND) rc = 0;
    if (rc) return rc;
    if (index != total) return EPROTO;
    memcpy(out_sources_sha256, digest, 32);
    *out_source_count = total;
    *out_total_rewards = rewards;
    return 0;
}

/* Reserve an immutable batch ONLY when two supplied snapshots match every
 * locally credited block inside the same serial LMDB transaction. This
 * prevents local TOCTOU against the pool writer, but snapshots are UNTRUSTED
 * until collected and authenticated outside this module.
 *
 * A successful reservation is an offline held intent, NEVER permission to
 * broadcast a wallet transfer. Earlier research reservation APIs remain
 * for test fixtures, not for the eventual reviewed production sender.
 */
static inline int
frg_payout_batch_reserve_crosschecked(
    MDB_env *env, MDB_dbi blocks_db, MDB_dbi intent_db,
    const uint8_t chain_uuid[16], uint64_t anchor_height,
    const uint8_t anchor_hash[32],
    const struct json_object *observer_a,
    const struct json_object *observer_b,
    const frg_payout_recipient_t *recipients, size_t recipient_count,
    uint64_t max_fee_atomic,
    uint8_t out_batch_id[32], uint8_t out_manifest_sha256[32],
    uint64_t *out_total_atomic)
{
    if (!env || !chain_uuid || !anchor_hash || !observer_a ||
        !observer_b || !recipients || !out_batch_id ||
        !out_manifest_sha256 || !out_total_atomic ||
        out_batch_id == out_manifest_sha256 ||
        memcmp(chain_uuid, FRG_PAYOUT_FROZEN_CHAIN_ID, 16) != 0)
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
    uint64_t count = 0, rewards = 0;
    rc = frg_payout_credited_headers_crosscheck(
        txn, blocks_db, chain_uuid, anchor_height, anchor_hash,
        observer_a, observer_b, sources, &count, &rewards);
    if (rc) {
        mdb_txn_abort(txn);
        return rc;
    }
    /* Count and full coinbase rewards are NOT spendable miner balances. */
    (void)count;
    (void)rewards;

    uint8_t batch[32] = {0}, manifest[32] = {0};
    uint64_t amount = 0;
    rc = frg_payout_manifest_hash(
        chain_uuid, sources, anchor_hash, anchor_height, recipients,
        recipient_count, max_fee_atomic, batch, manifest, &amount);
    if (rc) {
        mdb_txn_abort(txn);
        return rc;
    }
    rc = frg_payout_intent_prepare(
        txn, intent_db, batch, manifest, anchor_hash, anchor_height,
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
    rc = frg_payout_intent_read(txn, intent_db, batch, &record);
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

    memcpy(out_batch_id, batch, 32);
    memcpy(out_manifest_sha256, manifest, 32);
    *out_total_atomic = amount;
    return 0;
}

#endif /* FRG_PAYOUT_HEADER_CROSSCHECK_H */
